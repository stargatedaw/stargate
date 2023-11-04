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
from sglib.models.theme import get_asset_path
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
        shared.ALL_PEAK_METERS[a_track_num].append(self.peak_meter)
        self.main_hlayout.addWidget(self.peak_meter.widget)
        self.group_box.setLayout(self.main_hlayout)
        self.track_name_lineedit = QLineEdit()
        self.track_name_lineedit.returnPressed.connect(
            self.track_name_lineedit.clearFocus
        )
        self.track_name_lineedit.setFocusPolicy(
            QtCore.Qt.FocusPolicy.ClickFocus,
        )
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

        self.toolbar = QToolBar()
        #self.toolbar.setObjectName('track_panel')
        self.toolbar.setIconSize(QtCore.QSize(21, 21))
        self.hlayout3.addWidget(self.toolbar)
        self.hlayout3.addItem(
            QSpacerItem(1, 1, QSizePolicy.Policy.Expanding),
        )

        self.menu_button = QToolButton()
        icon = QIcon(get_asset_path('menu.svg'))
        self.menu_button.setIcon(icon)
        self.button_menu = QMenu()
        self.menu_button.setMenu(self.button_menu)
        self.menu_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        self.toolbar.addWidget(self.menu_button)
        self.button_menu.aboutToShow.connect(self.menu_button_pressed)
        self.menu_created = False

        self.plugins_button = QToolButton()
        self.plugins_button.setToolTip('Show the plugin rack for this track')
        icon = QIcon(get_asset_path('fx-off.svg'))
        self.plugins_button.setIcon(icon)
        self.plugins_button.setToolTip('Open this track in the plugin rack')
        self.toolbar.addWidget(self.plugins_button)
        self.plugins_button.pressed.connect(self.open_plugins)

        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('solo-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('solo-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.solo_checkbox = QAction(icon, '', self.toolbar)
        self.solo_checkbox.setToolTip('Solo this track')
        self.solo_checkbox.setCheckable(True)
        if self.track_number != 0:
            self.toolbar.addAction(self.solo_checkbox)
        self.solo_checkbox.triggered.connect(self.on_solo)

        icon = QIcon()
        icon.addPixmap(
            QPixmap(
                get_asset_path('mute-on.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.On,
        )
        icon.addPixmap(
            QPixmap(
                get_asset_path('mute-off.svg'),
            ),
            QIcon.Mode.Normal,
            QIcon.State.Off,
        )
        self.mute_checkbox = QAction(icon, '', self.toolbar)
        self.mute_checkbox.setToolTip('Mute this track')
        self.mute_checkbox.setCheckable(True)
        if self.track_number != 0:
            self.toolbar.addAction(self.mute_checkbox)
        self.mute_checkbox.triggered.connect(self.on_mute)

        self.action_widget = None
        self.automation_plugin_name = "None"
        self.port_num = None
        self.ccs_in_use_combobox = None
        self.suppress_osc = False
        self.automation_combobox = None

    def set_controls_enabled(self, enabled: bool):
        self.menu_button.setEnabled(enabled)
        self.track_name_lineedit.setEnabled(enabled)

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
        shared.MAIN_WINDOW.setCurrentIndex(shared.TAB_PLUGIN_RACK)
        self.button_menu.close()
        self.plugins_button._clear_hint_box(_all=True)

    def create_menu(self):
        if self.action_widget:
            self.button_menu.removeAction(self.action_widget)
        self.menu_created = True
        self.menu_widget = QWidget()
        self.menu_vlayout = QVBoxLayout(self.menu_widget)
        self.menu_auto_groupbox = SGGroupBox('Automation')
        self.menu_vlayout.addWidget(self.menu_auto_groupbox)
        self.menu_gridlayout = QGridLayout(self.menu_auto_groupbox.widget)
        self.action_widget = QWidgetAction(self.button_menu)
        self.action_widget.setDefaultWidget(self.menu_widget)
        self.button_menu.addAction(self.action_widget)

        self.automation_combobox = QComboBox()
        self.automation_combobox.setMinimumWidth(240)
        self.menu_gridlayout.addWidget(QLabel(_("Plugin:")), 5, 20)
        self.menu_gridlayout.addWidget(self.automation_combobox, 5, 21)
        self.automation_combobox.currentIndexChanged.connect(
            self.automation_callback,
        )
        self.automation_combobox.setToolTip(
            'Select the plugin for automation edit mode.  The first 10 '
            'options are from the plugin rack, the last 16 are the mixer '
            'channels for each send'
        )

        self.control_combobox = QComboBox()
        self.control_combobox.setToolTip(
            'Select the plugin control for automation edit mode'
        )
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
            self.ccs_in_use_combobox_changed,
        )
        self.ccs_in_use_combobox.setToolTip(
            'Select a plugin control already in use from the selected '
            'plugin.  Use this for easy access to controls that have '
            'already been edited'
        )
        self.menu_gridlayout.addWidget(QLabel(_("In Use:")), 10, 20)
        self.menu_gridlayout.addWidget(self.ccs_in_use_combobox, 10, 21)

        self.menu_color_groupbox = SGGroupBox('Color')
        self.menu_vlayout.addWidget(self.menu_color_groupbox)
        self.color_hlayout = QHBoxLayout(self.menu_color_groupbox.widget)

        self.color_button = QPushButton(_("Custom..."))
        self.color_button.setToolTip(
            'Select a custom color for sequencer items'
        )
        self.color_button.clicked.connect(self.on_color_change)
        self.color_hlayout.addWidget(self.color_button)

        self.color_copy_button = QPushButton(_("Copy"))
        self.color_copy_button.pressed.connect(self.on_color_copy)
        self.color_copy_button.setToolTip(
            'Copy this track\'s item color, to paste to another track'
        )
        self.color_hlayout.addWidget(self.color_copy_button)

        self.color_paste_button = QPushButton(_("Paste"))
        self.color_paste_button.setToolTip(
            'Paste another track\'s color to this track.\n'
            'You must press the copy button on another track first'
        )
        self.color_paste_button.pressed.connect(self.on_color_paste)
        self.color_hlayout.addWidget(self.color_paste_button)

    def pick_color(self, a_track_num):
        color = QColorDialog.getColor(
            QColor(
                shared.TRACK_COLORS.get_color(a_track_num),
            ),
            options=QColorDialog.ColorDialogOption.DontUseNativeDialog,
            parent=glbl_shared.MAIN_WINDOW,
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
                CC_NAMES[self.automation_plugin_name],
            )
        shared.TRACK_PANEL.update_plugin_track_map()
        self.update_in_use_combobox()

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
            shared.SEQ_WIDGET.update_solo_all()
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
            shared.SEQ_WIDGET.update_mute_all()
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
        if len(f_name) < 2:
            QMessageBox.warning(
                glbl_shared.MAIN_WINDOW,
                _("Error"),
                _("Name must be at least 2 characters"),
            )
            tracks = constants.DAW_PROJECT.get_tracks()
            self.track_name_lineedit.setText(
                tracks.tracks[self.track_number].name,
            )
            return

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
                int(_shared.SEQUENCE_EDITOR_HEADER_HEIGHT),
                vPolicy=QSizePolicy.Policy.MinimumExpanding,
            ),
        )
        self.tracks_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(_shared.SEQUENCE_EDITOR_TRACK_COUNT):
            f_track = SeqTrack(i, 'track')
            self.tracks[i] = f_track
            self.tracks_layout.addWidget(f_track.group_box)
        self.automation_dict = {
            x:(None, None) for x in range(
                _shared.SEQUENCE_EDITOR_TRACK_COUNT)
            }
        self.set_track_height()

    def set_track_names(self):
        for i in range(_shared.SEQUENCE_EDITOR_TRACK_COUNT):
            self.tracks[i].track_name_lineedit.setText(shared.TRACK_NAMES[i])

    def set_controls_enabled(self, enabled: bool):
        for track in self.tracks.values():
            track.set_controls_enabled(enabled)

    def set_track_height(self):
        self.tracks_widget.setUpdatesEnabled(False)
        self.tracks_widget.setFixedSize(
            QtCore.QSize(
                int(_shared.SEQUENCE_TRACK_WIDTH),
                int(
                    shared.SEQUENCE_EDITOR_TRACK_HEIGHT
                    *
                    _shared.SEQUENCE_EDITOR_TRACK_COUNT
                ) + int(_shared.SEQUENCE_EDITOR_HEADER_HEIGHT)
            ),
        )
        for f_track in self.tracks.values():
            f_track.group_box.setFixedHeight(
                shared.SEQUENCE_EDITOR_TRACK_HEIGHT,
            )
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
        shared.SEQ_WIDGET.update_mute_all()
        shared.SEQ_WIDGET.update_solo_all()

    def get_tracks(self):
        f_result = tracks()
        for k, v in self.tracks.items():
            f_result.add_track(k, v.get_track())
        return f_result

