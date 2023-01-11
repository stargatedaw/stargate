from sgui.sgqt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
)
from sglib import constants
from sglib.lib.util import remove_bad_chars
from sglib.log import LOG
from sglib.models.daw.midi_file import DawMidiFile, MIDIFileAnalysis
from sglib.models.daw._shared import TRACK_COUNT_ALL
from sgui.daw import shared
import os


def midi_file_dialog(path, beat, track_index):
    def ok_pressed():
        _item_name = item_name.text()
        _import_mode = import_mode.currentIndex()
        _notes = notes_checkbox.isChecked()
        _ccs = cc_checkbox.isChecked()
        _pbs = pitchbend_checkbox.isChecked()
        _channel = None
        if channel_checkbox.isChecked():
            _channel = channel_combobox.currentIndex()

        if len(_item_name) < 5:
            QMessageBox.warning(
                None,
                None,
                "Item name must be at least 5 characters",
            )
            return
        if not any([_notes, _ccs, _pbs]):
            QMessageBox.warning(
                None,
                None,
                "Must import at least one of notes, CCs, pitchbend",
            )
            return
        if (
            _import_mode == 1
            and
            len(analysis.channels) + track_index >= TRACK_COUNT_ALL
        ):
            QMessageBox.warning(
                None,
                'Error',
                'Empty MIDI file'
            )
            return
        midi_file = DawMidiFile(
            path,
            constants.DAW_PROJECT,
            _item_name,
            _channel,
            _notes,
            _ccs,
            _pbs,
        )
        if _import_mode == 1:
            midi_file.multi_item()
        else:
            midi_file.single_item()
        constants.DAW_PROJECT.import_midi_file(
            midi_file,
            beat,
            track_index,
            _item_name,
        )
        constants.DAW_PROJECT.commit("Import MIDI file")
        shared.SEQ_WIDGET.open_sequence()
        dialog.close()

    def item_name_changed(text):
        fixed = remove_bad_chars(text)[:20]
        if text != fixed:
            item_name.setText(fixed)

    def import_mode_changed(index: int=None):
        index = import_mode.currentIndex()
        LOG.info(index)
        channels_for_types = analysis.channels_for_types(
            notes_checkbox.isChecked(),
            cc_checkbox.isChecked(),
            pitchbend_checkbox.isChecked(),
        )
        channels_str = ','.join(str(x + 1) for x in channels_for_types)
        msg = f'Events on channels: {channels_str}'
        info_label.setText(msg)
        if index == 0:
            if len(channels_for_types) > 1:
                channel_checkbox.setChecked(False)
                channel_checkbox.hide()
                channel_combobox.hide()
            else:
                channel_checkbox.setChecked(True)
                channel_checkbox.show()
                channel_combobox.show()
        elif index == 1:
            channel_checkbox.setChecked(True)
            channel_checkbox.show()
            channel_combobox.show()
        else:
            raise ValueError

    dialog = QDialog()
    vlayout = QVBoxLayout(dialog)
    gridlayout = QGridLayout()
    vlayout.addLayout(gridlayout)
    item_name_label = QLabel('Item Name')
    gridlayout.addWidget(item_name_label, 0, 0)
    item_name = QLineEdit()
    item_name.setToolTip(
        'The name of the sequencer item(s) to create from this MIDI file. '
        'If creating more than one item, the items will be given numeric '
        'suffixes'
    )
    gridlayout.addWidget(item_name, 0, 1)
    fname = os.path.basename(path)
    default_name = remove_bad_chars(os.path.splitext(fname)[0])[:20]
    item_name.setText(default_name)
    item_name.textChanged.connect(item_name_changed)

    import_mode_label = QLabel('Import Mode')
    gridlayout.addWidget(import_mode_label, 5, 0)
    import_mode = QComboBox()
    import_mode.setToolTip(
        'Single Item: All MIDI channels go to a single item, maintaining '
        'their original channels.  Track Per Channel: Each channel becomes '
        'a separate item on a separate track'
    )
    import_mode.addItems(['Single Item', 'Track Per Channel'])
    import_mode.currentIndexChanged.connect(import_mode_changed)
    gridlayout.addWidget(import_mode, 5, 1)

    channel_checkbox = QCheckBox('Set to Channel')
    gridlayout.addWidget(channel_checkbox, 10, 0)
    channel_checkbox.setChecked(True)
    channel_checkbox.setToolTip(
        'Check this box to force multichannel MIDI to all map to the same '
        'channel in their new items. Single items will remap to this channel '
        'only if there is only one channel'
    )

    channel_combobox = QComboBox()
    gridlayout.addWidget(channel_combobox, 10, 1)
    channel_combobox.addItems(constants.MIDI_CHANNELS)
    channel_combobox.setToolTip(
        'The MIDI channel to use if the Set to Channel checkbox is checked. '
        'In single item mode, this control can only be set if all of the '
        'imported event types are on the same channel'
    )

    events_hlayout = QHBoxLayout()
    vlayout.addLayout(events_hlayout)

    notes_checkbox = QCheckBox("Notes")
    notes_checkbox.setChecked(True)
    events_hlayout.addWidget(notes_checkbox)
    notes_checkbox.setToolTip('Include MIDI note events in the imported items')
    notes_checkbox.stateChanged.connect(import_mode_changed)

    pitchbend_checkbox = QCheckBox("Pitchbend")
    events_hlayout.addWidget(pitchbend_checkbox)
    pitchbend_checkbox.setToolTip(
        'Include MIDI pitchbend evnts in the imported items'
    )
    pitchbend_checkbox.stateChanged.connect(import_mode_changed)

    cc_checkbox = QCheckBox("CCs")
    events_hlayout.addWidget(cc_checkbox)
    cc_checkbox.setToolTip('Include MIDI CC events in the imported items')
    cc_checkbox.stateChanged.connect(import_mode_changed)

    info_label = QLabel()
    vlayout.addWidget(info_label)

    vlayout.addItem(
        QSpacerItem(
            1,
            1,
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
        ),
    )

    ok_cancel_hlayout = QHBoxLayout()
    vlayout.addLayout(ok_cancel_hlayout)
    ok_button = QPushButton('OK')
    ok_cancel_hlayout.addWidget(ok_button)
    ok_button.pressed.connect(ok_pressed)
    cancel_button = QPushButton('Cancel')
    ok_cancel_hlayout.addWidget(cancel_button)
    cancel_button.pressed.connect(dialog.close)

    try:
        analysis = MIDIFileAnalysis.factory(path)
    except:
        msg = f'Could not read MIDI file: {path}'
        LOG.exception(msg)
        QMessageBox.warning(None, 'Error', msg)
        return
    if len(analysis.channels) == 1:
        import_mode_label.hide()
        import_mode.hide()
    if not any([analysis.has_notes, analysis.has_ccs, analysis.has_pbs]):
        QMessageBox.warning(None, 'Error', 'Empty MIDI file')
        return
    if not analysis.has_notes or not any([analysis.has_ccs, analysis.has_pbs]):
        notes_checkbox.hide()
    if not analysis.has_ccs:
        cc_checkbox.hide()
    if not analysis.has_pbs:
        pitchbend_checkbox.hide()
    import_mode_changed(0)

    dialog.exec()

