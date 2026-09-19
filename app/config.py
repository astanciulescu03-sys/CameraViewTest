import json
from pathlib import Path

from app.camera import Camera

CONFIG_DIR = Path.home() / ".camerax"
CONFIG_FILE = CONFIG_DIR / "config.json"
BACKUP_FILE = CONFIG_DIR / "config.json.bak"


class Config:
    def __init__(self):
        self.cameras = []
        self.default_record_folder = str(Path.home() / "Videos" / "CameraX")
        self.active_camera_name = None
        self.overlay_enabled = True
        self.overlay_position = "bottom-right"
        self.load()

    def _apply(self, data):
        self.cameras = [Camera.from_dict(c) for c in data.get("cameras", [])]
        self.default_record_folder = data.get(
            "default_record_folder", self.default_record_folder
        )
        self.active_camera_name = data.get("active_camera_name")
        self.overlay_enabled = data.get("overlay_enabled", self.overlay_enabled)
        self.overlay_position = data.get("overlay_position", self.overlay_position)

    def load(self):
        # Try the main file first, then fall back to the last known-good backup
        # (e.g. a power loss mid-save left config.json truncated/corrupted).
        for path in (CONFIG_FILE, BACKUP_FILE):
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                self._apply(data)
                return
            except Exception:
                continue

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "cameras": [c.to_dict() for c in self.cameras],
            "default_record_folder": self.default_record_folder,
            "active_camera_name": self.active_camera_name,
            "overlay_enabled": self.overlay_enabled,
            "overlay_position": self.overlay_position,
        }
        text = json.dumps(data, indent=2, ensure_ascii=False)

        # Keep the last good config as a backup before touching the real file.
        if CONFIG_FILE.exists():
            try:
                CONFIG_FILE.replace(BACKUP_FILE)
            except OSError:
                pass

        # Write to a temp file and rename it into place - a rename is a single
        # filesystem operation, so a power loss mid-save can't leave config.json
        # half-written/truncated the way writing to it directly could.
        tmp_file = CONFIG_FILE.with_suffix(".tmp")
        tmp_file.write_text(text, encoding="utf-8")
        tmp_file.replace(CONFIG_FILE)

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
