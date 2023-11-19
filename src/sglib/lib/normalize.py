import shutil

from sglib.log import LOG
from sglib.math import db_to_lin
from sg_py_vendor import wavefile

def normalize_in_place(path: str, db: float):
    dst = path + '.tmp-normalize'
    # This could be improved by reading the file in chunks to avoid
    # loading in memory using a WaveReader
    sr, arr = wavefile.load(path)
    factor = db_to_lin(db) / max((arr.max(), arr.min() * -1.))
    LOG.info(f'Normalizing {path} by {factor}')
    arr *= factor
    with wavefile.WaveWriter(dst, sr, arr.shape[0]) as f:
        f.write(arr)
    shutil.move(dst, path)

