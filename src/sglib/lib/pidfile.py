import os
import psutil
from sglib.constants import MAJOR_VERSION
from sglib.lib import util
from sglib.log import LOG

def check_pidfile(path):
    """ Check if a process is running.
        The process must create a pidfile for this to work
    """
    if os.path.exists(path):
        text = util.read_file_text(path).strip()
        try:
            pid = int(text)
        except Exception as ex:
            LOG.exception(ex)
            LOG.error(f"Invalid pidfile: {text}")
            os.remove(path)
            return None
        LOG.warning(f"{path} exists with pid {pid}")
        if not psutil.pid_exists(pid):
            LOG.info(f"pid {pid} no longer exists, deleting pidfile")
            os.remove(path)
            return None
        proc = psutil.Process(pid)
        cmdline = " ".join(proc.cmdline())
        if MAJOR_VERSION not in cmdline:
            LOG.info(f"Another process reclaimed {pid}: {cmdline}")
            os.remove(path)
            return None
        return pid

def create_pidfile(
    path,
    pid=str(os.getpid()),
):
    LOG.info(f"Creating pidfile {path} : {pid}")
    util.write_file_text(path, pid)

