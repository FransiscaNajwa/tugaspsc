"""
Generator sinyal latihan sintetis (contoh_demo.py)
Membuat SATU file suara buatan untuk mencoba seluruh pipeline sebelum rekaman asli selesai.
"""

from scipy.io import wavfile
import numpy as np
from konfigurasi import FOLDER_WAV, SAMPLE_RATE

FOLDER_WAV.mkdir(parents=True, exist_ok=True)
fs = SAMPLE_RATE
t = np.arange(fs * 2) / fs  # Durasi 2 detik
suara = np.zeros_like(t)

# Buat segmen aktif antara detik 0.4 s/d 1.55 (sisanya hening)
aktif = (t >= 0.4) & (t <= 1.55)
t2 = t[aktif] - 0.4
suara[aktif] = 0.32 * (np.sin(2 * np.pi * 180 * t2) + 0.4 * np.sin(2 * np.pi * 420 * t2))

# Envelope fade singkat
suara[aktif] *= np.sin(np.pi * t2 / 1.15) ** 2

output_path = FOLDER_WAV / 'DEMO_BUKAN_REKAMAN.wav'
wavfile.write(str(output_path), fs, (np.clip(suara, -1, 1) * 32767).astype(np.int16))
print(f"File demo sintetis berhasil dibuat di: {output_path}")
print("Ganti dengan 10 rekaman WAV asli saat pengerjaan laporan tugas.")
