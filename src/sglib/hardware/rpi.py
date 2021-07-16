try:
    from sg_py_vendor.pymarshal import pm_assert
except ImportError:
    from pymarshal import pm_assert
from sglib.log import LOG
from subprocess import getstatusoutput
import os
import re

__all__ = [
    'is_rpi',
    'gpu_mem',
    'desktop',
]

def gpu_mem(
    cmd: str= 'vcgencmd get_mem gpu',
    minimum: int=256,
) -> bool:
    """ Check that Raspberry Pi has allocated enough GPU memory
    """
    status, output = getstatusoutput(cmd)
    if status != 0:
        LOG.warning(
            f"Could not check gpu_mem: '{cmd}' returned {status}: '{output}'"
        )
        return True
    numbers = re.findall(r'\d+', output)
    pm_assert(
        len(numbers) == 1,
        ValueError,
        (numbers, output)
    )
    gpu_mem = int(numbers[0])
    if gpu_mem < minimum:
        LOG.warning(f"Detected {gpu_mem} GPU memory")
        return False
    return True

def desktop(
    cmd: str='wmctrl -m',
    allow: tuple=('fluxbox',),
):
    status, output = getstatusoutput(cmd)
    if status != 0:
        LOG.warning(
            f"Could not check DE: '{cmd}' returned {status}: '{output}'"
        )
        return True
    output = output.lower()
    for de in allow:
        if de in output:
            return True
    return False

def is_rpi(
    sysfs_path: str='/sys/firmware/devicetree/base/model',
    search: str='Raspberry Pi',
) -> bool:
    """ Check if running an Raspberry Pi
        @return:
            True if running on an rpi, False if not, or unable to determine
    """
    if os.path.exists(sysfs_path):
        with open(sysfs_path) as f:
            text = f.read()
            if search in text:
                LOG.info(f'Detected running on Raspberry Pi: "{text}"')
                return True
    return False

