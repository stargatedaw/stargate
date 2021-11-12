"""

"""
from typing import Any, Dict

__all__ = [
    'key_swap',
]


def key_swap(
    d: Dict[str, str],
    cls: Any,
    marshal: bool,
) -> dict:
    """ Swap the keys in a dictionary

        Args:
            d:       The dict to swap keys in
            cls:     class, If the class has a staticly defined
                     _marshal_key_swap and/or _unmarshal_key_swap dict,
                     the keys will be swapped.
                     Otherwise @d is returned
            marshal: True if marshalling class to JSON,
                     False if unmarshalling JSON to class
    """
    dname = '_{}marshal_key_swap'.format("" if marshal else "un")
    if hasattr(cls, dname):
        key_swap = getattr(cls, dname)
        return {
            key_swap[k] if k in key_swap else k: v
            for k, v in d.items()
        }
    else:
        return d
