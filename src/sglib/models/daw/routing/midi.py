
class MIDIRoute:
    def __init__(self, a_on, a_track_num, a_device_name, channel=0):
        self.on = int(a_on)
        self.track_num = int(a_track_num)
        self.device_name = str(a_device_name)
        self.channel = int(channel)

    def __str__(self):
        return "|".join(
            str(x) for x in (
                self.on,
                self.track_num,
                self.device_name,
                self.channel,
            )
        )


class MIDIRoutes:
    def __init__(self, a_routings=None):
        self.routings = a_routings if a_routings is not None else []

    def __str__(self):
        return "\n".join(str(x) for x in self.routings + ["\\"])

    def reorder(self, a_dict):
        for f_route in self.routings:
            if f_route.track_num in a_dict:
                f_route.track_num = a_dict[f_route.track_num]

    @staticmethod
    def from_str(a_str):
        f_routings = []
        for f_line in a_str.split("\n"):
            if f_line == "\\":
                break
            f_routings.append(MIDIRoute(*f_line.split("|")))
        return MIDIRoutes(f_routings)


