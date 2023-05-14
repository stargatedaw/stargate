from sglib import constants
from sglib.log import LOG
from sglib.api.daw import api_playlist
from sgui.daw.lib import sequence as sequence_lib
from sgui.widgets import FileDragDropListWidget
from sgui.sgqt import (
    QtCore,
    QAbstractItemView,
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QVBoxLayout,
    QListWidgetItem,
)


class PlaylistWidget:
    def __init__(self):
        self._current_sequence = None
        self.suppress_changes = True
        self.parent = QWidget()
        self.parent.setContentsMargins(0, 0, 0, 0)
        self.parent.setObjectName('sidebar')
        layout = QVBoxLayout(self.parent)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Sequence list
        self.sequence_widget = FileDragDropListWidget()
        self.sequence_widget.setObjectName('sidebar_list')
        layout.addWidget(self.sequence_widget)
        self.sequence_widget.setToolTip(
            'Select the song to show in the sequencer and play with the '
            'transport.  You can keep multiple songs to experiment, use '
            'as scratchpads, or re-use the tracks and plugins'
        )
        self.sequence_widget.setAlternatingRowColors(True)
        self.sequence_widget.setDragDropMode(
            QAbstractItemView.DragDropMode.NoDragDrop,
        )
        self.sequence_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection,
        )
        self.sequence_widget.itemChanged.connect(self.sequence_changed)
        self.sequence_widget.itemClicked.connect(self.sequence_item_clicked)

        # Add new sequence
        add_seq_layout = QHBoxLayout()
        layout.addLayout(add_seq_layout)
        self.add_seq_text = QLineEdit()
        self.add_seq_text.setToolTip(
            'The name of a new song to add to the song list'
        )
        self.add_seq_text.returnPressed.connect(self.add_seq)
        add_seq_layout.addWidget(self.add_seq_text)
        self.add_seq_button = QPushButton("Add")
        self.add_seq_button.setToolTip(
            'Add a new song by entering a name and pressing this button'
        )
        add_seq_layout.addWidget(self.add_seq_button)
        self.add_seq_button.pressed.connect(self.add_seq)
        self.suppress_changes = False

    def on_play(self):
        self.parent.setDisabled(True)

    def on_stop(self):
        self.parent.setEnabled(True)

    def add_seq(self):
        """ Add a new sequence to the pool.  Not to be confused with adding
            a sequence to the playlist.
        """
        name = self.add_seq_text.text().strip()
        if not name:
            QMessageBox.warning(
                self.parent,
                "Error",
                "Must have a name",
            )
            return
        try:
            api_playlist.new_seq(name)
        except FileExistsError:
            QMessageBox.warning(
                self.parent,
                "Error",
                "Sequence '{}' already exists".format(name),
            )
            return
        self.add_seq_text.clear()
        self.open()

    def sequence_item_clicked(self, item):
        items = self.sequence_widget.selectedItems()
        if (
            len(items) == 1
            and
            # User did not CTRL+click unselect one of 2 items
            items[0].text() == item.text()
        ):
            name = str(item.text())
            LOG.info(f"Opening sequence {name}")
            sequence_lib.change_sequence(name)
            self._current_sequence = name

    def sequence_changed(self, item):
        """ Currently only catches rename events when the user double clicks
            an item and changes the name
        """
        if self.suppress_changes:
            return
        new_name = item.text().strip()
        if new_name and new_name != item.orig_name:
            try:
                api_playlist.change_name(item.orig_name, new_name)
                sequence_lib.change_sequence(new_name)
                self._current_sequence = new_name
            except FileExistsError:
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    "Sequence '{}' already exists".format(new_name),
                )
            except FileNotFoundError:
                LOG.exception("orig_name not found, likely a bug")
                QMessageBox.warning(
                    self.parent,
                    "Error",
                    "Original Sequence name '{}' not found".format(
                        item.orig_name,
                    ),
                )
        self.open()

    def add_sequence_item(self, name):
        flags = (
            QtCore.Qt.ItemFlag.ItemIsDragEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsDropEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsEditable
            |
            QtCore.Qt.ItemFlag.ItemIsEnabled
            |
            QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        return self.add_item(
            name,
            self.sequence_widget,
            flags,
        )

    def add_item(
        self,
        name,
        parent,
        flags,
    ):
        """ Add a QListWidgetItem to a QListWidget
            @name:   str, The name to display on the item
            @parent: QListWidget, The list widget to add the item to
            @flags:  int, The item flags
        """
        self.suppress_changes = True
        item = QListWidgetItem(
            str(name),
            parent,
        )
        item.orig_name = name
        item.setFlags(flags)
        self.suppress_changes = False
        return item

    def open(self):
        """ Populate the widgets from the project files
        """
        self.sequence_widget.clear()
        playlist_names, sequence_names, selected = api_playlist.load()
        if self._current_sequence:
            selected = self._current_sequence
        else:
            self._current_sequence = selected
        for name in sequence_names:
            item = self.add_sequence_item(name)
            if name == selected:
                item.setSelected(True)

