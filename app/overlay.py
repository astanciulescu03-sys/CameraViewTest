from datetime import datetime

import cv2


def draw_datetime_overlay(frame, position="bottom-right"):
    """Burns the current system date/time onto a frame, separate from any
    on-screen display the camera itself might already embed in the stream."""
    h, w = frame.shape[:2]
    text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = max(0.5, w / 1280)
    thickness = max(1, int(scale * 2))
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    margin = 10

    if position == "top-left":
        x, y = margin, margin + th
    elif position == "top-right":
        x, y = w - tw - margin, margin + th
    elif position == "bottom-left":
        x, y = margin, h - margin
    else:  # bottom-right
        x, y = w - tw - margin, h - margin

    cv2.putText(frame, text, (x + 1, y + 1), font, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return frame
