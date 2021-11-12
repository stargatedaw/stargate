from typing import Any, Optional


def pm_assert(
    condition: Any,
    exc: Any=Exception,
    context: Any=None,
    msg: str="",
) -> Any:
    """ Generic assertion that can be used anywhere
        @condition: A condition to assert is true
        @exc:       Raise if @condition is False
        @context:   The relevant data structures
        @msg:       Any additional text to include
    """
    if not condition:
        raise exc(f"{msg}\n{context}")
    return condition

