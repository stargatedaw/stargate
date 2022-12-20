from sglib.lib import *
from sglib.lib.util import *


class SgTakes:
    def __init__(self):
        self._dict = {}   # map take uid to a list of item uids
        self._lookup = {}  # map item uid to take uid

    def are_common(self, uids):
        """ Return a take uid if all item uids are part of the same take,
            otherwise return None
        """
        takes = {self._lookup.get(x, None) for x in uids}
        if len(takes) == 1:
            # The take could be None, but then it would just return None,
            # which is still the correct outcome
            return takes.pop()
        return None

    def get_take_uid(self, a_item_uid):
        a_item_uid = int(a_item_uid)
        if a_item_uid in self._lookup:
            return self._lookup[a_item_uid]
        else:
            return None

    def get_take(self, a_item_uid):
        result = self.get_take_uid(a_item_uid)
        return None if result is None else (result, self._dict[result])

    def set_take(self, a_item_uid_list, a_take_uid=None):
        assert isinstance(a_item_uid_list, list)
        if a_take_uid is None:  #auto-assign a new value
            if self._dict:
                a_take_uid = max(self._dict) + 1
            else:
                a_take_uid = 0
        else:
            a_take_uid = int(a_take_uid)
        self._dict[a_take_uid] = a_item_uid_list
        for f_uid in a_item_uid_list:
            self._lookup[f_uid] = a_take_uid

    def add_item(self, a_orig_uid, a_new_uid):
        a_orig_uid, a_new_uid = (int(x) for x in (a_orig_uid, a_new_uid))
        f_take = self.get_take(a_orig_uid)
        if f_take:
            f_take_uid, f_take = f_take
            if a_new_uid not in f_take:
                f_take.append(a_new_uid)
                self.set_take(f_take, f_take_uid)
        else:
            f_take = [a_orig_uid, a_new_uid]
            self.set_take(f_take)

    def __str__(self):
        result = []
        for k in sorted(self._dict):
            v = self._dict[k]
            result.append("|".join(str(x) for x in [k] + v))
        return "\n".join(result)

    def __repr__(self):
        return str(self)

    @staticmethod
    def from_str(a_str):
        result = SgTakes()
        for row in ([int(y) for y in x.split("|")] for x in a_str.split("\n")):
            key = row[0]
            value = row[1:]
            result._dict[key] = value
            for f_uid in value:
                result._lookup[f_uid] = key
        return result

