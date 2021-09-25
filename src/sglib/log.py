import gzip
import logging
import os
import sys
import traceback

from logging.handlers import RotatingFileHandler

from sglib.constants import LOG_DIR

__all__ = [
    'LOG',
]

LOG = logging.getLogger(__name__)
FORMAT = (
    '[%(asctime)s] %(levelname)s %(pathname)-30s: %(lineno)s - %(message)s'
)

def namer(name):
    return f"{name}.gz"

def rotator(source, dest):
    with open(source, "rb") as sf:
        data = sf.read()
        compressed = gzip.compress(data, 9)
        with open(dest, "wb") as df:
            df.write(compressed)
    os.remove(source)

def setup_logging(
    format=FORMAT,
    level=logging.INFO,
    log=LOG,
    stream=sys.stdout,
    maxBytes=1024*1024*10,
):
    fmt = logging.Formatter(format)
    handler = logging.StreamHandler(
        stream=stream,
    )
    handler.setFormatter(fmt)
    log.addHandler(handler)

    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'stargate.log'),
        maxBytes=maxBytes,
        backupCount=3,
    )
    handler.setFormatter(fmt)
    handler.rotator = rotator
    handler.namer = namer
    log.addHandler(handler)

    log.setLevel(level)

    sys.excepthook = _excepthook


def _excepthook(exc_type, exc_value, tb):
    exc = traceback.format_exception(exc_type, exc_value, tb)
    LOG.error("\n".join(exc))

