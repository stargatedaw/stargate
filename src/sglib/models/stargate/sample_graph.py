from sglib.math import clip_value, db_to_lin, lin_to_db
from sglib.lib import *
from sglib.lib.util import *
import numpy
import os


def clear_sample_graph_cache():
    global global_sample_graph_cache
    global_sample_graph_cache = {}

def remove_item_from_sg_cache(a_path):
    global global_sample_graph_cache
    if os.path.exists(a_path):
        os.remove(a_path)
    if a_path in global_sample_graph_cache:
        global_sample_graph_cache.pop(a_path)
    else:
        print("\n\nremove_item_from_sg_cache: {} "
            "not found.\n\n".format(a_path))

global_sample_graph_cache = {}

class SampleGraph:
    __slots__ = [
        'sample_graph_cache',
        '_file',
        'sample_dir',
        'sample_dir_file',
        'timestamp',
        'channels',
        'high_peaks',
        'low_peaks',
        'count',
        'length_in_seconds',
        'sample_rate',
        'frame_count',
        'peak',
        'cache',
    ]
    @staticmethod
    def create(a_file_name, a_sample_dir):
        """ Used to instantiate a sample_graph, but
            grabs from the cache if it already exists...
            Prefer this over directly instantiating.
        """
        f_file_name = str(a_file_name)
        global global_sample_graph_cache
        if f_file_name in global_sample_graph_cache:
            return global_sample_graph_cache[f_file_name]
        else:
            f_result = SampleGraph(f_file_name, a_sample_dir)
            global_sample_graph_cache[f_file_name] = f_result
            return f_result

    def __init__(self, a_file_name, a_sample_dir):
        """
        a_file_name:  The full path to /.../sample_graphs/uid
        a_sample_dir:  The project's sample dir
        """
        self.sample_graph_cache = None
        f_file_name = str(a_file_name)
        self._file = None
        self.sample_dir = str(a_sample_dir)
        self.sample_dir_file = None
        self.timestamp = None
        self.channels = None
        self.high_peaks = ([],[])
        self.low_peaks = ([],[])
        self.count = None
        self.length_in_seconds = None
        self.sample_rate = None
        self.frame_count = None
        self.peak = 0.0
        self.cache = None

        if not os.path.isfile(f_file_name):
            return

        try:
            f_line_arr = util.read_file_lines(f_file_name)
        except:
            return

        for f_line in f_line_arr:
            f_line_arr = f_line.split("|")
            if f_line_arr[0] == "\\":
                break
            elif f_line_arr[0] == "meta":
                if f_line_arr[1] == "filename":
                    #Why does this have a newline on the end???
                    self._file = str(f_line_arr[2]).strip("\n")
                    self.sample_dir_file = "{}{}".format(
                        self.sample_dir, self._file)
                elif f_line_arr[1] == "timestamp":
                    self.timestamp = int(f_line_arr[2])
                elif f_line_arr[1] == "channels":
                    self.channels = int(f_line_arr[2])
                elif f_line_arr[1] == "count":
                    self.count = int(f_line_arr[2])
                elif f_line_arr[1] == "length":
                    self.length_in_seconds = float(f_line_arr[2])
                elif f_line_arr[1] == "frame_count":
                    self.frame_count = int(f_line_arr[2])
                elif f_line_arr[1] == "sample_rate":
                    self.sample_rate = int(f_line_arr[2])
            elif f_line_arr[0] == "p":
                f_p_val = float(f_line_arr[3])
                f_abs_p_val = abs(f_p_val)
                if f_abs_p_val > self.peak:
                    self.peak = f_abs_p_val
                if f_p_val > 1.0:
                    f_p_val = 1.0
                elif f_p_val < -1.0:
                    f_p_val = -1.0
                if f_line_arr[2] == "h":
                    self.high_peaks[int(f_line_arr[1])].append(f_p_val)
                elif f_line_arr[2] == "l":
                    self.low_peaks[int(f_line_arr[1])].append(f_p_val)
                else:
                    print("Invalid sample_graph [2] value " + f_line_arr[2])
        for f_list in self.low_peaks:
            f_list.reverse()

        self.low_peaks = [numpy.array(x) for x in self.low_peaks]
        self.high_peaks = [numpy.array(x) for x in self.high_peaks]

        for f_high_peaks, f_low_peaks in zip(self.high_peaks, self.low_peaks):
            numpy.clip(f_high_peaks, 0.01, 0.99, f_high_peaks)
            numpy.clip(f_low_peaks, -0.99, -0.01, f_low_peaks)

    def is_valid(self):
        if (self._file is None):
            print("\n\nsample_graph.is_valid() "
                "self._file is None {}\n".format(self._file))
            return False
        if self.timestamp is None:
            print("\n\nsample_graph.is_valid() "
                "self.timestamp is None {}\n".format(self._file))
            return False
        if self.channels is None:
            print("\n\nsample_graph.is_valid() "
                "self.channels is None {}\n".format(self._file))
            return False
        if self.frame_count is None:
            print("\n\nsample_graph.is_valid() "
                "self.frame_count is None {}\n".format(self._file))
            return False
        if self.sample_rate is None:
            print("\n\nsample_graph.is_valid() "
                "self.sample_rate is None {}\n".format(self._file))
            return False
        return True

    def normalize(self, a_db=0.0):
        if self.peak == 0.0:
            return 0.0
        f_norm_lin = db_to_lin(a_db)
        f_diff = f_norm_lin / self.peak
        f_result = round(lin_to_db(f_diff), 1)
        f_result = clip_value(f_result, -24, 24)
        return f_result

    def check_mtime(self):
        """ Returns False if the sample graph is older than
            the file modified time

            UPDATE:  Now obsolete, will require some fixing if used again...
        """
        try:
            if os.path.isfile(self._file):
                f_timestamp = int(os.path.getmtime(self._file))
            elif os.path.isfile(self.sample_dir_file):
                #f_timestamp = int(os.path.getmtime(self.sample_dir_file))
                return True
            else:
                raise Exception("Neither original nor cached file exists.")
            return self.timestamp > f_timestamp
        except Exception as f_ex:
            print("\n\nError getting mtime: \n{}\n\n".format(f_ex.message))
            return False

