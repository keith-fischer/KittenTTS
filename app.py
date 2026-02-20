from kittentts import KittenTTS
import sounddevice as sd
import conversation
import threading
import queue
import os
from threading import Semaphore, Lock

# 1. Configuration
BUFFER_SIZE = 5
NUM_WORKER_THREADS = 3
SPEED_OFFSET = 0.2
CONVERSATION_SOURCE = conversation.conversation1
CONVERSATION_SOURCE = "script_drama.txt"
DEFAULT_VOICE = "Leo"
dir = "KittenML/"
tts = ["kitten-tts-mini-0.8", "kitten-tts-nano-0.8-fp32"]
voices_she = ["Bella", "Luna", "Rosie", "Kiki"]
voices_he = ["Jasper", "Bruno", "Leo"]
voices = voices_she + voices_he
sample_rate = 24000

# 2. Color Definitions for Console Output
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

voice_colors = {
    "Bella": Colors.MAGENTA,
    "Luna": Colors.BLUE,
    "Rosie": Colors.CYAN,
    "Kiki": Colors.YELLOW,
    "Jasper": Colors.GREEN,
    "Bruno": Colors.RED,
    "Leo": Colors.WHITE,
}

# 3. Load Script Content
script_content = ""
if isinstance(CONVERSATION_SOURCE, str) and CONVERSATION_SOURCE.endswith('.txt'):
    script_path = os.path.join('scripts', CONVERSATION_SOURCE)
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
    except FileNotFoundError:
        print(f"Error: Script file not found at {script_path}")
        exit()
else:
    script_content = CONVERSATION_SOURCE

# 4. Queues and Synchronization
task_queue = queue.Queue()
results_queue = queue.PriorityQueue()
buffer_semaphore = Semaphore(BUFFER_SIZE)
print_lock = Lock()

# 5. Pre-parse the script to create a definitive list of tasks
tasks_to_process = []
valid_line_counter = 1
script_lines = script_content.split("\n")
for text in script_lines:
    if not text.strip():
        continue
    
    parts = text.split("|")
    if len(parts) < 3:
        continue
    try:
        voice = parts[0]
        speed = float(parts[1]) + SPEED_OFFSET
        text_to_speak = parts[2].replace("’", "")
    except (ValueError, IndexError):
        continue
    if voice not in voices:
        voice = DEFAULT_VOICE
    
    tasks_to_process.append((valid_line_counter, text_to_speak, speed, voice))
    valid_line_counter += 1

# 6. Worker and Player Functions
def worker():
    """Pulls tasks from task_queue, generates audio, and puts results in results_queue."""
    m = KittenTTS(dir + tts[1])
    while True:
        task = task_queue.get()
        if task is None:
            break
        
        line, txt, speed, voice = task
        color = voice_colors.get(voice, Colors.RESET)
        with print_lock:
            print(color + f"\tGenerating-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
        audio_data = m.generate(txt, voice=voice, speed=speed)
        results_queue.put((line, txt, speed, voice, audio_data))
        task_queue.task_done()

def player(total_lines):
    """Plays audio clips in the correct order as they become available."""
    if not tasks_to_process:
        with print_lock:
            print("No valid lines to play.")
        return

    next_line_to_play = 1
    results_buffer = {}
    played_lines_count = 0

    while played_lines_count < total_lines:
        # Try to play consecutive lines from the buffer first
        while next_line_to_play in results_buffer:
            line, txt, speed, voice, audio_data = results_buffer.pop(next_line_to_play)
            color = voice_colors.get(voice, Colors.RESET)
            with print_lock:
                print(color + f"Playing-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
            sd.play(audio_data, sample_rate)
            sd.wait()
            buffer_semaphore.release()
            played_lines_count += 1
            next_line_to_play += 1
        
        if played_lines_count == total_lines:
            break

        # If the next line wasn't in the buffer, get a new result from the queue
        try:
            line, txt, speed, voice, audio_data = results_queue.get(timeout=10)

            if line == next_line_to_play:
                color = voice_colors.get(voice, Colors.RESET)
                with print_lock:
                    print(color + f"Playing-{line}.{speed:.1f}.{voice}:{txt}" + Colors.RESET)
                sd.play(audio_data, sample_rate)
                sd.wait()
                buffer_semaphore.release()
                played_lines_count += 1
                next_line_to_play += 1
            else:
                results_buffer[line] = (line, txt, speed, voice, audio_data)
        except queue.Empty:
            with print_lock:
                print("Player timed out waiting for the next audio clip. Exiting.")
            break
    with print_lock:
        print("Finished playing.")

# 7. Main Execution
if __name__ == "__main__":
    total_lines_to_play = len(tasks_to_process)

    # Start worker threads
    threads = []
    for _ in range(NUM_WORKER_THREADS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Start player thread
    player_thread = threading.Thread(target=player, args=(total_lines_to_play,))
    player_thread.start()

    # Main thread acts as the producer manager
    for task in tasks_to_process:
        buffer_semaphore.acquire()
        task_queue.put(task)

    # Wait for all tasks to be processed by workers
    task_queue.join()

    # Stop worker threads by sending sentinel values
    for _ in range(NUM_WORKER_THREADS):
        task_queue.put(None)

    # Wait for all threads to complete
    for t in threads:
        t.join()
    player_thread.join()
