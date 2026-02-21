# Kitten TTS 😻 — Speech Script Player

<img width="607" height="255" alt="Kitten TTS" src="https://github.com/user-attachments/assets/f4646722-ba78-4b25-8a65-81bacee0d4f6" />

> **Turn AI-generated scripts into multi-voice audio dramas.**

Kitten TTS is an open-source text-to-speech model with just 15 million parameters, designed for lightweight deployment and high-quality voice synthesis. This project focuses on **`app.py`** — a drama script player that reads pipe-delimited scripts with multiple character voices, parallel audio generation, and ordered playback.

*Currently in developer preview*

[Join our Discord](https://discord.com/invite/VJ86W4SURW) · [KittenML Website](https://kittenml.com) · [Custom Support Form](https://docs.google.com/forms/d/e/1FAIpQLSc49erSr7jmh3H2yeqH4oZyRRuXm0ROuQdOgWguTzx6SMdUnQ/viewform?usp=preview)

---

## What It Does

`app.py` reads a **speech script** (e.g. `scripts/script_drama.txt`), assigns each line to a voice character, generates speech in parallel using KittenTTS, and plays the audio in order. Perfect for:

- **Voice stories** — Narratives with narrator + character dialogue
- **Audiobooks** — Multi-voice chapter readings
- **Podcasts** — Scripted content with distinct speakers
- **AI-generated scripts** — Output from ChatGPT, Claude, or other AI services formatted for TTS

---

## Quick Start

```bash
# 1. Clone and enter project
cd KittenTTS

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
# or: .venv\Scripts\activate  # Windows

# 3. Install dependencies (see Platform Setup below first)
pip install -e .
pip install sounddevice

# 4. Run the app
python app.py
```

By default, `app.py` plays `scripts/script_drama.txt`. Use `--script` to choose another: `python app.py --script script_travel.txt`

### API Mode (server + client)

```bash
# Terminal 1: Start server
python server.py

# Terminal 2: Send speech lines
python client.py
```

Or use `python client.py --start-server` to start the server automatically. See [server.md](server.md) and [client.md](client.md).

---

## Platform Setup

### macOS (Apple Silicon & Intel)

**1. Install Homebrew** (if not already installed):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. espeak-ng** — Provided by `espeakng_loader` (in requirements.txt); no system install needed. If phonemizer fails, install manually: `brew install espeak-ng`

**3. Python 3.10+** (3.12 recommended):

```bash
brew install python@3.12
```

**4. Optional:** If phonemizer can't find espeak-ng, set the library path:

```python
# Add before importing kittentts (e.g. in app.py or a config)
import os
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = '/opt/homebrew/Cellar/espeak-ng/1.52.0/lib/libespeak-ng.dylib'
# Intel Macs: use /usr/local/Cellar/espeak-ng/... instead of /opt/homebrew/...
```

---

### Windows 11

**1. Python 3.10+** — Install from [python.org](https://www.python.org/downloads/) or via Microsoft Store. Ensure "Add Python to PATH" is checked.

**2. No Homebrew** — Windows uses pip packages. `espeakng_loader` and `phonemizer` work with bundled/system espeak where available.

**3. PortAudio** — `sounddevice` installs PortAudio automatically via pip; no separate install needed.

**4. If phonemizer fails on Windows** — Try the Windows-specific phonemizer package:

```bash
pip install espeak-phonemizer-windows
```

---

## Python Dependencies

| Package | Purpose |
|---------|---------|
| **kittentts** | KittenTTS TTS engine (text → phonemes → ONNX → audio) |
| **sounddevice** | Audio playback (uses PortAudio) |
| **phonemizer** | Text → IPA phonemes (uses espeak-ng) |
| **flask** | API server (server.py) |
| **requests** | HTTP client (client.py) |
| **espeakng_loader** | Cross-platform espeak-ng library loader |
| **onnxruntime** | ONNX model inference (CPU or GPU) |
| **numpy** | Array handling for audio |
| **soundfile** | Audio file I/O (used by kittentts) |
| **huggingface_hub** | Model download from Hugging Face |
| **num2words** | Number-to-word conversion for TTS |
| **spacy** | NLP preprocessing (optional, for advanced text handling) |
| **misaki[en]** | Japanese text processing (optional) |

### Install All Dependencies

```bash
pip install -e .                    # kittentts + pyproject.toml deps
pip install sounddevice             # Required for app.py playback
```

Or from `requirements.txt`:

```bash
pip install -r requirements.txt
pip install sounddevice
```

---

## CPU vs GPU

KittenTTS runs well on **CPU** — the nano model (~15M params) is optimized for it. No GPU required.

### CPU (Default)

```bash
pip install onnxruntime
```

Works on Mac (including Apple Silicon), Windows, and Linux.

### GPU (Optional, for faster inference)

**NVIDIA GPU (CUDA):**

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

Requires CUDA 11.x or 12.x and cuDNN. See [ONNX Runtime GPU docs](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html).

**Windows (DirectML — AMD/Intel/NVIDIA):**

```bash
pip uninstall onnxruntime
pip install onnxruntime-directml
```

Uses DirectX 12 for GPU acceleration on a wide range of GPUs.

---

## Creating Speech Scripts

Scripts use a simple pipe-delimited format:

```
VOICE|SPEED|TEXT
```

| Field | Description | Example |
|-------|-------------|---------|
| `VOICE` | Character name | `Leo`, `Bella`, `Jasper`, `Kiki`, `Luna`, `Rosie`, `Bruno` |
| `SPEED` | Speed multiplier (float) | `1.2`, `1.4`, `1.0` |
| `TEXT` | Line to speak | `People think a quiet town is a safe town.` |

### Example Script

```
Leo|1.2|People think a quiet town is a safe town.
Leo|1.2|They hear crickets, see porch lights, and assume the universe is being polite.
Bella|1.4|Okay. Everyone stay together. No wandering.
Jasper|1.3|I'm not wandering. I'm strategically glued to the group.
```

Save as `scripts/your_script.txt` and run `python app.py --script your_script.txt`.

### Available Voices

| Voice | Character |
|-------|-----------|
| Leo | Male narrator (default) |
| Jasper, Bruno | Male characters |
| Bella, Luna, Rosie, Kiki | Female characters |

---

## Generating Scripts with AI

You can create voice story scripts using any major AI service (ChatGPT, Claude, etc.). Use a prompt like:

```
Create a short horror story script for text-to-speech. Use this exact format for each line:

VOICE|SPEED|TEXT

Rules:
- VOICE: Use character names: Leo (narrator), Bella, Jasper, Kiki, Luna, Rosie, Bruno
- SPEED: 1.0 to 2.0 (1.2 = normal, higher = faster/urgent)
- TEXT: One line of dialogue or narration per row
- Use Leo for narration, other names for character dialogue
- Blank lines between scenes
- No extra formatting or markdown
```

Example output:

```
Leo|1.2|The old house stood at the end of the street.
Leo|1.2|No one had lived there for years.
Bella|1.4|Are you sure we should go in?
Jasper|1.3|What's the worst that could happen?
```

Copy the output into `scripts/your_story.txt` and run `python app.py --script your_story.txt`.

---

## Configuration

### app.py (script player)

| Option | Default | Description |
|--------|---------|-------------|
| `--script`, `-s` | `script_drama.txt` | Script filename in `scripts/` |
| `--voice`, `-v` | `Leo` | Fallback for unknown voices |
| `--model-dir` | `KittenML/` | Model directory |
| `--model` | `kitten-tts-nano-0.8-fp32` | Model name |
| `--speed-offset` | `0.2` | Added to each line's speed |

See [app.md](app.md) for details.

### server.py (API)

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Bind host |
| `--port` | `5001` | Bind port |
| `--model` | `kitten-tts-nano-0.8-fp32` | Model name |

See [server.md](server.md) and [client.md](client.md) for API usage.

---

## Models

| Model | Params | Size | Use Case |
|-------|--------|------|----------|
| kitten-tts-nano | 15M | 56MB | Default, CPU-friendly |
| kitten-tts-mini | 80M | 80MB | Higher quality |
| kitten-tts-micro | 40M | 41MB | Middle ground |

`app.py` uses `kitten-tts-nano-0.8-fp32` by default. Models are downloaded from [Hugging Face](https://huggingface.co/KittenML) on first run.

---

## Project Structure

```
KittenTTS/
├── app.py              # Script player (loads script, uses Speech)
├── server.py            # API server (POST /speak)
├── client.py            # API client (sends speech lines)
├── speech.py            # Core Speech class (queuing, workers, player)
├── kittentts/           # KittenTTS library
├── KittenML/            # Local model configs (optional)
└── scripts/             # Speech scripts
    ├── script_drama.txt
    ├── script_action1.txt
    ├── script_hangout.txt
    └── script_travel.txt
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `phonemizer` can't find espeak | `espeakng_loader` (in requirements.txt) provides it; ensure it's installed. Fallback: `brew install espeak-ng` (Mac) or `espeak-phonemizer-windows` (Windows) |
| No audio playback | Ensure `sounddevice` is installed; check system audio device |
| Model download fails | Check internet; Hugging Face may require login for some models |
| Slow generation | Use `onnxruntime-gpu` (NVIDIA) or `onnxruntime-directml` (Windows) |

---

## Project Documentation

| Document | Description |
|----------|-------------|
| [app.md](app.md) | Script player — loads script file, uses Speech class |
| [speech.md](speech.md) | Core Speech class — queuing, workers, player |
| [server.md](server.md) | API server — POST /speak for speech lines |
| [client.md](client.md) | API client — POST options and usage |
| [README_orginal.md](README_orginal.md) | Original KittenTTS project README |
| [KittenML/kitten-tts-nano-0.8-fp32/README.md](KittenML/kitten-tts-nano-0.8-fp32/README.md) | Nano model (15M params) — default |
| [KittenML/kitten-tts-mini-0.8/README.md](KittenML/kitten-tts-mini-0.8/README.md) | Mini model (80M params) — higher quality |

---

## Links

- [KittenTTS GitHub](https://github.com/kittenml/kittentts)
- [KittenML on Hugging Face](https://huggingface.co/KittenML)

Email: info@stellonlabs.com
