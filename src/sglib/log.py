import gzip
import logging
import os
import sys
import traceback

from logging.handlers import RotatingFileHandler

from sglib.constants import LOG_DIR, USER_HOME

__all__ = [
    'LOG',
]

LOG = logging.getLogger(__name__)
FORMAT = (
    '[%(asctime)s] %(levelname)s %(pathname)-30s: %(lineno)s - %(message)s'
)


class RedactingFilter(logging.Filter):
    def __init__(self, patterns: dict):
        super(RedactingFilter, self).__init__()
        self._patterns = patterns

    def filter(self, record):
        record.msg = self.redact(record.msg)
        record.pathname = self.redact(record.pathname)
        if isinstance(record.args, dict):
            for k in record.args.keys():
                record.args[k] = self.redact(record.args[k])
        else:
            record.args = tuple(self.redact(arg) for arg in record.args)
        return True

    def redact(self, msg):
        msg = isinstance(msg, str) and msg or str(msg)
        for k, v in self._patterns.items():
            msg = msg.replace(k, v)
        return msg

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
    log.addFilter(
        RedactingFilter({
            USER_HOME.replace('\\', '/'): "~",
            USER_HOME.replace('/', '\\'): "~",
        })
    )
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

