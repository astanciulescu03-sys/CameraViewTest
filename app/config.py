import json
from pathlib import Path

from app.camera import Camera

CONFIG_DIR = Path.home() / ".camerax"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self):
        self.cameras = []
        self.default_record_folder = str(Path.home() / "Videos" / "CameraX")
        self.active_camera_name = None
        self.overlay_enabled = True
        self.overlay_position = "bottom-right"
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                self.cameras = [Camera.from_dict(c) for c in data.get("cameras", [])]
                self.default_record_folder = data.get(
                    "default_record_folder", self.default_record_folder
                )
                self.active_camera_name = data.get("active_camera_name")
                self.overlay_enabled = data.get("overlay_enabled", self.overlay_enabled)
                self.overlay_position = data.get("overlay_position", self.overlay_position)
            except Exception:
                self.cameras = []

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "cameras": [c.to_dict() for c in self.cameras],
            "default_record_folder": self.default_record_folder,
            "active_camera_name": self.active_camera_name,
            "overlay_enabled": self.overlay_enabled,
            "overlay_position": self.overlay_position,
        }
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_camera(self, camera: Camera):
        self.cameras.append(camera)
        if not self.active_camera_name:
            self.active_camera_name = camera.name
        self.save()

    def remove_camera(self, camera: Camera):
        self.cameras = [c for c in self.cameras if c is not camera]
        if self.active_camera_name == camera.name:
            self.active_camera_name = self.cameras[0].name if self.cameras else None
        self.save()

    def get_active_camera(self):
        return next((c for c in self.cameras if c.name == self.active_camera_name), None)
