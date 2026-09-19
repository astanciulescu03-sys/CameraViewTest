import sys

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CameraX")
    app.setQuitOnLastWindowClosed(False)  # keep running in the system tray

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.warning(
            None,
            "CameraX",
            "Zona de notificari (system tray) nu este disponibila. "
            "Aplicatia va porni normal, dar nu va putea rula minimizata in tray.",
        )

    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
