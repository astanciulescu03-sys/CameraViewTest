from datetime import datetime, timedelta
from pathlib import Path


def cleanup_old_recordings(folder, value, unit):
    """Deletes recorded .mp4 files older than the configured retention threshold."""
    if not folder or not value or value <= 0:
        return
    folder_path = Path(folder)
    if not folder_path.exists():
        return

    delta = timedelta(days=value) if unit == "days" else timedelta(hours=value)
    cutoff = datetime.now() - delta

    for f in folder_path.glob("*.mp4"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                f.unlink()
        except OSError:
            pass
