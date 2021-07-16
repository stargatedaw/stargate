from sglib.lib.translate import _
from sgui.sgqt import *


class preset_browser_widget:
    """ To eventually replace the legacy preset system """
    def __init__(
        self,
        a_plugin_name,
        a_configure_dict=None,
        a_reconfigure_callback=None,
    ):
        self.plugin_name = str(a_plugin_name)
        self.configure_dict = a_configure_dict
        self.reconfigure_callback = a_reconfigure_callback
        self.widget = QWidget()
        self.widget.setObjectName("plugin_groupbox")
        self.main_vlayout = QVBoxLayout(self.widget)
        self.hlayout1 = QHBoxLayout()
        self.menu_button = QPushButton(_("Menu"))
        self.hlayout1.addWidget(self.menu_button)
        self.menu = QMenu(self.menu_button)
        self.menu_button.setMenu(self.menu)
        self.reload_action = self.menu.addAction(_("Reload"))
        self.reload_action.triggered.connect(self.on_reload)
        self.main_vlayout.addLayout(self.hlayout1)
        self.hlayout2 = QHBoxLayout()
        self.main_vlayout.addLayout(self.hlayout2)
        self.tag_list = QListWidget()
        self.hlayout2.addWidget(self.tag_list)

    def on_reload(self):
        pass

