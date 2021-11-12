"""

"""

from typing import Any, Iterable, List, Optional, Tuple, Union
from .util.marshal import *
from .util.pm_assert import pm_assert
from .util.type import *


__all__ = [
    'csv_cast_empty_str_to_none',
    'InitArgsError',
    'marshal_csv',
    'pm_assert',
    'type_assert',
    'type_assert_iter',
    'unmarshal_csv',
    'unmarshal_csv_list',
]

CSV_TYPES = (
    float,
    int,
    str,
    type(None),
)

def csv_cast_empty_str_to_none(
    _type: Any,
) -> Any:
    """ Handle the Python csv module converting None to empty str
        Set the cast_to= argument of fields with allow_none=True to
        the output of this function call, and cast_from=str.

        @type: type-or-constructor, will be called on the input if != ''
        @return: None, or an instance of @_type
    """
    return lambda x: None if x == '' else _type(x)

def marshal_csv(
    iterable: Any,
    types=CSV_TYPES,
    fields: Optional[List[str]]=None,
) -> list:
    """ Marshal a list of Python objects to a CSV-compatible list of lists
        that can be passed to csv.writer.writerows.
        If @iterable is a class instance, it must offer a method to iterate
        through it's objects, or implement __iter__.

    Args:
        iterable: A list of objects that do not contain nested objects,
                  all fields must be of types in @types
        types:    The primitive types, typically you would not change this
        fields:   Explicitly marshal only these fields
    """
    if (
        hasattr(iterable, '_marshal_csv_dict')
        and
        iterable._marshal_csv_dict
    ):
        return [
            [k, iterable.__dict__[k]]
            for k in sorted(iterable.__dict__.keys())
            if isinstance(iterable.__dict__[k], types)
        ]
    return [
        marshal_list(
            x,
            types,
            fields,
        ) for x in iterable
    ]

def unmarshal_csv(
    iterable: Iterable,
    cls: Any,
    ignore_extras: bool=False,
) -> Any:
    """ Unmarshal @iterable into a single instance of @cls
    Args:
        @iterable: The data structure of CSV data
        @cls:
            A class that contains one or more of:

            _unmarshal_csv_map = {
                'row_header': {
                    'arg_name': '__init__ arg name',
                    'type': Class,  # Or a factory function
                }
            }
            field to map row headers to input arguments

            _unmarshal_csv_default_arg = {
                'arg_name': '__init__ arg name',
                'type': Class,  # Or a factory function
            }
            to set a default when no recognized header is in the row.
            This type should not implement _marshal_list_row_header

            _unmarshal_csv_singletons = {
                'row_header': {
                    'arg_name': '__init__ arg name',
                    'type': Class,  # Or a factory function
                }
            }
            To set a row header as a singleton (non-list/tuple) field
        @ignore_extras:
            True to ignore unrecognized rows, otherwise ValueError is
            raised when an unrecognized row it encountered
    """
    if (
        hasattr(cls, '_marshal_csv_dict')
        and
        cls._marshal_csv_dict
    ):
        kwargs = {x: y for x, y in iterable}
        return cls(**kwargs)

    if hasattr(cls, '_unmarshal_csv_map'):
        csv_map = cls._unmarshal_csv_map
    else:
        csv_map = {}
    if hasattr(cls, '_unmarshal_csv_singletons'):
        singletons = cls._unmarshal_csv_singletons
    else:
        singletons = {}
    kwargs = {
        v['arg_name']: []
        for v in cls._unmarshal_csv_map.values()
    }
    if hasattr(cls, '_unmarshal_csv_default_arg'):
        default_arg = cls._unmarshal_csv_default_arg
        default_arg_name = default_arg['arg_name']
        default_arg_type = default_arg['type']
        kwargs[default_arg_name] = []
    else:
        default_arg = None
    pm_assert(
        kwargs or singletons,
        AttributeError,
        msg="""\
            @cls must have one or more of _marshal_csv_map,
            _unmarshal_csv_singletons, _unmarshal_csv_default_arg
        """,
    )
    for x in iterable:
        row_header = x[0]
        if row_header in csv_map:
            arg_name = csv_map[row_header]['arg_name']
            _type = csv_map[row_header]['type']
            value = _type(*x[1:])
            kwargs[arg_name].append(value)
        elif row_header in singletons:
            arg_name = singletons[row_header]['arg_name']
            _type =  singletons[row_header]['type']
            kwargs[arg_name] = _type(*x[1:])
        elif default_arg:
            value = default_arg_type(*x)
            kwargs[default_arg_name].append(value)
        elif not ignore_extras:
            msg = "Unrecognized row: '{}'".format(x)
            raise ValueError(msg)

    return cls(**kwargs)

def unmarshal_csv_list(
    iterable: Iterable,
    cls: Any,
):
    """ Unmarshal @iterable into a list of @cls
        Assumes that @iterable are all a single type

    Args:
        iterable: list-or-tuple-of-lists
        cls:
            type-or-function or {"row header": function},
            The type to unmarshal into
    Returns:
        List of instances of @cls
    Raises:
        ValueError: If @cls.__init__ does not contain a self argument
    """
    return [
        unmarshal_list(x, cls)
        for x in iterable
    ]

