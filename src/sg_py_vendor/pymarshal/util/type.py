"""

"""

from typing import Optional

from .marshal import unmarshal_dict
from .key_swap import key_swap
import inspect


__all__ = [
    'type_assert',
    'type_assert_dict',
    'type_assert_iter',
]


def _msg(
    obj,
    cls,
):
    return '{0} is not an instance of {1}, is {2}'.format(
        obj,
        cls,
        type(obj),
    )


def _check_isinstance(obj, cls):
    if not isinstance(obj, cls):
        msg = _msg(obj, cls)
        raise TypeError(msg)


def _check(
    obj,
    cls,
    allow_none: bool=False,
    cast_from=None,
    cast_to=None,
    dynamic=None,
    ctor=None,
    false_to_none: bool=False,
    check=None,
    choices=None,
):
    if (
        allow_none
        and
        obj is None
    ):
        return obj

    if (
        false_to_none
        and
        not obj
    ):
        return None

    if (
        obj is None
        and
        dynamic is not None
    ):
        _check_isinstance(dynamic, cls)
        obj = dynamic

    if (
        cast_from
        and
        isinstance(obj, cast_from)
    ):
        if cast_to:
            cast = cast_to(obj)
            _check_isinstance(cast, cls)
            obj = cast
        else:
            obj = cls(obj)

    if (
        check
        and
        not check(obj)
    ):
        try:
            source = inspect.getsource(check)
        except OSError:
            # When running in the Python terminal, getting the source code
            # will fail.  So just give the function and address.
            source = check
        msg = "'{}' failed check '{}'".format(obj, source)
        raise ValueError(msg)

    if not isinstance(obj, cls):
        if isinstance(obj, dict):
            obj = key_swap(obj, cls, True)
            new_obj = unmarshal_dict(obj, cls, ctor=ctor)
            _check_isinstance(new_obj, cls)
            obj = new_obj
        elif isinstance(obj, (list, tuple)):
            obj = ctor(*obj) if ctor else cls(*obj)
            _check_choices(obj, choices)
            return obj
        else:
            msg = _msg(obj, cls)
            raise TypeError(msg)

    _check_choices(obj, choices)
    return obj


def _check_dstruct(obj, cls):
    if cls is not None:
        _check_isinstance(obj, cls)


def _check_choices(obj, choices):
    if (
        choices is not None
        and
        obj not in choices
    ):
        msg = "{} not in {}".format(obj, choices)
        raise ValueError(msg)


def type_assert(
    obj,
    cls,
    allow_none: bool=False,
    cast_from=None,
    cast_to=None,
    dynamic=None,
    choices=None,
    ctor=None,
    desc: Optional[str]=None,
    false_to_none=False,
    check=None,
):
    """ Assert that @obj is an instance of @cls

        Note that you cannot use this to unmarshal JSON if @cls
        is a tuple of types, it can only be a single type.

        Will also unmarshal JSON objects to Python objects if @obj
        is an instance of dict and @cls is not dict

        Args:
            obj:        object instance, The object to type assert
            cls:        type,  The class type to assert
            allow_none: bool, True to allow '@obj is None', otherwise False
            cast_from:  type-or-tuple-of-types, If @obj is an instance
                        of this type(s), cast it to @cast_to
            cast_to:    type, The type to cast @obj to if it's an instance
                        of @cast_from, or None to cast to @cls.
                        If you need more than type(x), use a lambda or
                        factory function.
            dynamic:    @cls, A dynamic default value if @obj is None,
                        and @dynamic is not None.  @allow_none should be False
                        Valid uses:
                            datetime.datetime.now()
                            int(time.time())
                            # Or, to avoid the Python singleton bug when
                            # using arg=[], for example:
                            [], {}, set()
            choices:    iterable-or-None, If not None, @obj must
                        be in @choices
            ctor:       None-or-static-method, Use this method as the
                        constructor instead of __init__
            desc:       None-or-string, an optional description for this field,
                        for using this function to fully replace docstrings
            false_to_none: bool, True to cast falsey values such as "", 0, [],
                        to None
            check:      None-lambda-function, Single argument function to check
                        a value, return False if not valid, for example:
                            lambda x: x >= 0 and x < 256
        Returns:
            @obj
        Raises:
            TypeError:  If @obj is not an instance of @cls
            ValueError: If @check is not None and @obj fails @check
    """
    return _check(
        obj,
        cls,
        allow_none,
        cast_from,
        cast_to,
        dynamic=dynamic,
        ctor=ctor,
        false_to_none=false_to_none,
        check=check,
        choices=choices,
    )


def type_assert_iter(
    iterable,
    cls,
    cast_from=None,
    cast_to=None,
    dynamic=None,
    objcls=None,
    choices=None,
    ctor=None,
    allow_none: bool=False,
    desc: str=None,
    false_to_none: bool=False,
    check=None,
):
    """ Checks that every object in @iterable is an instance of @cls

        Will also unmarshal JSON objects to Python objects if items in
        @iterable are an instance of dict

        Args:
            iterable:   Any iterable to check.  Note that it would not
                        make sense to pass a generator to this function
            cls:        type, The class type to assert each member
                        of @iterable is
            cast_from:  type-or-tuple-of-types, If @obj is an instance
                        of this type(s), cast it to @cast_to
            cast_to:    type, The type to cast @obj to if it's an instance
                        of @cast_from, or None to cast to @cls.
                        If you need more than type(x), use a lambda or
                        factory function.
            dynamic:    @cls, A dynamic default value if @iterable is None,
                        and @dynamic is not None.
            objcls:     None-or-type, a type to assert @iterable is,
                        ie:  list, set, etc...
            choices:    iterable-or-None, If not None, each object in
                        @iterable must be in @choices
            ctor:       None-or-static-method: Use this method as the
                        constructor instead of __init__
            allow_none: bool, True to allow @iterable to be None,
                        otherwise False
            desc:       None-or-string, an optional description for this field,
                        for using this function to fully replace docstrings
            false_to_none: bool, True to cast falsey values such as "", 0, [],
                        to None
            check:      None-lambda-function, Single argument function to check
                        a value, return False if not valid, for example:
                            lambda x: x >= 0 and x < 256
        Returns:
            @iterable, note that @iterable will be recreated, which
            may be a performance concern if @iterable has many items
        Raises:
            TypeError:  If @obj is not an instance of @cls
            ValueError: If @check is not None and a value fails @check
    """
    if (
        allow_none
        and
        iterable is None
    ):
        return iterable

    _check_dstruct(iterable, objcls)

    if (
        iterable is None
        and
        dynamic is not None
    ):
        iterable = dynamic
    t = type(iterable)
    return t(
        _check(
            obj,
            cls,
            False,
            cast_from,
            cast_to,
            ctor=ctor,
            false_to_none=false_to_none,
            check=check,
            choices=choices,
        ) for obj in iterable
    )


def type_assert_dict(
    d,
    kcls=None,
    vcls=None,
    allow_none: bool=False,
    cast_from=None,
    cast_to=None,
    dynamic=None,
    objcls=None,
    ctor=None,
    desc: str=None,
    false_to_none: bool=False,
    check=None,
):
    """ Checks that every key/value in @d is an instance of @kcls: @vcls

        Will also unmarshal JSON objects to Python objects if
        the value is an instance of dict and @vcls is a class type

        Args:
            d:          The dict to type assert
            kcls:       The class to type assert for keys.
                        NOTE: JSON only allows str keys
            vcls:       The class to type assert for values
            allow_none: Allow a None value for the values.
                        This would not make sense for the keys.
            cast_from:  type-or-tuple-of-types, If @obj is an instance
                        of this type(s), cast it to @cast_to
            cast_to:    type, The type to cast @obj to if it's an instance
                        of @cast_from, or None to cast to @cls.
                        If you need more than type(x), use a lambda or
                        factory function.
            dynamic:    @cls, A dynamic default value if @d is None,
                        and @dynamic is not None.
            objcls:     None-or-type, a type to assert @d is,
                        ie:  dict, etc...
                        Note that isinstance considers
                        collections.OrderedDict to be of type dict
            ctor:       None-or-static-method: Use this method as the
                        constructor instead of __init__
            desc:       None-or-string, an optional description for this field,
                        for using this function to fully replace docstrings
            false_to_none: bool, True to cast falsey values such as "", 0, [],
                        to None
            check:      None-lambda-function, Single argument function to check
                        a value, return False if not valid, for example:
                            lambda x: x >= 0 and x < 256
        Returns:
            @d, note that @d will be recreated, which
            may be a performance concern if @d has many items
        Raises:
            TypeError:  If a key is not an instance of @kcls or
                        a value is not an instance of @vcls
            ValueError: If @check is not None and a value fails @check
    """
    _check_dstruct(d, objcls)

    if (
        d is None
        and
        dynamic is not None
    ):
        d = dynamic
    t = type(d)
    return t(
        (
            _check(k, kcls) if kcls else k,
            _check(
                v,
                vcls,
                allow_none,
                cast_from,
                cast_to,
                ctor=ctor,
                false_to_none=false_to_none,
                check=check,
            ) if vcls else v,
        )
        for k, v in d.items()
    )

