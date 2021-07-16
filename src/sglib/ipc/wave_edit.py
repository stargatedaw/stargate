from .abstract import AbstractIPC
from sglib.lib.util import bool_to_int

class WaveEditIPC(AbstractIPC):
    def __init__(
        self,
        transport,
        a_with_audio=False,
        a_configure_path="/stargate/wave_edit",
    ):
        AbstractIPC.__init__(
            self,
            transport,
            a_with_audio,
            a_configure_path,
        )

    def wn_playback(self, a_mode):
        self.send_configure("wnp", str(a_mode))

    def set_plugin(
        self,
        a_track_num,
        a_index,
        a_plugin_index,
        a_uid,
        a_on,
    ):
        self.send_configure(
            "pi",
            "|".join(
                str(x) for x in (
                    a_track_num,
                    a_index,
                    a_plugin_index,
                    a_uid,
                    bool_to_int(a_on),
                )
            ),
        )

    def save_tracks(self):
        self.send_configure("st", "")

    def we_export(self, a_file_name):
        self.send_configure("wex", "{}".format(a_file_name))

    def ab_open(self, a_uid):
        self.send_configure("abo", str(a_uid))

    def we_set(self, a_val):
        self.send_configure("we", str(a_val))

    def panic(self):
        self.send_configure("panic", "")

    def save_audio_inputs(self):
        self.send_configure("ai", "")

