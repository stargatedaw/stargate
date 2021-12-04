from sglib import constants
from sglib.models.stargate.audio_pool import *
import copy

POOL_STR = """\
0|0.0|/path/to/file.wav
1|-6.0|/path/to/file2.wav
f|0|64|64|64|0|64|64|64|0|64|64|64|0|64|64|64|0|64|64|64|0|64|64|64|0\
|64|64|64|0|64|64|64|0
\\"""

POOL_STR_NO_FILE_FX = """\
0|0.0|/path/to/file.wav
1|-6.0|/path/to/file2.wav
\\"""

class MockProject:
    def to_long_audio_file_path(self, path):
        return path

    def to_short_audio_file_path(self, path):
        return path

def test_pool_from_str_to_str():
    constants.PROJECT = MockProject()
    pool = AudioPool.from_str(POOL_STR)
    assert len(pool.pool) == 2, pool.pool
    assert str(pool) == POOL_STR
    fx_by_uid = pool.per_file_fx_by_uid()
    assert 0 in fx_by_uid, fx_by_uid

def test_pool_no_fx_from_str_to_str():
    constants.PROJECT = MockProject()
    pool = AudioPool.from_str(POOL_STR_NO_FILE_FX)
    assert len(pool.pool) == 2, pool.pool
    assert str(pool) == POOL_STR_NO_FILE_FX

def test_pool_new_str_empty():
    constants.PROJECT = MockProject()
    pool = AudioPool.new()
    assert str(pool) == "\\", str(pool)

def test_pool_entry_repr():
    constants.PROJECT = MockProject()
    entry = AudioPoolEntry(0, 0., '/path/to')
    assert '/path/to' in repr(entry), repr(entry)

def test_add_remove():
    constants.PROJECT = MockProject()
    pool = AudioPool.new()
    entry = pool.add_entry(__file__)
    assert len(pool.pool) == 1
    assert entry.uid == 0, entry
    assert pool.next_uid() == 1
    pool.remove_by_uid([entry.uid])
    assert len(pool.pool) == 0

def test_set_per_file_fx():
    constants.PROJECT = MockProject()
    pool = AudioPool.from_str(POOL_STR)
    fx = copy.deepcopy(pool.per_file_fx[0])
    fx.uid = 2
    pool.set_per_file_fx(fx)
    assert len(pool.per_file_fx) == 2, pool.per_file_fx
    fx = copy.deepcopy(fx)
    pool.set_per_file_fx(fx)
    assert len(pool.per_file_fx) == 2, pool.per_file_fx

