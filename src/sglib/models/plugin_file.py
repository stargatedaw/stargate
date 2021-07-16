from .cc_mapping import CCMapping
from sglib.lib import util

class plugin_file:
    """ Abstracts an instrument state file.  Plugins are not required
        to implement this and can instead implement their own custom
        state files, but this should be a sane and well tested way
        for most plugins to save their state.
    """
    def __init__(self, a_path=None):
        self.port_dict = {}
        self.configure_dict = {}
        self.cc_map = {}
        if a_path is not None:
            f_text = util.read_file_text(a_path)
            self.set_from_str(f_text)

    def set_from_str(self, a_str):
        f_line_arr = a_str.split("\n")
        for f_line in f_line_arr:
            if f_line == "\\":
                break
            f_items = f_line.split("|", 1)
            if f_items[0] == 'c':
                f_items2 = f_items[1].split("|", 1)
                self.configure_dict[(f_items2[0])] = f_items2[1]
            elif f_items[0] == 'm':
                f_cc, f_val = f_items[1].split("|", 1)
                self.cc_map[int(f_cc)] = CCMapping.from_str(f_items[1])
            else:
                self.port_dict[int(f_items[0])] = int(float(f_items[1]))

    @staticmethod
    def from_str(a_str):
        f_result = plugin_file()
        f_result.set_from_str(a_str)
        return f_result

    @staticmethod
    def from_dict(a_port_dict, a_configure_dict, a_cc_map_dict):
        f_result = plugin_file()
        for k, v in a_port_dict.items():
            f_result.port_dict[int(k)] = v
        for k, v in a_configure_dict.items():
            f_result.configure_dict[k] = v
        for k, v in a_cc_map_dict.items():
            f_result.cc_map[k] = v
        return f_result

    def __str__(self):
        f_result = []
        for k in sorted(self.configure_dict):
            v = self.configure_dict[k]
            f_result.append("|".join(str(x) for x in ("c", k, v)))
        for k in sorted(self.cc_map):
            v = self.cc_map[k]
            f_result.append(str(v))
        for k in sorted(self.port_dict):
            v = self.port_dict[k]
            f_result.append(
                "|".join(
                    str(int(x))
                    for x in (k, v.get_value())
                )
            )
        f_result.append("\\")
        return "\n".join(f_result)

