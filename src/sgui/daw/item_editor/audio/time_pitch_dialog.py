from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib.util import *
from sgui.sgqt import *

from sgui import shared as glbl_shared
from sgui.widgets import TimePitchDialogWidget
from sgui.daw import shared
from sglib import constants
from sgui.daw.lib import item as item_lib
from sglib.lib import util
from sglib.lib.translate import _


class TimePitchDialogWidget(TimePitchDialogWidget):
    def __init__(self, audio_item):
        super().__init__(audio_item, ps_pitch=True)

    def ok_handler(self):
        if glbl_shared.IS_PLAYING:
            QMessageBox.warning(
                self.widget,
                _("Error"),
                _("Cannot edit audio items during playback"),
            )
            return

        self.end_mode = 0

        f_selected_count = 0

        f_was_stretching = False

        for f_item in shared.AUDIO_SEQ.audio_items:
            if f_item.isSelected():
                f_new_ts_mode = util.TIMESTRETCH_INDEXES[
                    self.timestretch_mode.currentText()
                ]
                f_new_ts = round(self.timestretch_amt.value(), 6)
                f_new_ps = round(self.pitch_shift.value(), 6)
                if self.timestretch_amt_end_checkbox.isChecked():
                    f_new_ts_end = round(
                        self.timestretch_amt_end.value(), 6)
                else:
                    f_new_ts_end = f_new_ts
                if self.pitch_shift_end_checkbox.isChecked():
                    f_new_ps_end = round(self.pitch_shift_end.value(), 6)
                else:
                    f_new_ps_end = f_new_ps
                f_item.audio_item.crispness = \
                    self.crispness_combobox.currentIndex()

                if (
                    f_item.audio_item.time_stretch_mode >= 3
                    or (
                        f_item.audio_item.time_stretch_mode == 1
                        and (
                            f_item.audio_item.pitch_shift_end
                            !=
                            f_item.audio_item.pitch_shift
                        )
                    ) or (
                        f_item.audio_item.time_stretch_mode == 2
                        and (
                            f_item.audio_item.timestretch_amt_end
                            !=
                            f_item.audio_item.timestretch_amt
                        )
                    )
                ) and (
                    f_new_ts_mode == 0
                    or (
                        f_new_ts_mode == 1
                        and
                        f_new_ps == f_new_ps_end
                    ) or (
                        f_new_ts_mode == 2
                        and
                        f_new_ts == f_new_ts_end
                    )
                ):
                    f_item.audio_item.uid = \
                        constants.PROJECT.timestretch_get_orig_file_uid(
                            f_item.audio_item.uid,
                        )

                f_item.audio_item.time_stretch_mode = f_new_ts_mode
                f_item.audio_item.pitch_shift = f_new_ps
                f_item.audio_item.timestretch_amt = f_new_ts
                f_item.audio_item.pitch_shift_end = f_new_ps_end
                f_item.audio_item.timestretch_amt_end = f_new_ts_end
                f_item.draw()
                f_item.clip_at_sequence_end()
                if (
                    f_new_ts_mode >= 3
                    or
                    (f_new_ts_mode == 1 and f_new_ps != f_new_ps_end)
                    or
                    (f_new_ts_mode == 2 and f_new_ts != f_new_ts_end)
                    and
                    f_item.orig_string != str(f_item.audio_item)
                ):
                    f_was_stretching = True
                    try:
                        constants.PROJECT.timestretch_audio_item(
                            f_item.audio_item,
                        )
                    except FileNotFoundError as ex:
                        QMessageBox.warning(
                            self.widget,
                            _("Error"),
                            str(ex),
                        )
                        global_open_audio_items(True)
                        return

                f_item.draw()
                f_selected_count += 1
        if f_selected_count == 0:
            QMessageBox.warning(
                self.widget, _("Error"), _("No items selected"))
        else:
            item_lib.save_item(shared.CURRENT_ITEM_NAME, shared.CURRENT_ITEM)
            global_open_audio_items(True)
            constants.DAW_PROJECT.commit(_("Update audio items"))
        self.widget.close()

