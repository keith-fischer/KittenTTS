"""
LLM Agent: prompts LM Studio for script lines, transforms response to Character|speed|text,
and sends them to the KittenTTS speech server for playback.

Requires:
  - LM Studio running with a model loaded (lms server start or Developer tab)
  - Speech server running (python server.py)

Usage:
  python llm_agent.py "Write a short drama between Leo and Bella"
  python llm_agent.py --prompt "3-line horror scene" --model my-model
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import utils
try:
    import requests
except ImportError:
    requests = None

from client import speak


# ANSI escape codes for colors
class Colors:
    GREEN = '\033[92m'
    RESET = '\033[0m'


def send_lines_background_speech(base_url: str, lines: list[str],script_path=None) -> None:
    """Fire-and-forget: send lines to speech server in a background thread."""
    if script_path:
        rc=utils.append_text(script_path,"\n"+"\n".join(lines))
        return
    def _send():
        for line in lines:
            # print(f"{Colors.GREEN}{line}{Colors.RESET}")
            speak(base_url, line.replace("’",""), use_json=True)
    t = threading.Thread(target=_send, daemon=True)
    t.start()

runid=utils.get_str_date_now()
cd=utils.get_current_directory()
script_path=f"{cd}/scripts/script_{runid}.txt"
# LM Studio default (use --lm-url to override)
LM_STUDIO_BASE = "http://192.168.1.106:1234/v1"
LM_STUDIO_API_KEY = None  # When None, no Authorization header is sent

# Speech server default (matches server.py)
SPEECH_HOST = "127.0.0.1"
SPEECH_PORT = 5001

VALID_VOICES = ["Leo", "Bella", "Jasper", "Kiki", "Luna", "Rosie", "Bruno", "Hugo"]
DEFAULT_VOICE = "Bruno"

SYSTEM_PROMPT = """You write drama scripts for text-to-speech. Each line must have:
- voice: one of Leo, Bella, Jasper, Kiki, Luna, Rosie, Bruno, Hugo
- speed: float 1.0 to 1.7 (1.2 = normal, higher = faster)
- text: the spoken dialogue or narration

Respond with valid JSON only, in this exact format:
{"lines": [{"voice": "Leo", "speed": 1.2, "text": "Hello."}, ...]}

Keep lines concise. Use varied voices for dialogue."""

SPEECH_SCRIPT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "speech_script",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "voice": {"type": "string"},
                            "speed": {"type": "number"},
                            "text": {"type": "string"},
                        },
                        "required": ["voice", "speed", "text"],
                    },
                }
            },
            "required": ["lines"],
        },
    },
}


def json_to_script_line(item: dict) -> str:
    """Convert a parsed JSON line to Character|speed|text format."""
    if type(item)!=dict:
        return ""
    voice = str(item.get("voice", DEFAULT_VOICE)).strip()
    if voice not in VALID_VOICES:
        voice = DEFAULT_VOICE
    speed = item.get("speed", 1.2)
    try:
        speed = float(speed)
    except (TypeError, ValueError):
        speed = 1.2
    text = str(item.get("text", "")).strip()
    return f"{voice}|{speed}|{text}"


def parse_json_response(content: str) -> list[dict] | None:
    """Parse JSON from LM response. Returns list of line dicts or None."""
    content = content.strip()
    # Try to extract JSON from markdown code blocks if present
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
    if match:
        content = match.group(1).strip()
    try:
        data = json.loads(content)
        lines = data.get("lines")
        if isinstance(lines, list):
            return lines
    except json.JSONDecodeError:
        pass
    return None


def parse_fallback_lines(content: str) -> list[dict]:
    """Fallback: look for Voice|speed|text patterns in plain text."""
    pattern = re.compile(
        r"(\w+)\s*\|\s*([\d.]+)\s*\|\s*(.+?)(?=\n\w+\s*\|\s*[\d.]+\s*\||\Z)",
        re.DOTALL,
    )
    lines = []
    for m in pattern.finditer(content):
        voice, speed, text = m.group(1), m.group(2), m.group(3).strip()
        if voice in VALID_VOICES:
            try:
                lines.append({"voice": voice, "speed": float(speed), "text": text})
            except ValueError:
                lines.append({"voice": voice, "speed": 1.2, "text": text})
    # Simpler line-by-line fallback: Voice|speed|text
    if not lines:
        for line in content.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3 and parts[0].strip() in VALID_VOICES:
                try:
                    lines.append({
                        "voice": parts[0].strip(),
                        "speed": float(parts[1].strip()),
                        "text": parts[2].strip(),
                    })
                except ValueError:
                    pass
    return lines


def query_llm(
    prompt: str,
    model: str,
    base_url: str = LM_STUDIO_BASE,
    use_structured: bool = True,
) -> list[dict]:
    """Call LM Studio via HTTP and return parsed script lines."""
    if requests is None:
        raise RuntimeError("Install requests: pip install requests")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if LM_STUDIO_API_KEY is not None:
        headers["Authorization"] = f"Bearer {LM_STUDIO_API_KEY}"


    if use_structured:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 5024,
            "stream": False,
        }
        payload["response_format"] = SPEECH_SCRIPT_SCHEMA
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 5024,
            "stream": False,
        }

    resp = requests.post(url, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    content = (data.get("choices", [{}])[0].get("message", {}).get("content") or "")

    lines = parse_json_response(content)
    if lines is None:
        lines = parse_fallback_lines(content)
    if len(lines)>0:
        return lines
    return content


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Agent: prompt LM Studio for scripts, send to KittenTTS speech server",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="""
        Write a 10-line conversation between Leo, Luna, Bruno, Kiki, Jasper, Rosie and Bella about the love of coffee in the morning. 
        You don't have to use all the voices. 
        Can keep one or two or all voices going in the conversation if it fits the conversation narrative. 
        Make it a nice story
        """,
        help="User prompt for the LLM (default: sample drama prompt)",
    )
    parser.add_argument(
        "--model",
        default="local-model",
        help="LM Studio model identifier (check Developer tab)",
    )
    parser.add_argument(
        "--lm-url",
        default=LM_STUDIO_BASE,
        help=f"LM Studio base URL (default: {LM_STUDIO_BASE})",
    )
    parser.add_argument(
        "--speech-host",
        default=SPEECH_HOST,
        help=f"Speech server host (default: {SPEECH_HOST})",
    )
    parser.add_argument(
        "--speech-port",
        type=int,
        default=SPEECH_PORT,
        help=f"Speech server port (default: {SPEECH_PORT})",
    )
    parser.add_argument(
        "--no-structured",
        action="store_true",
        help="Disable JSON schema (use for models that don't support structured output)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print script lines only, do not send to speech server",
    )
    args = parser.parse_args()

    if requests is None:
        print("Error: Install requests: pip install requests")
        sys.exit(1)
    plot_count="20"
    word_count="20"
    # the_story="""
    # The kitty disease comes to the group of friends town of cornball.
    # The friends have town people and family all turn into kittys.
    # They try to run and hide. But they also have to survive and live.
    # The kitty disease eventually effects the friends.
    # They attack each other and eat the flesh of their friends.
    # One person manages to run and hide in the deep woods and eventually make a living deep in the forest with bigfoot.
    # """
    words_theme="Make words of this theme of 5 words of 'adventure, danger' and remaining words about expedition, off-road, animals, survival, fear"
    make_ideas=f"""
    output {word_count} random words of comma delimited list of words that are not adjectives but nouns of person, place or things.
    {words_theme}
    """
    try:
        print(make_ideas)
        ideas = query_llm(
            prompt=make_ideas,
            model=args.model,
            base_url=args.lm_url,
            use_structured=False,
        )
    except Exception as e:
        print(f"LM Studio error: {e}")
        sys.exit(1)
    print(ideas)
    make_story=f"""
    Use these story narrative ideas: {ideas}
    Make a list of sentences to suggest a single short story plot narrative from begining to end we could expand on to build up and use these ideas into a more indepth plot.
    Make like 5-10 sentences as appropriate for what you think is good suggestion for the single short story.
    No other output comments except the plot paragraph/sentences with empty line between the plot sections.
    """
    try:
        print(make_story)
        the_story = query_llm(
            prompt=make_story,
            model=args.model,
            base_url=args.lm_url,
            use_structured=False,
        )
    except Exception as e:
        print(f"LM Studio error: {e}")
        sys.exit(1)
    if not the_story:
        print("No the_story lines parsed from LLM response.")
        sys.exit(1)
    print(the_story)
    prompt_narrative=f"""
    Create a story plot of about {plot_count} plot sections of the whole story. 
    {the_story}
    Each plot section will have new line.
    Keep each section as a paragraph.
    """

    try:
        print(prompt_narrative)
        the_plot = query_llm(
            prompt=prompt_narrative,
            model=args.model,
            base_url=args.lm_url,
            use_structured=False,
        )
    except Exception as e:
        print(f"LM Studio error: {e}")
        sys.exit(1)
    if not the_plot:
        print("No script lines parsed from LLM response.")
        sys.exit(1)
    print(the_plot)
    plot_list=the_plot.split("\n\n")
    # for i in range(len(plot_list)):
    for n,plot in enumerate(plot_list):
        if len(str(plot).strip())<180:
            plot_list.pop(n)

    plot_id=0
#     voices_prompt=f"""
#         Write a 20-line conversation between Leo, Luna, Bruno, Kiki, Jasper, Rosie and Bella.
#         You don't have to use all the voices.
#         The conversation is about this conversation narrative.
# {plot_list[plot_id]}.
#         Can keep one or two or all voices going in the conversation if it fits the conversation narrative.
#         Make it a good and interesting story
#         """
#     prompt = voices_prompt #args.prompt if args.prompt else voices_prompt
    # print(f"Prompting LM Studio: {prompt[:60]}{'...' if len(prompt) > 60 else ''}\n")
    story=""
    discussion=""
    plotcount=2
    for n,plot in enumerate(plot_list):
        if len(plot)<100:
            continue
        try:
            voices_prompt = f"""PLOT:{n} of {len(plot_list)}:
    Write a 10 to 30-line conversation of only these characters, Leo is male, Luna is female, Bruno is male, Kiki is female, Jasper is male, Rosie is female and Bella is female.
    
    We want plenty of narration in the story to help keep the story moving along in time and action.
    Bruno will be the narrator in the story.
    
    You don't have to use all the character names. 
    But you must only use these character names listed above.
    Can keep one or two or all the charaters going in the conversation.
    
    Here is The Plot to build the next discussion of the story:
    {plot}
    
    {story}
    """

            print(voices_prompt)
            lines = query_llm(
                prompt=voices_prompt,
                model=args.model,
                base_url=args.lm_url,
                use_structured=not args.no_structured,
            )
        except Exception as e:
            print(f"LM Studio error: {e}")
            sys.exit(1)

        if not lines:
            print("No script lines parsed from LLM response.")
            sys.exit(1)
        plot2=plot.split("\n")
        play_plot=f"{DEFAULT_VOICE}|1.0|{plot2[-1]}"
        script_lines = [json_to_script_line(item) for item in lines]
        script_lines.insert(0,play_plot)
        # print(f"Parsed {len(script_lines)} line(s):\n")
        for i, line in enumerate(script_lines):
            if len(line)<10:
                script_lines.pop(i)
                continue
            ln=line.split("|")
            if len(ln)>2:
                line = line.replace("'", "")
                txt=str(ln[2])
                rc1,x=utils.get_text_between_2str(text=txt,str1="(",str2=")",start=0)
                if len(rc1)>0:
                    rc2=str(rc1).lower()
                    if rc2=="narration":
                        rc3=f"({rc1}) "
                        ln[2] = ln[2].replace(rc3, "")
                        ln[0]=DEFAULT_VOICE
                    else:
                        rc3=f"({rc1}) "
                        ln[2] = ln[2].replace(rc3, "")
                sp=float(ln[1])
                if ((sp > 1.5) or
                        ("Kiki" in line) or
                        ("Leo" in line) or
                        ("Jasper" in line)
                ):

                    sp="1.0"
                    ln[1]=str(sp)

                line = "|".join(ln)
                script_lines[i]=line
            else:
                continue
            # print(f"  [{i}] {line}")

        if args.dry_run:
            print("\nDry run: not sending to speech server.")
            return

        base_url = f"http://{args.speech_host}:{args.speech_port}"
        print(f"\nSending to {base_url}/speak (background)\n")
        # Synchronous (blocks until each line is queued):
        # for i, line in enumerate(script_lines, 1):
        #     ok, msg = speak(base_url, line, use_json=True)
        #     if ok:
        #         print(f"  [{i}] Queued: {line[:50]}{'...' if len(line) > 50 else ''}")
        #     else:
        #         print(f"  [{i}] FAIL: {msg}")
        # Threaded (fire-and-forget; proceeds immediately to next LM Studio call):
        if len(script_lines)>0:
            send_lines_background_speech(base_url, script_lines,script_path)
            # print(f"  Queued {len(script_lines)} line(s) in background; proceeding to next LM Studio call.")
            story="\n\nHere is the past back story for context to build the plot from:\n"
            for ll in script_lines:
                story+=str(ll)+"\n"
            story+="\n"
        else:
            story=""
    print("\nDone.")


if __name__ == "__main__":
    main()
