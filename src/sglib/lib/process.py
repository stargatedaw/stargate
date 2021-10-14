from . import util
from .pidfile import create_pidfile
from sglib.log import LOG
import subprocess
import threading

def run_process(cmd, pidfile=None):
    exe = "SUBPROCESS" if isinstance(cmd, str) else cmd[0]
    kwargs = {
        "bufsize": 1024*1024,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": isinstance(cmd, str),
        "universal_newlines": True,
    }
    if util.IS_WINDOWS:
        kwargs["creationflags"] = (
            subprocess.REALTIME_PRIORITY_CLASS
            |
            subprocess.CREATE_NO_WINDOW
        )
        kwargs['stdin'] = subprocess.DEVNULL
    LOG.info(f"Starting subprocess with: {cmd}")
    process = subprocess.Popen(
        cmd,
        **kwargs
    )
    for args in (
        (LOG.info, process.stdout, "stdout", exe),
        (_stderr_handler, process.stderr, "stderr", exe),
    ):
        t = threading.Thread(
            target=_log_fd,
            args=args,
        )
        t.daemon = True
        t.start()
    if pidfile:
        create_pidfile(
            pidfile,
            str(process.pid),
        )
    return process

def _stderr_handler(line: str):
    lower = line.lower()
    if (
        "WARNING" in line
        or
        any(x in lower for x in ("alsa", "jack"))
    ):
        LOG.warn(line)
    else:
        LOG.error(line)

def _log_fd(log_func, fd, name, exe):
    try:
        for line in fd:
            line = line.strip()
            if line:
                log_func(f'{exe}: "{line}"')
        LOG.info(f"Engine finished writing to {name}")
    except Exception as ex:
        LOG.exception(ex)

