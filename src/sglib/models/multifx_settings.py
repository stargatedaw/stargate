from sglib.lib import util


class multifx_settings:
    def __init__(self, a_knob0, a_knob1, a_knob2, a_type):
        self.knobs = []
        self.knobs.append(int(a_knob0))
        self.knobs.append(int(a_knob1))
        self.knobs.append(int(a_knob2))
        self.fx_type = int(a_type)

    def __lt__(self, other):
        if self.index > other.index:
            return False
        else:
            return self.fx_num < other.fx_num

    def __str__(self):
        return "|{}".format(
            "|".join(
                util.proj_file_str(x)
                for x in (
                    self.knobs[0],
                    self.knobs[1],
                    self.knobs[2],
                    self.fx_type,
                )
            )
        )

