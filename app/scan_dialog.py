from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from app.onvif_client import xaddr_to_ip_port
from app.scanner import discover_onvif, get_local_subnet, scan_subnet_for_rtsp


class ScanWorker(QThread):
    onvif_found = Signal(dict)
    rtsp_found = Signal(str)
    progress = Signal(int, int)
    finished_scan = Signal()

    def run(self):
        for device in discover_onvif():
            self.onvif_found.emit(device)

        _, network = get_local_subnet()

        def progress_cb(done, total):
            self.progress.emit(done, total)

        for ip in scan_subnet_for_rtsp(network=network, progress_cb=progress_cb):
            self.rtsp_found.emit(ip)

        self.finished_scan.emit()


class ScanDialog(QDialog):
    camera_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scaneaza reteaua dupa camere IP")
        self.resize(500, 420)

        self.status_label = QLabel("Se scaneaza reteaua...")
        self.progress = QProgressBar()
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_chosen)

        add_btn = QPushButton("Adauga camera selectata")
        add_btn.clicked.connect(self.on_add_clicked)
        close_btn = QPushButton("Inchide")
        close_btn.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(QLabel("Dubla-click sau selecteaza si apasa 'Adauga camera selectata':"))
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_row)

        self.worker = ScanWorker()
        self.worker.onvif_found.connect(self.add_onvif_result)
        self.worker.rtsp_found.connect(self.add_rtsp_result)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.start()

    def add_onvif_result(self, device):
        ip, port = xaddr_to_ip_port(device["xaddr"])
        item = QListWidgetItem(f"[ONVIF] {ip}  ({device['xaddr']})")
        item.setData(1000, {"type": "onvif", "ip": ip, "port": port})
        self.list_widget.addItem(item)

    def add_rtsp_result(self, ip):
        item = QListWidgetItem(f"[Port RTSP 554 deschis] {ip}")
        item.setData(1000, {"type": "rtsp", "ip": ip})
        self.list_widget.addItem(item)

    def update_progress(self, done, total):
        self.progress.setMaximum(max(total, 1))
        self.progress.setValue(done)
        self.status_label.setText(f"Scanez subreteaua locala... {done}/{total}")

    def on_finished(self):
        self.status_label.setText(f"Scanare finalizata. {self.list_widget.count()} rezultate gasite.")

    def on_item_chosen(self, item):
        self.on_add_clicked()

    def on_add_clicked(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        self.camera_selected.emit(item.data(1000))
        self.accept()

    def closeEvent(self, event):
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        event.accept()
