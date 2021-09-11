from .audio_item_viewer import *
from sglib.lib.translate import _
from sgui.sgqt import *


AUDIO_LOOP_CLIPBOARD = None
LOOP_GRADIENT = QLinearGradient(0.0, 0.0, 66.0, 66.0)
LOOP_GRADIENT.setColorAt(0.0, QColor.fromRgb(246, 180, 30))
LOOP_GRADIENT.setColorAt(1.0, QColor.fromRgb(226, 180, 42))
LOOP_PEN = QPen(QColor.fromRgb(246, 180, 30), 12.0)


def global_set_audio_loop_clipboard(a_ls, a_le):
    global AUDIO_LOOP_CLIPBOARD
    AUDIO_LOOP_CLIPBOARD = (float(a_ls), float(a_le))


class sample_viewer_widget(AudioItemViewerWidget):
    def __init__(
        self,
        a_start_callback,
        a_end_callback,
        a_loop_start_callback,
        a_loop_end_callback,
        a_fade_in_callback,
        a_fade_out_callback,
        bg_brush=None,
        fg_brush=None,
    ):
        AudioItemViewerWidget.__init__(
            self,
            a_start_callback,
            a_end_callback,
            a_fade_in_callback,
            a_fade_out_callback,
            bg_brush=bg_brush,
            fg_brush=fg_brush,
        )
        self.loop_start_callback_x = a_loop_start_callback
        self.loop_end_callback_x = a_loop_end_callback
        self.scene_context_menu.addSeparator()
        self.loop_copy_action = self.scene_context_menu.addAction(
            _("Copy Loop Markers"),
        )
        self.loop_copy_action.triggered.connect(self.copy_loop)
        self.loop_paste_action = self.scene_context_menu.addAction(
            _("Paste Loop Markers"),
        )
        self.loop_paste_action.triggered.connect(self.paste_loop)

    def copy_loop(self):
        if self.graph_object is not None:
            global_set_audio_loop_clipboard(
                self.loop_start_marker.value, self.loop_end_marker.value)

    def paste_loop(self):
        if self.graph_object is not None and \
        AUDIO_LOOP_CLIPBOARD is not None:
            self.loop_start_marker.set_value(AUDIO_LOOP_CLIPBOARD[0])
            self.loop_end_marker.set_value(AUDIO_LOOP_CLIPBOARD[1])

    def loop_start_callback(self, a_val):
        self.loop_start_callback_x(a_val)
        self.update_label()

    def loop_end_callback(self, a_val):
        self.loop_end_callback_x(a_val)
        self.update_label()

    def draw_item(
        self,
        a_path_list,
        a_start,
        a_end,
        a_loop_start,
        a_loop_end,
        a_fade_in,
        a_fade_out,
    ):
        AudioItemViewerWidget.draw_item(
            self,
            a_path_list,
            a_start,
            a_end,
            a_fade_in,
            a_fade_out,
        )
        self.loop_start_marker = audio_marker_widget(
            0, a_loop_start, LOOP_PEN, LOOP_GRADIENT, "L",
            self.graph_object, audio_marker_widget.mode_loop,
            2, self.loop_start_callback)
        self.scene.addItem(self.loop_start_marker)
        self.loop_end_marker = audio_marker_widget(
            1, a_loop_end, LOOP_PEN, LOOP_GRADIENT, "L",
            self.graph_object, audio_marker_widget.mode_loop,
            2, self.loop_end_callback)
        self.scene.addItem(self.loop_end_marker)

        self.loop_start_marker.set_other(self.loop_end_marker)
        self.loop_end_marker.set_other(self.loop_start_marker)
        self.loop_start_marker.set_pos()
        self.loop_end_marker.set_pos()

        self.drag_start_markers.append(self.loop_start_marker)
        self.drag_end_markers.append(self.loop_end_marker)
        self.update_label()
