from sglib.lib.translate import _
from sgui.sgqt import *
import os


class file_select_widget:
    def __init__(
        self,
        a_load_callback,
    ):
        """
            @a_load_callback: function to call when loading that accepts a
                              single argument of [list of paths,...]
        """
        self.load_callback = a_load_callback
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.clear_button = QPushButton(_("Clear"))
        self.clear_button.setMaximumWidth(60)
        self.copy_to_clipboard = QPushButton(_("Copy"))
        self.copy_to_clipboard.setToolTip(
            "Copy file path to the system clipboard"
        )
        self.copy_to_clipboard.pressed.connect(self.copy_to_clipboard_pressed)
        self.copy_to_clipboard.setMaximumWidth(60)
        self.paste_from_clipboard = QPushButton(_("Paste"))
        self.paste_from_clipboard.setToolTip(
            "Paste file path from the system clipboard"
        )
        self.paste_from_clipboard.pressed.connect(
            self.paste_from_clipboard_pressed)
        self.paste_from_clipboard.setMaximumWidth(60)
        self.reload_button = QPushButton(_("Reload"))
        self.reload_button.setToolTip('Reload the current directory')
        self.reload_button.setMaximumWidth(60)
        self.file_path = QLineEdit()
        self.file_path.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.file_path.setReadOnly(True)
        self.file_path.setMinimumWidth(210)
        self.last_directory = ("")
        self.layout.addWidget(self.file_path)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.copy_to_clipboard)
        self.layout.addWidget(self.paste_from_clipboard)
        self.layout.addWidget(self.reload_button)


    def clear_button_pressed(self):
        self.file_path.setText("")

    def get_file(self):
        return self.file_path.text()

    def set_file(self, a_file):
        self.file_path.setText(str(a_file))

    def copy_to_clipboard_pressed(self):
        f_text = str(self.file_path.text())
        if f_text != "":
            f_clipboard = QApplication.clipboard()
            f_clipboard.setText(f_text)

    def paste_from_clipboard_pressed(self):
        f_clipboard = QApplication.clipboard()
        f_text = f_clipboard.text()
        if f_text is None:
            QMessageBox.warning(
                self.paste_from_clipboard, _("Error"),
                _("No file path in the system clipboard."))
        else:
            f_text = str(f_text).strip()
            if os.path.isfile(f_text):
                self.set_file(f_text)
                self.load_callback([f_text])
            else:
                #Don't show more than 100 chars just in case somebody had an
                #entire book copied to the clipboard
                f_str = f_text[100:]
                QMessageBox.warning(
                    self.paste_from_clipboard, _("Error"),
                    _("{} does not exist.").format(f_str))


