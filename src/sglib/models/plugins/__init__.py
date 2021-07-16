from . import sampler1

_LOOKUP = {
    1: sampler1,
}

def get_plugin_by_uid(uid: int):
    """ Return a plugin models module if the plugin has one
        @uid:
            The UID of the plugin (the plugin itself, not it's uid
            of the plugin pool instance)

    """
    return _LOOKUP.get(uid, None)

__all__ = [
    'get_plugin',
]
