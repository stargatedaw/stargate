
class CCMapping:
    def __init__(self, a_cc_num):
        self.cc_num = int(a_cc_num)
        self.ports = {}  # port_num : (low, high)

    def set_port(self, a_port, a_low=0.0, a_high=1.0):
        """ Return None on success or the ports on failure """
        a_port = int(a_port)
        if len(self.ports) >= 5 and a_port not in self.ports:
            return self.ports.keys()
        else:
            self.ports[a_port] = (float(a_low), float(a_high))
            return None

    def has_port(self, a_port):
        return int(a_port) in self.ports

    def remove_port(self, a_port):
        a_port = int(a_port)
        if a_port in self.ports:
            self.ports.pop(a_port)
            return True
        else:
            return False

    @staticmethod
    def from_str(a_str):
        f_cc_num, f_count, f_list = a_str.split("|", 2)
        f_list = f_list.split("|")
        f_result = CCMapping(f_cc_num)
        for f_i in range(0, int(f_count) * 3, 3):
            f_result.set_port(*f_list[f_i:f_i + 3])
        return f_result

    def __str__(self):
        f_result = ["|".join(str(x) for x in
            ("m", self.cc_num, len(self.ports)))]
        for k, v in self.ports.items():
            f_low, f_high = v
            f_result.append("|".join(str(x) for x in (k, f_low, f_high)))
        return "|".join(f_result)

