from sglib.models.cc_mapping import CCMapping
from sglib.models.plugin_file import plugin_file
from sglib.models.stargate import folder_plugins
from sglib.lib.translate import _
from sglib.log import LOG
from sgui import shared as glbl_shared
from sgui.sgqt import *
import os

from sglib.lib import util
from jinja2 import Template

DEFAULT_STYLE = """\
QWidget {
    background-color: #222222;
    color: #cccccc;
}

QLabel#screw {
    background-color: none;
    border: none;
    border-image: url({{ PLUGIN_ASSETS_DIR }}/screw.svg) 0 0 0 0 stretch stretch;
}

QComboBox::drop-down
{
    border-bottom-right-radius: 3px;
    border-left-color: #222222;
    border-left-style: solid; /* just a single line */
    border-left-width: 0px;
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    color: #cccccc;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
}

QComboBox::down-arrow
{
    image: url({{ PLUGIN_ASSETS_DIR }}/drop-down.svg);
}

QScrollBar:horizontal
{
    background: #aaaaaa;
    border: 1px solid #222222;
    height: 15px;
    margin: 0px 16px 0 16px;
}

QScrollBar::add-line:horizontal,
QScrollBar::handle:horizontal,
QScrollBar::sub-line:horizontal
{
    background: #aaaaaa;
}

QScrollBar::add-line:vertical,
QScrollBar::handle:vertical,
QScrollBar::sub-line:vertical
{
    background: #aaaaaa;
}

QScrollBar::add-line:horizontal,
QScrollBar::add-line:vertical,
QScrollBar::handle:horizontal,
QScrollBar::handle:vertical,
QScrollBar::sub-line:horizontal,
QScrollBar::sub-line:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: right;
    width: 14px;
}

QScrollBar::sub-line:horizontal
{
    border: 1px solid #222222;
    subcontrol-origin: margin;
    subcontrol-position: left;
    width: 14px;
}

QScrollBar[hide="true"]::down-arrow:vertical,
QScrollBar[hide="true"]::left-arrow:horizontal,
QScrollBar[hide="true"]::right-arrow:horizontal,
QScrollBar[hide="true"]::up-arrow:vertical
{
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical
{
    background: #222222;
    border: 1px solid #222222;
}

QScrollBar:vertical
{
    background: #666666;
    border: 1px solid #222222;
    margin: 16px 0 16px 0;
    width: 15px;
}

QScrollBar::handle:vertical
{
    min-height: 20px;
}

QScrollBar::add-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: bottom;
}

QScrollBar::sub-line:vertical
{
    border: 1px solid #222222;
    height: 14px;
    subcontrol-origin: margin;
    subcontrol-position: top;
}

QAbstractItemView
{
    background-color: #222222;
    border: 2px solid #aaaaaa;
    selection-background-color: #cccccc;
}

QWidget::item:hover,
QWidget::item:selected,
QMenu::item:hover,
QMenu::item:selected
{
    background-color: #cccccc;
    color: #222222;
}

QWidget::item,
QMenu::item
{
    background-color: #222222;
    color: #cccccc;
}

QMenu::separator
{
    height: 2px;
    background-color: #cccccc;
}

QMenu,
QMenu::item,
QPushButton,
QWidget#plugin_window {
    background: #222222;
    color: #cccccc;
}

QToolTip {
    background: #222222;
    color: #cccccc;
}
"""

STYLESHEET_CACHE = {}

def render_stylesheet(
    stylesheet: str,
    **kwargs
) -> str:
    if stylesheet not in STYLESHEET_CACHE:
        STYLESHEET_CACHE[stylesheet] = DEFAULT_STYLE + stylesheet
    _stylesheet = STYLESHEET_CACHE[stylesheet]
    t = Template(_stylesheet)
    return t.render(
        PLUGIN_ASSETS_DIR=util.pi_path(util.PLUGIN_ASSETS_DIR),
        **kwargs,
    )

class AbstractPluginUI:
    def __init__(
        self,
        a_val_callback,
        a_project,
        a_plugin_uid,
        a_configure_callback,
        a_folder,
        a_midi_learn_callback,
        a_cc_map_callback,
        a_is_mixer=False,
        stylesheet="",
    ):
        self.is_mixer = a_is_mixer
        self.plugin_uid = int(a_plugin_uid)
        self.folder = str(a_folder)
        self.sg_project = a_project
        self.val_callback = a_val_callback
        self.configure_callback = a_configure_callback
        self.midi_learn_callback = a_midi_learn_callback
        self.cc_map_callback = a_cc_map_callback
        self.widget = QWidget()
        self.widget.closeEvent = self.widget_close_event
        self.widget.setObjectName("plugin_window")
        if stylesheet:
            self.widget.setStyleSheet(
                render_stylesheet(stylesheet),
            )
        self.widget.keyPressEvent = self.widget_keyPressEvent

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.widget.setLayout(self.layout)
        self.port_dict = {}
        self.effects = []
        self.configure_dict = {}
        self.cc_map = {}
        self.save_file_on_exit = True
        self.is_quitting = False
        self._plugin_name = None
        self.has_updated_controls = False

    @staticmethod
    def get_audio_pool_uids(a_plugin_uid):
        return set()

    def widget_keyPressEvent(self, a_event):
        QWidget.keyPressEvent(self.widget, a_event)
        if a_event.key() == QtCore.Qt.Key.Key_Space:
            glbl_shared.TRANSPORT.on_spacebar()

    def set_midi_learn(self, a_port_map):
        self.port_map = a_port_map
        self.reverse_port_map = {
            int(v):k
            for k, v in self.port_map.items()
        }
        for f_port in (int(x) for x in a_port_map.values()):
            self.port_dict[f_port].set_midi_learn(
                self.midi_learn, self.get_cc_map)

    def midi_learn(
        self,
        a_ctrl,
        a_cc_num=None,
        a_low=None,
        a_high=None,
    ):
        if a_cc_num is not None:
            if a_low is not None:
                self.cc_map[a_cc_num].ports[a_ctrl.port_num] = (a_low, a_high)
                self.set_cc_map(a_cc_num)
                return
            if (
                a_cc_num in self.cc_map
                and
                self.cc_map[a_cc_num].has_port(a_ctrl.port_num)
            ):
                if self.cc_map[a_cc_num].remove_port(a_ctrl.port_num):
                    self.set_cc_map(a_cc_num)
                    if not self.cc_map[a_cc_num].ports:
                        self.cc_map.pop(a_cc_num)
            else:
                self.update_cc_map(a_cc_num, a_ctrl)
        else:
            self.midi_learn_callback(self, a_ctrl)

    def update_cc_map(self, a_cc_num, a_ctrl):
        a_cc_num = int(a_cc_num)
        if a_cc_num not in self.cc_map:
            self.cc_map[a_cc_num] = CCMapping(a_cc_num)
        f_result = self.cc_map[a_cc_num].set_port(a_ctrl.port_num)
        if f_result:
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _(
                    "CCs can only be assigned to 5 controls at a time, "
                    "CC {} is already assigned to {}"
                ).format(
                    a_cc_num,
                    [self.reverse_port_map[x] for x in f_result],
                )
            )
        else:
            self.set_cc_map(a_cc_num)

    def get_cc_map(self):
        return self.cc_map

    def set_cc_map(self, a_cc_num):
        f_str = str(self.cc_map[a_cc_num])
        self.cc_map_callback(self.plugin_uid, f_str[2:])

    def get_plugin_name(self):
        return self._plugin_name

    def set_default_size(self):
        """ Override this for plugins that can't properly resize
            automatically and can be resized
        """
        pass

    def delete_plugin_file(self):
        self.save_file_on_exit = False

    def open_plugin_file(self):
        if self.folder is not None:
            f_file_path = os.path.join(
                *(str(x) for x in (self.folder, self.plugin_uid)))
            if os.path.isfile(f_file_path):
                f_file = plugin_file(f_file_path)
                for k, v in f_file.port_dict.items():
                    self.set_control_val(int(k), v)
                for k, v in f_file.configure_dict.items():
                    self.set_configure(k, v)
                self.cc_map = f_file.cc_map
            else:
                LOG.warning(
                    "AbstractPluginUI.open_plugin_file():"
                    " '{}' did not exist, not loading.".format(f_file_path)
                )
                self.has_updated_controls = True

    def widget_show(self):
        """ Override to do something when the widget is shown """
        pass

    def save_plugin_file(self):
        if self.folder is not None:
            f_file = plugin_file.from_dict(
                self.port_dict,
                self.configure_dict,
                self.cc_map,
            )
            self.sg_project.save_file(
                folder_plugins,
                self.plugin_uid,
                str(f_file),
            )
#            self.sg_project.commit(
#                _("Update controls for {}").format(self.track_name))
#            self.sg_project.flush_history()

    def widget_close_event(self, a_event):
        self.widget_close()
        QWidget.closeEvent(self.widget, a_event)

    def widget_close(self):
        """ Override to do something when the widget is hidden """
        if (
            self.has_updated_controls
            and
            self.save_file_on_exit
        ):
            self.save_plugin_file()

    def plugin_rel_callback(self, a_port, a_val):
        """ This can optionally be implemented, otherwise it's
            just ignored
        """
        pass

    def plugin_val_callback(self, a_port, a_val):
        self.val_callback(self.plugin_uid, a_port, a_val)
        self.has_updated_controls = True

    def set_control_val(self, a_port, a_val):
        f_port = int(a_port)
        if f_port in self.port_dict:
            self.port_dict[int(a_port)].set_value(a_val)
        else:
            LOG.warning(
                "AbstractPluginUI.set_control_val():  "
                "Did not have port {}".format(f_port)
            )

    def set_cc_val(self, a_cc, a_val):
        a_cc = int(a_cc)
        if a_cc in self.cc_map:
            a_val = float(a_val) * 0.007874016 # / 127.0
            for f_port, f_tuple in self.cc_map[a_cc].ports.items():
                f_low, f_high = f_tuple
                f_frac = (a_val * (f_high - f_low)) + f_low
                f_ctrl = self.port_dict[f_port]
                f_min = float(f_ctrl.control.minimum())
                f_max = float(f_ctrl.control.maximum())
                f_val = int(f_frac * (f_max - f_min) + f_min)
                f_ctrl.set_value(f_val, True)

    def configure_plugin(self, a_key, a_message):
        """ Override this function to allow str|str key/value pair
            messages to be sent to the back-end
        """
        self.has_updated_controls = True

    def set_configure(self, a_key, a_message):
        """ Override this function to configure the
            plugin from the state file
        """
        pass

    def reconfigure_plugin(self, a_dict):
        """ Override this to re-configure a plugin from scratch with the
            values in a_dict
        """
        self.has_updated_controls = True

    def ui_message(self, a_name, a_value):
        """ Override to display ephemeral data such as
            meters/scopes/spectra using key value pairs
        """
        LOG.warning("Unknown ui_message: {} : {}".format(a_name, a_value))


