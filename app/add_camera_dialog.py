from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class AddCameraDialog(QDialog):
    def __init__(self, parent=None, default_folder="", prefill=None, editing=False):
        super().__init__(parent)
        self.setWindowTitle("Editeaza camera" if editing else "Adauga camera")
        self.resize(440, 420)
        self.editing = editing

        self.name_edit = QLineEdit()
        self.rtsp_edit = QLineEdit()
        self.rtsp_edit.setPlaceholderText("rtsp://user:parola@192.168.1.50:554/stream1")

        self.ip_edit = QLineEdit()
        self.onvif_port_edit = QLineEdit("80")
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)

        detect_btn = QPushButton("Detecteaza stream (ONVIF)")
        detect_btn.clicked.connect(self.detect_stream)

        onvif_form = QFormLayout()
        onvif_form.addRow("IP camera:", self.ip_edit)
        onvif_form.addRow("Port ONVIF:", self.onvif_port_edit)
        onvif_form.addRow("Utilizator:", self.user_edit)
        onvif_form.addRow("Parola:", self.pass_edit)

        onvif_tab = QWidget()
        onvif_layout = QVBoxLayout(onvif_tab)
        onvif_layout.addLayout(onvif_form)
        onvif_layout.addWidget(detect_btn)
        onvif_layout.addStretch()

        manual_tab = QWidget()
        manual_form = QFormLayout(manual_tab)
        manual_form.addRow("RTSP URL:", self.rtsp_edit)

        self.tabs = QTabWidget()
        self.tabs.addTab(onvif_tab, "ONVIF (automat)")
        self.tabs.addTab(manual_tab, "RTSP manual")

        self.folder_edit = QLineEdit(default_folder)
        browse_btn = QPushButton("Alege / creeaza folder...")
        browse_btn.clicked.connect(self.choose_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(browse_btn)

        self.retention_value = QSpinBox()
        self.retention_value.setRange(1, 3650)
        self.retention_value.setValue(3)
        self.retention_unit = QComboBox()
        self.retention_unit.addItem("Ore", "hours")
        self.retention_unit.addItem("Zile", "days")
        self.retention_unit.setCurrentIndex(1)
        retention_row = QHBoxLayout()
        retention_row.addWidget(QLabel("Pastreaza inregistrarile timp de:"))
        retention_row.addWidget(self.retention_value)
        retention_row.addWidget(self.retention_unit)
        retention_row.addStretch()

        top_form = QFormLayout()
        top_form.addRow("Nume camera:", self.name_edit)

        ok_btn = QPushButton("Salveaza" if editing else "Adauga")
        ok_btn.clicked.connect(self.on_accept)
        cancel_btn = QPushButton("Renunta")
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(top_form)
        layout.addWidget(self.tabs)
        layout.addWidget(QLabel("Folder salvare inregistrari:"))
        layout.addLayout(folder_row)
        layout.addWidget(
            QLabel(
                "Inregistrarea porneste automat cand camera devine principala. Filmarile se "
                "salveaza in fisiere de maxim 1 ora, unul dupa altul, iar cele mai vechi se "
                "sterg automat pe masura ce se depaseste perioada de mai jos (ca la o camera auto)."
            )
        )
        layout.addLayout(retention_row)
        layout.addLayout(btn_row)

        self.result_rtsp_url = None
        self.result_name = None
        self.result_folder = None
        self.result_ip = ""
        self.result_onvif_port = 80
        self.result_onvif_username = ""
        self.result_onvif_password = ""
        self.result_retention_value = 3
        self.result_retention_unit = "days"

        if prefill:
            self.ip_edit.setText(prefill.get("ip", ""))
            self.name_edit.setText(prefill.get("name", ""))
            if prefill.get("onvif_port"):
                self.onvif_port_edit.setText(str(prefill["onvif_port"]))
            if prefill.get("onvif_username"):
                self.user_edit.setText(prefill["onvif_username"])
            if prefill.get("onvif_password"):
                self.pass_edit.setText(prefill["onvif_password"])
            if prefill.get("rtsp_url"):
                self.rtsp_edit.setText(prefill["rtsp_url"])
                self.tabs.setCurrentIndex(1)
            if prefill.get("folder"):
                self.folder_edit.setText(prefill["folder"])
            if prefill.get("retention_value") is not None:
                self.retention_value.setValue(prefill["retention_value"])
            if prefill.get("retention_unit"):
                idx = self.retention_unit.findData(prefill["retention_unit"])
                self.retention_unit.setCurrentIndex(max(idx, 0))

    def choose_folder(self):
        # Windows' native folder picker has a built-in "New Folder" button,
        # so this already lets the user create the destination folder themselves.
        folder = QFileDialog.getExistingDirectory(
            self, "Alege sau creeaza un folder", self.folder_edit.text() or ""
        )
        if folder:
            self.folder_edit.setText(folder)

    def detect_stream(self):
        from app.onvif_client import get_stream_uri

        ip = self.ip_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "Eroare", "Introdu IP-ul camerei.")
            return
        try:
            port = int(self.onvif_port_edit.text().strip() or "80")
        except ValueError:
            port = 80
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()

        try:
            uri, device_name = get_stream_uri(ip, port, username, password)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Eroare ONVIF",
                f"Nu am putut obtine stream-ul de la camera:\n{e}\n\n"
                "Poti introduce manual URL-ul RTSP in tab-ul 'RTSP manual'.",
            )
            return

        self.rtsp_edit.setText(uri)
        if not self.name_edit.text().strip():
            self.name_edit.setText(device_name)
        self.tabs.setCurrentIndex(1)
        QMessageBox.information(self, "Succes", "Stream detectat cu succes.")

    def on_accept(self):
        name = self.name_edit.text().strip()
        rtsp = self.rtsp_edit.text().strip()
        folder = self.folder_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Eroare", "Introdu un nume pentru camera.")
            return
        if not rtsp:
            QMessageBox.warning(
                self, "Eroare", "Introdu URL-ul RTSP sau detecteaza-l automat prin ONVIF."
            )
            return
        if not folder:
            QMessageBox.warning(self, "Eroare", "Alege un folder de salvare.")
            return

        self.result_name = name
        self.result_rtsp_url = rtsp
        self.result_folder = folder
        self.result_ip = self.ip_edit.text().strip()
        try:
            self.result_onvif_port = int(self.onvif_port_edit.text().strip() or "80")
        except ValueError:
            self.result_onvif_port = 80
        self.result_onvif_username = self.user_edit.text().strip()
        self.result_onvif_password = self.pass_edit.text()
        self.result_retention_value = self.retention_value.value()
        self.result_retention_unit = self.retention_unit.currentData()
        self.accept()
