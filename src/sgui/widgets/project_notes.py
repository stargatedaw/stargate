from sgui.sgqt import QtWidgets


class ProjectNotes:
    def __init__(
        self,
        parent,
        _load,
        _save,
    ):
        """
            @_load: function():str, A function to load saved notes
            @_save: function(str), A function to save notes to disk
        """
        self._save = _save
        self._load = _load
        self.widget = QtWidgets.QTextEdit(parent)
        self.widget.setAcceptRichText(False)
        self.widget.leaveEvent = self.on_edit_notes

    def load(self):
        self.widget.setText(
            self._load(),
        )

    def on_edit_notes(self, a_event=None):
        QtWidgets.QTextEdit.leaveEvent(self.widget, a_event)
        self._save(
            self.widget.toPlainText(),
        )

