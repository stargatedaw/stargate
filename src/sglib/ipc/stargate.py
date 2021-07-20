import os

from .abstract import AbstractIPC
from sglib import constants
from sglib.lib import util
from sglib.lib.util import get_wait_file_path, wait_for_finished_file
from sglib.log import LOG

class StargateIPC(AbstractIPC):
    def __init__(
        self,
        transport,
        with_audio,
        path="/stargate/main",
    ):
        AbstractIPC.__init__(
            self,
            transport,
            with_audio,
            path,
        )

    def stop_server(self):
        LOG.info("stop_server called")
        if self.with_audio:
            self.send_configure("exit", "")
            constants.IPC_ENABLED = False

    def kill_engine(self):
        self.send_configure("abort", "")

    def main_vol(self, a_vol):
        self.send_configure("mvol", str(round(a_vol, 8)))

    def update_plugin_control(self, a_plugin_uid, a_port, a_val):
        self.send_configure(
            "pc",
            "|".join(
                str(x) for x in (a_plugin_uid, a_port, a_val)
            ),
        )

    def configure_plugin(self, a_plugin_uid, a_key, a_message):
        self.send_configure(
            "co",
            "|".join(
                str(x) for x in (a_plugin_uid, a_key, a_message)
            )
        )

    def midi_learn(self):
        self.send_configure("ml", "")

    def load_cc_map(self, a_plugin_uid, a_str):
        self.send_configure(
            "cm",
            "|".join(
                str(x) for x in (a_plugin_uid, a_str)
            )
        )

    def add_to_audio_pool(
        self,
        a_file: str,
        a_uid: int,
        vol: float=0.0,
    ):
        """ Load a new file into the audio pool

            @a_file: The path to an audio file
            @a_uid:  The audio pool uid of the file
        """
        path = os.path.join(
            constants.PROJECT.samplegraph_folder,
            str(a_uid),
        )
        f_wait_file = get_wait_file_path(path)
        a_file = util.pi_path(a_file)
        self.send_configure(
            "wp",
            "|".join(
                str(x) for x in (a_uid, vol, a_file)
            ),
        )
        wait_for_finished_file(f_wait_file)

    def audio_pool_entry_volume(self, uid, vol):
        """ Update the volume of a single audio pool entry

            @uid: The uid of the audio pool entry
            @vol: The dB amplitude of the audio pool entry
        """
        self.send_configure(
            "apv",
            f"{uid}|{vol}",
        )

    def rate_env(self, a_in_file, a_out_file, a_start, a_end):
        f_wait_file = get_wait_file_path(a_out_file)
        self.send_configure(
            "renv",
            "{}\n{}\n{}|{}".format(
                a_in_file,
                a_out_file,
                a_start,
                a_end,
            ),
        )
        wait_for_finished_file(f_wait_file)

    def pitch_env(self, a_in_file, a_out_file, a_start, a_end):
        f_wait_file = get_wait_file_path(a_out_file)
        self.send_configure(
            "penv",
            "{}\n{}\n{}|{}".format(
                a_in_file,
                a_out_file,
                a_start,
                a_end,
            ),
        )
        wait_for_finished_file(f_wait_file)

    def preview_audio(self, a_file):
        self.send_configure("preview", util.pi_path(a_file))

    def stop_preview(self):
        self.send_configure("spr", "")

    def set_host(self, a_index):
        self.send_configure("abs", str(a_index))

    def reload_audio_pool_item(self, a_uid):
        self.send_configure("wr", str(a_uid))

    def audio_input_volume(self, a_index, a_vol):
        self.send_configure(
            "aiv",
            "|".join(
                str(x) for x in (a_index, a_vol)
            ),
        )

    def pause_engine(self):
        self.send_configure("engine", "1")

    def resume_engine(self):
        self.send_configure("engine", "0")

    def clean_audio_pool(self, a_msg):
        self.send_configure("cwp", a_msg)


