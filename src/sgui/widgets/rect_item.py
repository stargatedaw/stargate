from sgui.sgqt import *

class QGraphicsRectItemNDL(QGraphicsRectItem):
    """ QGraphicsRectItem without that awful dotted line when selected """
    def paint(
        self,
        painter,
        option,
        arg4=None,
    ):
        option.state &= ~QStyle.StateFlag.State_Selected
        QGraphicsRectItem.paint(self, painter, option)

