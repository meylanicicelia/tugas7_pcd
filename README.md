# Verifikasi Ijazah: OCR Nomor & Deteksi Tanda Tangan

Prototype pengolahan citra untuk (1) membaca **nomor ijazah** dengan OCR dan
(2) menentukan **ada/tidaknya tanda tangan** Rektor.

```
Input : ijazah_001_highquality_nosig.png
Output: Nomor Ijazah : 571012022000056
        Tanda Tangan : PRESENT   (rektor)
```

## Alur besar (main.py)

```
Citra Ijazah -> Koreksi rotasi -> Grayscale -> Image Enhancement (median denoise)
        |-> Area Nomor  -> Enhancement -> OCR (Tesseract)      -> Nomor Ijazah
        |-> Area TTD    -> Thresholding -> Morphology -> CCA   -> PRESENT/ABSENT
                                   -> Hasil Verifikasi
```

## Metode yang Digunakan

| Tahap | Metode | Alasan |
|---|---|---|
| Grayscale | `cv2.cvtColor` BGR->Gray | OCR & threshold tidak butuh warna; mengurangi dimensi |
| Enhancement global | Median blur 3x3 | Membuang noise salt-and-pepper sebelum ROI dipotong |
| Enhancement area nomor | Salah satu: `none`, `hist_eq`, `clahe`, `gaussian_unsharp`, `median_denoise`, `clahe_unsharp`, `otsu`, `adaptive` + upscaling 2.5x | Dibandingkan lewat CER |
| OCR | Tesseract (`--psm 7`, whitelist digit) + regex 12-16 digit | Satu baris teks; whitelist menekan salah baca |
| Thresholding TTD | Otsu inverse + batas kontras minimum terhadap latar (cegah area kosong terbaca sebagai tinta) | Pemisahan tinta/kertas otomatis |
| Morphology TTD | Opening 2x2 (buang noise) + closing 9x9 (sambung goresan putus) | Goresan tipis menjadi komponen utuh |
| Signature detection | Connected components; PRESENT jika rasio tinta >= 1,5% **dan** lebar komponen terbesar >= 15% lebar ROI | Membedakan goresan nyata dari bintik/noise | 

## Struktur Proyek

```
tugas7_pcd/
├── main.py              # Program utama: menjalankan seluruh pipeline untuk 1 citra atau 1 folder
├── evaluate_cer.py      # Membandingkan 8 metode enhancement berdasarkan CER
├── config.json          # Posisi area (ROI) nomor & tanda tangan, serta parameter deteksi
├── requirements.txt     # Dependensi Python
├── README.md            # Dokumentasi (file ini)
│
├── src/                 # Modul pengolahan citra
│   ├── orient.py        # Koreksi rotasi otomatis (0/90/180/270 derajat)
│   ├── enhance.py       # Grayscale dan metode enhancement/thresholding
│   ├── roi.py           # Memuat config dan memotong area (crop)
│   ├── ocr.py           # OCR nomor ijazah (Tesseract)
│   ├── signature.py     # Deteksi tanda tangan (threshold, morphology, connected components)
│   └── metrics.py       # Perhitungan jarak Levenshtein dan CER
│
├── tools/
│   └── select_roi.py    # Alat bantu memilih ROI secara interaktif
│
├── data/
│   ├── images/          # 9 citra ijazah (satu dokumen, 9 jenis degradasi)
│   └── ground_truth.csv # Nomor ijazah yang benar, untuk menghitung CER
│
└── results/
    ├── cer_summary.csv  # Rata-rata CER per metode
    ├── cer_detail.csv   # Hasil OCR dan CER per citra per metode
    └── debug/           # Citra tiap tahap (dibuat saat memakai --debug)
```

**Letak tahap pipeline di kode:**

| Tahap | File |
|---|---|
| Koreksi rotasi | `src/orient.py` |
| Grayscale dan enhancement | `src/enhance.py` |
| Pemotongan area nomor dan tanda tangan | `src/roi.py` |
| OCR nomor | `src/ocr.py` |
| Deteksi tanda tangan | `src/signature.py` |
| Perhitungan CER | `src/metrics.py`, `evaluate_cer.py` |
| Perakitan seluruh alur | `main.py` |

## How to Run

1. **Install Tesseract OCR** (Windows): https://github.com/UB-Mannheim/tesseract/wiki, lalu tambahkan ke PATH.
2. **Install dependensi Python (>= 3.9)**
```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
```
3. **Jalankan satu citra**
```bash
   python main.py data/images/ijazah_001_highquality_nosig.png --debug
```
   Tanpa `--debug`, hanya hasil verifikasi yang dicetak. Dengan `--debug`, citra tiap tahap disimpan di `results/debug/`.
4. **Jalankan semua citra**
```bash
   python main.py data/images
```
5. **Evaluasi CER semua metode enhancement**
```bash
   python evaluate_cer.py
```
   Hasil tersimpan di `results/cer_summary.csv` dan `results/cer_detail.csv`.
6. **Template ijazah lain**: kalibrasi area dengan `python tools/select_roi.py <gambar>`, lalu salin hasilnya ke `config.json`.
## Dataset & Hasil

`data/images/` berisi 9 citra ijazah Universitas Indonesia (satu dokumen, 9 jenis degradasi):
highquality, lowcontrast, blurred, highnoise, lowres, faded, colorshift, jpeg, combined.
Citra asli **terputar 90 derajat**; `src/orient.py` mengoreksinya otomatis (mencoba 4 rotasi,
memilih yang paling banyak mengandung kata kunci "universitas/ijazah/nomor/...").

Ground truth nomor ijazah: `571012022000056` (dari citra high quality; citra lain adalah versi degradasinya).

Hasil `python main.py data/images`: nomor terbaca benar **9/9** dan tanda tangan Rektor
**PRESENT 9/9**. Uji negatif (tanda tangan dihapus dengan mengisi warna kertas): **ABSENT 18/18**
(Rektor + Dekan x 9 citra).

## CER dan hasil evaluasi
CER = (S + D + I) / N: S = salah ganti huruf, D = huruf hilang, I = huruf tambahan, N = panjang teks yang benar. 
Contoh: 371012022000056 vs 571012022000056 ada 1 substitusi dari 15 karakter, jadi CER = 1/15 ≈ 0,067.

## Analisis Metode Enhancement Terefektif (CER)

`python evaluate_cer.py` (pra-proses global: median blur 3x3, lalu metode di bawah pada area nomor):

| Peringkat | Metode | Mean CER | Citra salah |
|---|---|---|---|
| 1 | gaussian_unsharp | 0.0000 | - |
| 2 | none | 0.0074 | combined |
| 3 | adaptive / clahe_unsharp / median_denoise / otsu | 0.0148 | 2 citra masing-masing |
| 7 | clahe | 0.0222 | highnoise, faded, combined |
| 8 | hist_eq | 0.9556 | hampir semua (OCR kosong) |

**Kesimpulan:** *Gaussian unsharp masking* paling efektif (CER 0, benar di semua jenis degradasi).
Unsharp menajamkan tepi angka yang melunak akibat blur, low-res, dan kompresi JPEG, tanpa
menggeser distribusi intensitas. *Histogram equalization* global paling buruk: kontras
diregangkan di seluruh area (termasuk tekstur kertas dan noise), sehingga angka tenggelam.
CLAHE dan thresholding (Otsu/adaptive) lebih buruk dari `none` karena memperkuat noise atau
memutus goresan angka pada citra bernoise/pudar.

Catatan: data hanya 1 dokumen x 9 degradasi (15 karakter per citra), dan selisih antar
metode peringkat 1-6 hanya 1 karakter pada 1-2 citra. Peringkat atas belum tentu bertahan di
dataset yang lebih besar; temuan yang kuat hanya bahwa `hist_eq` buruk dan `gaussian_unsharp`
tidak pernah lebih buruk dari tanpa enhancement.
