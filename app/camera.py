from dataclasses import dataclass


@dataclass
class Camera:
    name: str
    rtsp_url: str
    ip: str = ""
    onvif_port: int = 80
    onvif_username: str = ""
    onvif_password: str = ""
    record_folder: str = ""
    retention_value: int = 3
    retention_unit: str = "days"  # "hours" or "days"

    def to_dict(self):
        return {
            "name": self.name,
            "rtsp_url": self.rtsp_url,
            "ip": self.ip,
            "onvif_port": self.onvif_port,
            "onvif_username": self.onvif_username,
            "onvif_password": self.onvif_password,
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
            onvif_port=d.get("onvif_port", 80),
            onvif_username=d.get("onvif_username", ""),
            onvif_password=d.get("onvif_password", ""),
            record_folder=d.get("record_folder", ""),
            retention_value=d.get("retention_value", 3),
            retention_unit=d.get("retention_unit", "days"),
        )
