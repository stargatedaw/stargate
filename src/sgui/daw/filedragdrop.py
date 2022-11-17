from sglib import constants
from sgui import widgets
from sgui.daw import shared
from sglib.lib import util
from sgui.sgqt import *
import os

class FileDragDropListWidget(QListWidget):
    def startDrag(self, *args, **kwargs):
        drag = QtGui.QDrag(self)
        drag.setMimeData(self.model().mimeData(self.selectedIndexes()))
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec(QtCore.Qt.DropAction.MoveAction)

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
        f_list = self.list_file.selectedItems()
        if f_list:
            constants.IPC.preview_audio(
                os.path.join(
                    *(
                        str(x) for x in (
                            self.last_open_dir,
                            f_list[0].text()
                        )
                    )
                )
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
