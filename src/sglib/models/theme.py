try:
    from sg_py_vendor.pymarshal.json import *
except ImportError:
    from pymarshal.json import *

from sglib.constants import HOME, MAJOR_VERSION
from sglib.lib.util import (
    get_file_setting,
    INSTALL_PREFIX,
    IS_WINDOWS,
    SHARE_DIR,
    THEMES_DIR,
)
from sglib.log import LOG

import json
import os
import shutil

import jinja2
import yaml


ASSETS_DIR = None
ICON_PATH = None
THEME_FILE = None

class DawColors:
    def __init__(
        self,
        seq_atm_item='#ffffff',
        seq_atm_item_selected='#000000',
        seq_atm_line='#ffffff',
        seq_item_note="#a5a5a5",
        seq_item_audio="#969696",
        seq_item_text="#ffffff",
        seq_item_text_selected="#000000",
        seq_bar_line="#787878",
        seq_beat_line="#d2d2d2",
        seq_16th_line="#090909",
        seq_track_line="#181818",
        seq_background="#424242",
        seq_item_background="#424242",
        seq_selected_item="#eeeeee",
        seq_header="#1d1e22",
        seq_header_text="#ffffff",
        seq_header_sequence_start="#7878ff",
        seq_header_sequence_end="#ff3c3c",
        seq_tempo_marker="#ffffff",
        track_default_colors=[
            "#b00fb8",
            "#0f1cb8",
            "#62b80f",
            "#b3b80f",
            "#b80f0f",
        ],
        item_audio_handle="#ffffff",
        item_audio_handle_selected="#181818",
        item_audio_vol_line="#ff0000",
        item_audio_label="#ffffff",
        item_audio_label_selected="#1e1e1e",
        item_audio_waveform="#1e1e1e",
        item_atm_point="#f00e0e",
        item_atm_point_selected="#f0f0f0",
        item_atm_point_pen="#d00e0e",
        note_beat_line="#000000",
        note_black_background="#1e1e1e",
        note_root_background="#5f1e1e",
        note_snap_line="#000000",
        note_white_background="#5f5f61",
        playback_cursor="#ff0000",
    ):
        self.seq_atm_item = type_assert(
            seq_atm_item,
            str,
            desc="Sequencer automation points",
        )
        self.seq_atm_item_selected = type_assert(
            seq_atm_item_selected,
            str,
            desc="Selected sequencer automation points",
        )
        self.seq_atm_line = type_assert(
            seq_atm_line,
            str,
            desc="Sequencer automation lines",
        )
        self.seq_item_note = type_assert(
            seq_item_note,
            str,
            desc="Used to paint notes on sequencer items",
        )
        self.seq_item_audio = type_assert(
            seq_item_audio,
            str,
            desc="Used to paint audio on sequencer items",
        )
        self.seq_item_text = type_assert(
            seq_item_text,
            str,
            desc="The label text for sequencer items",
        )
        self.seq_item_text_selected = type_assert(
            seq_item_text_selected,
            str,
            desc="The label text for selected sequencer items",
        )
        self.seq_bar_line = type_assert(
            seq_bar_line,
            str,
            desc="Vertical bar lines in the sequencer",
        )
        self.seq_beat_line = type_assert(
            seq_beat_line,
            str,
            desc="Vertical beat lines in the sequencer",
        )
        self.seq_16th_line = type_assert(
            seq_16th_line,
            str,
            desc="Vertical beat lines in the sequencer",
        )
        self.seq_track_line = type_assert(
            seq_track_line,
            str,
            desc="Horizontal track lines in the sequencer",
        )
        self.seq_background = type_assert(
            seq_background,
            str,
            desc="Sequencer QGraphicsScene background",
        )
        self.seq_item_background = type_assert(
            seq_item_background,
            str,
            desc="The background fill color of the sequencer items",
        )
        self.seq_selected_item = type_assert(
            seq_selected_item,
            str,
            desc="Selected sequencer items",
        )
        self.seq_header = type_assert(
            seq_header,
            str,
            desc="Sequencer header",
        )
        self.seq_header_text = type_assert(
            seq_header_text,
            str,
            desc="Sequencer header text",
        )
        self.seq_header_sequence_start = type_assert(
            seq_header_sequence_start,
            str,
            desc="Sequencer header sequence start marker",
        )
        self.seq_header_sequence_end = type_assert(
            seq_header_sequence_end,
            str,
            desc="Sequencer header sequence end marker",
        )
        self.seq_tempo_marker = type_assert(
            seq_tempo_marker,
            str,
            desc="Sequencer tempo marker",
        )
        self.track_default_colors = type_assert_iter(
            track_default_colors,
            str,
            desc="Default track colors",
        )
        self.item_audio_handle = type_assert(
            item_audio_handle,
            str,
            desc="Item editor audio item handle",
        )
        self.item_audio_handle_selected = type_assert(
            item_audio_handle_selected,
            str,
            desc="Item editor selected audio item handle",
        )
        self.item_audio_vol_line = type_assert(
            item_audio_vol_line,
            str,
            desc=("""
                The horizontal line that is drawn on audio items during
                volume manipulation using mouse click+drag with
                modifier keys.  The item will be selected, so this color
                must contrast with the selected color
            """),
        )
        self.item_audio_label = type_assert(
            item_audio_label,
            str,
            desc=("""
                The text on an audio item that displays data such as file
                name, and volume during mouse modifier operations.  The item
                will be selected, this color must contrast with the selected
                color
            """),
        )
        self.item_audio_label_selected = type_assert(
            item_audio_label_selected,
            str,
            desc=("""
                The text on an audio item that displays data such as file
                name, and volume during mouse modifier operations.  The item
                will be selected, this color must contrast with the selected
                color
            """),
        )
        self.item_audio_waveform = type_assert(
            item_audio_waveform,
            str,
            desc=("""
                The color used to draw the audio file waveform onto the
                audio item
            """),
        )
        self.item_atm_point = type_assert(
            item_atm_point,
            str,
            desc="Item editor CC/pitchbend automation point",
        )
        self.item_atm_point_selected = type_assert(
            item_atm_point_selected,
            str,
            desc="Item editor selected CC/pitchbend automation point",
        )
        self.item_atm_point_pen = type_assert(
            item_atm_point,
            str,
            desc=(
                "The pen drawing the outline of an item editor "
                "CC/pitchbend automation point"
            ),
        )
        self.note_root_background = type_assert(
            note_root_background,
            str,
            desc=(
                "The background of the note editor for the root key of the"
                "scale"
            ),
        )
        self.note_white_background = type_assert(
            note_white_background,
            str,
            desc="The background of the note editor for the white keys"
        )
        self.note_black_background = type_assert(
            note_black_background,
            str,
            desc="The background of the note editor for the black keys"
        )
        self.note_beat_line = type_assert(
            note_beat_line,
            str,
            desc="The vertical line drawn at each beat"
        )
        self.note_snap_line = type_assert(
            note_snap_line,
            str,
            desc="""
                The vertical lines drawn between beats according to
                snap settings, ie: 1/16th, 1/8th note, etc...
            """,
        )
        self.playback_cursor = type_assert(
            playback_cursor,
            str,
            desc="The sequencer playback cursor",
        )

class WidgetColors:
    def __init__(
        self,
        default_scene_background="#424242",
        knob_arc_pen="#ffffff",
        knob_background_pen="#5a5a5a",
        knob_bg_image="knob-bg.png",
        knob_fg_image="knob-fg.png",
        playback_cursor="#ff0000",
        rout_graph_node="#e7e700",
        rout_graph_node_text="#e7e7e7",
        rout_graph_to="#e7a0a0",
        rout_graph_from="#a0a0e7",
        rout_graph_lines="#696969",
    ):
        self.default_scene_background = type_assert(
            default_scene_background,
            str,
            desc=(
                "The default QGraphicsScene background color used by"
                "the widgets library"
            ),
        )
        self.knob_arc_pen = type_assert(
            knob_arc_pen,
            str,
            desc="Used to draw the arc around the knob",
        )
        self.knob_background_pen = type_assert(
            knob_background_pen,
            str,
            desc="Used to draw the knob background",
        )
        self.knob_bg_image = type_assert(
            knob_bg_image,
            str,
            desc="The knob background.",
        )
        self.knob_fg_image = type_assert(
            knob_fg_image,
            str,
            desc="The knob image.  Will be rotated as the knob moves",
        )
        self.playback_cursor = type_assert(
            playback_cursor,
            str,
            desc=(
                "The color of a playback cursor line"
            ),
        )
        self.rout_graph_node = type_assert(
            rout_graph_node,
            str,
            desc="Routing graph widget node",
        )
        self.rout_graph_node_text = type_assert(
            rout_graph_node_text,
            str,
            desc="Routing graph widget node text",
        )
        self.rout_graph_to = type_assert(
            rout_graph_to,
            str,
            desc="Routing graph widget to node when mouse hovering",
        )
        self.rout_graph_from = type_assert(
            rout_graph_from,
            str,
            desc="Routing graph widget from node when mouse hovering",
        )
        self.rout_graph_lines = type_assert(
            rout_graph_lines,
            str,
            desc="Routing graph widget matrix lines",
        )


class SystemColors:
    def __init__(
        self,
        daw,
        widgets
    ):
        self.daw = type_assert(daw, DawColors)
        self.widgets = type_assert(widgets, WidgetColors)

class VarsFile:
    def __init__(
        self,
        path,
        overrides,
    ):
        self.path = type_assert(path, str)
        self.overrides = type_assert_dict(
            overrides,
            kcls=str,
            vcls=str,
        )

class SystemOverrides:
    def __init__(
        self,
        daw,
        widgets,
    ):
        self.daw = type_assert_dict(
            daw,
            kcls=str,
            vcls=str,
        )
        self.widgets = type_assert_dict(
            widgets,
            kcls=str,
            vcls=str,
        )

class SystemFile:
    def __init__(
        self,
        path,
        overrides,
    ):
        self.path = type_assert(path, str)
        self.overrides = type_assert(overrides, SystemOverrides)

class Theme:
    def __init__(
        self,
        template,
        variables,
        system=None,
    ):
        self.template = type_assert(
            template,
            str,
            desc=(
                "The path to a QSS Jinja template file relative to the "
                "theme directory"
            ),
        )
        self.variables = type_assert(
            variables,
            VarsFile,
            desc=(
                "The path to a YAML file of variables to pass to the QSS "
                "Jinja template, and any overrides"
            ),
        )
        self.system = type_assert(
            system,
            SystemFile,
            allow_none=True,
            desc=(
                "The path to a YAML file containing a system colors "
                "definition, and any overrides"
            ),
        )

    def render(self, path):
        rendered_dir = os.path.join(HOME, 'rendered_theme')
        if not os.path.isdir(rendered_dir):
            os.makedirs(rendered_dir)
        dirname = os.path.dirname(path)
        var_path = os.path.join(dirname, 'vars', self.variables.path)
        shutil.copy(
            var_path,
            os.path.join(rendered_dir, 'variables.yaml'),
        )
        with open(var_path) as f:
            variables = yaml.safe_load(f)
        variables.update(self.variables.overrides)

        system_path = os.path.join(dirname, 'system', self.system.path)
        with open(system_path) as f:
            template = jinja2.Template(f.read())
            y = template.render(**variables)
            y = yaml.safe_load(y)
        y['daw'].update(self.system.overrides.daw)
        y['widgets'].update(self.system.overrides.widgets)
        system_colors = unmarshal_json(y, SystemColors)
        with open(
            os.path.join(rendered_dir, 'system.yaml'),
            'w'
        ) as f:
            json.dump(
                marshal_json(system_colors),
                f,
                indent=4,
            )

        template_path = os.path.join(dirname, 'templates', self.template)
        with open(template_path) as f:
            template = jinja2.Template(f.read())
            qss = template.render(
                ASSETS_DIR=ASSETS_DIR,
                SYSTEM_COLORS=system_colors,
                **variables
            )
        qss_path = os.path.join(rendered_dir, 'theme.qss')
        with open(qss_path, 'w') as f:
            f.write(qss)

        return qss, system_colors


def setup_globals():
    global ASSETS_DIR, ICON_PATH, THEME_FILE

    ICON_PATH = os.path.join(
        os.path.dirname(__file__),
        '..',
        '..',
        'files',
        "share",
        "pixmaps",
        "{}.png".format(
            MAJOR_VERSION
        ),
    )
    if not os.path.exists(ICON_PATH):
        ICON_PATH = os.path.join(
            SHARE_DIR,
            "pixmaps",
            "{}.png".format(
                MAJOR_VERSION
            ),
        )

    if IS_WINDOWS:
        ICON_PATH = os.path.join(
            INSTALL_PREFIX,
            "{}.ico".format(
                MAJOR_VERSION,
            ),
        )

    DEFAULT_THEME_FILE = os.path.join(
        THEMES_DIR,
        "default",
        "default.yaml",
    )

    if not os.path.exists(DEFAULT_THEME_FILE):
        DEFAULT_THEME_FILE = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '..',
                '..',
                'files',
                'themes',
                'default',
                'default.yaml',
            )
        )

    THEME_FILE = get_file_setting("default-style", str, None)
    if (
        not THEME_FILE
        or
        not os.path.isfile(THEME_FILE)
    ):
        THEME_FILE = DEFAULT_THEME_FILE

    LOG.info(f"Using stylesheet {THEME_FILE}")
    STYLESHEET_DIR = os.path.dirname(THEME_FILE)
    if IS_WINDOWS:
        STYLESHEET_DIR = STYLESHEET_DIR.replace("\\", "/")

    # In QSS, backslashes are not valid
    ASSETS_DIR = "/".join([
        STYLESHEET_DIR,
        'assets',
    ])

def load_theme():
    """ Load the QSS theme and system colors.  Do this before creating any
        widgets.
    """
    global QSS, SYSTEM_COLORS
    setup_globals()
    with open(THEME_FILE) as f:
        y = yaml.safe_load(f)
    theme = unmarshal_json(y, Theme)
    QSS, SYSTEM_COLORS = theme.render(THEME_FILE)

