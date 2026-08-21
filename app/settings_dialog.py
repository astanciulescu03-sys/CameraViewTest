from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.add_camera_dialog import AddCameraDialog
from app.camera import Camera
from app.scan_dialog import ScanDialog


def _retention_label(cam):
    unit = "ora" if cam.retention_unit == "hours" else "zile"
    return f"{cam.retention_value} {unit}"


class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.setWindowTitle("Setari CameraX")
        self.resize(520, 560)
        self.config = config

        # --- Camere ---
        self.camera_list = QListWidget()

        scan_btn = QPushButton("Scaneaza reteaua")
        scan_btn.clicked.connect(self.open_scan_dialog)
        add_btn = QPushButton("Adauga camera manual")
        add_btn.clicked.connect(self.open_add_dialog)
        edit_btn = QPushButton("Editeaza camera")
        edit_btn.clicked.connect(self.edit_selected_camera)
        primary_btn = QPushButton("Foloseste ca principala")
        primary_btn.clicked.connect(self.set_primary)
        remove_btn = QPushButton("Sterge camera")
        remove_btn.clicked.connect(self.remove_selected_camera)

        cam_btn_row1 = QHBoxLayout()
        cam_btn_row1.addWidget(scan_btn)
        cam_btn_row1.addWidget(add_btn)
        cam_btn_row2 = QHBoxLayout()
        cam_btn_row2.addWidget(edit_btn)
        cam_btn_row2.addWidget(primary_btn)
        cam_btn_row2.addWidget(remove_btn)

        camera_group = QGroupBox("Camere")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.addWidget(
            QLabel(
                "Camera principala se deschide automat la pornirea aplicatiei si "
                "inregistreaza continuu (fisiere de maxim 1 ora, cele mai vechi se sterg "
                "automat dupa perioada de pastrare a fiecarei camere)."
            )
        )
        camera_layout.addWidget(self.camera_list)
        camera_layout.addLayout(cam_btn_row1)
        camera_layout.addLayout(cam_btn_row2)

        # --- Overlay data/ora ---
        self.overlay_checkbox = QCheckBox("Afiseaza data si ora pe imagine (overlay separat)")
        self.overlay_checkbox.setChecked(config.overlay_enabled)
        self.overlay_position = QComboBox()
        self.overlay_position.addItem("Stanga-Sus", "top-left")
        self.overlay_position.addItem("Dreapta-Sus", "top-right")
        self.overlay_position.addItem("Stanga-Jos", "bottom-left")
        self.overlay_position.addItem("Dreapta-Jos", "bottom-right")
        self.overlay_position.setCurrentIndex(
            max(self.overlay_position.findData(config.overlay_position), 0)
        )

        overlay_group = QGroupBox("Overlay data/ora")
        overlay_layout = QFormLayout(overlay_group)
        overlay_layout.addRow(self.overlay_checkbox)
        overlay_layout.addRow("Pozitie:", self.overlay_position)

        close_btn = QPushButton("Inchide")
        close_btn.clicked.connect(self.on_close)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(camera_group)
        layout.addWidget(overlay_group)
        layout.addLayout(btn_row)

        self.refresh_camera_list()

    def refresh_camera_list(self):
        self.camera_list.clear()
        for cam in self.config.cameras:
            label = f"{cam.name}  -  pastreaza {_retention_label(cam)}"
            if cam.name == self.config.active_camera_name:
                label += "  (principala)"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, cam)
            self.camera_list.addItem(item)

    def current_camera(self):
        item = self.camera_list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def open_add_dialog(self):
        dlg = AddCameraDialog(self, default_folder=self.config.default_record_folder)
        if dlg.exec():
            cam = Camera(
                name=dlg.result_name,
                rtsp_url=dlg.result_rtsp_url,
                ip=dlg.result_ip,
                record_folder=dlg.result_folder,
                retention_value=dlg.result_retention_value,
                retention_unit=dlg.result_retention_unit,
            )
            self.config.add_camera(cam)
            self.refresh_camera_list()

    def edit_selected_camera(self):
        cam = self.current_camera()
        if not cam:
            return
        prefill = {
            "name": cam.name,
            "ip": cam.ip,
            "rtsp_url": cam.rtsp_url,
            "folder": cam.record_folder,
            "retention_value": cam.retention_value,
            "retention_unit": cam.retention_unit,
        }
        dlg = AddCameraDialog(
            self, default_folder=self.config.default_record_folder, prefill=prefill, editing=True
        )
        if dlg.exec():
            cam.name = dlg.result_name
            cam.rtsp_url = dlg.result_rtsp_url
            cam.ip = dlg.result_ip
            cam.record_folder = dlg.result_folder
            cam.retention_value = dlg.result_retention_value
            cam.retention_unit = dlg.result_retention_unit
            self.config.save()
            self.refresh_camera_list()

    def open_scan_dialog(self):
        dlg = ScanDialog(self)

        def on_selected(data):
            prefill = {"ip": data.get("ip", "")}
            if data["type"] == "rtsp":
                prefill["rtsp_url"] = f"rtsp://{data['ip']}:554/"
            add_dlg = AddCameraDialog(
                self, default_folder=self.config.default_record_folder, prefill=prefill
            )
            if data["type"] == "onvif":
                add_dlg.ip_edit.setText(data["ip"])
                add_dlg.onvif_port_edit.setText(str(data.get("port", 80)))
            if add_dlg.exec():
                cam = Camera(
                    name=add_dlg.result_name,
                    rtsp_url=add_dlg.result_rtsp_url,
                    ip=add_dlg.result_ip,
                    record_folder=add_dlg.result_folder,
                    retention_value=add_dlg.result_retention_value,
                    retention_unit=add_dlg.result_retention_unit,
                )
                self.config.add_camera(cam)
                self.refresh_camera_list()

        dlg.camera_selected.connect(on_selected)
        dlg.exec()

    def remove_selected_camera(self):
        cam = self.current_camera()
        if not cam:
            return
        confirm = QMessageBox.question(self, "Confirma", f"Stergi camera '{cam.name}'?")
        if confirm != QMessageBox.Yes:
            return
        self.config.remove_camera(cam)
        self.refresh_camera_list()

    def set_primary(self):
        cam = self.current_camera()
        if not cam:
            return
        self.config.active_camera_name = cam.name
        self.config.save()
        self.refresh_camera_list()

    def on_close(self):
        self.config.overlay_enabled = self.overlay_checkbox.isChecked()
        self.config.overlay_position = self.overlay_position.currentData()
        self.config.save()
        self.accept()
