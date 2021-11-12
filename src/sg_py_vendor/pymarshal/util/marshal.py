"""

"""

from typing import Any, Callable, Iterable, Optional, Tuple

from .init_args import init_args
from .key_swap import key_swap


__all__ = [
    'ExtraKeysError',
    '_get_dict',
    'InitArgsError',
    'marshal_dict',
    'unmarshal_dict',
    'marshal_list',
    'unmarshal_list',
]


def _get_dict(
    obj: Any,
) -> Tuple[bool, dict]:
    """ Hack to work around the lack of __dict__ when __slots__ is used
    Returns:
        (has slots, dictionary of object fields)
    """
    if isinstance(obj, dict):
        return False, obj
    has_slots = hasattr(obj, '__slots__')
    if has_slots:
        d = {k:getattr(obj, k) for k in obj.__slots__}
    else:
        d = obj.__dict__
    return has_slots, d


class ExtraKeysError(Exception):
    """ Raised when extra object keys are present

        This exception can be marshalled into JSON for sending
        to clients.  However, it cannot be unmarshalled back into
        an ExtraKeysError
    """
    def __init__(
        self,
        cls: Any,
        diff: dict,
    ):
        """ Note that type_assert can't be used because it would
            create a circular dependency.

        Args:
            cls,  The type that was attempted to unmarshal into
            diff: The extra arguments that were passed to @cls
        """
        msg = "\n".join([
            "", # Newline to make the output cleaner
            "ctor: {}".format(cls),
            "extras: {}".format(diff)
        ])
        Exception.__init__(self, msg)
        self.type = str(
            type(self),
        )
        self.cls = str(cls)
        self.diff = str(diff)
        self.type = self.__class__.__name__


class InitArgsError(Exception):
    """ Raised when unmarshalling a class raises an Exception

        This exception can be marshalled into JSON for sending
        to clients.  However, it cannot be unmarshalled back into
        an InitArgsError
    """
    def __init__(
        self,
        cls: Any,
        cls_args: Iterable[Any],
        kwargs: dict,
        ex: Exception,
    ):
        """ Note that type_assert can't be used because it would
            create a circular dependency.

        Args:
            cls,      type-or-static-method, The type or constructor
                      that was attempted to unmarshal into
            cls_args: list, The arguments of @cls
            kwargs:   dict, The arguments that were passed to @cls
            ex:       Exception, The exception that was raised
        """
        msg = "\n".join([
            "", # Newline to make the output cleaner
            "module: {}".format(cls.__module__),
            "ctor: {}".format(cls),
            "ctor_args: {}".format(cls_args),
            "args (after removing args not in ctor_args): {}".format(kwargs),
            "only in ctor_args: {}".format(
                [x for x in cls_args if x not in kwargs]
            ),
            "exception: {}".format(ex),
        ])
        Exception.__init__(self, msg)
        self.type = str(
            type(self),
        )
        self.cls = str(cls)
        self.cls_args = str(cls_args)
        self.kwargs = str(kwargs)
        self.ex = str(ex)
        self.type = self.__class__.__name__

def _marshal_value(
    k,
    v,
    types,
    method,
    **m_kwargs
):
    if isinstance(v, dict):
        return marshal_dict(v, types)
    elif isinstance(v, list):
        return _marshal_list(v, types)
    elif isinstance(v, types):
        return v
    elif method:
        return getattr(v, method)(**m_kwargs)
    else:
        return marshal_dict(v, types)

def _marshal_list(
    _list: Iterable,
    types,
) -> list:
    return [
        x if isinstance(x, (bool, float, int, str, type(None)))
        else marshal_dict(x, types)
        for x in _list
    ]

def marshal_dict(
    obj: object,
    types,
    method: Optional[str]=None,
    fields: Optional[Iterable[str]]=None,
    **m_kwargs
) -> dict:
    """ Recursively marshal a Python object to a dict
        that can be passed to json.{dump,dumps}, a web client,
        or a web server, document database, etc...

    Args:
        obj:      object, It's members can be nested Python
                  objects which will be converted to dictionaries
        types:    tuple-of-types, The primitive types that can be
                  serialized
        method:   None-or-str, None to use 'marshal_dict' recursively,
                  or a str that corresponds to the name of a class method
                  to use.  Any nested types that are not an instance of
                  @types must have this method defined.
        fields:   None-list-of-str, Explicitly marshal only these fields
        m_kwargs: Keyword arguments to pass to @method
    """
    has_slots, d = _get_dict(obj)

    if fields:
        for field in fields:
            assert field in d
        return {
            k: _marshal_value(k, v, types, method, **m_kwargs)
            for k, v in d.items()
            if k in fields
        }

    excl = getattr(obj, '_marshal_exclude', [])

    if (
        has_slots
        or
        getattr(obj, '_marshal_only_init_args', False)
    ):
        args = init_args(obj)
        excl.extend([x for x in d if x not in args])

    if getattr(obj, '_marshal_exclude_none', False):
        excl.extend(k for k, v in d.items() if v is None)
    else:
        none_keys = getattr(obj, '_marshal_exclude_none_keys', [])
        if none_keys:
            excl.extend(x for x in none_keys if d.get(x) is None)

    return {
        k: _marshal_value(k, v, types, method, **m_kwargs)
        for k, v in d.items()
        if k not in excl
    }

def unmarshal_dict(
    obj: dict,
    cls: Any,
    allow_extra_keys: bool=True,
    ctor: Optional[Callable]=None,
):
    """ Unmarshal @obj into @cls

    Args:
        obj:              The dict to unmarshal into @cls
        cls:              The class to unmarshal into
        allow_extra_keys: False to raise an exception when extra
                          keys are present, True to ignore
        ctor:             Use this as a constructor instead of __init__
    Returns:
        instance of @cls
    Raises:
        ExtraKeysError: If allow_extra_keys == False, and extra keys
                        are present in @obj and not in @cls.__init__
        ValueError:     If @cls.__init__ does not contain a self argument
    """
    if not ctor:
        ctor = cls
    args = init_args(ctor)
    obj = key_swap(obj, cls, False)
    kwargs = {k: v for k, v in obj.items() if k in args}

    # If either is set to False, do not allow extra keys
    # to be present in obj but not in cls.__init__
    allow_extra_keys = (
        getattr(cls, '_unmarshal_allow_extra_keys', True)
        and
        allow_extra_keys
    )

    if not allow_extra_keys and len(obj) > len(kwargs):
        diff = {k: v for k, v in obj.items() if k not in args}
        raise ExtraKeysError(cls, diff)

    try:
        return ctor(**kwargs)
    except ExtraKeysError as ex:
        raise ex
    except Exception as ex:
        raise InitArgsError(
            cls,
            args,
            kwargs,
            ex,
        )


def marshal_list(
    obj: Any,
    types,
    fields=None,
) -> list:
    """ Marshal @obj into a list
    Args:
        obj:   the object to marshal into a list
        types: an iterable of valid types for this serialization format
    Raises:
        ValueError: If the class fields contain invalid types
    """
    if not fields:
        fields = obj.__init__.__code__.co_varnames
        # Calling the self arg something other than self is not supported
        if fields[0] == 'self':
            fields = fields[1:]
    result = [
        getattr(obj, arg)
        for arg in fields
    ]

    if (
        hasattr(obj, '_marshal_list_row_header')
        and
        isinstance(
            obj._marshal_list_row_header,
            types,
        )
    ):
        result.insert(0, obj._marshal_list_row_header)

    invalid = [
        x for x in result
        if type(x) not in types
    ]
    if invalid:
        raise ValueError("Invalid fields: {}".format(invalid))
    return result

def unmarshal_list(
    _list,
    cls,
):
    """ Unmarshal @_list into @cls.
        @_list must be ordered correctly for the positional arguments of @cls

    Args:
        _list:
            list-or-tuple, The list to unmarshal into @cls
        cls:
            type-or-function-or-dict-of-str:function,
            The class to unmarshal into.  If a dict, it should have str keys
            with __init__ function values, the key will be the row header
    Returns:
        List of instances of @cls
    Raises:
        InitArgsError: If instantiation fails
    """
    if isinstance(cls, dict):
        cls = cls[_list[0]]
        _list = _list[1:]
    try:
        return cls(*_list)
    except Exception as ex:
        raise InitArgsError(
            cls,
            _list,
            {},
            ex,
        )
