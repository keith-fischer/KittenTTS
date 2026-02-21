# app.py — Drama Script TTS Player

Loads a script file and speaks all lines using the `Speech` class. Run directly with optional startup parameters or use defaults.

---

## Quick Start

```bash
# Play default script (scripts/script_drama.txt)
python app.py

# Custom script
python app.py --script script_travel.txt

# Full options
python app.py -s script_drama.txt --voice Leo --model kitten-tts-nano-0.8-fp32
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         app.py                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Script File ──▶ load_script() ──▶ parse_script_lines()         │
│       │                    │                    │                │
│       │                    └────────────────────┼──▶ Speech      │
│       │                                         │    .add_speech_line()
│       │                                         │    .mark_complete()
│       │                                         │    .wait_until_complete()
│       │                                         │                │
│       └─────────────────────────────────────────┴────────────────┘
│                                                                  │
│  Core pipeline (queuing, workers, player) lives in speech.py     │
└─────────────────────────────────────────────────────────────────┘
```

`app.py` handles script loading and parsing; the `Speech` class handles queuing, parallel TTS generation, and ordered playback. See [speech.md](speech.md) for pipeline details.

---

## Command-Line Options

| Option | Default | Description |
|-------|---------|-------------|
| `--script`, `-s` | `script_drama.txt` | Script file name (in `scripts/`) or path |
| `--voice`, `-v` | `Leo` | Default voice for unknown characters |
| `--model-dir` | `KittenML/` | Model directory |
| `--model` | `kitten-tts-nano-0.8-fp32` | Model name |
| `--speed-offset` | `0.2` | Speed offset applied to script values |

---

## Script Format

Scripts use a pipe-delimited format:

```
VOICE|SPEED|TEXT
```

| Field | Description | Example |
|-------|-------------|---------|
| VOICE | Character voice name | `Leo`, `Bella`, `Jasper`, `Kiki`, `Luna`, `Rosie`, `Bruno` |
| SPEED | Base speed multiplier (float) | `1.2`, `1.4`, `1.0` |
| TEXT | Line to synthesize | `People think a quiet town is a safe town.` |

### Example Script

```
Leo|1.2|People think a quiet town is a safe town.
Leo|1.2|They hear crickets, see porch lights, and assume the universe is being polite.
Bella|1.4|Okay. Everyone stay together. No wandering.
Jasper|1.3|I'm not wandering. I'm strategically glued to the group.
```

### Parsing Rules

- Blank lines are skipped.
- Lines must have at least 3 pipe-separated parts.
- `speed` used in synthesis = `float(parts[1]) + speed_offset` (default `0.2`).
- Curly apostrophes (`'`) are removed from text.
- Unknown voices fall back to `DEFAULT_VOICE` (`Leo`).

---

## Available Voices

| Voice | Character |
|-------|-----------|
| Leo | Male narrator (default) |
| Jasper, Bruno | Male characters |
| Bella, Luna, Rosie, Kiki | Female characters |

---

## Script Location

- Relative paths (e.g. `script_drama.txt`) are resolved under `scripts/`
- Absolute paths are used as-is
- `.txt` suffix is added if omitted

---

## Flow

```
main()
  ├── Parse args
  ├── load_script(path) → content
  ├── parse_script_lines(content) → speech_lines
  ├── Speech(...) as speech
  │     for line in speech_lines:
  │       speech.add_speech_line(line)
  │     speech.mark_complete()
  │     speech.wait_until_complete()
  └── "App finished."
```

---

## File Structure

```
KittenTTS/
├── app.py              # This application
├── app.md              # This documentation
├── speech.py           # Core Speech class
├── server.py           # API server
├── client.py           # API client
├── kittentts/           # KittenTTS library
└── scripts/
    ├── script_drama.txt
    ├── script_action1.txt
    ├── script_hangout.txt
    └── script_travel.txt
```

---

## See Also

- [speech.md](speech.md) — Core Speech class (queuing, workers, player)
- [server.md](server.md) — API server
- [client.md](client.md) — API client
