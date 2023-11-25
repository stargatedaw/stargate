from sglib import constants
from sglib.log import LOG
from sgui.daw import shared
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
    QListWidget,
    QListWidgetItem,
)

class ItemListItem(QListWidgetItem):
    def __init__(self, name, parent, uid):
        super().__init__(name, parent)
        self._uid = uid
        self._name = name
        self.setFlags(
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

class ItemListWidget:
    def __init__(self):
        self.suppress_changes = True
        self.parent = QWidget()
        self.parent.setContentsMargins(0, 0, 0, 0)
        self.parent.setObjectName('sidebar')
        layout = QVBoxLayout(self.parent)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        self.items_widget = FileDragDropListWidget()
        self.items_widget.mousePressEvent = self.mousePressEvent
        self.items_widget.setObjectName('sidebar_list')
        layout.addWidget(self.items_widget)
        self.items_widget.setToolTip(
            'A list of all items in the item pool for this project.  '
            'Drag and drop items from the item list into a song'
        )
        self.items_widget.setAlternatingRowColors(True)
        self.items_widget.setDragDropMode(
            QAbstractItemView.DragDropMode.DragOnly,
        )
        self.items_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection,
        )
        self.items_widget.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers,
        )

        self.suppress_changes = False

    def on_play(self):
        self.parent.setDisabled(True)

    def on_stop(self):
        self.parent.setEnabled(True)

    def add_item(
        self,
        name: str,
        uid: int,
    ):
        """ Add a QListWidgetItem to a QListWidget
            @name: The name to display on the item
            @uid:  The uid of the item
        """
        self.suppress_changes = True
        item = ItemListItem(
            str(name),
            self.items_widget,
            int(uid),
        )
        self.suppress_changes = False
        return item

    def open(self):
        """ Populate the widgets from the project files
        """
        self.items_widget.clear()
        items_dict = constants.DAW_PROJECT.get_items_dict()
        for name, uid in items_dict.uid_lookup.items():
            self.add_item(name, uid)
        self.items_widget.sortItems()

    def mousePressEvent(self, event):
        QListWidget.mousePressEvent(self.items_widget, event)
        shared.ITEM_TO_DROP = None
        for item in self.items_widget.selectedItems():
            LOG.info(item)
            shared.ITEM_TO_DROP = item

