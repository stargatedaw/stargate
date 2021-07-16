from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.sgqt import *

from sglib import constants
from sgui import shared as glbl_shared
from sgui.daw import shared
from sgui.daw.lib import item as item_lib
from sglib.lib.translate import _


class FadeVolDialogWidget:
    def __init__(self, a_audio_item):
        self.widget = QDialog(
            parent=glbl_shared.MAIN_WINDOW.widget,
        )
        self.widget.setWindowTitle(_("Fade Volume..."))
        self.widget.setMaximumWidth(480)
        self.main_vlayout = QVBoxLayout(self.widget)

        self.layout = QGridLayout()
        self.main_vlayout.addLayout(self.layout)

        self.fadein_vol_layout = QHBoxLayout()
        self.fadein_vol_checkbox = QCheckBox(_("Fade-In:"))
        self.fadein_vol_layout.addWidget(self.fadein_vol_checkbox)
        self.fadein_vol_spinbox = QSpinBox()
        self.fadein_vol_spinbox.setRange(-50, -6)
        self.fadein_vol_spinbox.setValue(a_audio_item.fadein_vol)
        self.fadein_vol_spinbox.valueChanged.connect(self.fadein_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadein_vol_spinbox)
        self.fadein_vol_layout.addItem(
            QSpacerItem(5, 5, QSizePolicy.Policy.Expanding),
        )
        self.main_vlayout.addLayout(self.fadein_vol_layout)

        self.fadeout_vol_checkbox = QCheckBox(_("Fade-Out:"))
        self.fadein_vol_layout.addWidget(self.fadeout_vol_checkbox)
        self.fadeout_vol_spinbox = QSpinBox()
        self.fadeout_vol_spinbox.setRange(-50, -6)
        self.fadeout_vol_spinbox.setValue(a_audio_item.fadeout_vol)
        self.fadeout_vol_spinbox.valueChanged.connect(self.fadeout_vol_changed)
        self.fadein_vol_layout.addWidget(self.fadeout_vol_spinbox)

        self.ok_layout = QHBoxLayout()
        self.ok = QPushButton(_("OK"))
        self.ok.pressed.connect(self.ok_handler)
        self.ok_layout.addWidget(self.ok)
        self.cancel = QPushButton(_("Cancel"))
        self.cancel.pressed.connect(self.widget.close)
        self.ok_layout.addWidget(self.cancel)
        self.main_vlayout.addLayout(self.ok_layout)

        self.last_open_dir = HOME

    def fadein_vol_changed(self, a_val=None):
        self.fadein_vol_checkbox.setChecked(True)

    def fadeout_vol_changed(self, a_val=None):
        self.fadeout_vol_checkbox.setChecked(True)

    def ok_handler(self):
        if glbl_shared.IS_PLAYING:
            QMessageBox.warning(
                self.widget, _("Error"),
                _("Cannot edit audio items during playback"))
            return

        self.end_mode = 0

        f_selected_count = 0

        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                if self.fadein_vol_checkbox.isChecked():
                    f_item.audio_item.fadein_vol = \
                        self.fadein_vol_spinbox.value()
                if self.fadeout_vol_checkbox.isChecked():
                    f_item.audio_item.fadeout_vol = \
                        self.fadeout_vol_spinbox.value()
                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            item_lib.save_item(
                shared.CURRENT_ITEM_NAME,
                shared.CURRENT_ITEM,
            )
            global_open_audio_items(True)
            constants.DAW_PROJECT.commit(_("Update audio items"))
        self.widget.close()

