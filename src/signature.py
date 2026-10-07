"""Deteksi tanda tangan: thresholding -> morphology -> connected components."""
import cv2
import numpy as np


def detect(gray_roi, cfg):
    """Return (PRESENT/ABSENT, info dict, mask_morfologi)."""
    g = cv2.GaussianBlur(gray_roi, (5, 5), 0)
    # 1. Thresholding (Otsu, inverse: tinta = putih)
    t_otsu, _ = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    # batas tidak boleh lebih tinggi dari (latar - min_contrast): area kosong tidak jadi "tinta"
    bg = float(np.median(g))
    t = min(t_otsu, bg - cfg["min_contrast"])
    th = (g < t).astype(np.uint8) * 255
    # buang tepi (garis border hasil crop)
    m = max(2, int(0.03 * min(th.shape)))
    th[:m, :] = th[-m:, :] = 0
    th[:, :m] = th[:, -m:] = 0
    # 2. Morphology: opening buang noise, closing sambung goresan
    th = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2)))
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    # 3. Analisis komponen terhubung
    n, labels, stats, _ = cv2.connectedComponentsWithStats(th, connectivity=8)
    total = th.shape[0] * th.shape[1]
    keep = np.zeros_like(th)
    max_w = 0
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area / total >= cfg["min_component_area_ratio"]:
            keep[labels == i] = 255
            max_w = max(max_w, stats[i, cv2.CC_STAT_WIDTH])
    ink_ratio = float(np.count_nonzero(keep)) / total
    width_ratio = float(max_w) / th.shape[1]
    present = ink_ratio >= cfg["min_ink_ratio"] and width_ratio >= cfg["min_width_ratio"]
    info = {"ink_ratio": round(ink_ratio, 4), "width_ratio": round(width_ratio, 3)}
    return ("PRESENT" if present else "ABSENT"), info, keep
