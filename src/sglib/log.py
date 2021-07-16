import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from sglib.constants import LOG_DIR

__all__ = [
    'LOG',
]

LOG = logging.getLogger(__name__)
FORMAT = (
    '[%(asctime)s] %(levelname)s %(pathname)-30s: %(lineno)s - %(message)s'
)

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
    log.addHandler(handler)

    log.setLevel(level)

