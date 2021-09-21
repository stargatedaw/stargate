import os
import signal
import subprocess
import sys
import threading
import time

import psutil

from sglib import constants
from sglib.constants import ENGINE_PIDFILE, MAJOR_VERSION
from sglib.hardware.rpi import is_rpi
from sglib.log import LOG
from sglib.lib import util
from sglib.lib import strings as sg_strings
from sglib.lib.translate import _


__all__ = [
    'check_engine',
    'close_engine',
    'kill_engine',
    'open_engine',
    'reopen_engine',
]

ENGINE_SUBPROCESS = None

def close_engine():
    """ Ask the engine to gracefully stop itself, then kill the process if it
        doesn't exit on it's own
    """
    constants.IPC.stop_server()
    global ENGINE_SUBPROCESS
    if ENGINE_SUBPROCESS is not None:
        f_exited = False
        for i in range(50):
            if ENGINE_SUBPROCESS.poll() is not None:
                f_exited = True
                break
            else:
                time.sleep(0.1)
        if not f_exited:
            LOG.warning(
                "ENGINE_SUBPROCESS did not exit on it's "
                "own, sending SIGKILL..."
            )
            try:
                ENGINE_SUBPROCESS.kill()
            except Exception as ex:
                LOG.error(
                    "Exception raised while trying to kill engine process"
                )
                LOG.exception(ex)
        ENGINE_SUBPROCESS = None

def check_engine():
    """ Check if the engine is running.  Only works for subprocess engine mode
        @return: int, the pid of the process, or None if not running
    """
    if os.path.exists(ENGINE_PIDFILE):
        with open(ENGINE_PIDFILE) as f:
            text = f.read().strip()
            try:
                pid = int(text)
            except Exception as ex:
                LOG.exception(ex)
                LOG.error(f"Invalid pidfile: {text}")
                os.remove(ENGINE_PIDFILE)
                return
        LOG.warning(f"{ENGINE_PIDFILE} exists with pid {pid}")
        if not psutil.pid_exists(pid):
            LOG.info(f"pid {pid} no longer exists, deleting pidfile")
            os.remove(ENGINE_PIDFILE)
            return None
        proc = psutil.Process(pid)
        cmdline = " ".join(proc.cmdline())
        if MAJOR_VERSION not in cmdline:
            LOG.info(f"Another process reclaimed {pid}: {cmdline}")
            os.remove(ENGINE_PIDFILE)
            return
        return pid

def kill_engine(pid):
    """ Kill any zombie instances of the engine if they exist.
        A new instance of the engine will fail to launch if an
        existing instance is connected to the same audio device.
        You should try exiting gracefully first by sending the "abort"
        message.
    """
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(1.0)
        if psutil.pid_exists(pid):
            LOG.warning(
                f"Failed to kill {pid} with SIGTERM, sending SIGKILL"
            )
            os.kill(pid, signal.SIGKILL)
    except Exception as ex:
        LOG.exception(ex)
    time.sleep(2.0)

def open_engine(a_project_path, fps):
    if not util.WITH_AUDIO:
        LOG.info(
            "Not starting audio because of the audio engine setting, "
            "you can change this in File->HardwareSettings"
        )
        return

    #ensure no running instances of the engine
    pid = check_engine()
    if pid:
        kill_engine(pid)
    constants.PROJECT_DIR = os.path.dirname(a_project_path)

    f_pid = os.getpid()
    LOG.info(f"Starting audio engine with {a_project_path}")
    global ENGINE_SUBPROCESS
    if (
        not is_rpi()
        and
        util.which("pasuspender") is not None
        and
        os.system("pasuspender sleep 0.1") == 0
    ):
        f_pa_suspend = True
    else:
        f_pa_suspend = False

    if f_pa_suspend:
        f_cmd = 'pasuspender -- "{}" "{}" "{}" {} {} {}'.format(
            util.BIN_PATH,
            util.INSTALL_PREFIX,
            constants.PROJECT_DIR,
            f_pid,
            util.USE_HUGEPAGES,
            fps,
        )
    else:
        f_cmd = [
            str(x) for x in (
                util.BIN_PATH,
                util.INSTALL_PREFIX,
                constants.PROJECT_DIR,
                f_pid,
                util.USE_HUGEPAGES,
                fps,
            )
        ]
    run_engine(f_cmd)

def reopen_engine():
    open_engine(PROJECT_FILE)
    constants.IPC_ENABLED = True

def run_engine(cmd):
    global ENGINE_SUBPROCESS
    LOG.info(f"Starting engine subprocess with: {cmd}")
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
    ENGINE_SUBPROCESS = subprocess.Popen(
        cmd,
        **kwargs
    )
    for args in (
        (LOG.info, ENGINE_SUBPROCESS.stdout, "stdout"),
        (_stderr_handler, ENGINE_SUBPROCESS.stderr, "stderr"),
    ):
        t = threading.Thread(
            target=_log_fd,
            args=args,
        )
        t.daemon = True
        t.start()

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

def _log_fd(log_func, fd, name):
    try:
        for line in fd:
            line = line.strip()
            if line:
                log_func(f'ENGINE PROC: "{line}"')
        LOG.info(f"Engine finished writing to {name}")
    except Exception as ex:
        LOG.exception(ex)

