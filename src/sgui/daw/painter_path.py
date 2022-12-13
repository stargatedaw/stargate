from sglib import constants
from sglib.math import clip_max
from sgui import shared as glbl_shared
from sglib.models import theme
from sgui.daw import shared
from sgui.sgqt import *
from sgui.widgets.sample_graph import create_sample_graph

PIXMAP_BEAT_WIDTH = 48
PIXMAP_TILE_HEIGHT = 32
PIXMAP_TILE_WIDTH = 4000

PIXMAP_CACHE = {}
PIXMAP_CACHE_UNSCALED = {}


def scale_sizes(a_width_from, a_height_from, a_width_to, a_height_to):
    f_x = a_width_to / a_width_from
    f_y = a_height_to / a_height_from
    return (f_x, f_y)

def get_item_path(
    a_uid,
    a_px_per_beat,
    a_height,
    a_tempo,
):
    project = constants.DAW_PROJECT
    a_uid = int(a_uid)
    f_key = (a_px_per_beat, a_height, round(a_tempo, 1))
    if (
        a_uid in PIXMAP_CACHE
        and
        f_key in PIXMAP_CACHE[a_uid]
    ):
        return PIXMAP_CACHE[a_uid][f_key]
    else:
        f_item_obj = project.get_item_by_uid(a_uid)
        if a_uid not in PIXMAP_CACHE_UNSCALED:
            f_path = painter_path(
                f_item_obj,
                PIXMAP_BEAT_WIDTH,
                PIXMAP_TILE_HEIGHT,
                a_tempo,
            )
            PIXMAP_CACHE_UNSCALED[a_uid] = f_path
        if a_uid not in PIXMAP_CACHE:
            PIXMAP_CACHE[a_uid] = {}
        PIXMAP_CACHE[a_uid][f_key] = [
            x.scaled(
                int(a_px_per_beat * f_item_obj.get_length(a_tempo)),
                int(a_height),
            )
            for x in PIXMAP_CACHE_UNSCALED[a_uid]
        ]
        return PIXMAP_CACHE[a_uid][f_key]

def pop_path_from_cache(a_uid):
    if a_uid in PIXMAP_CACHE:
        PIXMAP_CACHE.pop(a_uid)
    if a_uid in PIXMAP_CACHE_UNSCALED:
        PIXMAP_CACHE_UNSCALED.pop(a_uid)

def clear_caches():
    PIXMAP_CACHE.clear()
    PIXMAP_CACHE_UNSCALED.clear()

def painter_path(
    item,
    a_px_per_beat,
    a_height,
    a_tempo,
):
    f_seconds_per_beat = 60.0 / a_tempo
    f_audio_path = QPainterPath()
    f_audio_path.addRect(0., 0., 1., 1.)
    for f_item in sorted(
        item.items.values(),
        key=lambda x: x.start_beat
    ):
        f_graph = constants.PROJECT.get_sample_graph_by_uid(f_item.uid)
        f_width = (
            f_graph.length_in_seconds / f_seconds_per_beat) * a_px_per_beat
        f_paths = create_sample_graph(
            f_graph,
            True,
            f_width,
            a_height,
            f_item,
        )
        f_y_inc = a_height / len(f_paths)
        f_y_pos = 0.0
        for f_painter_path in f_paths:
            f_painter_path.translate(
                a_px_per_beat * f_item.start_beat,
                f_y_pos,
            )
            f_audio_path.addPath(f_painter_path)
            f_y_pos += f_y_inc

    f_notes_path = QPainterPath()
    f_notes_path.addRect(0., 0., 1., 1.)
    if item.notes:
        f_note_set = sorted(
            set(x.note_num for x in item.notes),
            reverse=True,
        )
        f_note_h_area = (a_height * 0.6)
        f_note_height = round(f_note_h_area / len(f_note_set))
        f_note_height = clip_max(
            f_note_height,
            a_height * 0.05,
        )
        f_min = 1.0 - (min(f_note_set) / 127.0)
        f_note_bias = (
            f_note_h_area - (f_note_height * len(f_note_set))
        ) * f_min
        f_note_dict = {
            x:((((y * f_note_height) + a_height * 0.36)) + f_note_bias)
            for x, y in zip(f_note_set, range(len(f_note_set)))
        }
        for f_note in item.notes:
            f_y_pos = f_note_dict[f_note.note_num]
            f_x_pos = f_note.start * a_px_per_beat
            f_width = f_note.length * a_px_per_beat
            f_notes_path.addRect(
                float(f_x_pos),
                float(f_y_pos),
                float(f_width),
                float(f_note_height),
            )

    f_audio_width = f_audio_path.boundingRect().width()
    f_notes_width = f_notes_path.boundingRect().width()

    f_width = max(f_audio_width, f_notes_width)

    f_count = int(f_width // PIXMAP_TILE_WIDTH) + 1
    f_result = []

    f_note_brush = QColor(
        theme.SYSTEM_COLORS.daw.seq_item_note,
    )
    f_audio_brush = QColor(
        theme.SYSTEM_COLORS.daw.seq_item_audio,
    )
    f_note_pen = QPen(f_note_brush)
    f_pen = QPen(f_audio_brush)
    f_pen.setCosmetic(True)

    for f_i in range(f_count):
        f_pixmap = QPixmap(
            int(min(f_width, PIXMAP_TILE_WIDTH)),
            int(a_height),
        )
        f_width -= PIXMAP_TILE_WIDTH
        f_pixmap.fill(
            QColor(
                theme.SYSTEM_COLORS.daw.seq_item_background,
            )
        )
        f_painter = QPainter(f_pixmap)
        f_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        f_painter.setPen(f_pen)
        f_painter.setBrush(f_audio_brush)
        f_painter.drawPath(f_audio_path)
        f_painter.setPen(f_note_pen)
        f_painter.setBrush(f_note_brush)
        f_painter.drawPath(f_notes_path)
        f_painter.end()
        f_result.append(f_pixmap)
        for f_path in (f_notes_path, f_audio_path):
            f_path.translate(-PIXMAP_TILE_WIDTH, 0)
    return f_result

