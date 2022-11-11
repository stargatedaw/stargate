from sglib.models.plugins import get_plugin_by_uid

class track_plugin:
    def __init__(
        self,
        a_index,
        a_plugin_index,
        a_plugin_uid,
        a_mute=0,
        a_solo=0,
        a_power=1,
        route=0,
        audio_input=1,
        midi_channel=0,
    ):
        self.index = int(a_index)  # index in the plugin chain
        self.plugin_index = int(a_plugin_index) # the plugin type
        self.plugin_uid = int(a_plugin_uid) # the uid in the project
        self.mute = int(a_mute)
        self.solo = int(a_solo)
        self.power = int(a_power)
        self.route = int(route)
        self.audio_input = int(audio_input)
        self.midi_channel = int(midi_channel)

    def get_audio_pool_uids(self):
        if not self.plugin_index:
            return set()
        plugin = get_plugin_by_uid(self.plugin_index)
        if hasattr(plugin, 'get_audio_pool_uids'):
            return plugin.get_audio_pool_uids(self.plugin_uid)
        return set()

    def __str__(self):
        return "|".join(
            str(x) for x in (
                "p",
                self.index,
                self.plugin_index,
                self.plugin_uid,
                self.mute,
                self.solo,
                self.power,
                self.route,
                self.audio_input,
                self.midi_channel,
            )
        )


class track_plugins:
    def __init__(self):
        self.plugins = []

    def get_audio_pool_uids(self):
        result = set()
        for plugin in self.plugins:
            for uid in plugin.get_audio_pool_uids():
                result.add(uid)
        return result

    def __str__(self):
        return "\n".join(str(x) for x in self.plugins + ["\\"])

    @staticmethod
    def from_str(a_str):
        f_result = track_plugins()
        f_str = str(a_str)
        for f_line in f_str.split():
            if f_line == "\\":
                break
            f_line_arr = f_line.split("|")
            if f_line_arr[0] == "p":
                f_result.plugins.append(track_plugin(*f_line_arr[1:]))
            else:
                assert(False)
        # TODO: STARGATEv2:  Remove this kludge for handing the track send
        #                    limit increase from 4 to 16
        if len(f_result.plugins) < 26:
            for i in range(len(f_result.plugins), 26):
                f_result.plugins.append(track_plugin(i, 0, -1))
        assert len(f_result.plugins) == 26, (
            len(f_result.plugins),
            f_result.plugins,
        )
        return f_result

