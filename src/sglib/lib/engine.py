import os
import signal
import sys
import time

import psutil

from .pidfile import check_pidfile
from .process import run_process
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
ENGINE_PSUTIL = None

def close_engine():
    """ Ask the engine to gracefully stop itself, then kill the process if it
        doesn't exit on it's own
    """
    constants.IPC.stop_server()
    global ENGINE_SUBPROCESS, ENGINE_PSUTIL
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
        ENGINE_PSUTIL = None
    if os.path.exists(ENGINE_PIDFILE):
        os.remove(ENGINE_PIDFILE)
    constants.READY = False

def check_engine():
    """ Check if the engine is running.  Only works for subprocess engine mode
        @return: int, the pid of the process, or None if not running
    """
    return check_pidfile(ENGINE_PIDFILE)

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
        os.remove(ENGINE_PIDFILE)
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

    threads = int(util.DEVICE_SETTINGS['threads'])
    if threads == 0:
        threads = util.AUTO_CPU_COUNT
    threads = str(threads)

    f_cmd = [
        str(x) for x in (
            util.BIN_PATH,
            util.INSTALL_PREFIX,
            constants.PROJECT_DIR,
            f_pid,
            util.USE_HUGEPAGES,
            fps,
            threads,
        )
    ]
    f_cmd = util.has_pasuspender(f_cmd)
    run_engine(f_cmd)

def reopen_engine():
    open_engine(PROJECT_FILE)
    constants.IPC_ENABLED = True

def run_engine(cmd):
    global ENGINE_SUBPROCESS, ENGINE_PSUTIL
    ENGINE_SUBPROCESS = run_process(cmd, ENGINE_PIDFILE)
    try:
        ENGINE_PSUTIL = psutil.Process(ENGINE_SUBPROCESS.pid)
    except:
        LOG.exception('Could not create ENGINE_PSUTIL')

