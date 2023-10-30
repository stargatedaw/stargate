from sglib.constants import *
from sglib.hardware.rpi import is_rpi
from sglib.log import LOG
from sglib.math import clip_max, clip_min, clip_value
import ctypes
import json
import math
import os
import platform
import random
import re
import subprocess
import sys
import tempfile
import time
from sg_py_vendor import wavefile

import psutil
import yaml

KEY_CTRL = 'CTRL'
KEY_ALT = 'ALT'

if IS_LINUX:
    from .path.linux import *
elif IS_MACOS:
    KEY_CTRL = 'CMD'
    KEY_ALT = 'OPT'
    from .path.macos import *
elif IS_WINDOWS:
    from .path.windows import *
else:
    raise OSError('Unsupported platform: {platform.platform()}')

terminating_char = "\\"

PROJECT_FILE_TYPE = f'Stargate Project ({MAJOR_VERSION}.project)'
SAMPLER_FILE_TYPE = 'Sampler1 Sample File (*.sampler1)'
SAMPLER_FILE_TYPE_EXT = '.sampler1'

TIMESTRETCH_MODES = [
    "None",
    "Pitch (affecting time)",
    "Time (affecting pitch)",
    "Rubberband",
    "Rubberband (formants)",
    "SBSMS",
    "Paulstretch",
    'Soundtouch',
    'Soundtouch (speech)',
]
SBSMS = None

TIMESTRETCH_INDEXES = {
    x:y for x, y in zip(
        TIMESTRETCH_MODES,
        range(len(TIMESTRETCH_MODES)),
    )
}
TIMESTRETCH_INDEXES_REVERSE = {y: x for x, y in TIMESTRETCH_INDEXES.items()}


CRISPNESS_SETTINGS = [
    "0 (smeared)",
    "1 (piano)",
    "2",
    "3",
    "4",
    "5 (normal)",
    "6 (sharp, drums)",
]

ITEM_SNAP_DIVISORS = {
    0: 4.0,
    1: 1.0,
    2: 2.0,
    3: 3.0,
    4: 4.0,
    5: 8.0,
    6: 16.0,
    7: 32.0,
}

BIN_PATH = None

WITH_AUDIO = True

ENGINE_RETCODE = None

CPU_COUNT = psutil.cpu_count(logical=False)
if CPU_COUNT is None:
    import multiprocessing
    CPU_COUNT = multiprocessing.cpu_count()
    if not is_rpi():  # Assume SMT
        CPU_COUNT /= 2
# engine does not support more than 16
CPU_COUNT = clip_value(CPU_COUNT, 1, 16)
AUTO_CPU_COUNT = clip_value(
    CPU_COUNT if CPU_COUNT <= 2 else CPU_COUNT - 1,
    1,
    4,
)

def sg_open(path: str, mode: str='r', **kwargs):
    return open(path, mode, encoding='utf-8', **kwargs)

def _meta():
    with sg_open(META_DOT_JSON_PATH) as f:
        meta_dot_json = json.load(f)
    if os.path.exists(COMMIT_PATH):
        with sg_open(COMMIT_PATH) as f:
            commit_hash = f.read()
    else:
        commit_hash = 'unknown'
    return meta_dot_json, commit_hash

META_DOT_JSON, COMMIT_HASH = _meta()

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
    appdir = os.environ.get('APPDIR', None)
    if IS_LINUX and appdir:
        f_path_arr = [
            os.path.join(appdir, x)
            for x in (
                'usr/bin',
                'usr/local/bin',
            )
        ] + f_path_arr
    for f_path in (pi_path(x) for x in f_path_arr):
        f_file_path = os.path.join(f_path, a_file)
        if os.path.exists(f_file_path) and not os.path.isdir(f_file_path):
            return f_file_path
        if IS_WINDOWS:
            f_file_path += ".exe"
            if os.path.exists(f_file_path) \
            and not os.path.isdir(f_file_path):
                return f_file_path
    LOG.warning(f'which(): failed to find {a_file} in {f_path_arr}')
    return None


if IS_WINDOWS:
    RUBBERBAND_PATH = os.path.join(
        ENGINE_DIR,
        'rubberband.exe',
    )
    SBSMS = os.path.join(
        ENGINE_DIR,
        "sbsms.exe",
    )
    SOUNDSTRETCH = os.path.join(
        ENGINE_DIR,
        "soundstretch.exe",
    )
    PAULSTRETCH_PATH = sys.executable
elif IS_MACOS:
    if IS_LOCAL_DEVEL:
        RUBBERBAND_PATH = which('rubberband')
        PAULSTRETCH_PATH = sys.argv[0]
        # Prefer the vendored SBSMS
        SBSMS = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'vendor',
            'sbsms',
            'cli',
            'sbsms',
        )
        SOUNDSTRETCH = os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'vendor',
            'stargate-soundstretch',
        )
    else:
        PAULSTRETCH_PATH = sys.executable
        RUBBERBAND_PATH = os.path.join(
            ENGINE_DIR,
            "rubberband",
        )
        SBSMS = os.path.join(
            ENGINE_DIR,
            "sbsms",
        )
        SOUNDSTRETCH = os.path.join(
            ENGINE_DIR,
            "stargate-soundstretch",
        )
elif IS_LINUX:
    RUBBERBAND_PATH = which("rubberband")
    SOUNDSTRETCH = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'vendor',
        'stargate-soundstretch',
    )
    if not os.path.exists(SOUNDSTRETCH):
        SOUNDSTRETCH = os.path.join(
            ENGINE_DIR,
            'stargate-soundstretch',
        )
    if not os.path.exists(SOUNDSTRETCH):
        SOUNDSTRETCH = os.path.join(
            ENGINE_DIR,
            'stargate-soundstretch',
        )
    if not os.path.exists(SOUNDSTRETCH):
        SOUNDSTRETCH = which("stargate-soundstretch")
    assert SOUNDSTRETCH, SOUNDSTRETCH
    # Prefer the vendored SBSMS
    SBSMS = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'vendor',
        'sbsms',
        'cli',
        'sbsms',
    )
    if not os.path.exists(SBSMS):
        try:
            SBSMS = os.path.join(
                ENGINE_DIR,
                "sbsms",
            )
        except NameError:
            pass
    if not os.path.exists(SBSMS):
        SBSMS = which(f"{MAJOR_VERSION}-sbsms")
        if not SBSMS:
            SBSMS = which("sbsms")
    if IS_NUITKA:
        PAULSTRETCH_PATH = sys.executable
    else:
        PAULSTRETCH_PATH = sys.argv[0]
else:
    raise NotImplementedError("Unsupported platform")

if not SBSMS or not os.path.exists(SBSMS):
    LOG.info(f'Cannot find SBSMS, removing from timestretch options')
    TIMESTRETCH_MODES.remove("SBSMS")

def has_pasuspender(cmd) -> list:
    """ Test for the presence of PulseAudio pasuspender and see it if works
    """
    if (
        not is_rpi()
        and
        which("pasuspender") is not None
        and
        os.system("pasuspender sleep 0.1") == 0
    ):
        return ['pasuspender', '--'] + cmd
    return cmd


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
            None,
            None,
            None,
            self.fileSystemNameBuffer,
            ctypes.sizeof(self.fileSystemNameBuffer),
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

def set_bin_path():
    global BIN_PATH
    # Try the local dev version first, if one is running stargate.py from
    # the repo
    BIN_PATH = os.path.abspath(
        os.path.join(
            ENGINE_DIR,
            f"{MAJOR_VERSION}-engine",
        )
    )
    if IS_WINDOWS:
        BIN_PATH += '.exe'
    LOG.info(f"BIN_PATH=={BIN_PATH}")

set_bin_path()

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

BEAT_FRAC_INDICES = {
    0: 0.0625,
    1:  0.125,
    2: 0.25,
    3: 0.33333333,
    4: 0.5,
    5: 1.0,
}

def beat_frac_text_to_float(f_index):
    return BEAT_FRAC_INDICES.get(f_index, 0.25)

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

def soundstretch(
    src_path,
    dst_path,
    time_stretch,
    pitch_shift,
    speech=False,
):
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in ('.wav', '.wave'):
        with tempfile.NamedTemporaryFile() as t:
            tmp = t.name + '.wav'
        convert_to_wav(src_path, tmp)
        src_path = tmp
    rate = ((1.0 / time_stretch) - 1.0) * 100.
    cmd = [
        SOUNDSTRETCH,
        src_path,
        dst_path,
        f'-rate={rate}',
        f'-pitch={pitch_shift}',
    ]
    if speech:
        cmd.append('-speech')
    return subprocess.Popen(cmd, encoding='UTF-8')


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
    f_proc = subprocess.Popen(f_cmd, encoding='UTF-8')
    return f_proc

def sbsms(
    src_path,
    dest_path,
    timestretch_start,
    pitch_start,
    timestretch_end=None,
    pitch_end=None,
):
    cmd = [
        SBSMS,
        src_path,
        dest_path,
        str(1.0 / timestretch_start),
        str(1.0 /timestretch_end) if timestretch_end is not None \
            else str(1.0 / timestretch_start),
        str(pitch_start),
        str(pitch_end) if pitch_end is not None else str(pitch_start),
    ]
    LOG.info("Running {}".format(" ".join(cmd)))
    proc = subprocess.Popen(cmd, encoding='UTF-8')
    return proc

def paulstretch(
    a_src_path,
    a_dest_path,
    a_timestretch_amt,
):
    f_cmd = [
        PAULSTRETCH_PATH,
        'paulstretch',
        "-s", str(a_timestretch_amt),
        a_src_path,
        a_dest_path,
    ]
    if IS_WINDOWS and IS_LOCAL_DEVEL:
        f_cmd.insert(1, sys.argv[0])
    LOG.info("Running {}".format(" ".join(f_cmd)))
    f_proc = subprocess.Popen(f_cmd, encoding='UTF-8')
    return f_proc

def read_file_text(a_file):
    with sg_open(pi_path(a_file)) as f:
        return f.read()

def read_file_lines(path):
    with sg_open(pi_path(path)) as f:
        return f.readlines()

def read_file_json(path):
    with sg_open(pi_path(path)) as f:
        return json.load(f)

def read_file_yaml(path):
    with sg_open(pi_path(path)) as f:
        return yaml.safe_load(f)

def write_file_text(a_file, a_text):
    with sg_open(pi_path(a_file), "w", newline="\n") as f:
        f.write(str(a_text))

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

FILE_SETTING_CACHE = {}

def get_file_setting(a_name, a_type, a_default):
    if a_name in FILE_SETTING_CACHE:
        return FILE_SETTING_CACHE[a_name]
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    if os.path.exists(f_file_name):
        try:
            content = read_file_text(f_file_name)
            value = a_type(content)
            FILE_SETTING_CACHE[a_name] = value
            return value
        except Exception as ex:
            LOG.error("Error in get_file_setting {}".format(ex))
            os.remove(f_file_name)
    return a_default

def set_file_setting(a_name, a_val):
    FILE_SETTING_CACHE[a_name] = a_val
    f_file_name = os.path.join(CONFIG_DIR, "{}.txt".format(a_name))
    write_file_text(f_file_name, a_val)

def clear_file_setting(a_name):
    if a_name in FILE_SETTING_CACHE:
        FILE_SETTING_CACHE.pop(a_name)
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
            for f_line in read_file_lines(DEVICE_CONFIG_PATH):
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

def resolve_symlinks(path: str, max_depth=20) -> str:
    """ Recursively resolve symlinks to get the true path of a file or folder

        @path:      The path to check
        @max_depth: The maximum number of links to resolve

        @returns: The fully resolved path
        @raises:
            FileNotFoundError: If @path does not exist
            RecursionError: If max_depth is exceeded
    """
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    for i in range(max_depth):
        if os.path.islink(path):
            path = os.readlink(path)
        else:
            break
    if os.path.islink(path):
        raise RecursionError(path)
    return path

def convert_to_wav(src_path: str, dst_path: str):
    """ Convert an AIF, FLAC, etc... file to a wav.  Supports any format
        supported by libsndfile
    """
    sr, arr = wavefile.load(src_path)
    with wavefile.WaveWriter(dst_path, sr, arr.shape[0]) as f:
        f.write(arr)

