from sglib.constants import *
from sglib.log import LOG
from sglib.math import clip_max, clip_min
import ctypes
import json
import math
import multiprocessing
import os
import random
import re
import subprocess
import sys
import time


if IS_LINUX:
    from .path.linux import *
elif IS_WINDOWS:
    from .path.windows import *

IS_A_TTY = sys.stdin.isatty()

terminating_char = "\\"

PROJECT_FILE_TYPE = f'Stargate Project ({MAJOR_VERSION}.project)'
SAMPLER_FILE_TYPE = 'Sampler1 Sample File (*.sampler1)'
SAMPLER_FILE_TYPE_EXT = '.sampler1'

TIMESTRETCH_MODES = [
    "None",
    "Pitch(affecting time)",
    "Time(affecting pitch)",
    "Rubberband",
    "Rubberband(formants)",
    "SBSMS",
    "Paulstretch",
]

TIMESTRETCH_INDEXES = {
    x:y for x, y in zip(
        TIMESTRETCH_MODES,
        range(len(TIMESTRETCH_MODES)),
    )
}

if IS_WINDOWS:
    TIMESTRETCH_MODES.remove("SBSMS")
elif IS_MAC_OSX:
    TIMESTRETCH_MODES.remove("Paulstretch")

CRISPNESS_SETTINGS = [
    "0 (smeared)",
    "1 (piano)",
    "2",
    "3",
    "4",
    "5 (normal)",
    "6 (sharp, drums)",
]

BIN_PATH = None

WITH_AUDIO = True

ENGINE_RETCODE = None

CPU_COUNT = multiprocessing.cpu_count()
if CPU_COUNT < 1:
    CPU_COUNT = 1

def _meta_dot_json():
    with open(META_DOT_JSON_PATH) as f:
        return json.load(f)

META_DOT_JSON = _meta_dot_json()

LOG.info("install prefix:  {}".format(INSTALL_PREFIX))

beat_fracs = ['1/16', '1/8', '1/4', '1/3', '1/2', '1/1']

BAR_FRACS = ['1/4', '1/8', '1/12', '1/16', '1/32']

BAR_FRACS_DICT = {
    '1/4':0.25,
    '1/8':0.125,
    '1/12':0.083333333,
    '1/16':0.0625,
    '1/32':0.03125,
}

INT_TO_NOTE = [
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',
]

TERMINAL = None
PYTHON3 = sys.executable

PAULSTRETCH_PATH = f"{MAJOR_VERSION}-paulstretch"

if IS_WINDOWS:
    sbsms_util = os.path.join(
        INSTALL_PREFIX,
        "sgui",
        "engine",
        "sbsms.exe",
    )
else:
    sbsms_util = f"{MAJOR_VERSION}-sbsms"

AUDIO_FILE_EXTS = [".WAV", ".AIF", ".AIFF", ".FLAC"]
MIDI_FILE_EXTS = [".MIDI", ".MID"]
AUDIO_MIDI_FILE_EXTS = AUDIO_FILE_EXTS + MIDI_FILE_EXTS

MAX_EXT_LEN = max(len(x) for x in AUDIO_MIDI_FILE_EXTS)

SHOW_CREATE_FOLDER_ERROR = False

IS_LIVE_MODE = False

USE_HUGEPAGES = 0

DEVICE_SETTINGS = {}
DEVICE_CONFIG_PATH = os.path.join(CONFIG_DIR, "device.txt")

MIDI_IN_DEVICES = []

SAMPLE_RATE = None
NYQUIST_FREQ = None

PROJECT_HISTORY_SCRIPT = f"{MAJOR_VERSION}-project-recover"

bad_chars = ["|", "\\", "~", "."]

def pi_path(a_file):
    "Platform independent path"
    a_file = os.path.normpath(str(a_file))
    return a_file.replace("\\", "/") if IS_WINDOWS else a_file

def which(a_file):
    """ Python equivalent of the UNIX "which" command """
    f_path_arr = os.getenv("PATH").split(";" if IS_WINDOWS else ":")
    if IS_WINDOWS and BIN_DIR not in f_path_arr:
        f_path_arr.insert(0, BIN_DIR)
    for f_path in (pi_path(x) for x in f_path_arr):
        f_file_path = os.path.join(f_path, a_file)
        if os.path.exists(f_file_path) and not os.path.isdir(f_file_path):
            return f_file_path
        if IS_WINDOWS:
            f_file_path += ".exe"
            if os.path.exists(f_file_path) \
            and not os.path.isdir(f_file_path):
                return f_file_path
    return None

for _terminal in ("x-terminal-emulator", "gnome-terminal", "konsole"):
    if which(_terminal):
        TERMINAL = _terminal
        break

RUBBERBAND_PATH = which("rubberband")


class WinVolInfo:
    def __init__(self):
        self.volumeNameBuffer = ctypes.create_unicode_buffer(1024)
        self.fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)

    def get_label(self, drive):
        #retcode = \
        ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            self.volumeNameBuffer,
            ctypes.sizeof(self.volumeNameBuffer),
            None, None, None,
            self.fileSystemNameBuffer,
            ctypes.sizeof(self.fileSystemNameBuffer)
        )
        return str(self.volumeNameBuffer.value)

if IS_WINDOWS:
    WIN_VOL_INFO = WinVolInfo()

def get_win_drives():
    from ctypes import windll
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for x in range(ord('A'), ord('Z') + 1):
        if bitmask & 1:
            drive = chr(x) + ":\\"
            label = WIN_VOL_INFO.get_label(drive)
            drives.append((drive, label))
        bitmask >>= 1
    return drives

def run_stargate():
    f_bin = which(MAJOR_VERSION)
    subprocess.Popen([f_bin])

def set_bin_path():
    global BIN_PATH
    # Try the local dev version first, if one is running stargate.py from
    # the repo
    BIN_PATH = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'engine',
            f"{MAJOR_VERSION}-engine",
        )
    )
    if IS_WINDOWS:
        BIN_PATH += '.exe'
    if not os.path.exists(BIN_PATH):
        # Otherwise, use the system binary
        BIN_PATH = f"{MAJOR_VERSION}-engine"
    LOG.info(f"BIN_PATH=={BIN_PATH}")

def get_unix_timestamp(a_dt):
    if IS_WINDOWS:
        assert sys.version_info >= (3, 3), "Must have Python3.3 or later"
        return int(a_dt.timestamp())
    else:
        return int(a_dt.strftime("%s"))

def remove_bad_chars(a_str):
    """ Remove any characters that have special meaning to Stargate """
    f_str = str(a_str)
    for f_char in bad_chars:
        f_str = f_str.replace(f_char, "")
    return f_str

def str_has_bad_chars(a_str):
    f_str = str(a_str)
    for f_char in bad_chars:
        if f_char in f_str:
            return False
    return True

def case_insensitive_path(a_path, a_assert=True):
    f_path = os.path.abspath(str(a_path))
    if os.path.exists(f_path):
        return a_path
    else:
        if os.path.sep != '/' and os.path.sep in f_path:
            f_path_arr = f_path.split(os.path.sep)
        else:
            f_path_arr = f_path.split('/')
        f_path_arr = [x for x in f_path_arr if x]
        f_path = "" if IS_WINDOWS else "/"
        for f_dir in f_path_arr:
            if os.path.exists(os.path.join(f_path, f_dir)):
                f_path = os.path.join(f_path, f_dir)
            else:
                f_found = False
                for f_real_dir in os.listdir(f_path):
                    if f_dir.lower() == f_real_dir.lower():
                        f_found = True
                        f_path = os.path.join(f_path, f_real_dir)
                        break
                if not f_found:
                    if a_assert:
                        assert False, "File not found '{}'".format(a_path)
                    else:
                        return None
        LOG.info(f_path)
        return f_path

def is_audio_file(a_file):
    return is_file_type(a_file, AUDIO_FILE_EXTS)

def is_midi_file(a_file):
    return is_file_type(a_file, MIDI_FILE_EXTS)

def is_audio_midi_file(a_file):
    return is_file_type(a_file, AUDIO_MIDI_FILE_EXTS)

def is_file_type(a_file, a_list):
    """ Only checks the extension, not the MIME type """
    f_file = str(a_file)[-MAX_EXT_LEN:].upper()
    for f_file in (x for x in a_list if f_file.endswith(x)):
        return True
    return False

def beat_frac_text_to_float(f_index):
    if f_index == 0:
        return 0.0625
    elif f_index == 1:
        return 0.125
    elif f_index == 2:
        return 0.25
    elif f_index == 3:
        return 0.33333333
    elif f_index == 4:
        return 0.5
    elif f_index == 5:
        return 1.0
    else:
        return 0.25

def bar_frac_text_to_float(a_text):
    return BAR_FRACS_DICT[str(a_text)] * 4.0

def scale_to_rect(a_to_scale, a_scale_to):
    """ Returns a tuple that scales one QRectF to another """
    f_x = (a_scale_to.width() / a_to_scale.width())
    f_y = (a_scale_to.height() / a_to_scale.height())
    return (f_x, f_y)

def beats_to_index(a_beat, a_divisor=4.0):
    f_index = int(a_beat / a_divisor)
    f_start = a_beat - (float(f_index) * a_divisor)
    return f_index, round(f_start, 6)

def rubberband(
    a_src_path,
    a_dest_path,
    a_timestretch_amt,
    a_pitch_shift,
    a_crispness,
    a_preserve_formants=False,
):
    if a_preserve_formants:
        f_cmd = [
            RUBBERBAND_PATH,
            "-F",
            "-c",
            str(a_crispness),
            "-t",
            str(a_timestretch_amt),
            "-p",
            str(a_pitch_shift),
            "-R",
            "--pitch-hq",
            a_src_path,
            a_dest_path,
        ]
    else:
        f_cmd = [
            RUBBERBAND_PATH,
            "-c",
            str(a_crispness),
            "-t",
            str(a_timestretch_amt),
            "-p",
            str(a_pitch_shift),
            "-R",
            "--pitch-hq",
            a_src_path,
            a_dest_path,
        ]
    LOG.info("Running {}".format(" ".join(f_cmd)))
    f_proc = subprocess.Popen(f_cmd)
    return f_proc

def sbsms(
    a_src_path,
    a_dest_path,
    a_timestretch_amt,
    a_pitch_shift,
):
    f_cmd = [
        sbsms_util,
        a_src_path,
        a_dest_path,
        str(1.0 / a_timestretch_amt),
        str(1.0 / a_timestretch_amt),
        str(a_pitch_shift), str(a_pitch_shift)
    ]
    LOG.info("Running {}".format(" ".join(f_cmd)))
    f_proc = subprocess.Popen(f_cmd)
    return f_proc

def read_file_text(a_file):
    with open(pi_path(a_file)) as f_handle:
        return f_handle.read()

def write_file_text(a_file, a_text):
    with open(pi_path(a_file), "w", newline="\n") as f_handle:
        f_handle.write(str(a_text))

def gen_uid():
    """Generated an integer uid.  Adding together multiple random
        numbers gives a far less uniform distribution of
        numbers, more of a natural white noise kind of sample graph
        than a brick-wall digital white noise... """
    f_result = 5
    for i in range(6):
        f_result += random.randint(6, 50000000)
    return f_result

def note_num_to_string(a_note_num):
    f_note = int(a_note_num) % 12
    f_octave = (int(a_note_num) // 12) - 2
    return "{}{}".format(INT_TO_NOTE[f_note], f_octave)

def string_to_note_num(a_str):
    f_str = str(a_str).lower()
    if len(f_str) >=2 and len(f_str) < 5 and re.match('[a-g](.*)[0-8]', f_str):
        f_notes = {'c':0, 'd':2, 'e':4, 'f':5, 'g':7, 'a':9, 'b':11}
        for k, v in f_notes.items():
            if f_str.startswith(k):
                f_str = f_str.replace(k, "", 1)
                f_sharp_flat = 0
                if f_str.startswith("#"):
                    f_sharp_flat = 1
                    f_str = f_str[1:]
                elif f_str.startswith("b"):
                    f_sharp_flat = -1
                    f_str = f_str[1:]
                f_result = (int(f_str) * 12) + v + f_sharp_flat
                assert(f_result >= 0 and f_result <= 127)
                return f_result
        return a_str
    else:
        return a_str

def bool_to_int(a_bool):
    if a_bool:
        return "1"
    else:
        return "0"

def int_to_bool(a_int):
    if isinstance(a_int, bool):
        return a_int

    if int(a_int) == 0:
        return False
    elif int(a_int) == 1:
        return True
    else:
        assert(False)

def print_sorted_dict(a_dict):
    """ Mostly intended for printing locals() and globals() """
    for k in sorted(list(a_dict.keys())):
        print("{} : {}".format(k, a_dict[k]))

def time_quantize_round(a_input):
    """Properly quantize time values from QDoubleSpinBoxes
        that measure beats
    """
    if round(a_input) == round(a_input, 2):
        return round(a_input)
    else:
        return round(a_input, 6)

def musical_time_to_seconds(a_tempo, a_bar, a_beat):
    f_seconds_per_beat = 60.0 / float(a_tempo)
    f_beats = (float(a_bar) * 4.0) + float(a_beat)
    return f_seconds_per_beat * f_beats

class OnePoleLP:
    def __init__(self, a_val, a_fc=0.33):
        self.a0 = 1.0
        self.b1 = 0.0
        self.z1 = a_val
        self.set_fc(a_fc)

    def set_fc(self, a_fc):
        self.b1 = math.exp(-2.0 * math.pi * a_fc);
        self.a0 = 1.0 - self.b1;

    def process(self, a_in):
        self.z1 = a_in * self.a0 + self.z1 * self.b1
        return self.z1

def wait_for_finished_file(a_file):
    """ Wait until a_file exists, then delete it and return.  It should
        already have the .finished extension
    """
    while True:
        if os.path.isfile(a_file):
            try:
                os.remove(a_file)
                break
            except:
                LOG.error("wait_for_finished_file:  Exception "
                    "when deleting {}".format(a_file))
        else:
            time.sleep(0.1)

def get_wait_file_path(a_file):
    f_wait_file = "{}.finished".format(a_file)
    if os.path.isfile(f_wait_file):
        os.remove(f_wait_file)
    return f_wait_file

def seconds_to_time_str(a_seconds, a_sections=1):
    f_seconds = float(a_seconds)
    f_inc = f_seconds / a_sections
    if f_seconds > 3600.0:  # 60 * 60
        if a_sections == 1:
            return time.strftime("%H:%M", time.gmtime(f_seconds))
        else:
            return [time.strftime("%H:%M", time.gmtime(x * f_inc))
                for x in range(a_sections)]
    elif f_seconds > 60.0:
        if a_sections == 1:
            return time.strftime("%M:%S", time.gmtime(f_seconds))
        else:
            return [time.strftime("%M:%S", time.gmtime(x * f_inc))
                for x in range(a_sections)]
    else:
        if a_sections == 1:
            return str(round(f_seconds, 2))
        else:
            return [str(round(x * f_inc, 2)) for x in range(a_sections)]

def get_file_setting(a_name, a_type, a_default):
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    if os.path.exists(f_file_name):
        try:
            with open(f_file_name) as f_file:
                return a_type(f_file.read())
        except Exception as ex:
            LOG.error("Error in get_file_setting {}".format(ex))
            os.remove(f_file_name)
    return a_default

def set_file_setting(a_name, a_val):
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    with open(f_file_name, "w", newline="\n") as f_file:
        f_file.write(str(a_val))

def clear_file_setting(a_name):
    path = os.path.join(CONFIG_DIR, f"{a_name}.txt")
    if os.path.exists(path):
        os.remove(path)

def delete_device_config():
    global DEVICE_SETTINGS
    DEVICE_SETTINGS = {}
    if os.path.exists(DEVICE_CONFIG_PATH):
        os.remove(DEVICE_CONFIG_PATH)

def read_device_config():
    global BIN_PATH, DEVICE_SETTINGS, MIDI_IN_DEVICES
    global WITH_AUDIO, USE_HUGEPAGES

    DEVICE_SETTINGS = {}
    MIDI_IN_DEVICES = []

    try:
        if os.path.isfile(DEVICE_CONFIG_PATH):
            f_file_text = read_file_text(DEVICE_CONFIG_PATH)
            for f_line in f_file_text.split("\n"):
                if f_line.strip() == "\\":
                    break
                if f_line.strip() != "":
                    f_key, f_val = (x.strip() for x in f_line.split("|", 1))
                    if f_key == "midiInDevice":
                        MIDI_IN_DEVICES.append(f_val)
                    else:
                        DEVICE_SETTINGS[f_key] = f_val
            MIDI_IN_DEVICES.sort()
            set_bin_path()
            WITH_AUDIO = True

            if (
                "hugePages" in DEVICE_SETTINGS
                and
                int(DEVICE_SETTINGS["hugePages"]) == 1
            ):
                USE_HUGEPAGES = 1

            global SAMPLE_RATE, NYQUIST_FREQ
            SAMPLE_RATE = int(DEVICE_SETTINGS["sampleRate"])
            NYQUIST_FREQ = SAMPLE_RATE / 2
    except Exception as ex:
        LOG.error(
            "Exception while reading device config,"
            " deleting and starting over\n{}".format(ex)
        )
        LOG.exception(ex)
        DEVICE_SETTINGS = {}

    LOG.info("BIN_PATH == {}".format(BIN_PATH))

read_device_config()

def rgb_minus(a_rgb, a_amt):
    f_result = []
    for f_color in a_rgb:
        f_result.append(clip_min(f_color - a_amt, 0))
    return f_result

def rgb_plus(a_rgb, a_amt):
    f_result = []
    for f_color in a_rgb:
        f_result.append(clip_max(f_color + a_amt, 255))
    return f_result

class name_uid_dict:
    def gen_file_name_uid(self):
        while self.high_uid in self.name_lookup:
            self.high_uid += 1
        return self.high_uid

    def __init__(self):
        self.high_uid = 0
        self.name_lookup = {}
        self.uid_lookup = {}

    def add_item(self, a_uid, a_name):
        f_uid = int(a_uid)
        a_name = pi_path(a_name)
        self.name_lookup[f_uid] = a_name
        self.uid_lookup[a_name] = f_uid
        if f_uid > self.high_uid:
            self.high_uid = f_uid

    def add_new_item(self, a_name, a_uid=None):
        if a_name in self.uid_lookup:
            raise Exception
        if a_uid is None:
            f_uid = self.gen_file_name_uid()
        else:
            f_uid = a_uid
        self.add_item(f_uid, a_name)
        return f_uid

    def get_uid_by_name(self, a_name):
        return self.uid_lookup[str(a_name)]

    def get_name_by_uid(self, a_uid):
        return self.name_lookup[int(a_uid)]

    def rename_item(self, a_old_name, a_new_name):
        f_uid = self.get_uid_by_name(a_old_name)
        f_new_name = str(a_new_name)
        f_old_name = self.name_lookup[f_uid]
        self.uid_lookup.pop(f_old_name)
        self.add_item(f_uid, f_new_name)

    def uid_exists(self, a_uid):
        return int(a_uid) in self.name_lookup

    def name_exists(self, a_name):
        return str(a_name) in self.uid_lookup

    def get_takes(self):
        f_result = {}
        for k in self.uid_lookup:
            f_regex = re.search("[0-9]+$", k)
            if f_regex:
                f_int = f_regex.group()
                f_str = k[:f_regex.start()]
                if f_str in f_result:
                    f_result[f_str].append(f_int)
                else:
                    f_result[f_str] = [f_int]
        return {k:sorted(v, key=lambda x: int(x))
            for k, v in f_result.items() if len(v) > 1}

    @staticmethod
    def from_str(a_str):
        f_result = name_uid_dict()
        f_lines = a_str.split("\n")
        for f_line in f_lines:
            if f_line == terminating_char:
                break
            f_arr = f_line.split("|", 1)
            f_uid = int(f_arr[0])
            f_name = f_arr[1]
            f_result.add_item(f_uid, f_name)
        return f_result

    def __str__(self):
        f_result = []
        for k in sorted(self.name_lookup.keys()):
            v = self.name_lookup[k]
            f_result.append("|".join((str(k), pi_path(v))))
        f_result.append(terminating_char)
        return "\n".join(f_result)

    def __len__(self):
        return len(self.name_lookup)

def proj_file_str(a_val):
    f_val = a_val
    if isinstance(f_val, float):
        f_val = round(a_val, 6)
    return str(f_val)

