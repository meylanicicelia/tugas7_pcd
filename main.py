"""Prototype verifikasi ijazah.
Contoh : python main.py data/images/ijazah_001_highquality_nosig.png --debug
         python main.py data/images            (semua citra dalam folder)
"""
import argparse
import glob
import os
import cv2
from src import enhance, roi as R, ocr, signature
from src.orient import auto_rotate


def verify(path, cfg, method=None, debug=False):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    method = method or cfg["default_method"]
    img, angle = auto_rotate(img)                     # 0. koreksi orientasi
    gray = enhance.to_gray(img)                       # 1. Grayscale
    gray_enh = enhance.apply(gray, cfg["global_enhancement"])          # 2. Image enhancement global
    num_roi = R.crop(gray_enh, cfg["number_roi"])     # 3a. Area nomor
    nomor, raw = ocr.read_number(num_roi, method, cfg["number_pattern"])  # enhancement -> OCR

    sigs, masks, rois = {}, {}, {}
    for name, box in cfg["signature_rois"].items():   # 3b. Area tanda tangan
        rois[name] = R.crop(gray_enh, box)
        status, info, masks[name] = signature.detect(rois[name], cfg["signature"])
        sigs[name] = (status, info)

    if debug:
        os.makedirs("results/debug", exist_ok=True)
        base = os.path.splitext(os.path.basename(path))[0]
        cv2.imwrite(f"results/debug/{base}_1_gray.png", gray)
        cv2.imwrite(f"results/debug/{base}_2_enhanced.png", gray_enh)
        cv2.imwrite(f"results/debug/{base}_3_number_roi.png", num_roi)
        for n in rois:
            cv2.imwrite(f"results/debug/{base}_4_{n}_roi.png", rois[n])
            cv2.imwrite(f"results/debug/{base}_5_{n}_mask.png", masks[n])
    return nomor, sigs, angle


def report(path, cfg, method, debug):
    nomor, sigs, angle = verify(path, cfg, method, debug)
    head = cfg["head_signer"]
    print(f"Input: {os.path.basename(path)}  (rotasi dikoreksi {angle} derajat)\n")
    print(f"Nomor Ijazah : {nomor}")
    print(f"Tanda Tangan : {sigs[head][0]}   ({head})")
    others = ", ".join(f"{k}={v[0]}" for k, v in sigs.items() if k != head)
    if others:
        print(f"(tambahan)   : {others}")
    if debug:
        print(f"(debug)      : {sigs[head][1]}")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="file citra atau folder")
    ap.add_argument("--config", default=None)
    ap.add_argument("--method", default=None, choices=list(enhance.METHODS))
    ap.add_argument("--debug", action="store_true", help="simpan citra tiap tahap")
    a = ap.parse_args()
    cfg = R.load_config(a.config)
    files = sorted(glob.glob(os.path.join(a.path, "*.[jp][pn]g"))) if os.path.isdir(a.path) else [a.path]
    for f in files:
        report(f, cfg, a.method, a.debug)
