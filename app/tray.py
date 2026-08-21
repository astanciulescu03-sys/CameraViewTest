from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, icon: QIcon):
        super().__init__(icon, main_window)
        self.main_window = main_window
        self.setToolTip("CameraX - Monitorizare camere IP")

        menu = QMenu()
        open_action = menu.addAction("Deschide CameraX")
        open_action.triggered.connect(self.show_main_window)
        settings_action = menu.addAction("Setari")
        settings_action.triggered.connect(self.open_settings)
        menu.addSeparator()
        quit_action = menu.addAction("Iesire")
        quit_action.triggered.connect(main_window.quit_app)

        self.setContextMenu(menu)
        self.activated.connect(self.on_activated)

    def on_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_main_window()

    def show_main_window(self):
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def open_settings(self):
        self.show_main_window()
        self.main_window.open_settings()

    def notify_minimized(self):
        self.showMessage(
            "CameraX ruleaza in fundal",
            "Aplicatia continua sa filmeze/inregistreze in system tray. "
            "Click dreapta pe icon pentru optiuni.",
            QSystemTrayIcon.Information,
            4000,
        )
