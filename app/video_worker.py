import os
import time
from datetime import datetime
from pathlib import Path

# Force RTSP over TCP instead of OpenCV/FFmpeg's default UDP. Over UDP, lost
# packets leave FFmpeg unable to reconstruct frames, which shows up as a
# connected stream that never errors but only ever renders a black frame.
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from app.overlay import draw_datetime_overlay
from app.retention import cleanup_old_recordings

SEGMENT_SECONDS = 3600  # dashcam-style loop: max 1h per file, then roll to a new one


class VideoWorker(QThread):
    frame_ready = Signal(QImage)
    error = Signal(str)
    connected = Signal()
    disconnected = Signal()

    def __init__(self, rtsp_url, name="camera"):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.name = name
        self._running = False
        self._recording = False
        self._writer = None
        self._segment_start = None
        self._record_folder = None
        self._retention_value = 3
        self._retention_unit = "days"
        self._fps = 20.0
        self.overlay_enabled = False
        self.overlay_position = "bottom-right"

    def set_overlay(self, enabled, position="bottom-right"):
        self.overlay_enabled = enabled
        self.overlay_position = position

    def start_recording(self, folder, retention_value=3, retention_unit="days"):
        Path(folder).mkdir(parents=True, exist_ok=True)
        self._record_folder = folder
        self._retention_value = retention_value
        self._retention_unit = retention_unit
        self._recording = True

    def stop_recording(self):
        self._recording = False
        if self._writer is not None:
            self._writer.release()
            self._writer = None

    def is_recording(self):
        return self._recording

    def stop(self):
        self._running = False

    def _open_new_segment(self, w, h):
        fname = datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{self.name}.mp4"
        path = str(Path(self._record_folder) / fname)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(path, fourcc, self._fps, (w, h))
        if not writer.isOpened():
            self.error.emit(
                f"Nu am putut porni inregistrarea pentru {self.name} in "
                f"{self._record_folder} (fisierul nu s-a putut crea)."
            )
            self._recording = False
            self._writer = None
            return
        self._writer = writer
        self._segment_start = time.monotonic()

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        # Without these, a stalled connection (socket open, no more data) blocks
        # cap.read() forever: the thread never notices stop() was called, and
        # if the app then exits/reconnects, Qt can tear down a QThread that is
        # still running underneath, which crashes the process.
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
        if not cap.isOpened():
            self.error.emit(f"Nu m-am putut conecta la {self.name}.")
            self.disconnected.emit()
            return

        self.connected.emit()
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps and fps > 1:
            self._fps = fps

        while self._running:
            try:
                ok, frame = cap.read()
                if not ok or frame is None:
                    self.error.emit(f"S-a pierdut conexiunea la {self.name}.")
                    break

                if self.overlay_enabled:
                    frame = draw_datetime_overlay(frame, self.overlay_position)

                h, w = frame.shape[:2]

                if self._recording:
                    if self._writer is None:
                        self._open_new_segment(w, h)
                    elif time.monotonic() - self._segment_start >= SEGMENT_SECONDS:
                        # Close this segment and immediately start the next one, back-to-back.
                        self._writer.release()
                        self._writer = None
                        cleanup_old_recordings(
                            self._record_folder, self._retention_value, self._retention_unit
                        )
                        self._open_new_segment(w, h)
                    self._writer.write(frame)
                elif self._writer is not None:
                    self._writer.release()
                    self._writer = None

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                qimg = QImage(rgb.data, w, h, rgb.strides[0], QImage.Format_RGB888).copy()
                self.frame_ready.emit(qimg)
            except Exception as e:
                self.error.emit(f"Eroare la {self.name}: {e}")
                break

        if self._writer is not None:
            self._writer.release()
            self._writer = None
        cap.release()
        self.disconnected.emit()
