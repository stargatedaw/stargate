"""

"""

import sys
import types
from typing import Any, List


def init_args(
    cls: Any,
) -> List[str]:
    """ Return the __init__ args (minus 'self') for @cls

    Args:
        cls: class, instance or callable
    Returns:
        The arguments minus 'self'
    """
    # This looks insanely goofy, but seems to literally be the
    # only thing that actually works.  Your obvious ways to
    # accomplish this task do not apply here.
    try:
        # Assume it's a factory function, static method, or other callable
        args = cls.__code__.co_varnames
    except AttributeError:
        # assume it's a class
        args = cls.__init__.__code__.co_varnames

    # Note:  There is a special place in hell for people who don't
    #        call the first method argument 'self'.
    if args[0] == 'self':
        args = args[1:]

    return args

