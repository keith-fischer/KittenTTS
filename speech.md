# speech.py — Core Speech Class

Handles input queuing, threading, and audio playback for KittenTTS. Used by `app.py` (script mode) and `server.py` (API mode).

---

## Overview

The `Speech` class:

- **Queues** speech lines in `Character|speed|text` format
- **Generates** audio via parallel worker threads (KittenTTS)
- **Plays** audio in order via a dedicated player thread
- **Supports** batch mode (app) and streaming mode (server)

---

## Usage

### Script Mode (app.py)

```python
from speech import Speech

with Speech(model_dir="KittenML/", model_name="kitten-tts-nano-0.8-fp32") as speech:
    for line in speech_lines:
        speech.add_speech_line(line)
    speech.mark_complete()
    speech.wait_until_complete()
```

### API Mode (server.py)

```python
from speech import Speech

speech = Speech(...)
speech.start()  # Preload model
# On each POST: speech.add_speech_line(line)
# Never call mark_complete() — lines stream indefinitely
```

---

## Constructor Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model_dir` | `KittenML/` | Model directory |
| `model_name` | `kitten-tts-nano-0.8-fp32` | Model name |
| `voices` | `ALL_VOICES` | Valid voice names |
| `default_voice` | `Leo` | Fallback for unknown voices |
| `sample_rate` | `24000` | Audio sample rate |
| `speed_offset` | `0.2` | Added to each line's speed |
| `buffer_size` | `5` | Max tasks in flight |
| `num_workers` | `3` | Parallel TTS worker threads |
| `player_timeout` | `10.0` | Player queue timeout (seconds) |

---

## Methods

| Method | Description |
|-------|-------------|
| `add_speech_line(line)` | Parse `Character\|speed\|text` and queue. Returns `True` if valid. |
| `add_speech_line_parts(voice, speed, text)` | Queue a pre-parsed line. Returns `True`. |
| `mark_complete()` | Signal no more lines will be added. Required before `wait_until_complete()`. |
| `wait_until_complete()` | Block until all queued lines have been played. |
| `start()` | Start worker and player threads (lazy-started on first `add_speech_line` otherwise). |
| `shutdown()` | Stop workers and cleanup. |
| `__enter__` / `__exit__` | Context manager for automatic cleanup. |

---

## Speech Line Format

`Character|speed|text`

| Field | Description |
|-------|-------------|
| Character | Voice: Bella, Luna, Rosie, Kiki, Jasper, Bruno, Leo |
| speed | Float (e.g. 1.2); `speed_offset` is added |
| text | Text to synthesize |

---

## Architecture

```
add_speech_line() → task_queue → Worker threads (KittenTTS.generate)
                                        ↓
                               results_queue (PriorityQueue)
                                        ↓
                               Player thread (sd.play, ordered)
```

- **Buffer semaphore** limits in-flight tasks to `buffer_size`
- **Results buffer** caches out-of-order results for ordered playback
- **Worker threads** each load a KittenTTS model instance

---

## Voice Colors (Console Output)

| Voice | Color |
|-------|-------|
| Bella | Magenta |
| Luna | Blue |
| Rosie | Cyan |
| Kiki | Yellow |
| Jasper | Green |
| Bruno | Red |
| Leo | White |

---

## See Also

- [app.md](app.md) — Script player
- [server.md](server.md) — API server
- [client.md](client.md) — API client
