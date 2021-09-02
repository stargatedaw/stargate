from sgui.sgqt import *

__all__ = [
    'get_screws',
]

def get_screws() -> QVBoxLayout:
    layout = QVBoxLayout()
    top = QLabel("")
    bottom = QLabel("")
    for screw in (top, bottom):
        screw.setObjectName("screw")
        screw.setFixedHeight(24)
        screw.setFixedWidth(24)
    layout.addWidget(top)
    layout.addItem(
        QSpacerItem(1, 1, vPolicy=QSizePolicy.Policy.Expanding),
    )
    layout.addWidget(bottom)
    return layout
