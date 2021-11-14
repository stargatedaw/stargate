from sglib.lib._ctypes import *
import ctypes
import os
import pytest


def test_patch_ctypes():
    try:
        patch_ctypes(env_vars=('SG_TEST_CTYPES',))
        os.environ['SG_TEST_CTYPES'] = '/sg/test/path;/sg/test/path2/lib'
        ctypes.CDLL(("libportaudio.so", "libportaudio.so.2"))
        revert_patch_ctypes()
        patch_ctypes(True, env_vars=('SG_TEST_CTYPES',))
        ctypes.CDLL(("libportaudio.so", "libportaudio.so.2"))
    finally:
        revert_patch_ctypes()

def test_patch_ctypes_raises():
    try:
        patch_ctypes(env_vars=('SG_TEST_CTYPES',))
        os.environ['SG_TEST_CTYPES'] = '/sg/test/path;/sg/test/path2/lib'
        with pytest.raises(ImportError):
            ctypes.CDLL(("portmidiiiii.so", "portmidi.*"))
    finally:
        revert_patch_ctypes()

