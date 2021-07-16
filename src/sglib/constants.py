import os

__all__ = [
    'CONFIG_DIR',
    'DEFAULT_PROJECT_DIR',
    'HOME',
    'LOG_DIR',
    'MAJOR_VERSION',
    'PRESET_DIR',
    'USER_HOME',
]

MAJOR_VERSION = 'stargate'

USER_HOME = os.path.expanduser("~")
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

