from sglib.hardware.rpi import *
import tempfile

def test_is_rpi():
    with tempfile.NamedTemporaryFile() as f:
        sysfs_path = f.name
    for contents, expected in (
        ('Raspberry Pi 4B', True),
        ('Ryzen 9 9999X', False),
    ):
        with open(sysfs_path, 'w') as f:
            f.write(contents)
        result = is_rpi(
            sysfs_path=sysfs_path,
        )
        assert result == expected, (result, expected)

def test_gpu_mem():
    for cmd, expected in (
        ('echo 512MB', True),
        ('echo 128MB', False),
        ('exit 1', True),
    ):
        result = gpu_mem(cmd=cmd)
        assert result == expected, (result, expected)

def test_desktop():
    for cmd, expected in (
        ('echo fluxbox', True),
        ('echo kde', False),
        ('exit 1', True),
    ):
        result = desktop(cmd=cmd)
        assert result == expected, (result, expected)

