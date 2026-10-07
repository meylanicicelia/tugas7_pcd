"""Pilih ROI secara interaktif dan cetak fraksinya untuk config.json.
Jalankan: python tools/select_roi.py data/images/ijazah_001.jpg
"""
import sys
import cv2

img = cv2.imread(sys.argv[1])
h, w = img.shape[:2]
scale = 900 / max(h, w)
small = cv2.resize(img, None, fx=scale, fy=scale)
for name in ("number_roi (area nomor)", "signature_roi (area tanda tangan)"):
    x, y, rw, rh = cv2.selectROI(name, small, False)
    cv2.destroyAllWindows()
    sw, sh = small.shape[1], small.shape[0]
    print(f'"{name.split()[0]}": [{x/sw:.3f}, {y/sh:.3f}, {rw/sw:.3f}, {rh/sh:.3f}],')
