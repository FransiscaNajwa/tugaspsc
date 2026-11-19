"""
Program Utama - Pipeline Pengolahan Audio PSC ke Excel & Grafik
Jalankan dari root atau folder kode: python kode/jalankan.py
"""

import os
import tempfile
os.environ.setdefault('MPLCONFIGDIR', tempfile.gettempdir())

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font

from konfigurasi import FOLDER_WAV, FOLDER_HASIL
from anggota1 import baca_wav, clipping_berdasarkan_power
from anggota2 import frame_blocking, hamming_window
from anggota3 import fft_frames, hitung_mfcc


def gambar_garis(x, y, judul, xlab, ylab, lokasi):
    """Membuat dan menyimpan plot grafik garis Matplotlib beresolusi tinggi."""
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(x, y, linewidth=0.85, color='#1f77b4')
    ax.set_title(judul, fontsize=11, fontweight='bold')
    ax.set_xlabel(xlab, fontsize=9)
    ax.set_ylabel(ylab, fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--')
    fig.tight_layout()
    fig.savefig(lokasi, dpi=150)
    plt.close(fig)


def isi_sheet(ws, judul_kolom, kolom_data, maksimal=8000):
    """Mengisi worksheet Excel dengan data kolom numerik."""
    ws.append(judul_kolom)
    jumlah = min(maksimal, len(kolom_data[0]))
    for i in range(jumlah):
        ws.append([float(k[i]) for k in kolom_data])
    ws.freeze_panes = 'A2'
    for c in ws[1]:
        c.font = Font(bold=True)
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 18


def kerjakan(file):
    """Memproses satu file rekaman WAV melalui keseluruhan pipeline."""
    # 1. Anggota 1: Baca WAV & Level Clipping
    fs, sinyal = baca_wav(file)
    potong, power_blok, ambang, awal, akhir = clipping_berdasarkan_power(sinyal, fs)

    # 2. Anggota 2: Frame Blocking & Hamming Window
    frames, ukuran, langkah = frame_blocking(potong, fs)
    windowed, window = hamming_window(frames)

    # 3. Anggota 3: FFT & MFCC
    frek, magnitudo, power_spec = fft_frames(windowed, fs)
    mfcc, bank, log_mel = hitung_mfcc(power_spec, frek, fs)

    folder = FOLDER_HASIL / file.stem
    folder.mkdir(parents=True, exist_ok=True)

    # Simpan Gambar Grafik Matplotlib
    nama = [
        '01_sinyal_asli',
        '02_sinyal_clipping',
        '03_frame_pertama',
        '04_hamming_frame_pertama',
        '05_fft_frame_pertama',
        '06_mfcc_koef_1'
    ]

    gambar_garis(np.arange(len(sinyal)) / fs, sinyal, 'Sinyal Asli', 'Waktu (s)', 'Amplitudo', folder / (nama[0] + '.png'))
    gambar_garis(np.arange(len(potong)) / fs, potong, 'Sinyal Setelah Clipping', 'Waktu Lokal (s)', 'Amplitudo', folder / (nama[1] + '.png'))
    gambar_garis(np.arange(ukuran) / fs, frames[0], 'Frame Pertama (Mentah)', 'Waktu Lokal (s)', 'Amplitudo', folder / (nama[2] + '.png'))
    gambar_garis(np.arange(ukuran) / fs, windowed[0], 'Hamming Frame Pertama', 'Waktu Lokal (s)', 'Amplitudo', folder / (nama[3] + '.png'))
    gambar_garis(frek, magnitudo[0], 'FFT Frame Pertama (0 - 8000 Hz)', 'Frekuensi (Hz)', 'Magnitudo', folder / (nama[4] + '.png'))
    gambar_garis(np.arange(len(mfcc)), mfcc[:, 0], 'MFCC Koefisien 1 terhadap Frame', 'Indeks Frame', 'Koefisien', folder / (nama[5] + '.png'))

    # Buat Workbook Excel
    wb = Workbook()
    ws = wb.active
    ws.title = 'Ringkasan'
    ringkasan = [
        ('File', file.name),
        ('Fs (Hz)', fs),
        ('Jumlah sampel asli', len(sinyal)),
        ('Durasi asli (s)', len(sinyal) / fs),
        ('Awal clipping (s)', awal / fs),
        ('Akhir clipping (s)', akhir / fs),
        ('Durasi setelah clipping (s)', len(potong) / fs),
        ('Threshold power', float(ambang)),
        ('Jumlah frame', len(frames)),
        ('Sampel per frame', ukuran),
        ('Hop (sampel)', langkah),
        ('Jumlah koefisien MFCC', mfcc.shape[1])
    ]
    for r in ringkasan:
        ws.append(r)
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 30

    datasets = [
        ('Sinyal_Asli', ['waktu_s', 'amplitudo'], [np.arange(len(sinyal)) / fs, sinyal]),
        ('Clipping', ['waktu_s', 'amplitudo'], [np.arange(len(potong)) / fs, potong]),
        ('Frame_1', ['waktu_s', 'amplitudo'], [np.arange(ukuran) / fs, frames[0]]),
        ('Hamming_1', ['waktu_s', 'amplitudo'], [np.arange(ukuran) / fs, windowed[0]]),
        ('FFT_1', ['frekuensi_Hz', 'magnitudo'], [frek, magnitudo[0]]),
        ('MFCC', ['frame'] + [f'mfcc_{i+1}' for i in range(mfcc.shape[1])],
         [np.arange(len(mfcc))] + [mfcc[:, j] for j in range(mfcc.shape[1])]),
    ]

    for judul, headers, values in datasets:
        sheet = wb.create_sheet(judul)
        isi_sheet(sheet, headers, values)
        if sheet.max_row > 2:
            chart = ScatterChart()
            chart.title = judul.replace('_', ' ')
            chart.x_axis.title = headers[0]
            chart.y_axis.title = headers[1]
            x = Reference(sheet, min_col=1, min_row=2, max_row=sheet.max_row)
            y = Reference(sheet, min_col=2, min_row=2, max_row=sheet.max_row)
            chart.series.append(Series(y, x, title=headers[1]))
            chart.width = 19
            chart.height = 9
            sheet.add_chart(chart, 'D2' if len(headers) <= 2 else 'Q2')

    ws_g = wb.create_sheet('Grafik_Python')
    for i, key in enumerate(nama):
        img_path = folder / (key + '.png')
        if img_path.exists():
            img = XLImage(str(img_path))
            img.width = 700
            img.height = 233
            ws_g.add_image(img, f'A{1 + i * 14}')

    excel_path = folder / f'{file.stem}_hasil.xlsx'
    wb.save(excel_path)
    print(f"[BERHASIL] {file.name}: {len(sinyal)} sampel -> {len(frames)} frame -> MFCC {mfcc.shape}")
    print(f"           Hasil tersimpan di: {folder}")


def main():
    berkas = sorted(FOLDER_WAV.glob('*.wav'))
    if not berkas:
        print("PERINGATAN: Belum ada file .wav di folder data_wav.")
        print("Silakan jalankan 'python kode/contoh_demo.py' untuk membuat file demo sintetis,")
        print("atau letakkan 10 file rekaman WAV asli di dalam folder data_wav/.")
        return

    for file in berkas:
        try:
            kerjakan(file)
        except Exception as exc:
            print(f"[GAGAL] {file.name}: {exc}")


if __name__ == '__main__':
    main()
