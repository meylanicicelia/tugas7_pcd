import json
import os

DEFAULT_CFG = os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_config(path=None):
    with open(path or DEFAULT_CFG, encoding="utf-8") as f:
        return json.load(f)


def crop(img, roi):
    h, w = img.shape[:2]
    x, y, rw, rh = roi
    x0, y0 = int(x * w), int(y * h)
    x1, y1 = int((x + rw) * w), int((y + rh) * h)
    return img[y0:y1, x0:x1]
