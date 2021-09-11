from . import _shared
from sglib import constants
from sglib.math import clip_max, clip_min
from sgui import shared as sg_shared
from sgui.daw import shared
from sglib.models.daw import *
from sgui.daw.shared import *
from sglib.lib import util
from sglib.lib.util import *
from sglib.lib.translate import _
from sgui.sgqt import *


class TempoMarkerEvent:
    """ Used to override tempo marker events """
    def __init__(self, beat):
        self.beat = beat

    def mouse_press(self, event):
        shared.SEQUENCER.header_event_pos = self.beat
        shared.SEQUENCER.header_time_modify()

def show(event):
    shared.SEQUENCER.context_menu_enabled = False
    shared.SEQUENCER.header_event_pos = int(
        qt_event_pos(event).x() / _shared.SEQUENCER_PX_PER_BEAT
    )
    menu = QMenu(shared.MAIN_WINDOW)
    marker_action = menu.addAction(_("Text Marker..."))
    marker_action.triggered.connect(header_marker_modify)
    time_modify_action = menu.addAction(_("Time/Tempo Marker..."))
    time_modify_action.triggered.connect(header_time_modify)
    time_range_action = menu.addAction(_("Tempo Range..."))
    time_range_action.triggered.connect(header_time_range)
    menu.addSeparator()
    clear_tempo_range_action = menu.addAction(
        _("Clear Time/Tempo Markers in Region")
    )
    clear_tempo_range_action.triggered.connect(header_tempo_clear)
    menu.addSeparator()
    loop_start_action = menu.addAction(_("Set Region Start"))
    loop_start_action.triggered.connect(header_loop_start)
    if shared.CURRENT_SEQUENCE.loop_marker:
        loop_end_action = menu.addAction(_("Set Region End"))
        loop_end_action.triggered.connect(header_loop_end)
        select_sequence = menu.addAction(_("Select Items in Region"))
        select_sequence.triggered.connect(shared.SEQUENCER.select_sequence_items)
        copy_sequence_action = menu.addAction(_("Copy Region"))
        copy_sequence_action.triggered.connect(copy_sequence)
        if shared.SEQUENCER.sequence_clipboard:
            insert_sequence_action = menu.addAction(_("Insert Region"))
            insert_sequence_action.triggered.connect(insert_sequence)
    menu.exec(QCursor.pos())

def header_time_modify():
    def ok_handler():
        marker = tempo_marker(
            shared.SEQUENCER.header_event_pos, tempo.value(),
            tsig_num.value(), int(str(tsig_den.currentText())))
        shared.CURRENT_SEQUENCE.set_marker(marker)
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Set tempo marker"))
        shared.SEQ_WIDGET.open_sequence()
        window.close()

    def delete_handler():
        marker = shared.CURRENT_SEQUENCE.has_marker(
            shared.SEQUENCER.header_event_pos,
            2,
        )
        if marker and shared.SEQUENCER.header_event_pos:
            shared.CURRENT_SEQUENCE.delete_marker(marker)
            constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
            constants.DAW_PROJECT.commit(_("Delete tempo marker"))
            shared.SEQ_WIDGET.open_sequence()
        window.close()

    window = QDialog(shared.MAIN_WINDOW)
    window.setWindowTitle(_("Tempo / Time Signature"))
    layout = QGridLayout()
    window.setLayout(layout)

    marker = shared.CURRENT_SEQUENCE.has_marker(
        shared.SEQUENCER.header_event_pos,
        2,
    )

    tempo = QSpinBox()
    tempo.setRange(30, 240)
    layout.addWidget(QLabel(_("Tempo")), 0, 0)
    layout.addWidget(tempo, 0, 1)
    tsig_layout = QHBoxLayout()
    layout.addLayout(tsig_layout, 1, 1)
    tsig_num = QSpinBox()
    tsig_num.setRange(1, 16)
    layout.addWidget(QLabel(_("Time Signature")), 1, 0)
    tsig_layout.addWidget(tsig_num)
    tsig_layout.addWidget(QLabel("/"))

    tsig_den = QComboBox()
    tsig_den.setMinimumWidth(60)
    tsig_layout.addWidget(tsig_den)
    tsig_den.addItems(["2", "4", "8", "16"])

    if marker:
        tempo.setValue(marker.tempo)
        tsig_num.setValue(marker.tsig_num)
        tsig_den.setCurrentIndex(
            tsig_den.findText(str(marker.tsig_den)))
    else:
        tempo.setValue(128)
        tsig_num.setValue(4)
        tsig_den.setCurrentIndex(1)

    ok = QPushButton(_("Save"))
    ok.pressed.connect(ok_handler)
    layout.addWidget(ok, 6, 0)
    if shared.SEQUENCER.header_event_pos:
        cancel = QPushButton(_("Delete"))
        cancel.pressed.connect(delete_handler)
    else:
        cancel = QPushButton(_("Cancel"))
        cancel.pressed.connect(window.close)
    layout.addWidget(cancel, 6, 1)
    window.exec()

def header_tempo_clear():
    if not shared.CURRENT_SEQUENCE.loop_marker:
        QMessageBox.warning(
            sg_shared.MAIN_WINDOW,
            _("Error"),
            _("No region set, please set a region first"),
        )
        return
    deleted = False
    for i in range(
        shared.CURRENT_SEQUENCE.loop_marker.start_beat,
        shared.CURRENT_SEQUENCE.loop_marker.beat + 1,
    ):
        if i == 0:
            continue
        marker = shared.CURRENT_SEQUENCE.has_marker(i, 2)
        if marker:
            shared.CURRENT_SEQUENCE.delete_marker(marker)
            deleted += 1
    if deleted:
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Delete tempo ranger"))
        shared.SEQ_WIDGET.open_sequence()

def header_time_range():
    if not shared.CURRENT_SEQUENCE.loop_marker:
        QMessageBox.warning(
            sg_shared.MAIN_WINDOW,
            _("Error"),
            _("No region set, please set a region first"),
        )
        return
    def ok_handler():
        tempo = start_tempo.value()
        beat = shared.CURRENT_SEQUENCE.loop_marker.start_beat
        beats = (
            shared.CURRENT_SEQUENCE.loop_marker.beat
            -
            shared.CURRENT_SEQUENCE.loop_marker.start_beat
        )
        inc = (float(end_tempo.value()) - float(tempo)) / beats
        for i in range(
            shared.CURRENT_SEQUENCE.loop_marker.start_beat,
            shared.CURRENT_SEQUENCE.loop_marker.beat + 1,
        ):
            marker = tempo_marker(
                i,
                int(round(tempo)),
                tsig_num.value(),
                int(str(tsig_den.currentText())),
            )
            tempo += inc
            beat += 1
            shared.CURRENT_SEQUENCE.set_marker(marker)
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Set tempo range"))
        shared.SEQ_WIDGET.open_sequence()
        window.close()

    def cancel_handler():
        window.close()

    window = QDialog(shared.MAIN_WINDOW)
    window.setWindowTitle(_("Tempo Range"))
    layout = QGridLayout()
    window.setLayout(layout)

    marker = shared.CURRENT_SEQUENCE.has_marker(
        shared.SEQUENCER.header_event_pos,
        2,
    )

    start_tempo = QSpinBox()
    start_tempo.setRange(30, 240)
    layout.addWidget(QLabel(_("Start Tempo")), 0, 0)
    layout.addWidget(start_tempo, 0, 1)
    end_tempo = QSpinBox()
    end_tempo.setRange(30, 240)
    layout.addWidget(QLabel(_("End Tempo")), 1, 0)
    layout.addWidget(end_tempo, 1, 1)
    tsig_layout = QHBoxLayout()
    layout.addLayout(tsig_layout, 2, 1)
    tsig_num = QSpinBox()
    tsig_num.setRange(1, 16)
    layout.addWidget(QLabel(_("Time Signature")), 2, 0)
    tsig_layout.addWidget(tsig_num)
    tsig_layout.addWidget(QLabel("/"))

    tsig_den = QComboBox()
    tsig_den.setMinimumWidth(60)
    tsig_layout.addWidget(tsig_den)
    tsig_den.addItems(["2", "4", "8", "16"])

    if marker:
        start_tempo.setValue(marker.tempo)
        end_tempo.setValue(marker.tempo)
        tsig_num.setValue(marker.tsig_num)
        tsig_den.setCurrentIndex(
            tsig_den.findText(str(marker.tsig_den)))
    else:
        start_tempo.setValue(128)
        end_tempo.setValue(128)
        tsig_num.setValue(4)
        tsig_den.setCurrentIndex(1)

    ok = QPushButton(_("Create"))
    ok.pressed.connect(ok_handler)
    layout.addWidget(ok, 6, 0)
    cancel = QPushButton(_("Cancel"))
    cancel.pressed.connect(cancel_handler)
    layout.addWidget(cancel, 6, 1)
    window.exec()

def header_marker_modify():
    def ok_handler():
        marker = sequencer_marker(
            shared.SEQUENCER.header_event_pos, text.text())
        shared.CURRENT_SEQUENCE.set_marker(marker)
        constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
        constants.DAW_PROJECT.commit(_("Add text marker"))
        shared.SEQ_WIDGET.open_sequence()
        window.close()

    def cancel_handler():
        marker = shared.CURRENT_SEQUENCE.has_marker(
            shared.SEQUENCER.header_event_pos,
            3,
        )
        if marker:
            shared.CURRENT_SEQUENCE.delete_marker(marker)
            constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
            constants.DAW_PROJECT.commit(_("Delete text marker"))
            shared.SEQ_WIDGET.open_sequence()
        window.close()

    window = QDialog(shared.MAIN_WINDOW)
    window.setWindowTitle(_("Marker"))
    layout = QGridLayout()
    window.setLayout(layout)

    marker = shared.CURRENT_SEQUENCE.has_marker(
        shared.SEQUENCER.header_event_pos,
        3,
    )

    text = QLineEdit()
    text.setMaxLength(21)

    if marker:
        text.setText(marker.text)

    layout.addWidget(QLabel(_("Text")), 0, 0)
    layout.addWidget(text, 0, 1)
    ok_cancel_layout = QHBoxLayout()
    layout.addLayout(ok_cancel_layout, 6, 1)
    ok = QPushButton(_("Save"))
    ok.pressed.connect(ok_handler)
    ok_cancel_layout.addWidget(ok)
    if shared.CURRENT_SEQUENCE.has_marker(
        shared.SEQUENCER.header_event_pos,
        3,
    ):
        cancel = QPushButton(_("Delete"))
    else:
        cancel = QPushButton(_("Cancel"))
    cancel.pressed.connect(cancel_handler)
    ok_cancel_layout.addWidget(cancel)
    window.exec()

def header_loop_start():
    tsig_beats = shared.CURRENT_SEQUENCE.get_tsig_at_pos(
        shared.SEQUENCER.header_event_pos,
    )
    if shared.CURRENT_SEQUENCE.loop_marker:
        end = clip_min(
            shared.CURRENT_SEQUENCE.loop_marker.beat,
            shared.SEQUENCER.header_event_pos + tsig_beats,
        )
    else:
        end = shared.SEQUENCER.header_event_pos + tsig_beats

    marker = loop_marker(
        end,
        shared.SEQUENCER.header_event_pos,
    )
    shared.CURRENT_SEQUENCE.set_loop_marker(marker)
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.commit(_("Set sequence start"))
    shared.SEQ_WIDGET.open_sequence()

def header_loop_end():
    tsig_beats = shared.CURRENT_SEQUENCE.get_tsig_at_pos(
        shared.SEQUENCER.header_event_pos,
    )
    shared.CURRENT_SEQUENCE.loop_marker.beat = clip_min(
        shared.SEQUENCER.header_event_pos,
        tsig_beats,
    )
    shared.CURRENT_SEQUENCE.loop_marker.start_beat = clip_max(
            shared.CURRENT_SEQUENCE.loop_marker.start_beat,
            shared.CURRENT_SEQUENCE.loop_marker.beat - tsig_beats,
        )
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.commit(_("Set sequence end"))
    shared.SEQ_WIDGET.open_sequence()

def copy_sequence():
    sequence_start = shared.CURRENT_SEQUENCE.loop_marker.start_beat
    sequence_end = shared.CURRENT_SEQUENCE.loop_marker.beat
    sequence_length = sequence_end - sequence_start
    item_list = [
        x.audio_item.clone()
        for x in shared.SEQUENCER.get_sequence_items()
    ]
    atm_list = shared.ATM_SEQUENCE.copy_range_all(
        sequence_start,
        sequence_end,
    )
    for item in item_list:
        item.start_beat -= sequence_start
    for point in atm_list:
        point.beat -= sequence_start
    shared.SEQUENCER.sequence_clipboard = (
        sequence_length,
        item_list,
        atm_list,
    )

def insert_sequence():
    (
        sequence_length,
        item_list,
        atm_list,
    ) = shared.SEQUENCER.sequence_clipboard
    item_list = [x.clone() for x in item_list]
    atm_list = [x.clone() for x in atm_list]
    shared.CURRENT_SEQUENCE.insert_space(
        shared.SEQUENCER.header_event_pos,
        sequence_length,
    )
    for item in item_list:
        item.start_beat += shared.SEQUENCER.header_event_pos
        shared.CURRENT_SEQUENCE.add_item_ref_by_uid(item)
    for point in atm_list:
        point.beat += shared.SEQUENCER.header_event_pos
        shared.ATM_SEQUENCE.add_point(point)
    shared.SEQUENCER.automation_save_callback()
    constants.DAW_PROJECT.save_sequence(shared.CURRENT_SEQUENCE)
    constants.DAW_PROJECT.commit(_("Insert sequence"))
    shared.SEQ_WIDGET.open_sequence()

