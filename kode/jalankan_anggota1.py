"""
Program Khusus Anggota 1 - Pengolahan Sinyal Suara & Level Clipping ke Excel
HANYA memproses tugas murni Anggota 1:
1. Membaca WAV mono 16 kHz 16-bit
2. Normalisasi sinyal
3. Level Clipping berbasis Power
4. Menghasilkan grafik sinyal asli, sinyal clipping, dan workbook Excel khusus Anggota 1
(TIDAK ADA Frame Blocking, Hamming, FFT, atau MFCC)
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

from konfigurasi import FOLDER_WAV, AKAR, SAMPLE_RATE, JUMLAH_BIT, JUMLAH_CHANNEL
from anggota1 import baca_wav, clipping_berdasarkan_power

FOLDER_HASIL_ANGGOTA1 = AKAR / 'hasil_anggota1'
FOLDER_HASIL_ANGGOTA1.mkdir(parents=True, exist_ok=True)


def gambar_garis(x, y, judul, xlab, ylab, lokasi):
    """Menyimpan gambar grafik sinyal domain waktu."""
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
    """Mengisi sheet dengan data numerik sinyal."""
    ws.append(judul_kolom)
    jumlah = min(maksimal, len(kolom_data[0]))
    for i in range(jumlah):
        ws.append([float(k[i]) for k in kolom_data])
    ws.freeze_panes = 'A2'
    for c in ws[1]:
        c.font = Font(bold=True)
    for column in ws.columns:
        ws.column_dimensions[column[0].column_letter].width = 18


def proses_anggota1(file_path):
    file_path = Path(file_path)
    # 1. Baca WAV & Validasi
    fs, sinyal = baca_wav(file_path)
    
    # 2. Level Clipping berbasis Power
    potong, power_blok, ambang, awal, akhir = clipping_berdasarkan_power(sinyal, fs)

    folder = FOLDER_HASIL_ANGGOTA1 / file_path.stem
    folder.mkdir(parents=True, exist_ok=True)

    # 3. Simpan 2 Gambar Grafik Khusus Tugas Anggota 1
    file_img_asli = folder / '01_sinyal_asli.png'
    file_img_clip = folder / '02_sinyal_clipping.png'
    
    gambar_garis(
        np.arange(len(sinyal)) / fs, sinyal,
        f'Sinyal Asli ({file_path.name})', 'Waktu (s)', 'Amplitudo',
        file_img_asli
    )
    gambar_garis(
        np.arange(len(potong)) / fs, potong,
        f'Sinyal Setelah Level Clipping ({file_path.name})', 'Waktu Lokal (s)', 'Amplitudo',
        file_img_clip
    )

    # 4. Buat Workbook Excel Khusus Anggota 1 (Tanpa Hamming/FFT/MFCC)
    wb = Workbook()
    
    # Sheet 1: Ringkasan Parameter Anggota 1
    ws = wb.active
    ws.title = 'Ringkasan_Anggota1'
    ringkasan = [
        ('Nama Berkas', file_path.name),
        ('Frekuensi Sampling (Fs)', f'{fs} Hz'),
        ('Kedalaman Bit', f'{JUMLAH_BIT}-bit PCM'),
        ('Jumlah Channel', f'{JUMLAH_CHANNEL} (Mono)'),
        ('Jumlah Sampel Sinyal Asli', len(sinyal)),
        ('Durasi Sinyal Asli (detik)', round(len(sinyal) / fs, 4)),
        ('Waktu Awal Suara Aktif (detik)', round(awal / fs, 4)),
        ('Waktu Akhir Suara Aktif (detik)', round(akhir / fs, 4)),
        ('Jumlah Sampel Setelah Clipping', len(potong)),
        ('Durasi Setelah Clipping (detik)', round(len(potong) / fs, 4)),
        ('Persentase Reduksi Hening', f'{round((1 - len(potong)/len(sinyal))*100, 2)} %'),
        ('Nilai Ambang Batas (Threshold Power)', float(ambang)),
    ]
    for r in ringkasan:
        ws.append(r)
    ws.column_dimensions['A'].width = 35
    ws.column_dimensions['B'].width = 30
    for c in ws['A']:
        c.font = Font(bold=True)

    # Sheet 2 & 3: Data Numerik Sinyal Asli & Sinyal Clipping + Scatter Chart
    datasets = [
        ('Sinyal_Asli', ['waktu_s', 'amplitudo'], [np.arange(len(sinyal)) / fs, sinyal]),
        ('Clipping', ['waktu_s', 'amplitudo'], [np.arange(len(potong)) / fs, potong])
    ]

    for judul, headers, values in datasets:
        sheet = wb.create_sheet(judul)
        isi_sheet(sheet, headers, values)
        if sheet.max_row > 2:
            chart = ScatterChart()
            chart.title = f'{judul} ({file_path.stem})'
            chart.x_axis.title = headers[0]
            chart.y_axis.title = headers[1]
            x = Reference(sheet, min_col=1, min_row=2, max_row=sheet.max_row)
            y = Reference(sheet, min_col=2, min_row=2, max_row=sheet.max_row)
            chart.series.append(Series(y, x, title=headers[1]))
            chart.width = 19
            chart.height = 9
            sheet.add_chart(chart, 'D2')

    # Sheet 4: Gambar Grafik Khusus Anggota 1
    ws_g = wb.create_sheet('Grafik_Anggota1')
    img1 = XLImage(str(file_img_asli))
    img1.width = 700; img1.height = 233
    ws_g.add_image(img1, 'A1')

    img2 = XLImage(str(file_img_clip))
    img2.width = 700; img2.height = 233
    ws_g.add_image(img2, 'A16')

    excel_path = folder / f'{file_path.stem}_khusus_anggota1.xlsx'
    wb.save(excel_path)
    print(f"[BERHASIL] {file_path.name}: {len(sinyal)} sampel -> {len(potong)} sampel ({len(potong)/fs:.3f} s)")
    print(f"           Hasil Anggota 1 di: {excel_path}")


def main():
    berkas = sorted(FOLDER_WAV.glob('*.wav'))
    if not berkas:
        print("Tidak ada file audio di data_wav/.")
        return

    print("===================================================================")
    print(" MENJALANKAN PENGOLAHAN KHUSUS ANGGOTA 1 (WAV & POWER CLIPPING) ")
    print("===================================================================")
    for f in berkas:
        if f.name == 'DEMO_BUKAN_REKAMAN.wav':
            continue
        try:
            proses_anggota1(f)
        except Exception as e:
            print(f"[GAGAL] {f.name}: {e}")
    print("===================================================================")
    print(f"Selesai! Seluruh hasil khusus Anggota 1 tersimpan di folder: {FOLDER_HASIL_ANGGOTA1}")


if __name__ == '__main__':
    main()
