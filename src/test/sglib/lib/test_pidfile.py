from sglib.lib.pidfile import check_pidfile, create_pidfile
import os
import tempfile

def test_create_check_reclaimed():
    with tempfile.NamedTemporaryFile() as f:
        pidfile = f.name
    pid = check_pidfile(pidfile)
    assert pid is None, (pid, pidfile)
    create_pidfile(pidfile)
    check_pidfile(pidfile)

def test_malformed():
    with tempfile.NamedTemporaryFile() as f:
        pidfile = f.name
    with open(pidfile, 'w') as f:
        f.write("invalidpid")
    pid = check_pidfile(pidfile)
    assert pid is None, (pid, pidfile)

def test_pid_does_not_exist():
    # Assumes the tests are running on a 64 bit system, and hopefully nothing
    # has claimed this pid
    pid = "2000001"
    with tempfile.NamedTemporaryFile() as f:
        pidfile = f.name
    with open(pidfile, 'w') as f:
        f.write(pid)
    pid = check_pidfile(pidfile)
    assert pid is None, (pid, pidfile)

