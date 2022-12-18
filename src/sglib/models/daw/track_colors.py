from sglib.models import theme
import ast


class TrackColors:
    __slots__ = [
        'colors',
    ]
    def __init__(self):
        self.colors = {}

    def _check_color(self, a_track_num):
        a_track_num = int(a_track_num)
        if a_track_num not in self.colors:
            default_track_colors = \
                theme.SYSTEM_COLORS.daw.track_default_colors
            index = a_track_num % len(default_track_colors)
            self.colors[a_track_num] = default_track_colors[index]

    def get_color(self, a_track_num):
        self._check_color(a_track_num)
        return self.colors[int(a_track_num)]

    def set_color(self, a_track_num, a_color):
        """ Associate a track number with a color

            @a_track_num: int, the track number
            @a_color:     str, hex color
        """
        self.colors[int(a_track_num)] = a_color

    def __str__(self):
        return str(self.colors)

    @staticmethod
    def from_str(a_str):
        result = TrackColors()
        result.colors = ast.literal_eval(a_str)
        return result

