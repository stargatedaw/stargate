try:
    from sg_py_vendor.pymarshal import pm_assert, type_assert, type_assert_iter
except ImportError:
    from pymarshal import pm_assert, type_assert, type_assert_iter

class PlaylistPoolEntry:
    def __init__(
        self,
        name,
        seq_uid,
    ):
        self.name = type_assert(
            name,
            str,
            desc="The friendly name of this sequence",
        )
        self.seq_uid = type_assert(
            seq_uid,
            int,
            desc="The UID of the sequence this corresponds to",
        )

class PlaylistEntry:
    def __init__(
        self,
        seq_uid,
    ):
        self.seq_uid = type_assert(
            seq_uid,
            int,
            desc="The UID of the sequence this corresponds to",
        )


class Playlist:
    def __init__(
        self,
        pool,
        playlist,
    ):
        self.pool = type_assert_iter(
            pool,
            PlaylistPoolEntry,
            desc="A mapping of sequence uid and name",
        )
        self.playlist = type_assert_iter(
            playlist,
            PlaylistEntry,
            desc="The playlist",
        )

    def add_to_pool(
        self,
        entry: PlaylistPoolEntry,
    ):
        type_assert(entry, PlaylistPoolEntry)
        by_name = self.pool_by_name()
        pm_assert(
            entry.name not in by_name,
            FileExistsError,
            msg=f"{entry.name} already exists",
        )
        self.pool.append(entry)
        self.pool.sort(key=lambda x: x.name)

    def pool_by_uid(self):
        return {
            x.seq_uid: x
            for x in self.pool
        }

    def pool_by_name(self):
        return {
            x.name: x
            for x in self.pool
        }

    @staticmethod
    def new():
        return Playlist(
            pool=[
                PlaylistPoolEntry(
                    'default',
                    0,
                )
            ],
            playlist=[
                PlaylistEntry(
                    0,
                )
            ],
        )

