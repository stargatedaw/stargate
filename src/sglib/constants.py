import os
import sys

__all__ = [
    'CONFIG_DIR',
    'DEFAULT_PROJECT_DIR',
    'HOME',
    'IS_LINUX',
    'IS_MAC_OSX',
    'IS_WINDOWS',
    'LOG_DIR',
    'MAJOR_VERSION',
    'PRESET_DIR',
    'USER_HOME',
]

MAJOR_VERSION = 'stargate'

assert "cygwin" not in sys.platform, "Cygwin is unsupported"
IS_WINDOWS = "win32" in sys.platform or "msys" in sys.platform
IS_LINUX = "linux" in sys.platform
IS_MAC_OSX = "darwin" in sys.platform

USER_HOME = os.path.expanduser("~")
IS_PORTABLE_INSTALL = False

# Check if the exe was run from a flash drive, with a '_stargate_home' file
# created in the same directory
if IS_WINDOWS:
    dirname = os.path.dirname(sys.executable)
    if os.path.isfile(
        os.path.join(dirname, '_stargate_home'),
    ):
        print(
            f"Using {dirname} for USER_HOME because _stargate_home "
            "file exists"
        )
        USER_HOME = dirname
        IS_PORTABLE_INSTALL = True

HOME = os.path.join(
    USER_HOME,
    MAJOR_VERSION,
)
DEFAULT_PROJECT_DIR = os.path.join(
    HOME,
    'projects',
)
READY = False
PROJECT_DIR = None
DAW_MAX_SONG_COUNT = 20
DAW_CURRENT_SEQUENCE_UID = 0

IPC_ENABLED = False
IPC_TRANSPORT = None
IPC = None
DAW_IPC = None
WAVE_EDIT_IPC = None

CONFIG_DIR = os.path.join(HOME, "config")
PRESET_DIR = os.path.join(CONFIG_DIR, "preset")
LOG_DIR = os.path.join(HOME, "log")
ENGINE_PIDFILE = os.path.join(HOME, 'engine.pid')

for _f_dir in (
    CONFIG_DIR,
    DEFAULT_PROJECT_DIR,
    HOME,
    LOG_DIR,
    PRESET_DIR,
):
    if not os.path.isdir(_f_dir):
        print(f"Creating {_f_dir}")
        os.makedirs(_f_dir)

# Plugins
PLUGINS_PER_TRACK = 10
SENDS_PER_TRACK = 4
TOTAL_PLUGINS_PER_TRACK = PLUGINS_PER_TRACK + SENDS_PER_TRACK

# Projects
PROJECT = None
DAW_PROJECT = None
WAVE_EDIT_PROJECT = None

