import sys
import json
import datetime
import os
import shutil
import hashlib
import base64
import time
from pathlib import Path
from datetime import datetime, timedelta
from glob2 import glob
from cryptography.fernet import Fernet
# import pandas as pd
import re
import threading
import queue
import time
from typing import Dict, Optional
import stat

DEBUG = True
get_ms = lambda: int(round(time.time() * 1000))
get_sec = lambda: int(round(time.time()))

pd_csv = None
pd_last_row = -1
pd_row = None


def sanitize_filename(name: str, strlen: int = 0) -> str:
    # Replace spaces with hyphens
    name = name.replace(' ', '-')

    # Remove control characters and non-printables
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)

    # Remove any other unsafe filename characters (optional strictness)
    name = re.sub(r'[<>:"/\\|?*\']', '', name)

    # Trim to max 10 characters
    if strlen == 0:
        return name
    else:
        return name[:strlen]


def is_python_debug_mode():
    # Check if debugger is attached (works across platforms)
    debugger_attached = sys.gettrace() is not None

    # PyCharm specific debug flag (works on both Windows and OSX)
    pycharm_debug = bool(os.getenv('PYCHARM_HOSTED'))

    return debugger_attached or pycharm_debug


def rename_file_of_full_path(full_path, old_find, new_replace, verify_path=False):
    full_path = full_path.replace("\\", "/")
    basename1 = os.path.basename(full_path)
    basename2 = basename1.replace(old_find, new_replace)
    if basename1 == basename2:
        return None  # No change needed
    new_full_path = os.path.join(os.path.dirname(full_path), basename2)
    if verify_path:
        if not os.path.exists(new_full_path):
            return None
    return new_full_path


def replace_last_occurrence(original_str, substring, replacement):
    # Reverse the original string and the substring
    reversed_str = original_str[::-1]
    reversed_substring = substring[::-1]
    reversed_replacement = replacement[::-1]

    # Replace the first occurrence of the reversed substring in the reversed string
    modified_reversed_str = reversed_str.replace(reversed_substring, reversed_replacement, 1)

    # Reverse the modified string back to original order
    modified_str = modified_reversed_str[::-1]

    return modified_str


def init_csv(path):
    pass
    # global pd_csv
    # pd_csv = pd.read_csv(path)


def get_csv_row(index):
    global pd_csv
    global pd_last_row
    global pd_row
    pd_last_row = index
    pd_row = pd_csv.iloc[index]
    return pd_row


def num_to_str(obj):
    if isinstance(obj, (int, float)):
        return int(obj)
    return obj


def convert_dict_values_to_str(dict):
    for key, value in dict.items():
        dict[key] = str(value)
        if dict[key] == "nan":
            dict[key] = ""
        elif type(value) == float or type(value) == int:
            dict[key] = str(int(value))
    return dict


# def csv_to_json(key_field, csv_file_path, json_file_path):
#     # Read the CSV file
#     df = pd.read_csv(csv_file_path)
#     # Replace "nan" values with empty strings
#     df.fillna('', inplace=True)
#     # Convert the DataFrame to a dictionary with 'pid' as the key
#     data = df.set_index(key_field).T.to_dict()
#
#     # Save to a JSON file
#     with open(json_file_path, 'w', encoding='utf-8') as json_file:
#         pd.json.dump(data, json_file, indent=4, cls=json.JSONEncoder(default=num_to_str))
# def get_csv_row(index):
#     global pd_csv
#     global pd_last_row
#     global pd_row
#     pd_last_row = index
#     pd_row = pd_csv.iloc[index]
#     return pd_row

def get_utils_path() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def search_csv(csv_file_path, field_name, search_value):
    pass
    # fpath = csv_file_path
    # if not os.path.exists(fpath):
    #     current_path = os.path.dirname(os.path.abspath(__file__))
    #     fpath = f"{current_path}/{csv_file_path}"
    # df = pd.read_csv(fpath)
    # # Replace "nan" values with empty strings
    # # df = df.fillna('', inplace=True)
    # # Filter the DataFrame based on the search criteria
    # matching_rows = df[df[field_name] == search_value]
    # # Convert matching rows to a list of dictionaries
    # result = matching_rows.to_dict(orient='records')
    # result[0] = convert_dict_values_to_str(result[0])  # removes floats and nan
    #
    # return result


def is_path_ok(path, _executable=False):
    if not path:
        return False
    if not os.path.exists(path):
        print(f"{path} not exist.")
        return False
    if not os.access(path, os.R_OK):
        print(f"{path} not readable.")
        return False
    if not os.access(path, os.W_OK):
        print(f"{path} not writable.")
        return False
    if _executable and (not os.access(path, os.X_OK)):
        print(f"{path} not executable.")
        return False
    return True


def get_current_directory():
    return str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")


def get_parent_directory():
    return str(Path(get_current_directory()).parent).replace("\\", "/")


def get_text_between_2str(text: str,
                          str1: str,
                          str2: str,
                          start: int = 0
                          ):
    # Find the first occurrence of str1 starting from the given index
    if start > len(text):
        return "", 0
    start = text.find(str1, start)
    if start < 0:
        return "", 0

    # Adjust start to be right after the found str1
    start += len(str1)

    # Find the first occurrence of str2 starting from the new start index
    end = text.find(str2, start)
    if end < 0:
        return "", 0

    # Extract the substring between str1 and str2
    substring = text[start:end]
    return substring, end


def computeMD5hash(self, data_string):
    m = hashlib.md5()
    s = str(data_string).encode('utf-8')
    m.update(s)
    return m.hexdigest()


def get_str_date_now():
    rundt = datetime.now()
    date_str = rundt.strftime("%y%m%d_%H%M%S")
    return date_str


def get_set_dict_default(dictobj: dict, key: str, default: any):
    if dictobj and key in dictobj:
        return dictobj[key]
    else:
        dictobj[key] = default
    return default


def safe_field_access(obj, fieldname):
    msg = ""
    if obj and hasattr(obj, fieldname):
        msg = getattr(obj, fieldname)
    return msg


def get_platform():
    platform = None
    if sys.platform == "darwin":
        platform = "mac"
    elif sys.platform == "linux":
        platform = "linux"
    elif sys.platform == "win32":
        platform = "windows"
    return platform


def get_platform_path(path):
    platform = get_platform()
    if platform == "windows":
        path = convert_posix_to_win_path(path)
    return path


def convert_posix_to_win_path(posix_path: str = None):
    mod_path = None
    if posix_path and len(posix_path) > 0:
        mod_path = Path(posix_path)
    return mod_path


def json_save(json_path: str = "", data_dict: dict = None, indentsize: int = 1):
    path = Path(json_path)
    try:
        # Use text mode instead of binary for JSON
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=indentsize)

        # Cross-platform permission setting
        if os.name != 'nt':  # Not Windows
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)  # 644
        else:  # Windows
            # Make file readable/writable for owner
            os.chmod(path, stat.S_IWRITE | stat.S_IREAD)

        return True
    except Exception as err:
        print(f"Error saving JSON: {err}")
        return False


def json_open(json_path: str = None):
    path = Path(json_path)
    if not path or not os.path.exists(path):
        # print("Invalid input JSON path", path)
        return None
    with open(path) as f:
        return json.load(f)


def get_text(path):
    with open(path, "rb") as f:
        rc = f.read()
    return "".join(map(chr, rc))


def put_text(path, data, _async=False):
    if _async:
        put_text_async(path, data)
        return True
    with open(path, 'wt', encoding='utf-8') as f:
        rc = f.write(data)
    time.sleep(1)
    if len(get_text(path)) == len(data):
        return True
    return False


def delete_file(path):
    if not path:
        return False
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


# manager‐wide lock to protect creation of per-path queues
_manager_lock = threading.Lock()
# map file path -> queue of pending data strings
_queues: Dict[str, queue.Queue] = {}


def put_text_async(path: str, data: str) -> None:
    """
    Enqueue a save for `path` and return immediately.
    If this is the first time we’ve seen `path`, start a dedicated worker thread.
    Subsequent calls to the same path simply queue up data to be written, one after another.
    """
    with _manager_lock:
        if path not in _queues:
            q = queue.Queue()
            _queues[path] = q
            worker = threading.Thread(target=put_text_worker, args=(path,), daemon=True)
            worker.start()
        else:
            q = _queues[path]
    # enqueue the new data
    q.put(data)


def put_text_worker(path: str):
    """
    Worker thread for a single file path: pulls pending data off the queue
    and does the blocking write+verify before pulling the next one.
    """
    q = _queues[path]
    while True:
        data = q.get()
        try:
            # synchronous save
            with open(path, 'wt', encoding='utf-8') as f:
                f.write(data)
            # your existing sleep/verify logic
            time.sleep(1)
            if len(_get_text(path)) != len(data):
                # handle verification failure however you like
                print(f"[Warning] write‐verification failed for {path}")
        except Exception as e:
            print(f"[Error] saving {path}: {e}")
        finally:
            q.task_done()


def _get_text(path: str) -> str:
    """Helper to read back the file for your length‐check."""
    with open(path, 'rt', encoding='utf-8') as f:
        return f.read()


def get_files_in_dir(path: str = None):
    if path:
        return glob.glob(path)
    return None


def list_files(rootpath, filter='*.*'):
    result = []
    for x in os.walk(rootpath):
        for y in glob(os.path.join(x[0], filter)):
            result.append(y)
    return result


def list_directories(rootpath, filter='*/'):
    result = []
    path = rootpath + filter
    for y in glob(path):
        result.append(y)
    return result


def generate_key_from_password(password: str) -> bytes:
    """
    Generate a Fernet key from a password using SHA-256
    """
    # Create SHA-256 hash of the password
    password_hash = hashlib.sha256(password.encode()).digest()
    # Convert the hash to URL-safe base64 format (required by Fernet)
    key = base64.urlsafe_b64encode(password_hash)
    return key


def encrypt_data(data: str, password: str) -> str:
    """
    Encrypt data using a password

    Args:
        data: String to encrypt
        password: Password to generate encryption key

    Returns:
        Encrypted data as a string
    """
    try:
        # Generate key from password
        key = generate_key_from_password(password)

        # Create Fernet cipher
        cipher = Fernet(key)

        # Encrypt the data
        encrypted_data = cipher.encrypt(data.encode())

        # Return encrypted data as string
        return encrypted_data.decode()

    except Exception as e:
        raise Exception(f"Encryption error: {str(e)}")


def decrypt_data(encrypted_data: str, password: str) -> str:
    """
    Decrypt data using a password

    Args:
        encrypted_data: Encrypted string to decrypt
        password: Password used for encryption

    Returns:
        Decrypted data as a string
    """
    try:
        # Generate key from password
        key = generate_key_from_password(password)

        # Create Fernet cipher
        cipher = Fernet(key)

        # Decrypt the data
        decrypted_data = cipher.decrypt(encrypted_data.encode())

        # Return decrypted data as string
        return decrypted_data.decode()

    except Exception as e:
        raise Exception(f"Decryption error: {str(e)}")


def encode_base64(data: str) -> str:
    """
    Encode a string to base64

    Args:
        data: String to encode

    Returns:
        Base64 encoded string
    """
    try:
        # Convert string to bytes and encode to base64
        encoded_bytes = base64.b64encode(data.encode())
        # Convert bytes back to string and return
        return encoded_bytes.decode()
    except Exception as e:
        print(f"Base64 encoding error: {str(e)}")
    return None


def decode_base64(encoded_data: str) -> str:
    """
    Decode a base64 string

    Args:
        encoded_data: Base64 encoded string to decode

    Returns:
        Decoded string
    """
    try:
        # Convert string to bytes and decode from base64
        decoded_bytes = base64.b64decode(encoded_data.encode())
        # Convert bytes back to string and return
        return decoded_bytes.decode()
    except Exception as e:
        print(f"Base64 decoding error: {str(e)}")
    return encoded_data


def find_file(folder_path: str, find: str = "tableDownload*", version: int = 0) -> Optional[str]:
    """
    Find a file in a folder by glob pattern, return the Nth most recent by modification time.
    Cross-platform (Mac, Windows, Linux).

    Args:
        folder_path: Directory to search in
        find: Glob pattern (e.g. "tableDownload*.csv" or "tableDownload*")
        version: 0 = most recent, 1 = second most recent (or sole file if only 1 found), etc.

    Returns:
        Full path to the file, or None if not found
    """
    if not folder_path or not os.path.exists(folder_path):
        return None
    if not os.path.isdir(folder_path):
        return None
    # Use pathlib for cross-platform path handling (Mac/Windows)
    pattern = str(Path(folder_path) / find)
    matches = glob(pattern)
    if not matches:
        return None
    # Sort by mtime descending (most recent first); os.path.getmtime is cross-platform
    matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    if version < 0:
        return None
    # version=1 with only 1 file: return that file path
    if version >= len(matches):
        if version == 1 and len(matches) == 1:
            return str(Path(matches[0]).resolve())
        return None
    return str(Path(matches[version]).resolve())


def file_copy(src_path: str, dst_path: str, overwrite: bool = False, move: bool = False) -> bool:
    """
    Copy or move a file from source to destination. Renames to dst_path.
    Validates the copy succeeded (destination exists and same size as source).

    Args:
        src_path: Source file path
        dst_path: Destination file path (can include new filename)
        overwrite: If True, overwrite destination file if it exists
        move: If True, move the file instead of copying

    Returns:
        bool: True if operation succeeded and validated, False otherwise
    """
    try:
        if not os.path.exists(src_path):
            print(f"Source file '{src_path}' does not exist")
            return False

        if os.path.exists(dst_path):
            if not overwrite:
                print(f"Destination file '{dst_path}' already exists and overwrite=False")
                return False

        src_size = os.path.getsize(src_path)

        if move:
            shutil.move(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)  # copy2 preserves metadata

        # Validate: destination exists and has same size
        if not os.path.exists(dst_path):
            print(f"Validation failed: destination '{dst_path}' does not exist after copy")
            return False
        if not move and os.path.getsize(dst_path) != src_size:
            print(f"Validation failed: destination size {os.path.getsize(dst_path)} != source size {src_size}")
            return False

        return True

    except Exception as e:
        print(f"Error {'moving' if move else 'copying'} file: {str(e)}")
        return False

def append_text(path, text):
    """Appends text to a file, creating the file if it doesn't exist.

    Args:
        path (str): The path to the file.
        text (str): The text to append.

    Returns:
        bool: True if the text was successfully appended, False otherwise.
    """
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"Error appending to file: {e}")
        return False
