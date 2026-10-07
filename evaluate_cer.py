"""Bandingkan metode enhancement berdasarkan CER.
Ground truth: data/ground_truth.csv  (kolom: filename,number)
Jalankan: python evaluate_cer.py
"""
import csv
import os
import cv2
from src import enhance, roi as R, ocr
from src.metrics import cer
from src.orient import auto_rotate

cfg = R.load_config()
rows = list(csv.DictReader(open("data/ground_truth.csv", encoding="utf-8")))
methods = list(enhance.METHODS)
scores = {m: [] for m in methods}
detail = []

for r in rows:
    img = cv2.imread(os.path.join("data/images", r["filename"]))
    if img is None:
        print("skip (tidak ditemukan):", r["filename"]); continue
    img, _ = auto_rotate(img)
    g = enhance.apply(enhance.to_gray(img), cfg["global_enhancement"])
    num_roi = R.crop(g, cfg["number_roi"])
    ref = r["number"].strip().upper()
    for m in methods:
        hyp, _ = ocr.read_number(num_roi, m, cfg["number_pattern"])
        c = cer(ref, hyp)
        scores[m].append(c)
        detail.append([r["filename"], m, ref, hyp, round(c, 4)])

os.makedirs("results", exist_ok=True)
with open("results/cer_detail.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["file", "method", "ref", "hyp", "cer"]); w.writerows(detail)

summary = sorted(((sum(v) / len(v), m) for m, v in scores.items() if v))
with open("results/cer_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["method", "mean_cer"])
    for c, m in summary: w.writerow([m, round(c, 4)])

print(f"{'Metode':<20}{'Mean CER':>10}")
for c, m in summary: print(f"{m:<20}{c:>10.4f}")
print(f"\nMetode paling efektif (CER terendah): {summary[0][1]}")
