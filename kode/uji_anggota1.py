"""
Skrip Khusus Anggota 1: Pengujian & Visualisasi Level Clipping
Gunakan skrip ini untuk mengevaluasi apakah suara terpotong dengan baik atau terpotong berlebihan.
"""

import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', tempfile.gettempdir())

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from konfigurasi import FOLDER_WAV, FOLDER_HASIL, THRESHOLD_K, DURASI_POWER_MS
from anggota1 import baca_wav, clipping_berdasarkan_power


def uji_file(file_path, k=THRESHOLD_K):
    file_path = Path(file_path)
    print(f"\n==========================================")
    print(f"Menguji file: {file_path.name}")
    print(f"==========================================")
    
    fs, sinyal = baca_wav(file_path)
    durasi_awal = len(sinyal) / fs
    print(f"Sample Rate         : {fs} Hz")
    print(f"Jumlah Sampel Awal  : {len(sinyal)}")
    print(f"Durasi Awal         : {durasi_awal:.3f} detik")
    
    potong, power, ambang, awal, akhir = clipping_berdasarkan_power(sinyal, fs, threshold_k=k)
    durasi_potong = len(potong) / fs
    t_awal = awal / fs
    t_akhir = akhir / fs
    
    print(f"Durasi Blok Power   : {DURASI_POWER_MS} ms")
    print(f"Nilai K             : {k}")
    print(f"Power Mean          : {power.mean():.6e}")
    print(f"Power Std           : {power.std():.6e}")
    print(f"Ambang (Threshold)  : {ambang:.6e}")
    print(f"Sampel Aktif        : {awal} s.d. {akhir} (detik {t_awal:.3f} s.d. {t_akhir:.3f})")
    print(f"Jumlah Sampel Potong: {len(potong)}")
    print(f"Durasi Akhir        : {durasi_potong:.3f} detik ({durasi_potong/durasi_awal*100:.1f}% dari asli)")
    
    # Buat plot visualisasi 3 panel khusus analisis Anggota 1
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=False)
    
    t_sinyal = np.arange(len(sinyal)) / fs
    axes[0].plot(t_sinyal, sinyal, color='#1f77b4', linewidth=0.8)
    axes[0].axvline(t_awal, color='red', linestyle='--', label=f'Awal Clipping ({t_awal:.2f} s)')
    axes[0].axvline(t_akhir, color='green', linestyle='--', label=f'Akhir Clipping ({t_akhir:.2f} s)')
    axes[0].set_title(f"1. Sinyal Asli dengan Batas Deteksi Aktif ({file_path.name})", fontweight='bold')
    axes[0].set_ylabel("Amplitudo")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(loc='upper right')
    
    # Plot power per blok
    panjang_blok = max(1, round(fs * DURASI_POWER_MS / 1000))
    t_power = (np.arange(len(power)) * panjang_blok) / fs
    axes[1].plot(t_power, power, color='#ff7f0e', linewidth=1.2, label='Power per Blok')
    axes[1].axhline(ambang, color='crimson', linestyle='-', linewidth=1.5, label=f'Threshold = mean + {k}*std')
    axes[1].set_title(f"2. Kurva Short-Time Power dan Nilai Ambang Batas", fontweight='bold')
    axes[1].set_ylabel("Power ($x^2$)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc='upper right')
    
    # Plot sinyal hasil pemotongan
    t_potong = np.arange(len(potong)) / fs
    axes[2].plot(t_potong, potong, color='#2ca02c', linewidth=0.8)
    axes[2].set_title(f"3. Sinyal Setelah Level Clipping (Durasi: {durasi_potong:.3f} s)", fontweight='bold')
    axes[2].set_xlabel("Waktu (detik)")
    axes[2].set_ylabel("Amplitudo")
    axes[2].grid(True, alpha=0.3)
    
    fig.tight_layout()
    output_dir = FOLDER_HASIL / 'evaluasi_anggota1'
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f'evaluasi_{file_path.stem}.png'
    fig.savefig(out_file, dpi=150)
    plt.close(fig)
    print(f"Plot analisis Anggota 1 tersimpan di: {out_file}")


def main():
    wav_files = sorted(FOLDER_WAV.glob('*.wav'))
    if not wav_files:
        print("Tidak ada file WAV di data_wav/. Silakan jalankan 'python kode/contoh_demo.py' terlebih dahulu.")
        return
    for wf in wav_files:
        try:
            uji_file(wf)
        except Exception as e:
            print(f"Error memproses {wf.name}: {e}")


if __name__ == '__main__':
    main()
