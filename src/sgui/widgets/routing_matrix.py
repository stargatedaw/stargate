from . import _shared
from sgui.sgqt import *
from sglib.models import theme
from sgui.util import get_font
from sgui.daw import shared as daw_shared

ROUTING_GRAPH_NODE_BRUSH = None
ROUTING_GRAPH_TO_BRUSH = None
ROUTING_GRAPH_FROM_BRUSH = None

ROUTE_TYPES = {
    0: 'Audio',
    1: 'Sidechain',
    2: 'MIDI',
}

class RoutingGraphNode(QGraphicsRectItem):
    def __init__(
        self,
        a_text: str,
        a_width: float,
        a_height: float,
        track_index: int,
    ):
        QGraphicsRectItem.__init__(
            self,
            0.,
            0.,
            float(a_width),
            float(a_height),
        )
        self.track_index = int(track_index)
        self.text = get_font().QGraphicsSimpleTextItem(a_text, self)
        self.setZValue(2400)
        self.setToolTip(a_text)
        self.text.setPos(3.0, 3.0)
        text_color = QColor(
            theme.SYSTEM_COLORS.widgets.rout_graph_node_text,
        )
        self.text.setBrush(text_color)
        self.text.setPen(text_color)
        self.set_brush()
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape,
            False,
        )
        # Required for mouseDoubleClickEvent
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
            True,
        )

    def mouseDoubleClickEvent(self, event):
        daw_shared.open_rack(self.track_index)

    def set_brush(self, a_to=False, a_from=False):
        if a_to:
            brush = ROUTING_GRAPH_TO_BRUSH
        elif a_from:
            brush = ROUTING_GRAPH_FROM_BRUSH
        else:
            brush = ROUTING_GRAPH_NODE_BRUSH
        self.setBrush(brush)


class RoutingGraphWidget(QGraphicsView):
    def __init__(self, a_toggle_callback=None):
        super().__init__()
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setBackgroundBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.default_scene_background,
            ),
        )
        self.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft
            |
            QtCore.Qt.AlignmentFlag.AlignTop
        )
        self.node_dict = {}
        self.setMouseTracking(True)
        self.toggle_callback = a_toggle_callback

    def prepare_to_quit(self):
        self.scene.clearSelection()
        self.scene.clear()

    def get_coords(self, a_pos):
        f_x = int(a_pos.x() // self.node_width)
        f_y = int(a_pos.y() // self.node_height)
        return (f_x, f_y)

    def backgroundMousePressEvent(self, a_event):
        #QGraphicsRectItem.mousePressEvent(self.background_item, a_event)
        if self.toggle_callback:
            f_x, f_y = self.get_coords(a_event.scenePos())
            if f_x == f_y or f_y == 0:
                return
            if a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ControlModifier
            ):
                route_type = 1
            elif a_event.modifiers() == (
                QtCore.Qt.KeyboardModifier.ShiftModifier
            ):
                route_type = 2
            else:
                route_type = 0
            self.toggle_callback(f_y, f_x, route_type)

    def backgroundHoverEvent(self, a_event):
        QGraphicsRectItem.hoverMoveEvent(self.background_item, a_event)
        f_x, f_y = self.get_coords(a_event.scenePos())
        if f_x == f_y or f_y == 0:
            self.clear_selection()
            return
        for k, v in self.node_dict.items():
            v.set_brush(k == f_x, k == f_y)

    def backgroundHoverLeaveEvent(self, a_event):
        self.clear_selection()

    def clear_selection(self):
        for v in self.node_dict.values():
            v.set_brush()

    def resizeEvent(self, event):
        QGraphicsView.resizeEvent(self, event)
        self.draw()

    def draw_graph(self, a_graph, a_track_names):
        self.graph = a_graph
        self.track_names = a_track_names
        self.draw()

    def draw(self):
        a_graph = self.graph
        a_track_names = self.track_names
        self.graph_height = self.height() - 36.0
        self.graph_width = self.width() - 36.0
        self.scene.setSceneRect(
            0.0,
            0.0,
            float(self.width()),
            float(self.height()),
        )
        self.node_width = self.graph_width / 32.0
        self.node_height = self.graph_height / 32.0
        self.wire_width = self.node_height * 0.25
        self.wire_width_div2 = self.wire_width * 0.5
        ROUTING_GRAPH_WIRE_INPUT = ((self.node_width * 0.5) -
            (self.wire_width * 0.5))

        f_line_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_lines,
            ),
        )

        global \
            ROUTING_GRAPH_NODE_BRUSH, \
            ROUTING_GRAPH_TO_BRUSH, \
            ROUTING_GRAPH_FROM_BRUSH
        ROUTING_GRAPH_NODE_BRUSH = QBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_node,
            ),
        )
        ROUTING_GRAPH_TO_BRUSH = QBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_to,
            ),
        )
        ROUTING_GRAPH_FROM_BRUSH = QBrush(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_from,
            ),
        )

        self.node_dict = {}
        f_wire_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_wire_audio,
            ),
            self.wire_width_div2,
        )
        f_midi_wire_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_wire_midi,
            ),
            self.wire_width_div2,
        )
        f_sc_wire_pen = QPen(
            QColor(
                theme.SYSTEM_COLORS.widgets.rout_graph_wire_sc,
            ),
            self.wire_width_div2,
        )
        pen_dict = {0: f_wire_pen, 1: f_sc_wire_pen, 2: f_midi_wire_pen}
        self.setUpdatesEnabled(False)
        self.scene.clear()
        self.background_item = QGraphicsRectItem(
            0.0,
            0.0,
            float(self.graph_width),
            float(self.graph_height),
        )
        self.background_item.setBrush(QtCore.Qt.GlobalColor.transparent)
        self.background_item.setPen(QPen(QtCore.Qt.GlobalColor.black))
        self.scene.addItem(self.background_item)
        self.background_item.hoverMoveEvent = self.backgroundHoverEvent
        self.background_item.hoverLeaveEvent = self.backgroundHoverLeaveEvent
        self.background_item.setAcceptHoverEvents(True)
        self.background_item.mousePressEvent = self.backgroundMousePressEvent
        conn_type_y_pos = {0: 1, 1:0, 2: 2}
        for k, f_i in zip(
            a_track_names,
            range(len(a_track_names)),
        ):
            f_node_item = RoutingGraphNode(
                k,
                self.node_width,
                self.node_height,
                f_i,
            )
            self.node_dict[f_i] = f_node_item
            self.scene.addItem(f_node_item)
            f_x = self.node_width * f_i
            f_y = self.node_height * f_i
            if f_i != 0:
                self.scene.addLine(
                    0.0,
                    f_y,
                    self.graph_width,
                    f_y,
                    f_line_pen
                )
                self.scene.addLine(
                    f_x,
                    0.0,
                    f_x,
                    self.graph_height,
                    f_line_pen,
                )
            f_node_item.setPos(f_x, f_y)
            if f_i == 0 or f_i not in a_graph.graph:
                continue
            f_connections = [
                (x.output, x.index, x.conn_type)
                for x in a_graph.graph[f_i].values()
            ]
            for f_dest_pos, f_wire_index, conn_type in f_connections:
                if f_dest_pos < 0:
                    continue
                f_pen = pen_dict[conn_type]
                f_y_wire_offset = (
                    conn_type_y_pos[conn_type] * self.wire_width
                ) + self.wire_width
                if f_dest_pos > f_i:
                    f_src_x = f_x + self.node_width
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = (
                        (f_dest_pos - f_i - 1) * self.node_width
                    ) + (
                        (self.node_width * 0.5)
                        +
                        (self.wire_width_div2 * 0.5)
                    )
                    f_v_wire_x = f_src_x + f_wire_width
                    if conn_type == 1:  # sidechain
                        f_v_wire_x += self.wire_width
                    elif conn_type == 2:  # MIDI
                        f_v_wire_x -= self.wire_width
                    f_wire_height = ((f_dest_pos - f_i) *
                        self.node_height) - f_y_wire_offset
                    f_dest_y = f_src_y + f_wire_height
                    # horizontal wire
                    line = self.scene.addLine(
                        f_src_x,
                        f_src_y,
                        f_v_wire_x,
                        f_src_y,
                        f_pen,
                    )
                    line.setZValue(2000)
                    # vertical wire
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_src_y,
                        f_v_wire_x,
                        f_dest_y,
                        f_pen,
                    )
                    line.setZValue(2000)
                    # Arrow
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_dest_y,
                        f_v_wire_x - 4,
                        f_dest_y - 4,
                        f_pen,
                    )
                    line.setZValue(2700)
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_dest_y,
                        f_v_wire_x + 4,
                        f_dest_y - 4,
                        f_pen,
                    )
                    line.setZValue(2700)
                    # Connection circle
                    circle = QGraphicsEllipseItem(
                        f_v_wire_x - self.wire_width_div2,
                        f_src_y - self.wire_width_div2,
                        self.wire_width,
                        self.wire_width,
                    )
                    circle.setPen(f_pen)
                    circle.setToolTip(
                        (
                            f'from: {k}\n'
                            f'to:   {a_track_names[f_dest_pos]} \n'
                            f'type: {ROUTE_TYPES[conn_type]}'
                        ),
                        reformat=False,
                    )
                    circle.setZValue(2000)
                    self.scene.addItem(circle)
                else:
                    f_src_x = f_x
                    f_src_y = f_y + f_y_wire_offset
                    f_wire_width = ((f_i - f_dest_pos - 1) *
                        self.node_width) + (
                        (self.node_width * 0.5)
                        +
                        (self.wire_width_div2 * 0.5)
                    )
                    f_v_wire_x = f_src_x - f_wire_width
                    if conn_type == 1:  # sidechain
                        f_v_wire_x += self.wire_width
                    elif conn_type == 2:  # MIDI
                        f_v_wire_x -= self.wire_width
                    f_wire_height = ((f_i - f_dest_pos - 1) *
                        self.node_height) + f_y_wire_offset
                    f_dest_y = f_src_y - f_wire_height
                    # horizontal wire
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_src_y,
                        f_src_x,
                        f_src_y,
                        f_pen,
                    )
                    line.setZValue(2000)
                    # vertical wire
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_dest_y,
                        f_v_wire_x,
                        f_src_y,
                        f_pen,
                    )
                    line.setZValue(2000)
                    # Arrow
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_dest_y,
                        f_v_wire_x - 4,
                        f_dest_y + 4,
                        f_pen,
                    )
                    line.setZValue(2700)
                    line = self.scene.addLine(
                        f_v_wire_x,
                        f_dest_y,
                        f_v_wire_x + 4,
                        f_dest_y + 4,
                        f_pen,
                    )
                    line.setZValue(2700)

                    # Connection circle
                    circle = QGraphicsEllipseItem(
                        f_v_wire_x - self.wire_width_div2,
                        f_src_y - self.wire_width_div2,
                        self.wire_width,
                        self.wire_width,
                    )
                    circle.setPen(f_pen)
                    circle.setToolTip(
                        (
                            f'from: {k}\n'
                            f'to:   {a_track_names[f_dest_pos]} \n'
                            f'type: {ROUTE_TYPES[conn_type]}'
                        ),
                        reformat=False,
                    )
                    circle.setZValue(2000)
                    self.scene.addItem(circle)

        self.setUpdatesEnabled(True)
        self.update()


