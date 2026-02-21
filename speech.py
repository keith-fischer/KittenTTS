"""
Core Speech class for KittenTTS: handles input queuing, threading, and audio playback.
Used by app.py (script mode) and server.py (API mode).
"""

from __future__ import annotations

from kittentts import KittenTTS
import sounddevice as sd
import threading
import queue
from threading import Semaphore, Lock

# Color definitions for console output
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

VOICE_COLORS = {
    "Bella": Colors.MAGENTA,
    "Luna": Colors.BLUE,
    "Rosie": Colors.CYAN,
    "Kiki": Colors.YELLOW,
    "Jasper": Colors.GREEN,
    "Bruno": Colors.RED,
    "Leo": Colors.WHITE,
}

VOICES_SHE = ["Bella", "Luna", "Rosie", "Kiki"]
VOICES_HE = ["Jasper", "Bruno", "Leo"]
ALL_VOICES = VOICES_SHE + VOICES_HE


class Speech:
    """
    Core TTS engine: queues speech lines, generates audio via worker threads,
    plays in order. Supports script mode (batch) and API mode (streaming).
    """

    def __init__(
        self,
        model_dir: str = "KittenML/",
        model_name: str = "kitten-tts-nano-0.8-fp32",
        voices: list | None = None,
        default_voice: str = "Leo",
        sample_rate: int = 24000,
        speed_offset: float = 0.2,
        buffer_size: int = 5,
        num_workers: int = 3,
        player_timeout: float = 10.0,
    ):
        self.model_path = model_dir + model_name
        self.voices = voices or ALL_VOICES
        self.default_voice = default_voice
        self.sample_rate = sample_rate
        self.speed_offset = speed_offset
        self.buffer_size = buffer_size
        self.num_workers = num_workers
        self.player_timeout = player_timeout

        self._task_queue: queue.Queue = queue.Queue()
        self._results_queue: queue.PriorityQueue = queue.PriorityQueue()
        self._buffer_semaphore = Semaphore(buffer_size)
        self._print_lock = Lock()

        self._line_counter = 0
        self._total_lines = 0
        self._no_more_lines = threading.Event()
        self._all_played = threading.Event()
        self._shutdown = threading.Event()

        self._worker_threads: list[threading.Thread] = []
        self._player_thread: threading.Thread | None = None
        self._started = False

    def _worker(self) -> None:
        """Pulls tasks from queue, generates audio, puts results in results queue."""
        model = KittenTTS(self.model_path)
        while not self._shutdown.is_set():
            try:
                task = self._task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if task is None:
                break

            line, txt, speed, voice = task
            color = VOICE_COLORS.get(voice, Colors.RESET)
            with self._print_lock:
                print(color + f"\tGenerating-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
            audio_data = model.generate(txt, voice=voice, speed=speed)
            self._results_queue.put((line, txt, speed, voice, audio_data))
            self._task_queue.task_done()

    def _player(self) -> None:
        """Plays audio clips in order as they become available."""
        next_line_to_play = 1
        results_buffer: dict[int, tuple] = {}
        played_count = 0

        while not self._shutdown.is_set():
            # Check if we're done: no more lines coming and we've played all
            if self._no_more_lines.is_set() and self._total_lines > 0 and played_count >= self._total_lines:
                break

            # Play consecutive lines from buffer first
            while next_line_to_play in results_buffer:
                line, txt, speed, voice, audio_data = results_buffer.pop(next_line_to_play)
                color = VOICE_COLORS.get(voice, Colors.RESET)
                with self._print_lock:
                    print(color + f"Playing-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
                sd.play(audio_data, self.sample_rate)
                sd.wait()
                self._buffer_semaphore.release()
                played_count += 1
                next_line_to_play += 1

            if self._no_more_lines.is_set() and played_count >= self._total_lines:
                break

            # Get next result from queue
            try:
                line, txt, speed, voice, audio_data = self._results_queue.get(
                    timeout=self.player_timeout
                )
                if line == next_line_to_play:
                    color = VOICE_COLORS.get(voice, Colors.RESET)
                    with self._print_lock:
                        print(color + f"Playing-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
                    sd.play(audio_data, self.sample_rate)
                    sd.wait()
                    self._buffer_semaphore.release()
                    played_count += 1
                    next_line_to_play += 1
                else:
                    results_buffer[line] = (line, txt, speed, voice, audio_data)
            except queue.Empty:
                if self._no_more_lines.is_set():
                    with self._print_lock:
                        print("Player: no more lines expected, exiting.")
                    break
                with self._print_lock:
                    print("Player timed out waiting for next audio clip.")
                continue

        with self._print_lock:
            print("Finished playing.")
        self._all_played.set()

    def start(self) -> None:
        """Start worker and player threads. Call to preload model before first request."""
        self._ensure_started()

    def _ensure_started(self) -> None:
        """Start worker and player threads on first use."""
        if self._started:
            return
        self._started = True
        for _ in range(self.num_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._worker_threads.append(t)
        self._player_thread = threading.Thread(target=self._player, daemon=True)
        self._player_thread.start()

    def add_speech_line(self, line: str) -> bool:
        """
        Parse and queue a speech line. Format: Character|speed|text
        Returns True if valid and queued.
        """
        line = line.strip()
        if not line:
            return False

        parts = line.split("|")
        if len(parts) < 3:
            return False

        try:
            voice = parts[0].strip()
            speed = float(parts[1]) + self.speed_offset
            text = parts[2].replace("'", "").replace("'", "").strip()
        except (ValueError, IndexError):
            return False

        if voice not in self.voices:
            voice = self.default_voice

        return self.add_speech_line_parts(voice, speed, text)

    def add_speech_line_parts(self, voice: str, speed: float, text: str) -> bool:
        """Queue a parsed speech line. Returns True."""
        if not text.strip():
            return False

        self._ensure_started()
        self._line_counter += 1
        self._total_lines = self._line_counter
        line_num = self._line_counter

        self._buffer_semaphore.acquire()
        self._task_queue.put((line_num, text, speed, voice))
        return True

    def mark_complete(self) -> None:
        """Signal that no more lines will be added. Required before wait_until_complete()."""
        self._no_more_lines.set()

    def wait_until_complete(self) -> None:
        """
        Block until all queued lines have been played.
        Call mark_complete() first if you're done adding lines.
        """
        self._ensure_started()
        self._no_more_lines.set()
        self._task_queue.join()
        # Stop workers
        for _ in range(self.num_workers):
            self._task_queue.put(None)
        for t in self._worker_threads:
            t.join()
        if self._player_thread:
            self._player_thread.join()
        self._all_played.wait()

    def shutdown(self) -> None:
        """Stop workers and cleanup resources."""
        self._shutdown.set()
        self._no_more_lines.set()
        for _ in range(self.num_workers):
            try:
                self._task_queue.put(None)
            except Exception:
                pass
        for t in self._worker_threads:
            t.join(timeout=2.0)
        if self._player_thread:
            self._player_thread.join(timeout=2.0)

    def __enter__(self) -> "Speech":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()
