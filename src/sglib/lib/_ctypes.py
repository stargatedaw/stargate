from sglib.log import LOG
import ctypes
import ctypes.util
import glob
import os

__all__ = [
    'patch_ctypes',
    'revert_patch_ctypes',
]

ORIG_CDLL = None
ORIG_FIND_LIB = None

def revert_patch_ctypes():
    global ORIG_CDLL, ORIG_FIND_LIB
    ctypes.CDLL = ORIG_CDLL
    ORIG_CDLL = None
    ctypes.util.find_library = ORIG_FIND_LIB
    ORIG_FIND_LIB = None

def patch_ctypes(
    prefer_arg: bool=False,
    env_vars: tuple=('LIBRARY_PATH', 'LD_LIBRARY_PATH'),
    delim: str=';',
):
    """ Patch ctypes to be able to load libraries from non-default paths
        by reading one or more environment variables and searching those paths

        @prefer_arg: Try the function argument before @env_vars
        @env_vars:   The environment variables to search for libraries
        @delim:      The delimiter to split multiple paths with
    """
    global ORIG_CDLL, ORIG_FIND_LIB
    ORIG_CDLL = ctypes.CDLL
    ORIG_FIND_LIB = ctypes.util.find_library
    def _CDLL(_lib, *args, **kwargs):
        assert isinstance(_lib, (str, tuple)), _lib
        paths = []
        _libs = _lib if isinstance(_lib, tuple) else (_lib,)
        if prefer_arg:
            paths.extend(_libs)
        for env_var in (x for x in env_vars if x in os.environ):
            lib_paths = os.environ[env_var].split(delim)
            for lib_path in lib_paths:
                for lib in _libs:
                    basename = os.path.basename(lib)
                    pattern = os.path.join(lib_path, f"{basename}*")
                    LOG.info(pattern)
                    matches = glob.glob(pattern)
                    paths.extend(matches)
        if not prefer_arg:
            paths.extend(_libs)
        for path in paths:
            try:
                result = ORIG_CDLL(path, *args, **kwargs)
                LOG.info(f"Successfully loaded dynamic library from {path}")
                return result
            except Exception as ex:
                LOG.warning(f"Failed to load '{path}', {ex}")
        raise ImportError(f"Did not find {_lib} in {paths}")
    ctypes.CDLL = _CDLL
    ctypes.util.find_library = lambda x: x

