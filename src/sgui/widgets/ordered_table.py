from . import _shared
from sglib.math import clip_max
from sglib.models import theme
from sgui.sgqt import *
from sglib.lib import util
from sglib.lib.translate import _


class OrderedTable(QGraphicsView):
    def __init__(
        self,
        a_item_labels,
        a_item_height,
        a_item_width,
    ):
        QGraphicsView.__init__(self)
        self.item_height = a_item_height
        self.item_width = a_item_width
        self.total_height = self.item_height * len(a_item_labels)
        self.total_width = a_item_width
        self.scene = QGraphicsScene(self)
        self.scene.setBackgroundBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            ),
        )
        self.setScene(self.scene)
        self.setFixedSize(
            self.item_width + 20,
            clip_max(self.total_height + 10, 600),
        )
        self.item_list = []
        for f_i, f_label in zip(
            range(len(a_item_labels)),
            a_item_labels,
        ):
            f_item = OrderedTableItem(
                f_label,
                a_item_height,
                a_item_width,
                f_i * a_item_height,
                f_i,
                self,
                QtCore.Qt.GlobalColor.lightGray,
            )
            self.scene.addItem(f_item)
            self.item_list.append(f_item)

    def reorder_items(self, a_item_index, a_new_pos_y):
        f_list = self.item_list
        f_new_index = int(
            (a_new_pos_y / self.total_height) * len(self.item_list)
        )
        if f_new_index < 0:
            f_new_index = 0
        elif f_new_index >= len(self.item_list):
            f_new_index = len(self.item_list) - 1
        if a_item_index > f_new_index:
            f_list.insert(f_new_index, f_list.pop(a_item_index))
        elif  a_item_index < f_new_index:
            f_list.insert(f_new_index + 1, f_list.pop(a_item_index))
        for f_i, f_item in zip(range(len(f_list)), f_list):
            f_item.setPos(0, f_i * self.item_height)
            f_item.index = f_i


class OrderedTableItem(QGraphicsRectItem):
    def __init__(
        self,
        a_text,
        a_height,
        a_width,
        a_y,
        a_index,
        a_parent,
        a_brush
    ):
        QGraphicsRectItem.__init__(self)
        self.text = str(a_text)
        self.setToolTip('Click and drag this item up or down to reorder it')
        self.text_item = QGraphicsTextItem(a_text, self)
        self.text_item.setDefaultTextColor(QtCore.Qt.GlobalColor.black)
        self.setRect(0., 0., float(a_width), float(a_height))
        self.setPos(0, a_y)
        self.default_brush = a_brush
        self.setBrush(a_brush)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.index = self.orig_index = a_index
        self.parent = a_parent

    def mouseMoveEvent(self, a_event):
        QGraphicsRectItem.mouseMoveEvent(self, a_event)
        f_pos = a_event.scenePos()
        self.parent.reorder_items(self.index, f_pos.y())


def ordered_table_dialog(
    a_labels,
    a_list,
    a_item_height,
    a_item_width,
    a_parent=None,
):
    def ok_handler():
        f_dialog.retval = [
            a_list[x.orig_index]
            for x in f_table.item_list
        ]
        f_dialog.close()
    f_dialog = QDialog(a_parent)
    f_dialog.retval = None
    f_dialog.setWindowTitle(_("Order"))
    f_layout = QVBoxLayout(f_dialog)
    f_table = OrderedTable(a_labels, a_item_height, a_item_width)
    hlayout = QHBoxLayout()
    f_layout.addLayout(hlayout)
    hlayout.addItem(
        QSpacerItem(0, 0, QSizePolicy.Policy.Expanding),
    )
    hlayout.addWidget(f_table)
    hlayout.addItem(
        QSpacerItem(0, 0, QSizePolicy.Policy.Expanding),
    )
    f_ok_cancel_layout = QHBoxLayout()
    f_layout.addLayout(f_ok_cancel_layout)
    f_ok_button = QPushButton(_("OK"))
    f_ok_cancel_layout.addWidget(f_ok_button)
    f_ok_button.pressed.connect(ok_handler)
    f_cancel_button = QPushButton(_("Cancel"))
    f_ok_cancel_layout.addWidget(f_cancel_button)
    f_cancel_button.pressed.connect(f_dialog.close)
    f_dialog.exec()
    f_table.scene.clear()
    return f_dialog.retval


