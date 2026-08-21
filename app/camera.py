from dataclasses import dataclass


@dataclass
class Camera:
    name: str
    rtsp_url: str
    ip: str = ""
    record_folder: str = ""
    retention_value: int = 3
    retention_unit: str = "days"  # "hours" or "days"

    def to_dict(self):
        return {
            "name": self.name,
            "rtsp_url": self.rtsp_url,
            "ip": self.ip,
            "record_folder": self.record_folder,
            "retention_value": self.retention_value,
            "retention_unit": self.retention_unit,
        }

    @staticmethod
    def from_dict(d):
        return Camera(
            name=d.get("name", ""),
            rtsp_url=d.get("rtsp_url", ""),
            ip=d.get("ip", ""),
            record_folder=d.get("record_folder", ""),
            retention_value=d.get("retention_value", 3),
            retention_unit=d.get("retention_unit", "days"),
        )
