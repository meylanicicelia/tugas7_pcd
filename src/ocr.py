"""OCR nomor ijazah dengan Tesseract."""
import re
import cv2
import pytesseract
from . import enhance

TESS_CFG = "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789"


def read_number(gray_roi, method="clahe_unsharp", pattern=r"\d{12,16}"):
    """Return (nomor_terformat, teks_mentah)."""
    roi = cv2.resize(gray_roi, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
    roi = enhance.apply(roi, method)
    roi = cv2.copyMakeBorder(roi, 10, 10, 10, 10, cv2.BORDER_REPLICATE)
    raw = pytesseract.image_to_string(roi, config=TESS_CFG).strip()
    raw = re.sub(r"\s+", "", raw.upper())
    m = re.search(pattern, raw)
    return (m.group(0) if m else raw), raw
