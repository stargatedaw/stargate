from sglib import constants
from sglib.models.daw import *
from sgui.daw.shared import *
from sgui.plugins import *
from sgui.sgqt import *

from . import _shared
from sglib.lib import strings as sg_strings
from sglib.lib import util
from sglib.lib.translate import _
from sglib.lib.util import *
from sgui import shared as glbl_shared
from sgui import widgets
from sgui.daw import shared

TRACK_COLOR_CLIPBOARD = None


class SeqTrack:
    """ The widget that contains the controls for an individual track
    """
    def __init__(self, a_track_num, a_track_text=_("track")):
        self.suppress_osc = True
        self.automation_uid = None
        self.automation_plugin = None
        self.track_number = a_track_num
        self.group_box = QWidget()
        self.group_box.contextMenuEvent = self.context_menu_event
        self.group_box.setObjectName("track_panel")
        self.main_hlayout = QHBoxLayout()
        self.main_hlayout.setContentsMargins(2, 2, 2, 2)
        self.main_vlayout = QVBoxLayout()
        self.main_hlayout.addLayout(self.main_vlayout)
        self.peak_meter = widgets.peak_meter()
        if a_track_num in shared.ALL_PEAK_METERS:
            shared.ALL_PEAK_METERS[a_track_num].append(self.peak_meter)
        else:
            shared.ALL_PEAK_METERS[a_track_num] = [self.peak_meter]
        self.main_hlayout.addWidget(self.peak_meter.widget)
        self.group_box.setLayout(self.main_hlayout)
        self.track_name_lineedit = QLineEdit()
        self.track_name_lineedit.setObjectName("track_panel")
        if a_track_num == 0:
            self.track_name_lineedit.setText("Main")
            self.track_name_lineedit.setDisabled(True)
        else:
            self.track_name_lineedit.setText(a_track_text)
            self.track_name_lineedit.setMaxLength(48)
            self.track_name_lineedit.editingFinished.connect(
                self.on_name_changed,
            )
        self.main_vlayout.addWidget(self.track_name_lineedit)
        self.hlayout3 = QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout3)
        self.main_vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )

        self.menu_button = QPushButton()
        self.menu_button.setFixedWidth(42)
        self.button_menu = QMenu()
        self.menu_button.setMenu(self.button_menu)
        self.hlayout3.addWidget(self.menu_button)
        self.button_menu.aboutToShow.connect(self.menu_button_pressed)
        self.menu_created = False
        self.solo_checkbox = QCheckBox()
        self.mute_checkbox = QCheckBox()
        self.hlayout3.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )
        if self.track_number != 0:
            self.solo_checkbox.stateChanged.connect(self.on_solo)
            self.solo_checkbox.setObjectName("solo_checkbox")
            self.hlayout3.addWidget(self.solo_checkbox)
            self.mute_checkbox.stateChanged.connect(self.on_mute)
            self.mute_checkbox.setObjectName("mute_checkbox")
            self.hlayout3.addWidget(self.mute_checkbox)
        self.action_widget = None
        self.automation_plugin_name = "None"
        self.port_num = None
        self.ccs_in_use_combobox = None
        self.suppress_osc = False
        self.automation_combobox = None

    def menu_button_pressed(self):
        if not self.menu_created:
            self.create_menu()

        self.suppress_ccs_in_use = True
        plugins = constants.DAW_PROJECT.get_track_plugins(self.track_number)
        routing_graph = constants.DAW_PROJECT.get_routing_graph()
        routes = routing_graph.graph.get(self.track_number, {})
        route_types = {0: "Normal", 1: "Sidechain"}
        tracks = constants.DAW_PROJECT.get_tracks()
        if plugins:
            names = [
                PLUGIN_UIDS_REVERSE[plugins.plugins[i].plugin_index]
                for i in range(10)
            ]
            for i in range(10, 26):
                if i >= len(plugins.plugins):
                    names.append("None")
                    continue
                plugin_index = plugins.plugins[i].plugin_index
                if plugin_index:
                    name = PLUGIN_UIDS_REVERSE[plugin_index]
                    idx = i - 10
                    if idx in routes:
                        route = routes[idx]
                        entry = "{}: {} -> {}".format(
                            name,
                            route_types[route.conn_type],
                            tracks.tracks[route.output].name,
                        )
                    else:
                        entry = "None"
                    names.append(entry)
                else:
                    names.append("None")
        else:
            names = ["None" for x in range(14)]
        index = self.automation_combobox.currentIndex()
        self.automation_combobox.clear()
        self.automation_combobox.addItems(names)
        self.automation_combobox.setCurrentIndex(index)
        if names[index] == "None":
            self.control_combobox.clear()
        self.suppress_ccs_in_use = False

        self.update_in_use_combobox()

    def open_plugins(self):
        shared.PLUGIN_RACK.track_combobox.setCurrentIndex(self.track_number)
        shared.MAIN_WINDOW.main_tabwidget.setCurrentIndex(shared.TAB_PLUGIN_RACK)
        self.button_menu.close()

    def create_menu(self):
        if self.action_widget:
            self.button_menu.removeAction(self.action_widget)
        self.menu_created = True
        self.menu_widget = QWidget()
        self.menu_hlayout = QHBoxLayout(self.menu_widget)
        self.menu_gridlayout = QGridLayout()
        self.menu_hlayout.addLayout(self.menu_gridlayout)
        self.action_widget = QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)

        self.plugins_button = QPushButton(_("Show Plugins"))
        self.menu_gridlayout.addWidget(self.plugins_button, 0, 21)
        self.plugins_button.pressed.connect(self.open_plugins)

        self.menu_gridlayout.addWidget(QLabel(_("Automation")), 3, 21)
        self.automation_combobox = QComboBox()
        self.automation_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Plugin:")), 5, 20)
        self.menu_gridlayout.addWidget(self.automation_combobox, 5, 21)
        self.automation_combobox.currentIndexChanged.connect(
            self.automation_callback)

        self.control_combobox = QComboBox()
        self.control_combobox.setMaxVisibleItems(30)
        self.control_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Control:")), 9, 20)
        self.menu_gridlayout.addWidget(self.control_combobox, 9, 21)
        self.control_combobox.currentIndexChanged.connect(
            self.control_changed)
        self.ccs_in_use_combobox = QComboBox()
        self.ccs_in_use_combobox.setMinimumWidth(300)
        self.suppress_ccs_in_use = False
        self.ccs_in_use_combobox.currentIndexChanged.connect(
            self.ccs_in_use_combobox_changed)
        self.menu_gridlayout.addWidget(QLabel(_("In Use:")), 10, 20)
        self.menu_gridlayout.addWidget(self.ccs_in_use_combobox, 10, 21)

        self.color_hlayout = QHBoxLayout()
        self.menu_gridlayout.addWidget(QLabel(_("Color")), 28, 21)
        self.menu_gridlayout.addLayout(self.color_hlayout, 29, 21)

        self.color_button = QPushButton(_("Custom..."))
        self.color_button.clicked.connect(self.on_color_change)
        self.color_hlayout.addWidget(self.color_button)

        self.color_copy_button = QPushButton(_("Copy"))
        self.color_copy_button.pressed.connect(self.on_color_copy)
        self.color_hlayout.addWidget(self.color_copy_button)

        self.color_paste_button = QPushButton(_("Paste"))
        self.color_paste_button.pressed.connect(self.on_color_paste)
        self.color_hlayout.addWidget(self.color_paste_button)

    def pick_color(self, a_track_num):
        color = QColorDialog.getColor(
            QColor(
                shared.TRACK_COLORS.get_color(a_track_num),
            ),
            options=QColorDialog.ColorDialogOption.DontUseNativeDialog,
            parent=glbl_shared.MAIN_WINDOW.widget,
        )
        if color.isValid():
            shared.TRACK_COLORS.set_color(a_track_num, color.name())
            return True
        else:
            return False

    def on_color_change(self):
        if self.pick_color(self.track_number):
            constants.DAW_PROJECT.save_track_colors(shared.TRACK_COLORS)
            shared.SEQUENCER.open_sequence()

    def on_color_copy(self):
        global TRACK_COLOR_CLIPBOARD
        TRACK_COLOR_CLIPBOARD = shared.TRACK_COLORS.get_color(
            self.track_number,
        )

    def on_color_paste(self):
        if not TRACK_COLOR_CLIPBOARD:
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW,
                _("Error"),
                _("Nothing copied to clipboard"),
            )
        else:
            shared.TRACK_COLORS.set_color(
                self.track_number,
                TRACK_COLOR_CLIPBOARD,
            )
            constants.DAW_PROJECT.save_track_colors(shared.TRACK_COLORS)
            shared.SEQUENCER.open_sequence()

    def refresh(self):
        self.track_name_lineedit.setText(
            shared.TRACK_NAMES[self.track_number]
        )
        if self.menu_created:
            self.create_menu()

    def plugin_changed(self, a_val=None):
        self.control_combobox.clear()
        if self.automation_plugin_name != "None":
            self.control_combobox.addItems(
                CC_NAMES[self.automation_plugin_name])
        shared.TRACK_PANEL.update_plugin_track_map()

    def control_changed(self, a_val=None):
        self.set_cc_num()
        self.ccs_in_use_combobox.setCurrentIndex(0)
        if not glbl_shared.IS_PLAYING:
            shared.SEQUENCER.open_sequence()

    def set_cc_num(self, a_val=None):
        f_port_name = str(self.control_combobox.currentText())
        if f_port_name == "":
            self.port_num = None
        else:
            self.port_num = CONTROLLER_PORT_NAME_DICT[
                self.automation_plugin_name][f_port_name].port
        shared.TRACK_PANEL.update_automation()

    def ccs_in_use_combobox_changed(self, a_val=None):
        if not self.suppress_ccs_in_use:
            f_str = str(self.ccs_in_use_combobox.currentText())
            if f_str:
                self.control_combobox.setCurrentIndex(
                    self.control_combobox.findText(f_str),
                )

    def update_in_use_combobox(self):
        if self.ccs_in_use_combobox is not None:
            self.ccs_in_use_combobox.clear()
            if self.automation_uid is not None:
                f_list = shared.ATM_SEQUENCE.get_ports(self.automation_uid)
                self.ccs_in_use_combobox.addItems(
                    [""] +
                    [
                        CONTROLLER_PORT_NUM_DICT[
                            self.automation_plugin_name
                        ][x].name
                        for x in f_list
                    ],
                )

    def on_solo(self, value):
        if not self.suppress_osc:
            constants.DAW_PROJECT.ipc().set_solo(
                self.track_number,
                self.solo_checkbox.isChecked(),
            )
            constants.DAW_PROJECT.save_tracks(
                shared.TRACK_PANEL.get_tracks(),
            )
            constants.DAW_PROJECT.commit(
                _("Set solo for track {} to {}").format(
                    self.track_number,
                    self.solo_checkbox.isChecked()
                )
            )

    def on_mute(self, value):
        if not self.suppress_osc:
            constants.DAW_PROJECT.ipc().set_mute(
                self.track_number, self.mute_checkbox.isChecked())
            constants.DAW_PROJECT.save_tracks(shared.TRACK_PANEL.get_tracks())
            constants.DAW_PROJECT.commit(
                _("Set mute for track {} to {}").format(
                    self.track_number,
                    self.mute_checkbox.isChecked()
                )
            )

    def on_name_changed(self):
        f_name = util.remove_bad_chars(
            self.track_name_lineedit.text()
        )

        self.track_name_lineedit.setText(f_name)
        global_update_track_comboboxes(self.track_number, f_name)
        f_tracks = constants.DAW_PROJECT.get_tracks()
        f_tracks.tracks[self.track_number].name = f_name
        constants.DAW_PROJECT.save_tracks(f_tracks)
        constants.DAW_PROJECT.commit(
            _("Set name for track {} to {}").format(self.track_number,
            self.track_name_lineedit.text()))

    def context_menu_event(self, a_event=None):
        pass

    def automation_callback(self, a_val=None):
        if self.suppress_ccs_in_use:
            return
        plugins = constants.DAW_PROJECT.get_track_plugins(self.track_number)
        index = self.automation_combobox.currentIndex()
        plugin = plugins.plugins[index]
        self.automation_uid = int(plugin.plugin_uid)
        self.automation_plugin = int(plugin.plugin_index)
        self.automation_plugin_name = PLUGIN_UIDS_REVERSE[
            self.automation_plugin
        ]
        self.plugin_changed()
        if not glbl_shared.IS_PLAYING:
            shared.SEQUENCER.open_sequence()

    def save_callback(self):
        constants.DAW_PROJECT.check_output(self.track_number)
        self.plugin_changed()

    def name_callback(self):
        return str(self.track_name_lineedit.text())

    def open_track(self, a_track, a_notify_osc=False):
        if not a_notify_osc:
            self.suppress_osc = True
        if self.track_number != 0:
            self.track_name_lineedit.setText(a_track.name)
            self.solo_checkbox.setChecked(a_track.solo)
            self.mute_checkbox.setChecked(a_track.mute)
        self.suppress_osc = False

    def get_track(self):
        return track(
            self.track_number, self.solo_checkbox.isChecked(),
            self.mute_checkbox.isChecked(),
            self.track_number, self.track_name_lineedit.text())

class TrackPanel:
    """ The widget that sits next to the sequencer QGraphicsView and
        contains the individual tracks
    """
    def __init__(self):
        self.tracks = {}
        self.plugin_uid_map = {}
        self.tracks_widget = QWidget()
        self.tracks_widget.setObjectName("track_panel")
        self.tracks_widget.setContentsMargins(0, 0, 0, 0)
        self.tracks_layout = QVBoxLayout(self.tracks_widget)
        self.tracks_layout.addItem(
            QSpacerItem(
                0,
                _shared.SEQUENCE_EDITOR_HEADER_HEIGHT + 2.0,
                vPolicy=QSizePolicy.Policy.MinimumExpanding,
            ),
        )
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(_shared.SEQUENCE_EDITOR_TRACK_COUNT):
            f_track = SeqTrack(i, shared.TRACK_NAMES[i])
            self.tracks[i] = f_track
            self.tracks_layout.addWidget(f_track.group_box)
        self.automation_dict = {
            x:(None, None) for x in range(
                _shared.SEQUENCE_EDITOR_TRACK_COUNT)
            }
        self.set_track_height()

    def set_tooltips(self, a_on):
        if a_on:
            self.tracks_widget.setToolTip(sg_strings.track_panel)
        else:
            self.tracks_widget.setToolTip("")

    def set_track_height(self):
        self.tracks_widget.setUpdatesEnabled(False)
        self.tracks_widget.setFixedSize(
            QtCore.QSize(
                _shared.SEQUENCE_TRACK_WIDTH,
                (
                    shared.SEQUENCE_EDITOR_TRACK_HEIGHT
                    *
                    _shared.SEQUENCE_EDITOR_TRACK_COUNT
                ) + _shared.SEQUENCE_EDITOR_HEADER_HEIGHT
            ),
        )
        for f_track in self.tracks.values():
            f_track.group_box.setFixedHeight(shared.SEQUENCE_EDITOR_TRACK_HEIGHT)
        self.tracks_widget.setUpdatesEnabled(True)

    def get_track_names(self):
        return [
            self.tracks[k].track_name_lineedit.text()
            for k in sorted(self.tracks)]

    def get_atm_params(self, a_track_num):
        f_track = self.tracks[int(a_track_num)]
        return (
            f_track.automation_uid, f_track.automation_plugin)

    def update_automation(self):
        self.automation_dict = {
            x:(self.tracks[x].port_num, self.tracks[x].automation_uid)
            for x in self.tracks}

    def update_plugin_track_map(self):
        self.plugin_uid_map = {}
        for x in self.tracks:
            plugins = constants.DAW_PROJECT.get_track_plugins(x)
            if plugins:
                for y in plugins.plugins:
                    self.plugin_uid_map[int(y.plugin_uid)] = int(x)

    def has_automation(self, a_track_num):
        return self.automation_dict[int(a_track_num)]

    def update_ccs_in_use(self):
        for v in self.tracks.values():
            v.update_in_use_combobox()

    def open_tracks(self):
        f_tracks = constants.DAW_PROJECT.get_tracks()
        shared.TRACK_NAMES = f_tracks.get_names()
        global_update_track_comboboxes()
        for key, f_track in f_tracks.tracks.items():
            self.tracks[key].open_track(f_track)
            self.tracks[key].refresh()
        self.update_plugin_track_map()

    def get_tracks(self):
        f_result = tracks()
        for k, v in self.tracks.items():
            f_result.add_track(k, v.get_track())
        return f_result

