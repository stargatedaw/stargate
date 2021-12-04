try:
    from sg_py_vendor.pymarshal.csv import *
except ImportError:
    from pymarshal.csv import *
from sglib import constants
from sglib.lib.util import pi_path
from sglib.models.multifx_settings import multifx_settings
import os

__all__ = [
    'AudioPool',
    'AudioPoolEntry',
    'PerFileFX',
]

class AudioPoolEntry:
    def __init__(
        self,
        uid,
        volume,
        path,
    ):
        self.uid = type_assert(
            uid,
            int,
            cast_from=str,
            desc="The UID associated with this file",
        )
        self.volume = type_assert(
            volume,
            float,
            cast_from=str,
            desc="Volume level applied to the sample in dB",
        )
        self.path = type_assert(
            constants.PROJECT.to_long_audio_file_path(path),
            str,
            desc="The path to the audio file",
        )

    @staticmethod
    def from_str(_str):
        return AudioPoolEntry(
            *_str.split("|", 2),
        )

    def __str__(self):
        return "|".join(
            str(x) for x in (
                self.uid,
                self.volume,
                constants.PROJECT.to_short_audio_file_path(self.path),
            )
        )

    def __repr__(self):
        return (
            "AudioPoolEntry"
            f"(uid={self.uid}, volume={self.volume}, path={self.path})"
        )

class PerFileFX:
    def __init__(
        self,
        uid,
        controls,
    ):
        self.uid = type_assert(
            uid,
            int,
            cast_from=str,
        )
        self.controls = type_assert_iter(
            controls,
            multifx_settings,
            desc="""
                The controls associated with this file's effects
            """,
        )

    def __str__(self):
        return f"f|{self.uid}|" + "|".join(
            "|".join(
                str(y) for y in (
                    x.knobs[0],
                    x.knobs[1],
                    x.knobs[2],
                    x.fx_type,
                )
            )
            for x in self.controls
        )

    @staticmethod
    def from_str(_str):
        header, uid, rest = _str.split("|", 2)
        pm_assert(
            header == "f",
            KeyError,
            _str,
        )
        c = rest.split("|")
        controls = [
            multifx_settings(c[i], c[i+1], c[i+2], c[i+3])
            for i in range(0, 8 * 4, 4)
        ]
        return PerFileFX(
            uid,
            controls,
        )


class AudioPool:
    def __init__(
        self,
        pool,
        per_file_fx,
    ):
        self.pool = type_assert_iter(
            pool,
            AudioPoolEntry,
            desc="Entries describing audio files used in this project",
        )
        self.per_file_fx = type_assert_iter(
            per_file_fx,
            PerFileFX,
            desc="Entries describing audio files used in this project",
        )

    def add_entry(self, path, uid=None) -> AudioPoolEntry:
        path = pi_path(path)
        pm_assert(
            os.path.exists(path),
            FileNotFoundError,
            path,
        )
        by_path = self.by_path()
        pm_assert(
            path not in by_path,
            FileExistsError,
            (path, uid, by_path),
        )
        if uid is None:
            uid = self.next_uid()
        type_assert(uid, int)
        by_uid = self.by_uid()
        pm_assert(
            uid not in by_uid,
            FileExistsError,
            (uid, by_uid),
        )
        entry = AudioPoolEntry(uid, 0., path)
        self.pool.append(entry)
        return entry

    def remove_by_uid(self, uids):
        self.pool = [
            x for x in self.pool
            if x.uid not in uids
        ]

    def next_uid(self):
        if self.pool:
            return max(x.uid for x in self.pool) + 1
        else:
            return 0

    def by_uid(self):
        return {
            x.uid: x
            for x in self.pool
        }

    def by_path(self):
        return {
            x.path: x
            for x in self.pool
        }

    def per_file_fx_by_uid(self):
        return {
            x.uid: x
            for x in self.per_file_fx
        }

    def remove_per_file_fx(self, uid):
        length = len(self.per_file_fx)
        self.per_file_fx = [
            x for x in self.per_file_fx
            if x.uid != uid
        ]

    def set_per_file_fx(self, fx: PerFileFX):
        self.remove_per_file_fx(fx.uid)
        self.per_file_fx.append(fx)
        self.per_file_fx.sort(key=lambda x: x.uid)

    @staticmethod
    def from_str(_str):
        lines = [x for x in _str.split("\n") if x.strip()]
        if lines[-1] == "\\":
            lines = lines[:-1]
        pool = [
            x for x in lines
            if not x.startswith("f|")
        ]
        per_file_fx = [
            x for x in lines
            if x.startswith("f|")
        ]

        return AudioPool(
            pool=[
                AudioPoolEntry.from_str(x)
                for x in pool
            ],
            per_file_fx=[
                PerFileFX.from_str(x)
                for x in per_file_fx
            ]
        )

    @staticmethod
    def new():
        return AudioPool(
            pool=[],
            per_file_fx=[],
        )

    def __str__(self):
        if self.pool:
            pool = "\n".join(
                str(x) for x in self.pool
            )
            if self.per_file_fx:
                per_file_fx = "\n".join(
                    str(x) for x in self.per_file_fx
                )
                return f"{pool}\n{per_file_fx}\n\\"
            else:
                return f"{pool}\n\\"
        else:
            return "\\"

