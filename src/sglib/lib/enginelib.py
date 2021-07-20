"""
    Run the engine as a shared library instead of a separate process
"""
from sglib import constants
from sglib.lib import util
from sglib.log import LOG
import ctypes
import os

ENGINE_LIB = None
ENGINE_LIB_CALLBACK = None
ENGINE_LIB_CALLBACK_SIG = None

if util.IS_WINDOWS:
    DLL_EXT = ".dll"
elif util.IS_LINUX:
    DLL_EXT = ".so"
elif util.IS_MAC_OSX:
    DLL_EXT = ".dylib"

# Path is applicable in both local development and also when installed
SGENGINE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "engine",
    ),
)

def load_engine_lib(a_engine_callback):
    global ENGINE_LIB, ENGINE_LIB_CALLBACK, ENGINE_LIB_CALLBACK_SIG
    f_dll_name = "{}-engine{}".format(
        constants.MAJOR_VERSION,
        DLL_EXT,
    )
    f_dll = os.path.join(SGENGINE_DIR, f_dll_name)
    LOG.info(f"Using engine lib path {f_dll}")
    assert os.path.isfile(f_dll), "{f_dll} does not exist"
    ENGINE_LIB = ctypes.CDLL(f_dll)
    ENGINE_LIB.start_engine.restype = None
    ENGINE_LIB.start_engine.argstype = [ctypes.c_char_p]
    ENGINE_LIB.stop_engine.restype = None
    ENGINE_LIB.stop_engine.argstype = [ctypes.c_char_p]
    ENGINE_LIB.v_configure.argstype = [
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    ENGINE_LIB.v_configure.restype = ctypes.c_int
    if util.IS_WINDOWS:
        ENGINE_LIB_CALLBACK_SIG = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_char_p,
            ctypes.c_char_p,
        )
    else:
        ENGINE_LIB_CALLBACK_SIG = ctypes.CFUNCTYPE(
            None,
            ctypes.c_char_p,
            ctypes.c_char_p
        )
    ENGINE_LIB_CALLBACK = ENGINE_LIB_CALLBACK_SIG(a_engine_callback)
    ENGINE_LIB.v_set_ui_callback.restype = None
    ENGINE_LIB.v_set_ui_callback(ENGINE_LIB_CALLBACK)


def start_engine_lib(a_project_dir):
    constants.PROJECT_DIR = a_project_dir
    ENGINE_LIB.start_engine(
        ctypes.c_char_p(
            constants.PROJECT_DIR.encode("ascii"),
        )
    )

# Unused, the engine is stoped using messages
#def stop_engine_lib():
#    ENGINE_LIB.stop_engine()
#    util.ENGINE_RETCODE = 0

def engine_lib_configure(a_path, a_key, a_val):
    if ENGINE_LIB:
        ENGINE_LIB.v_configure(
            a_path.encode("ascii"),
            a_key.encode("ascii"),
            a_val.encode("ascii"),
        )
    else:
        LOG.warning(
            f"ENGINE_LIB==None, failed to send {a_path}::{a_key}::{a_val}"
        )
