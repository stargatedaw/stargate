"""

"""

from typing import Any, Iterable, List, Optional
from .util.marshal import *
from .util.pm_assert import pm_assert
from .util.type import *


__all__ = [
    'ExtraKeysError',
    'InitArgsError',
    'marshal_json',
    'pm_assert',
    'type_assert',
    'type_assert_dict',
    'type_assert_iter',
    'unmarshal_json',
]

JSON_TYPES = (
    bool,
    dict,
    float,
    int,
    list,
    str,
    tuple,
    type(None),
)


def marshal_json(
    obj: object,
    types: Iterable=JSON_TYPES,
    fields: Optional[Iterable[str]]=None,
) -> dict:
    """ Recursively marshal a Python object to a JSON-compatible dict
        that can be passed to json.{dump,dumps}, a web client,
        or a web server, etc...

    Args:
        obj:    It's members can be nested Python
                objects which will be converted to dictionaries
        types:  The JSON primitive types, typically you would not change this
        fields: Explicitly marshal only these fields
    """
    return marshal_dict(
        obj,
        types,
        fields=fields,
    )


def unmarshal_json(
    obj: dict,
    cls: type,
    allow_extra_keys: bool=True,
    ctor=None,
) -> Any:
    """ Unmarshal @obj into @cls

    Args:
        obj:              A JSON object
        cls:              The class to unmarshal into
        allow_extra_keys: False to raise an exception when extra
                          keys are present, True to ignore
        ctor:             Use this method as the constructor instead
                          of __init__
    Returns:
        instance of @cls
    Raises:
        ExtraKeysError: If allow_extra_keys == False, and extra keys
                        are present in @obj and not in @cls.__init__
        ValueError:     If @cls.__init__ does not contain a self argument
    """
    return unmarshal_dict(
        obj,
        cls,
        allow_extra_keys,
        ctor=ctor,
    )
