"""Koreksi orientasi otomatis (0/90/180/270) berdasarkan kata kunci hasil OCR."""
import re
import cv2
import pytesseract

KEYWORDS = re.compile(r"universitas|ijazah|nomor|memberikan|fakultas|program|studi|rektor|dekan|lahir", re.I)
ROTS = {0: None, 90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}


def _rotate(img, angle):
    return img if ROTS[angle] is None else cv2.rotate(img, ROTS[angle])


def auto_rotate(img):
    """Return (img_tegak, sudut_putar_searah_jarum_jam)."""
    scale = 1200 / max(img.shape[:2])
    small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    best, best_score = 0, -1
    for angle in ROTS:
        g = cv2.cvtColor(_rotate(small, angle), cv2.COLOR_BGR2GRAY)
        txt = pytesseract.image_to_string(g, config="--psm 11")
        score = len(KEYWORDS.findall(txt))
        if score > best_score:
            best, best_score = angle, score
    return _rotate(img, best), best
