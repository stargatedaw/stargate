"""

"""
import datetime
import time
from typing import Iterable, List, Optional

# Will raise an import error if the user hasn't installed 'bson'
import bson

from .json import JSON_TYPES
from .util.marshal import *
from .util.pm_assert import pm_assert
from .util.type import *


__all__ = [
    'bson',
    'ExtraKeysError',
    'InitArgsError',
    'marshal_bson',
    'MongoDocument',
    'pm_assert',
    'type_assert',
    'type_assert_dict',
    'type_assert_iter',
    'unmarshal_bson',
]


BSON_TYPES: tuple = (
    bool,
    bson.ObjectId,
    datetime.datetime,
    dict,
    float,
    int,
    list,
    tuple,
    str,
    type(None),
)


class MongoDocument:
    """ Abstract class to facilitate inserting into MongoDB.
        Inherit this for classes that represent BSON documents.

        Assumes that you assigned the ObjectId in your
        class like:

            def __init__(
                self,
                ...,
                _id=None,
                ...,
            ):

            self._id = type_assert(
                _id,
                bson.ObjectId,
                allow_none=True,
            )
    """
    # If you need to override this, just add '_id' to the new list
    _marshal_exclude_none_keys:List[str] = ['_id']

    def json(
        self,
        include_id: bool=False,
        date_fmt: Optional[str]=None,
        object_id_fmt: type=str,
    ) -> dict:
        """ Helper method to convert to MongoDB documents to JSON

            This includes helpers to convert non-JSON compatible types
            to valid JSON types.  HOWEVER, it cannot recurse into nested
            classes.

        Args:
            include_id:    True to cast _id to a str,
                           False to omit from the result
            date_fmt:      None to cast to UNIX timestamp,
                           str (strftime format) to convert to string,
                           for example: '%Y-%m-%d_%H:%M:%S'
            object_id_fmt: Cast the bson.ObjectId's to this format,
                           or None to exclude.  This only applies to
                           ObjectId variables other than _id.
        """
        has_slots, d = _get_dict(self)
        _id = self._id
        if not include_id:
            self._id = None

        object_ids = {
            k: v for k, v in d.items()
            if isinstance(v, bson.ObjectId)
        }

        for k, v in object_ids.items():
            if object_id_fmt is None:
                setattr(self, k, None)
            else:
                setattr(self, k, object_id_fmt(v))

        datetimes = {
            k: v for k, v in d.items()
            if isinstance(v, datetime.datetime)
        }

        for k, v in datetimes.items():
            if date_fmt is None:
                ts = (
                    time.mktime(
                        v.timetuple(),
                    )
                    + v.microsecond
                    / 1e6
                )
                setattr(self, k, ts)
            else:
                setattr(self, k, v.strftime(date_fmt))

        j = marshal_dict(
            self,
            JSON_TYPES,
            'json',
            include_id=include_id,
            date_fmt=date_fmt,
            object_id_fmt=object_id_fmt,
        )
        self._id = _id

        for k, v in object_ids.items():
            setattr(self, k, v)

        for k, v in datetimes.items():
            setattr(self, k, v)

        return j


def marshal_bson(
    obj: object,
    types: Iterable=BSON_TYPES,
    fields: Optional[List[str]]=None,
) -> dict:
    """ Recursively marshal a Python object to a BSON-compatible dict
        that can be passed to PyMongo, Motor, etc...

    Args:
        obj:    It's members can be nested Python
                objects which will be converted to dictionaries
        types:  The BSON primitive types, typically
                you would not change this
        fields: Explicitly marshal only these fields
    """
    return marshal_dict(
        obj,
        types,
        fields=fields,
    )


def unmarshal_bson(
    obj: dict,
    cls: type,
    allow_extra_keys: bool=True,
    ctor=None,
):
    """ Unmarshal @obj into @cls

    Args:
        obj:              A BSON object
        cls:              The class to unmarshal into
        allow_extra_keys: False to raise an exception when extra
                          keys are present, True to ignore
        ctor:             Use this method as the
                          constructor instead of __init__
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
