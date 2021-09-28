from sglib.lib.translate import _
from sgui.sgqt import QMenu, QPushButton

class NestedComboBox(QPushButton):
    def __init__(
        self,
        callback,
        lookup: dict,
    ):
        """
            callback: Callable with no args to call when the value changes
            lookup:   A dictionary of str: int that maps names to UIDs
        """
        self.callback = callback
        self.lookup = lookup
        self.reverse_lookup = {v: k for k, v in lookup.items()}
        assert len(lookup) == len(self.reverse_lookup), (
            len(lookup),
            len(self.reverse_lookup),
            lookup,
            self.reverse_lookup,
        )
        QPushButton.__init__(self, _("None"))
        self.setObjectName("nested_combobox")
        self.menu = QMenu()
        self.setMenu(self.menu)
        f_action = self.menu.addAction("None")
        f_action.plugin_name = "None"
        self._index = 0
        self.menu.triggered.connect(self.action_triggered)

    def currentIndex(self):
        return self._index

    def currentText(self):
        return self.reverse_lookup[self._index]

    def setCurrentIndex(self, a_index):
        a_index = int(a_index)
        self._index = a_index
        self.setText(self.reverse_lookup[a_index])

    def action_triggered(self, a_val):
        a_val = a_val.plugin_name
        self._index = self.lookup[a_val]
        self.setText(a_val)
        self.callback()

    def addItems(self, items):
        """ Add entries to the dropdown

            items: [("Submenu Name" ["EntryName1", "EntryName2"])]
        """
        for k, v in items:
            menu = self.menu.addMenu(k)
            for name in v:
                action = menu.addAction(name)
                action.plugin_name = name

