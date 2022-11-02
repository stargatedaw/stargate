from sgui.sgqt import QTextEdit


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
        self.widget = QTextEdit(parent)
        self.widget.setToolTip(
            'Project notes.  Keep notes about your project here, anything '
            'that is useful, for example: lyrics, scales, ideas'
        )
        self.widget.setAcceptRichText(False)
        self.widget.leaveEvent = self.on_edit_notes

    def load(self):
        self.widget.setText(
            self._load(),
        )

    def on_edit_notes(self, a_event=None):
        QTextEdit.leaveEvent(self.widget, a_event)
        self._save(
            self.widget.toPlainText(),
        )

