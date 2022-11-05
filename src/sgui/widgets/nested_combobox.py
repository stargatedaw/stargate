from typing import Dict, Optional, Tuple
from sglib.lib.translate import _
from sgui.sgqt import QAction, QMenu, QPushButton

class NestedComboBox(QPushButton):
    def __init__(
        self,
        lookup: Dict[str, Tuple[int, Optional[str]]],
        tooltip=None,
    ):
        """
            lookup:
                A dictionary of str: (int, str) that maps names to UIDs
                and tooltips
            tooltip:  A tooltip for the button.
        """
        self._callbacks = []
        self.lookup = lookup
        self.reverse_lookup = {v[0]: k for k, v in lookup.items()}
        assert len(lookup) == len(self.reverse_lookup), (
            len(lookup),
            len(self.reverse_lookup),
            lookup,
            self.reverse_lookup,
        )
        QPushButton.__init__(self, _("None"))
        self.setObjectName("nested_combobox")
        self.menu = QMenu(self)
        self.setMenu(self.menu)
        self._index = 0
        self.menu.triggered.connect(self.action_triggered)
        self.setToolTip(tooltip)

    def currentIndex(self):
        return self._index

    def currentIndexChanged_connect(self, callback):
        self._callbacks.append(callback)

    def _emit_currentIndexChanged(self, index):
        for callback in self._callbacks:
            callback(index)

    def currentText(self):
        return self.reverse_lookup[self._index]

    def setCurrentIndex(self, a_index):
        a_index = int(a_index)
        self._index = a_index
        self.setText(self.reverse_lookup[a_index])
        self._emit_currentIndexChanged(a_index)

    def action_triggered(self, a_val):
        a_val = a_val.plugin_name
        self._index = self.lookup[a_val][0]
        self.setText(a_val)
        self._emit_currentIndexChanged(self._index)

    def addItems(self, items):
        """ Add entries to the dropdown

            items: [("Submenu Name" ["EntryName1", "EntryName2"])]
        """
        for v in items:
            if isinstance(v, str):
                action = QAction(v, self.menu)
                self.menu.addAction(action)
                tooltip = self.lookup[v][1]
                action.setToolTip(tooltip)
                action.plugin_name = v
            else:
                k, v = v
                menu = self.menu.addMenu(k)
                for name in v:
                    action = QAction(name, menu)
                    menu.addAction(action)
                    tooltip = self.lookup[name][1]
                    action.setToolTip(tooltip)
                    action.plugin_name = name

