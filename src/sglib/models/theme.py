try:
    from sg_py_vendor.pymarshal.json import *
except ImportError:
    from pymarshal.json import *

from sglib.constants import HOME, MAJOR_VERSION
from sglib.lib.util import (
    get_file_setting,
    IS_WINDOWS,
    pi_path,
    set_file_setting,
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
_THEMES_DIR_SUB = '{{ SYSTEM_THEME_DIR }}'

class DawColors:
    def __init__(
        self,
        seq_antialiasing=False,
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
        seq_item_handle="#ffffff",
        seq_item_handle_selected="#ffffff",
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
        note_vel_max_color="#f89e19",
        note_vel_min_color="#199ef8",
        note_selected_color="#cccccc",
        playback_cursor="#ff0000",
    ):
        self.seq_antialiasing = type_assert(
            seq_antialiasing,
            bool,
        )
        self.seq_atm_item = type_assert(
            seq_atm_item,
            str,
        )
        self.seq_atm_item_selected = type_assert(
            seq_atm_item_selected,
            str,
        )
        self.seq_atm_line = type_assert(
            seq_atm_line,
            str,
        )
        self.seq_item_note = type_assert(
            seq_item_note,
            str,
        )
        self.seq_item_audio = type_assert(
            seq_item_audio,
            str,
        )
        self.seq_item_text = type_assert(
            seq_item_text,
            str,
        )
        self.seq_item_text_selected = type_assert(
            seq_item_text_selected,
            str,
        )
        self.seq_bar_line = type_assert(
            seq_bar_line,
            str,
        )
        self.seq_beat_line = type_assert(
            seq_beat_line,
            str,
        )
        self.seq_16th_line = type_assert(
            seq_16th_line,
            str,
        )
        self.seq_track_line = type_assert(
            seq_track_line,
            str,
        )
        self.seq_background = type_assert(
            seq_background,
            str,
        )
        self.seq_item_background = type_assert(
            seq_item_background,
            str,
        )
        self.seq_selected_item = type_assert(
            seq_selected_item,
            str,
        )
        self.seq_header = type_assert(
            seq_header,
            str,
        )
        self.seq_header_text = type_assert(
            seq_header_text,
            str,
        )
        self.seq_header_sequence_start = type_assert(
            seq_header_sequence_start,
            str,
        )
        self.seq_header_sequence_end = type_assert(
            seq_header_sequence_end,
            str,
        )
        self.seq_item_handle = type_assert(
            seq_item_handle,
            str,
        )
        self.seq_item_handle_selected = type_assert(
            seq_item_handle_selected,
            str,
        )
        self.seq_tempo_marker = type_assert(
            seq_tempo_marker,
            str,
        )
        self.track_default_colors = type_assert_iter(
            track_default_colors,
            str,
        )
        self.item_audio_handle = type_assert(
            item_audio_handle,
            str,
        )
        self.item_audio_handle_selected = type_assert(
            item_audio_handle_selected,
            str,
        )
        self.item_audio_vol_line = type_assert(
            item_audio_vol_line,
            str,
        )
        self.item_audio_label = type_assert(
            item_audio_label,
            str,
        )
        self.item_audio_label_selected = type_assert(
            item_audio_label_selected,
            str,
        )
        self.item_audio_waveform = type_assert(
            item_audio_waveform,
            str,
        )
        self.item_atm_point = type_assert(
            item_atm_point,
            str,
        )
        self.item_atm_point_selected = type_assert(
            item_atm_point_selected,
            str,
        )
        self.item_atm_point_pen = type_assert(
            item_atm_point_pen,
            str,
        )
        self.note_root_background = type_assert(
            note_root_background,
            str,
        )
        self.note_white_background = type_assert(
            note_white_background,
            str,
        )
        self.note_black_background = type_assert(
            note_black_background,
            str,
        )
        self.note_beat_line = type_assert(
            note_beat_line,
            str,
        )
        self.note_snap_line = type_assert(
            note_snap_line,
            str,
        )
        self.note_vel_max_color = type_assert(
            note_vel_max_color,
            str,
        )
        self.note_vel_min_color = type_assert(
            note_vel_min_color,
            str,
        )
        self.note_selected_color = type_assert(
            note_selected_color,
            str,
        )
        self.playback_cursor = type_assert(
            playback_cursor,
            str,
        )

class WidgetColors:
    def __init__(
        self,
        default_scene_background="#424242",
        knob_arc_pen="#ffffff",
        knob_background_pen="#5a5a5a",
        knob_bg_image="knob-bg.png",
        knob_fg_image="knob-fg.png",
        playback_cursor="#aa0000",
        rout_graph_node="#e7e700",
        rout_graph_node_text="#e7e7e7",
        rout_graph_to="#e7a0a0",
        rout_graph_from="#a0a0e7",
        rout_graph_lines="#696969",
        rout_graph_wire_audio="#cccccc",
        rout_graph_wire_midi="#6666cc",
        rout_graph_wire_sc="#cc6666",
        splash_screen="splash.png",
        splash_screen_text="#ffffff",
    ):
        self.default_scene_background = type_assert(
            default_scene_background,
            str,
        )
        self.knob_arc_pen = type_assert(
            knob_arc_pen,
            str,
        )
        self.knob_background_pen = type_assert(
            knob_background_pen,
            str,
        )
        self.knob_bg_image = type_assert(
            knob_bg_image,
            str,
        )
        self.knob_fg_image = type_assert(
            knob_fg_image,
            str,
        )
        self.playback_cursor = type_assert(
            playback_cursor,
            str,
        )
        self.rout_graph_node = type_assert(
            rout_graph_node,
            str,
        )
        self.rout_graph_node_text = type_assert(
            rout_graph_node_text,
            str,
        )
        self.rout_graph_to = type_assert(
            rout_graph_to,
            str,
        )
        self.rout_graph_from = type_assert(
            rout_graph_from,
            str,
        )
        self.rout_graph_lines = type_assert(
            rout_graph_lines,
            str,
        )
        self.rout_graph_wire_audio = type_assert(
            rout_graph_wire_audio,
            str,
        )
        self.rout_graph_wire_midi = type_assert(
            rout_graph_wire_midi,
            str,
        )
        self.rout_graph_wire_sc = type_assert(
            rout_graph_wire_sc,
            str,
        )
        self.splash_screen = type_assert(
            splash_screen,
            str,
        )
        self.splash_screen_text = type_assert(
            splash_screen_text,
            str,
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
        self.overrides = type_assert(
            overrides,
            dict,
        )

class SystemOverrides:
    def __init__(
        self,
        daw,
        widgets,
    ):
        self.daw = type_assert(
            daw,
            dict,
        )
        self.widgets = type_assert_dict(
            widgets,
            dict,
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
        LOG.info(f"Overriding {variables}")
        LOG.info(f"with {self.variables.overrides}")
        variables.update(self.variables.overrides)
        LOG.info(f"Result: {variables}")

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
        "{}.ico".format(
            MAJOR_VERSION
        ),
    )
    if not os.path.exists(ICON_PATH):
        ICON_PATH = os.path.join(
            SHARE_DIR,
            "pixmaps",
            "{}.ico".format(
                MAJOR_VERSION
            ),
        )
    ICON_PATH = os.path.abspath(ICON_PATH)

    DEFAULT_THEME_FILE = os.path.join(
        THEMES_DIR,
        "default",
        "default.sgtheme",
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
                'default.sgtheme',
            )
        )

    THEME_FILE = get_file_setting("default-style", str, None)
    if THEME_FILE:
        # The Windows install prefix changes everytime Stargate is launched,
        # so substitute it every time the file is saved or loaded
        THEME_FILE = THEME_FILE.replace(
            _THEMES_DIR_SUB,
            pi_path(THEMES_DIR),
        )

    if (
        not THEME_FILE
        or
        not os.path.isfile(THEME_FILE)
    ):
        LOG.warning(
            f"Theme file: '{THEME_FILE}', does not exist, using default"
        )
        THEME_FILE = DEFAULT_THEME_FILE


    LOG.info(f"Using theme file {THEME_FILE}")
    STYLESHEET_DIR = os.path.dirname(THEME_FILE)
    if IS_WINDOWS:
        STYLESHEET_DIR = STYLESHEET_DIR.replace("\\", "/")

    # In QSS, backslashes are not valid
    ASSETS_DIR = "/".join([
        STYLESHEET_DIR,
        'assets',
    ])

def open_theme(
    theme_file: str,
):
    with open(theme_file) as f:
        y = yaml.safe_load(f)
    theme = unmarshal_json(y, Theme)
    return theme.render(THEME_FILE)

def load_theme():
    """ Load the QSS theme and system colors.  Do this before creating any
        widgets.
    """
    global QSS, SYSTEM_COLORS
    setup_globals()
    QSS, SYSTEM_COLORS = open_theme(THEME_FILE)

def copy_theme(dest):
    theme_dir = os.path.dirname(THEME_FILE)
    shutil.copytree(theme_dir, dest)

def set_theme(path):
    path = pi_path(path)
    # Test that the theme parses before accepting it.
    # Will raise an exception if malformed data, you must use try/except
    open_theme(path)
    # The Windows install prefix changes everytime Stargate is launched,
    # so substitute it every time the file is saved or loaded
    path = path.replace(
        pi_path(THEMES_DIR),
        _THEMES_DIR_SUB,
    )
    LOG.info(f"Setting theme file {path}")
    set_file_setting("default-style", path)

