"""
KittenTTS script runner: loads a script file and speaks all lines via the Speech class.
Run directly with optional startup parameters, or uses defaults.
"""

import argparse
import os

from speech import Speech


# Default configuration
DEFAULT_SCRIPT = "script_260222_135832.txt"
DEFAULT_VOICE = "Leo"
DEFAULT_MODEL_DIR = "KittenML/"
DEFAULT_MODEL = "kitten-tts-nano-0.8-fp32"
SPEED_OFFSET = 0.2


def load_script(path: str) -> str:
    """Load script content from file path or scripts/ subdir."""
    if not path.endswith(".txt"):
        path = path + ".txt"
    if not os.path.isabs(path) and not path.startswith("scripts/"):
        path = os.path.join("scripts", path)
    with open(path, "r") as f:
        return f.read()


def parse_script_lines(content: str) -> list[str]:
    """Extract valid speech lines (Character|speed|text) from script content."""
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|")
        if len(parts) >= 3:
            lines.append(line)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="KittenTTS script player")
    parser.add_argument(
        "--script",
        "-s",
        default=DEFAULT_SCRIPT,
        help=f"Script file name (in scripts/) or path. Default: {DEFAULT_SCRIPT}",
    )
    parser.add_argument(
        "--voice",
        "-v",
        default=DEFAULT_VOICE,
        help=f"Default voice for unknown characters. Default: {DEFAULT_VOICE}",
    )
    parser.add_argument(
        "--model-dir",
        default=DEFAULT_MODEL_DIR,
        help=f"Model directory. Default: {DEFAULT_MODEL_DIR}",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model name. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--speed-offset",
        type=float,
        default=SPEED_OFFSET,
        help=f"Speed offset applied to script values. Default: {SPEED_OFFSET}",
    )
    args = parser.parse_args()

    try:
        script_content = load_script(args.script)
    except FileNotFoundError:
        print(f"Error: Script file not found: {args.script}")
        return

    speech_lines = parse_script_lines(script_content)
    if not speech_lines:
        print("No valid speech lines in script.")
        return

    with Speech(
        model_dir=args.model_dir,
        model_name=args.model,
        default_voice=args.voice,
        speed_offset=args.speed_offset,
    ) as speech:
        for line in speech_lines:
            speech.add_speech_line(line)
        speech.mark_complete()
        speech.wait_until_complete()

    print("App finished.")


if __name__ == "__main__":
    main()
