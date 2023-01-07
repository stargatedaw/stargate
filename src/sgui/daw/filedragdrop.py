from sglib import constants
from sgui import shared as glbl_shared, widgets
from sgui.daw import shared
from sglib.lib import util
from sgui.widgets import FileDragDropListWidget
from sgui.sgqt import *
import os

class FileDragDropper(widgets.AbstractFileBrowserWidget):
    def __init__(
        self,
        a_filter_func=util.is_audio_file,
    ):
        widgets.AbstractFileBrowserWidget.__init__(
            self,
            a_filter_func=a_filter_func,
            file_list_widget=FileDragDropListWidget,
        )
        self.list_file.setDragEnabled(True)
        self.list_file.mousePressEvent = self.file_mouse_press_event
        self.preview_button.pressed.connect(self.on_preview)
        self.stop_preview_button.pressed.connect(self.on_stop_preview)

    def on_preview(self):
        def exactly_one(msg='You must select exactly one audio file'):
            if glbl_shared.IS_PLAYING:
                return
            QMessageBox.warning(None, None, msg)
        _list = self.list_file.selectedItems()
        if len(_list) == 0:
            exactly_one()
            return
        if len(_list) > 1:
            exactly_one()
            return
        fname = _list[0].text()
        if os.path.splitext(fname)[1].lower() in ('.mid', '.midi'):
            exactly_one(
                'You must select exactly one audio file, MIDI files '
                'cannot be previewed'
            )
            return
        if fname:
            constants.IPC.preview_audio(
                os.path.join(self.last_open_dir, fname)
            )

    def on_stop_preview(self):
        constants.IPC.stop_preview()

    def file_mouse_press_event(self, a_event):
        QListWidget.mousePressEvent(self.list_file, a_event)
        shared.AUDIO_ITEMS_TO_DROP = []
        shared.MIDI_FILES_TO_DROP = []
        for f_item in self.list_file.selectedItems():
            f_path = os.path.join(
                *(str(x) for x in (self.last_open_dir, f_item.text())))
            if util.is_midi_file(f_path):
                shared.MIDI_FILES_TO_DROP.append(f_path)
            else:
                shared.AUDIO_ITEMS_TO_DROP.append(f_path)

__all__ = [
    'FileDragDropper',
]
