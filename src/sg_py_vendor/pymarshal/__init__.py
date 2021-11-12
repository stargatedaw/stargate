"""
    Replicates the functionality of Golang's
    struct (un)marshalling feature to/from JSON.

    For examples, see:
    https://github.com/stargateaudio/pymarshal/blob/master/README.md
"""

from . import json
from .json import *

__version__ = '2.2.0'
__all__ = json.__all__
