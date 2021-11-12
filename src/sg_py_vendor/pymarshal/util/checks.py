"""
    Various utility functions to supplement the functionality of
    the type assert functions
"""

from typing import Iterable

__all__ = [
    'check_dups',
]


def check_dups(
    iterable,
    debug_limit: int=1000,
):
    """ Checks an iterable for duplicates

        Note that it does not make sense to call this on a set()

        If calling on a collection without a .count method,
        set @debug_limit to -1.

        For custom equality comparisons, create a custom
        __eq__ and __hash__ method in the class contained in @iterable

    Args:
        iterable:    An iterable to check for duplicates
        debug_limit: Don't generate a list of duplicates for the
                     Exception message if the length of @iterable
                     is >= this value.  This exists because generating
                     the list does not scale efficiently.
    Raises:
        ValueError: If @iterable contains duplicates
    """
    if not iterable:
        return
    unique = set(iterable)
    if len(unique) != len(iterable):
        if len(iterable) < debug_limit:
            dups = [x for x in unique if iterable.count(x) > 1]
            msg = "Duplicate values: {}".format(dups)
        else:
            msg = (
                "Duplicate values, not generating list because "
                "len(iterable)={} is greater than debug_limit={}"
            ).format(
                len(iterable),
                debug_limit,
            )
        raise ValueError(msg)

