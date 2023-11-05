from sglib.lib import util
from sglib.lib.translate import _
from sglib.constants import PRESET_DIR
from sglib.log import LOG
from sgui.sgqt import *
import os
import shutil

PRESET_FILE_DIALOG_STRING = 'Stargate Presets (*.sgp)'
PLUGIN_SETTINGS_CLIPBOARD = {}
PLUGIN_CONFIGURE_CLIPBOARD = None

class preset_manager_widget:
    def __init__(
        self,
        a_plugin_name,
        a_configure_dict=None,
        a_reconfigure_callback=None,
        horizontal=True,
    ):
        self.suppress_change = False
        self.plugin_name = str(a_plugin_name)
        self.configure_dict = a_configure_dict
        self.reconfigure_callback = a_reconfigure_callback
        self.factory_preset_path = os.path.join(
            util.PRESETS_DIR,
            f"{a_plugin_name}.sgp",
        )
        self.bank_dir = os.path.join(PRESET_DIR, a_plugin_name)
        if not os.path.isdir(self.bank_dir):
            os.makedirs(self.bank_dir)
        self.user_factory_presets = os.path.join(self.bank_dir, "factory.sgp")
        self.bank_file = os.path.join(
            PRESET_DIR,
            f"{a_plugin_name}-last-bank.txt",
        )
        self.group_box = QWidget()
        self.group_box.setObjectName("plugin_groupbox")
        self.bank_label = QLabel(_("Bank"))
        self.bank_combobox = QComboBox()
        self.bank_combobox.setToolTip(
            'Presets are divided into "banks".  This selects the preset '
            'bank to browse'
        )
        self.bank_combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.bank_combobox.setMinimumWidth(210)
        self.presets_label = QLabel(_("Presets"))
        self.program_combobox = QComboBox()
        self.program_combobox.setToolTip('Select the preset to use')
        self.program_combobox.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.program_combobox.setMinimumWidth(300)
        self.more_button = QPushButton(_("Menu"))

        self.more_menu = QMenu(self.more_button)

        save_preset_action = QAction(_("Save Preset"), self.more_menu)
        self.more_menu.addAction(save_preset_action)
        save_preset_action.setToolTip(
            'Save the current plugin settings to the current preset'
        )
        save_preset_action.triggered.connect(self.save_preset)

        save_preset_as_action = QAction(
            _("Save Preset As..."),
            self.more_menu,
        )
        self.more_menu.addAction(save_preset_as_action)
        save_preset_as_action.setToolTip(
            'Save the current plugin settings to a new preset'
        )
        save_preset_as_action.triggered.connect(self.save_preset_as)

        self.more_menu.addSeparator()

        f_new_bank_action = QAction(_("New Bank..."), self.more_menu)
        f_new_bank_action.setToolTip(
            'Create a new bank of presets for this plugin'
        )
        self.more_menu.addAction(f_new_bank_action)
        f_new_bank_action.triggered.connect(self.on_new_bank)

        f_reload_bank_action = QAction(_("Reload Bank..."), self.more_menu)
        f_reload_bank_action.setToolTip(
            'Reload the current bank to get any preset changes created in '
            'other instances of this plugin'
        )
        self.more_menu.addAction(f_reload_bank_action)
        f_reload_bank_action.triggered.connect(self.reload_default_presets)

        f_save_as_action = QAction(_("Save Bank As..."), self.more_menu)
        f_save_as_action.setToolTip(
            'Save this preset bank as a new preset bank with a different name'
        )
        self.more_menu.addAction(f_save_as_action)
        f_save_as_action.triggered.connect(self.on_save_as)

        f_open_action = QAction(_("Open Bank..."), self.more_menu)
        f_open_action.setToolTip('Open a different preset bank')
        self.more_menu.addAction(f_open_action)
        f_open_action.triggered.connect(self.on_open_bank)

        f_restore_action = QAction(
            _("Restore Factory Bank..."),
            self.more_menu,
        )
        f_restore_action.setToolTip(
            "Restore this bank to it's original state (assuming it was a "
            "factory provided bank)"
        )
        self.more_menu.addAction(f_restore_action)
        f_restore_action.triggered.connect(self.on_restore_bank)

        self.more_menu.addSeparator()

        f_delete_action = QAction(_("Delete Preset"), self.more_menu)
        f_delete_action.setToolTip(
            'Delete the current preset from the current preset bank'
        )
        self.more_menu.addAction(f_delete_action)
        f_delete_action.triggered.connect(self.delete_preset)

        self.more_menu.addSeparator()

        f_copy_action = QAction(_("Copy Plugin Settings"), self.more_menu)
        f_copy_action.setToolTip(
            "Copy all controls from this plugin.  Use this to clone this "
            "instance of this plugin by using the 'Paste Plugin Settings' "
            "action on another instance of the same plugin"
        )
        self.more_menu.addAction(f_copy_action)
        f_copy_action.triggered.connect(self.on_copy)

        f_paste_action = QAction(_("Paste Plugin Settings"), self.more_menu)
        f_paste_action.setToolTip(
            "Replace all settings in this plugin with the settings previously "
            "copied from another instance of the same plugin using "
            "'Copy Plugin Settings'"
        )
        self.more_menu.addAction(f_paste_action)
        f_paste_action.triggered.connect(self.on_paste)

        self.more_menu.addSeparator()

        f_reset_default_action = QAction(
            _("Reset to Default Values"),
            self.more_menu,
        )
        f_reset_default_action.setToolTip(
            "Reset all controls to their default value.  This is the default "
            "plugin state when you open a new instance of the plugin"
        )
        self.more_menu.addAction(f_reset_default_action)
        f_reset_default_action.triggered.connect(self.reset_controls)

        self.more_button.setMenu(self.more_menu)
        self.presets_delimited = {}
        self.controls = {}
        self.suppress_bank_changes = False
        self.load_default_preset_path()
        self.load_banks()
        self.load_presets()
        self.program_combobox.currentIndexChanged.connect(self.program_changed)
        self.bank_combobox.currentIndexChanged.connect(self.bank_changed)

        if horizontal:
            self.layout = QHBoxLayout(self.group_box)
            self.layout.addWidget(self.bank_label)
            self.layout.addWidget(self.bank_combobox)
            self.layout.addWidget(self.presets_label)
            self.layout.setContentsMargins(3, 3, 3, 3)
            self.layout.addWidget(self.program_combobox)
            self.layout.addWidget(self.more_button)
        else:
            self.layout = QVBoxLayout(self.group_box)
            hlayout1 = QHBoxLayout()
            self.layout.addLayout(hlayout1)
            hlayout2 = QHBoxLayout()
            self.layout.addLayout(hlayout2)
            hlayout1.addWidget(self.bank_label)
            hlayout1.addWidget(self.bank_combobox)
            hlayout2.addWidget(self.presets_label)
            hlayout2.addWidget(self.program_combobox)
            hlayout1.addWidget(self.more_button)
            self.bank_label.setFixedWidth(45)
            self.presets_label.setFixedWidth(45)

    def delete_preset(self):
        f_name = self.program_combobox.currentText()
        if f_name:
            f_name = str(f_name)
        LOG.info(f_name)
        if f_name and f_name in self.presets_delimited:
            LOG.info("Found preset, deleting")
            self.presets_delimited.pop(f_name)
            self.program_combobox.clearEditText()
            self.commit_presets()

    def load_banks(self):
        if os.path.exists(self.factory_preset_path):
            if not os.path.isfile(self.user_factory_presets):
                shutil.copy(
                    self.factory_preset_path,
                    self.user_factory_presets,
                )
        elif not os.path.exists(self.user_factory_presets):
            LOG.info("No factory presets found, loading empty bank")
            util.write_file_text(self.user_factory_presets, self.plugin_name)
        self.bank_combobox.clear()
        self.bank_combobox.addItems(
            sorted(
                x.rsplit(".", 1)[0]
                for x in os.listdir(self.bank_dir)
                if x.endswith(".sgp")
            )
        )
        self.suppress_bank_changes = True
        self.bank_combobox.setCurrentIndex(
            self.bank_combobox.findText(self.bank_name),
        )
        self.suppress_bank_changes = False

    def bank_changed(self, a_val=None):
        if self.suppress_bank_changes:
            return
        self.preset_path = os.path.join(
            self.bank_dir,
            "{}.sgp".format(self.bank_combobox.currentText())
        )
        util.write_file_text(
            self.bank_file,
            self.preset_path,
        )
        self.load_presets()

    def load_default_preset_path(self):
        self.preset_path = self.user_factory_presets
        if os.path.isfile(self.bank_file):
            f_text = util.read_file_text(self.bank_file)
            if os.path.isfile(f_text):
                LOG.info("Setting self.preset_path to {}".format(f_text))
                self.preset_path = f_text
                self.bank_name = os.path.basename(f_text).rsplit(".", 1)[0]
                return
            else:
                LOG.info("{} does not exist".format(f_text))
        else:
            LOG.info("{} does not exist".format(self.bank_file))
        self.bank_name = "factory"

    def reload_default_presets(self):
        self.load_default_preset_path()
        self.load_presets()

    def on_copy(self):
        f_result = {}
        for k, v in self.controls.items():
            f_result[k] = v.get_value()
        PLUGIN_SETTINGS_CLIPBOARD[self.plugin_name] = f_result
        global PLUGIN_CONFIGURE_CLIPBOARD
        if self.configure_dict is None:
            PLUGIN_CONFIGURE_CLIPBOARD = None
        else:
            PLUGIN_CONFIGURE_CLIPBOARD = self.configure_dict.copy()

    def on_paste(self):
        if not self.plugin_name in PLUGIN_SETTINGS_CLIPBOARD:
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _("Nothing copied to clipboard for {}").format(
                    self.plugin_name
                ),
            )
            return
        f_dict = PLUGIN_SETTINGS_CLIPBOARD[self.plugin_name]
        for k, v in f_dict.items():
            self.controls[k].set_value(v, True)
        if PLUGIN_CONFIGURE_CLIPBOARD is not None:
            self.reconfigure_callback(PLUGIN_CONFIGURE_CLIPBOARD)

    def on_new_bank(self):
        self.on_save_as(True)

    def on_save_as(self, a_new=False):
        def ok_handler():
            f_name = util.remove_bad_chars(f_lineedit.text()).strip()
            if len(f_name.replace('.sgp', '')) < 4:
                QMessageBox.warning(
                    None,
                    _("Error"),
                    _("Names must contain at least 4 characters"),
                )
                return
            f_file = os.path.join(self.bank_dir, f_name)
            if not f_file.endswith(".sgp"):
                f_file += ".sgp"
            if os.path.exists(f_file):
                QMessageBox.warning(
                    None,
                    _("Error"),
                    _("This bank name already exists"),
                )
                return
            if a_new:
                util.write_file_text(
                    f_file, "\n".join([self.plugin_name]))
            else:
                shutil.copy(self.preset_path, f_file)
            self.preset_path = f_file
            util.write_file_text(self.bank_file, self.preset_path)
            self.load_banks()
            self.program_combobox.setCurrentIndex(
                self.program_combobox.findText(f_name),
            )
            f_dialog.close()

        f_dialog = QDialog(self.group_box)
        f_dialog.setWindowTitle(_("Save Bank"))
        vlayout = QVBoxLayout(f_dialog)
        f_groupbox_layout = QGridLayout()
        vlayout.addLayout(f_groupbox_layout)
        f_groupbox_layout.addWidget(QLabel(_("Name")), 0, 0)
        f_lineedit = QLineEdit()
        f_groupbox_layout.addWidget(f_lineedit, 0, 1)
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        f_sync_button = QPushButton(_("OK"))
        f_sync_button.pressed.connect(ok_handler)
        f_lineedit.returnPressed.connect(ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        ok_cancel_layout.addWidget(f_sync_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def on_open_bank(self):
        f_file, f_filter = QFileDialog.getOpenFileName(
            parent=self.group_box,
            caption=_('Open preset bank...'),
            directory=util.HOME,
            filter=PRESET_FILE_DIALOG_STRING,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not f_file is None and not str(f_file) == "":
            f_file = str(f_file)
            self.preset_path = f_file
            util.write_file_text(self.bank_file, self.preset_path)
            self.program_combobox.setCurrentIndex(0)
            self.load_presets()

    def on_restore_bank(self):
        shutil.copy(self.factory_preset_path, self.user_factory_presets)
        self.preset_path = self.user_factory_presets
        self.bank_name = "factory"
        self.load_banks()
        self.load_presets()

    def reset_controls(self):
        for v in self.controls.values():
            v.reset_default_value()
        if self.reconfigure_callback is not None:
            self.reconfigure_callback({})

    def load_presets(self):
        if os.path.isfile(self.preset_path):
            LOG.info("loading presets from file {}".format(self.preset_path))
            f_text = util.read_file_text(self.preset_path)
        elif os.path.isfile(self.user_factory_presets):
            LOG.info("loading factory presets")
            f_text = util.read_file_text(
                self.user_factory_presets,
            )
        else:
            LOG.error("Presets do not exist, not loading")
            return
        f_line_arr = f_text.split("\n")

        if f_line_arr[0].strip() != self.plugin_name:
            QMessageBox.warning(
                self.group_box,
                _("Error"),
                _(
                    "The selected preset bank is for {}, please select "
                    "one for {}"
                ).format(
                    f_line_arr[0],
                    self.plugin_name
                ),
            )
            if os.path.isfile(self.bank_file):
                os.remove(self.bank_file)
            return

        f_line_arr = f_line_arr[1:]
        self.presets_delimited = {}
        self.program_combobox.clear()
        self.program_combobox.addItem("")

        for f_line in f_line_arr:
            f_arr = f_line.split("|")
            f_name = f_arr[0]
            if f_name and f_name != "empty":  # legacy bank support
                self.presets_delimited[f_name] = f_arr[1:]
                self.program_combobox.addItem(f_name)

    def save_preset_as(self):
        def ok_handler():
            preset_name = str(f_lineedit.text())
            preset_name = util.remove_bad_chars(preset_name).strip()
            if len(preset_name) < 5:
                QMessageBox.warning(
                    self.group_box,
                    _("Error"),
                    _("Preset names must be at least 5 characters"),
                )
                return
            LOG.info(f"Saving preset '{preset_name}'")
            f_result_values = []
            for k in sorted(self.controls.keys()):
                f_control = self.controls[k]
                f_result_values.append(
                    "{}:{}".format(f_control.port_num, f_control.get_value())
                )
            if self.configure_dict is not None:
                for k in self.configure_dict.keys():
                    v = self.configure_dict[k]
                    f_result_values.append(
                        "c:{}:{}".format(k, v.replace("|", ":")))

            self.presets_delimited[preset_name] = f_result_values
            self.commit_presets()
            self.suppress_change = True
            self.program_combobox.setCurrentIndex(
                self.program_combobox.findText(preset_name),
            )
            self.suppress_change = False
            f_dialog.close()

        f_dialog = QDialog(self.group_box)
        f_dialog.setWindowTitle(_("Save Preset"))
        vlayout = QVBoxLayout(f_dialog)
        f_groupbox_layout = QGridLayout()
        vlayout.addLayout(f_groupbox_layout)
        f_groupbox_layout.addWidget(QLabel(_("Name")), 0, 0)
        f_lineedit = QLineEdit()
        f_groupbox_layout.addWidget(f_lineedit, 0, 1, 1, 2)
        vlayout.addItem(
            QSpacerItem(
                1,
                1,
                QSizePolicy.Policy.Minimum,
                QSizePolicy.Policy.Expanding,
            ),
        )
        f_sync_button = QPushButton(_("OK"))
        f_sync_button.pressed.connect(ok_handler)
        f_lineedit.returnPressed.connect(ok_handler)
        f_cancel_button = QPushButton(_("Cancel"))
        f_cancel_button.pressed.connect(f_dialog.close)
        ok_cancel_layout = QHBoxLayout()
        vlayout.addLayout(ok_cancel_layout)
        ok_cancel_layout.addWidget(f_sync_button)
        ok_cancel_layout.addWidget(f_cancel_button)
        f_dialog.exec()

    def save_preset(self):
        LOG.info("saving preset")
        f_index = self.program_combobox.currentIndex()
        f_preset_name = str(self.program_combobox.currentText())
        if not f_index and not f_preset_name:
            self.save_preset_as()
            return
        f_result_values = []
        for k in sorted(self.controls.keys()):
            f_control = self.controls[k]
            f_result_values.append(
                f"{f_control.port_num}:{f_control.get_value()}",
            )
        if self.configure_dict is not None:
            for k in self.configure_dict.keys():
                v = self.configure_dict[k]
                f_result_values.append(
                    "c:{}:{}".format(k, v.replace("|", ":")),
                )

        self.presets_delimited[f_preset_name] = f_result_values
        self.commit_presets()
        self.suppress_change = True
        self.program_combobox.setCurrentIndex(
            self.program_combobox.findText(f_preset_name),
        )
        self.suppress_change = False

    def commit_presets(self):
        f_presets = "\n".join(
            "|".join([x] + self.presets_delimited[x])
            for x in sorted(
                self.presets_delimited,
                key=lambda s: s.lower(),
            )
        )
        f_result = "{}\n{}".format(self.plugin_name, f_presets)
        util.write_file_text(self.preset_path, f_result)
        self.load_presets()

    def program_changed(self, a_val=None):
        if not a_val or self.suppress_change:
            return
        f_key = str(self.program_combobox.currentText())
        if not f_key:
            return
        f_preset = self.presets_delimited[f_key]
        f_preset_dict = {}
        f_configure_dict = {}
        for f_kvp in f_preset:
            f_list = f_kvp.split(":")
            if f_list[0] == "c":
                f_configure_dict[f_list[1]] = "|".join(f_list[2:])
            else:
                f_preset_dict[int(f_list[0])] = int(f_list[1])

        for k, v in self.controls.items():
            if int(k) in f_preset_dict:
                v.set_value(f_preset_dict[k], True)
            else:
                v.reset_default_value()
        if self.reconfigure_callback is not None:
            self.reconfigure_callback(f_configure_dict)

    def add_control(self, a_control):
        self.controls[a_control.port_num] = a_control

