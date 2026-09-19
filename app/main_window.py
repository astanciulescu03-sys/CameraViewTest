from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import Config
from app.resources import resource_path
from app.retention import cleanup_old_recordings
from app.settings_dialog import SettingsDialog
from app.tray import TrayIcon
from app.video_worker import VideoWorker

CLEANUP_INTERVAL_MS = 60 * 60 * 1000  # re-check retention thresholds hourly
RECONNECT_DELAY_MS = 5000  # retry a dropped feed automatically, unattended-camera style


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CameraX")
        self.resize(1000, 650)
        self.setWindowIcon(QIcon(resource_path("assets/icon.ico")))

        self.config = Config()
        self.worker = None
        self.active_camera = None
        self._quitting = False
        self._tray_notice_shown = False

        self.camera_name_label = QLabel("Nicio camera configurata")
        self.camera_name_label.setStyleSheet("font-weight: bold;")

        self.status_label = QLabel("")

        self.record_btn = QPushButton("Start inregistrare")
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setEnabled(False)

        settings_btn = QPushButton("⚙ Setari")
        settings_btn.clicked.connect(self.open_settings)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.camera_name_label)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)
        top_bar.addWidget(self.record_btn)
        top_bar.addWidget(settings_btn)

        self.video_label = QLabel("Adauga o camera din Setari pentru a incepe.")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setMinimumSize(640, 400)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(self.video_label, stretch=1)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.run_retention_cleanup)
        self.cleanup_timer.start(CLEANUP_INTERVAL_MS)

        self.tray = TrayIcon(self, QIcon(resource_path("assets/icon.ico")))
        self.tray.show()

        self.load_active_camera()
        self.run_retention_cleanup()

    # ---------- startup / active camera ----------

    def load_active_camera(self):
        cam = self.config.get_active_camera()
        if cam is None and self.config.cameras:
            cam = self.config.cameras[0]
            self.config.active_camera_name = cam.name
            self.config.save()
        self.set_active_camera(cam, autostart=True)

    def set_active_camera(self, cam, autostart=False):
        self.stop_feed()
        self.active_camera = cam
        if cam is None:
            self.camera_name_label.setText("Nicio camera configurata")
            self.video_label.setText("Adauga o camera din Setari pentru a incepe.")
            self.record_btn.setEnabled(False)
            return
        self.camera_name_label.setText(cam.name)
        self.record_btn.setEnabled(True)
        self.record_btn.setText("Start inregistrare")
        if autostart:
            self.start_feed()

    # ---------- feed / recording controls ----------

    def start_feed(self):
        if not self.active_camera or self.worker is not None:
            return
        worker = VideoWorker(self.active_camera.rtsp_url, name=self.active_camera.name)
        worker.set_overlay(self.config.overlay_enabled, self.config.overlay_position)
        worker.frame_ready.connect(self.on_frame)
        worker.error.connect(lambda msg: self.status_label.setText(msg))
        worker.disconnected.connect(self.on_worker_disconnected)
        self.worker = worker
        worker.start()

        # Recording starts automatically as soon as the camera has a folder set
        # (always true - it's required when adding a camera), looping in 1h segments.
        if self.active_camera.record_folder:
            worker.start_recording(
                self.active_camera.record_folder,
                self.active_camera.retention_value,
                self.active_camera.retention_unit,
            )
            self.record_btn.setText("Opreste inregistrarea")
            self.status_label.setText("INREGISTREAZA")
        else:
            self.record_btn.setText("Start inregistrare")
            self.status_label.setText("LIVE")

    def stop_feed(self):
        if self.worker is None:
            return
        worker = self.worker
        self.worker = None
        worker.stop()
        worker.wait(4000)
        self.video_label.setPixmap(QPixmap())
        self.status_label.setText("")

    def toggle_recording(self):
        if not self.worker or not self.active_camera:
            return
        if self.worker.is_recording():
            self.worker.stop_recording()
            self.record_btn.setText("Start inregistrare")
        else:
            folder = self.active_camera.record_folder or self.config.default_record_folder
            self.worker.start_recording(
                folder, self.active_camera.retention_value, self.active_camera.retention_unit
            )
            self.record_btn.setText("Opreste inregistrarea")
        self.status_label.setText("INREGISTREAZA" if self.worker.is_recording() else "LIVE")

    def on_frame(self, qimage):
        pixmap = QPixmap.fromImage(qimage).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)

    def on_worker_disconnected(self):
        self.worker = None
        self.status_label.setText("Deconectat - se reconecteaza...")
        self.record_btn.setText("Start inregistrare")
        if self.active_camera is not None and not self._quitting:
            QTimer.singleShot(RECONNECT_DELAY_MS, self.attempt_reconnect)

    def attempt_reconnect(self):
        if self._quitting or self.active_camera is None or self.worker is not None:
            return
        self.start_feed()

    # ---------- settings ----------

    def open_settings(self):
        dlg = SettingsDialog(self, self.config)
        dlg.exec()

        if self.worker:
            self.worker.set_overlay(self.config.overlay_enabled, self.config.overlay_position)

        new_active = self.config.get_active_camera()
        current_name = self.active_camera.name if self.active_camera else None
        new_name = new_active.name if new_active else None
        if new_name != current_name:
            self.set_active_camera(new_active, autostart=True)

        self.run_retention_cleanup()

    def run_retention_cleanup(self):
        for cam in self.config.cameras:
            folder = cam.record_folder or self.config.default_record_folder
            cleanup_old_recordings(folder, cam.retention_value, cam.retention_unit)

    def closeEvent(self, event):
        if self._quitting:
            self.stop_feed()
            self.tray.hide()
            event.accept()
            return

        # Closing the window just minimizes to tray; the feed/recording keep running.
        event.ignore()
        self.hide()
        if not self._tray_notice_shown:
            self.tray.notify_minimized()
            self._tray_notice_shown = True

    def quit_app(self):
        self._quitting = True
        self.close()
        QApplication.quit()
