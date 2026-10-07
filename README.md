# Verifikasi Ijazah: OCR Nomor & Deteksi Tanda Tangan

Prototype pengolahan citra untuk (1) membaca **nomor ijazah** dengan OCR dan
(2) menentukan **ada/tidaknya tanda tangan** kepala sekolah.

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
2. Grayscale dan enhancement
•Grayscale dipakai karena OCR dan threshold hanya butuh intensitas terang-gelap. Warna tidak membantu, dan data menjadi 1 kanal, bukan 3.
•Median blur 3x3 (enhancement global) mengganti tiap piksel dengan nilai tengah tetangganya. Cara ini efektif membuang noise bintik (salt-and-pepper) dan tetap menjaga tepi.

Metode yang dibandingkan di area nomor:
•Histogram equalization: meratakan histogram di seluruh gambar.
•CLAHE: seperti histogram equalization tetapi per blok kecil, dengan batas penguatan (clip limit).
•Unsharp masking: gambar asli dikurangi versi blur-nya, sehingga tepi menjadi lebih tajam.
•Otsu dan adaptive threshold: mengubah gambar menjadi hitam-putih.


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

## Dataset & Hasil

`data/images/` berisi 9 citra ijazah Universitas Indonesia (satu dokumen, 9 jenis degradasi):
highquality, lowcontrast, blurred, highnoise, lowres, faded, colorshift, jpeg, combined.
Citra asli **terputar 90 derajat**; `src/orient.py` mengoreksinya otomatis (mencoba 4 rotasi,
memilih yang paling banyak mengandung kata kunci "universitas/ijazah/nomor/...").

Ground truth nomor ijazah: `571012022000056` (dari citra high quality; citra lain adalah versi degradasinya).

Hasil `python main.py data/images`: nomor terbaca benar **9/9** dan tanda tangan Rektor
**PRESENT 9/9**. Uji negatif (tanda tangan dihapus dengan mengisi warna kertas): **ABSENT 18/18**
(Rektor + Dekan x 9 citra).

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

## CER dan hasil evaluasi
CER = (S + D + I) / N: S = salah ganti huruf, D = huruf hilang, I = huruf tambahan, N = panjang teks yang benar. 
Contoh: 371012022000056 vs 571012022000056 ada 1 substitusi dari 15 karakter, jadi CER = 1/15 ≈ 0,067.

