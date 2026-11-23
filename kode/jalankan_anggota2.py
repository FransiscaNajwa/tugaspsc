"""
Skrip Khusus Anggota 2 - Frame Blocking & Hamming Window
Mengikuti Panduan Kelompok 3 (Bab 7 & Bab 8 Modul):
- Validasi sinyal input 1D dan seluruh kriteria lolos
- Mencetak jumlah frame & bentuk matriks (untuk Anggota 3)
- Membuat grafik perbandingan frame pertama sebelum vs sesudah Hamming
- Menyimpan workbook Excel (sheet Frame_1 & Hamming_1 + ScatterChart native Excel)
- Menampilkan grafik sinyal langsung di layar untuk berkas contoh
"""

import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.chart import ScatterChart, Reference, Series

from konfigurasi import AKAR, FOLDER_WAV, FRAME_MS, HOP_MS
from anggota1 import baca_wav, clipping_berdasarkan_power
from anggota2 import frame_blocking, hamming_window

# Ubah ke False jika tidak ingin jendela grafik pop-up muncul di layar
TAMPILKAN_PLOT_DI_LAYAR = True
CONTOH_TAMPIL = "makan1"  # Berkas yang grafiknya akan ditampilkan langsung di layar


def validasi_anggota2(sinyal_potong, frames, windowed_frames):
    """Memeriksa seluruh syarat & kriteria lolos Anggota 2 sesuai panduan."""
    assert sinyal_potong.ndim == 1, f"Input harus 1D, ditemukan {sinyal_potong.ndim}D"
    assert frames.shape[1] == 400, f"Setiap frame harus 400 nilai, ditemukan {frames.shape[1]}"
    assert frames.shape[0] > 0, "Jumlah frame harus > 0"
    assert windowed_frames.shape == frames.shape, "Ukuran hasil windowing tidak sama dengan frame mentah"
    assert not np.isnan(frames).any(), "Terdapat nilai NaN pada frame mentah"
    assert not np.isnan(windowed_frames).any(), "Terdapat nilai NaN pada hasil windowing"
    return "LOLOS"


def simpan_dan_tampilkan_plot(folder_kata, nama_kata, fs, frame1, hamming1, window, tampilkan=False):
    waktu_ms = (np.arange(len(frame1)) / fs) * 1000.0

    # 1. Plot Frame Pertama (Mentah)
    fig1, ax1 = plt.subplots(figsize=(9, 3))
    ax1.plot(waktu_ms, frame1, color="#1f77b4", linewidth=1.0)
    ax1.set(
        title=f"Frame Pertama Sebelum Windowing ({nama_kata}.wav)",
        xlabel="Waktu lokal (ms)",
        ylabel="Amplitudo",
    )
    ax1.grid(alpha=0.3)
    fig1.tight_layout()
    fig1.savefig(folder_kata / "03_frame_pertama.png", dpi=150)
    plt.close(fig1)

    # 2. Plot Frame Pertama (Setelah Hamming Window)
    fig2, ax2 = plt.subplots(figsize=(9, 3))
    ax2.plot(waktu_ms, hamming1, color="#d62728", linewidth=1.0)
    ax2.set(
        title=f"Frame Pertama Setelah Hamming Window ({nama_kata}.wav)",
        xlabel="Waktu lokal (ms)",
        ylabel="Amplitudo",
    )
    ax2.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(folder_kata / "04_hamming_frame_pertama.png", dpi=150)
    plt.close(fig2)

    # 3. Plot Perbandingan Langsung Sebelum vs Sesudah Windowing
    fig3, axes = plt.subplots(3, 1, figsize=(9, 7), sharex=True)

    axes[0].plot(waktu_ms, frame1, color="#1f77b4", linewidth=1.0)
    axes[0].set_title(f"Perbandingan Frame Pertama: Sebelum vs Sesudah Hamming ({nama_kata}.wav)")
    axes[0].set_ylabel("Frame Mentah")
    axes[0].grid(alpha=0.3)

    axes[1].plot(waktu_ms, window, color="#2ca02c", linewidth=1.2)
    axes[1].set_ylabel("Hamming w[n]")
    axes[1].grid(alpha=0.3)

    axes[2].plot(waktu_ms, frame1, color="#1f77b4", alpha=0.45, label="Sebelum Window")
    axes[2].plot(waktu_ms, hamming1, color="#d62728", linewidth=1.1, label="Sesudah Hamming")
    axes[2].set_xlabel("Waktu lokal (ms)")
    axes[2].set_ylabel("Amplitudo")
    axes[2].legend(loc="upper right")
    axes[2].grid(alpha=0.3)

    fig3.tight_layout()
    fig3.savefig(folder_kata / f"perbandingan_anggota2_{nama_kata}.png", dpi=150)

    if tampilkan:
        plt.show()  # Memunculkan jendela grafik sinyal langsung di layar
    plt.close(fig3)


def buat_sheet_scatter(wb, nama_sheet, waktu_s, nilai, judul_grafik):
    ws = wb.create_sheet(nama_sheet)
    ws.append(["waktu_s", "amplitudo"])
    for t, y in zip(waktu_s, nilai):
        ws.append([float(t), float(y)])

    ws.freeze_panes = "A2"
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 18

    chart = ScatterChart()
    chart.title = judul_grafik
    chart.x_axis.title = "waktu_s"
    chart.y_axis.title = "amplitudo"
    x_ref = Reference(ws, min_col=1, min_row=2, max_row=ws.max_row)
    y_ref = Reference(ws, min_col=2, min_row=2, max_row=ws.max_row)
    chart.series.append(Series(y_ref, x_ref, title="amplitudo"))
    chart.legend = None
    chart.width = 19
    chart.height = 9
    ws.add_chart(chart, "D2")


def simpan_excel_anggota2(path_xlsx, nama_kata, fs, sinyal_potong, frames, windowed_frames, ukuran, langkah):
    wb = Workbook()

    # Sheet Ringkasan khusus Anggota 2 (memuat ukuran matriks untuk Anggota 3)
    ws_ringkas = wb.active
    ws_ringkas.title = "Ringkasan_Anggota2"
    ringkasan = [
        ("Berkas", f"{nama_kata}.wav"),
        ("Fs (Hz)", fs),
        ("Dimensi sinyal potong", f"{sinyal_potong.ndim}D ({len(sinyal_potong)} sampel)"),
        ("Panjang frame N (sampel)", ukuran),
        ("Hop / pergeseran (sampel)", langkah),
        ("Overlap (%)", round((1 - langkah / ukuran) * 100, 1)),
        ("Jumlah frame", int(frames.shape[0])),
        ("Bentuk matriks frames", str(frames.shape)),
        ("Bentuk matriks windowed_frames (input Anggota 3)", str(windowed_frames.shape)),
        ("Ada nilai NaN?", bool(np.isnan(windowed_frames).any())),
    ]
    for baris in ringkasan:
        ws_ringkas.append(baris)
    ws_ringkas.column_dimensions["A"].width = 45
    ws_ringkas.column_dimensions["B"].width = 25

    waktu_s = np.arange(ukuran) / fs
    buat_sheet_scatter(wb, "Frame_1", waktu_s, frames[0], f"Frame 1 Mentah - {nama_kata}.wav")
    buat_sheet_scatter(wb, "Hamming_1", waktu_s, windowed_frames[0], f"Hamming Frame 1 - {nama_kata}.wav")

    wb.save(path_xlsx)


def jalankan_semua():
    folder_out = AKAR / "hasil_anggota2"
    folder_out.mkdir(parents=True, exist_ok=True)

    daftar_wav = sorted(FOLDER_WAV.glob("*.wav"))
    if not daftar_wav:
        raise FileNotFoundError(f"Tidak ditemukan berkas .wav di {FOLDER_WAV}")

    print("=" * 112)
    print(
        f"{'No':<4}{'Berkas':<15}{'Sampel 1D':<11}{'Jml Frame':<11}"
        f"{'Bentuk Matriks':<17}{'Ujung F1 Awal':<15}{'Ujung F1 Hamming':<18}{'Kriteria':<10}"
    )
    print("-" * 112)

    for nomor, path_wav in enumerate(daftar_wav, start=1):
        nama_kata = path_wav.stem
        fs, sinyal = baca_wav(path_wav)
        potong, _, _, _, _ = clipping_berdasarkan_power(sinyal, fs)

        # Cek bentuk sinyal potong adalah array 1D (poin 1 panduan)
        if potong.ndim != 1:
            raise ValueError(f"Sinyal potong {path_wav.name} bukan array 1D.")

        frames, ukuran, langkah = frame_blocking(potong, fs, frame_ms=FRAME_MS, hop_ms=HOP_MS)
        windowed_frames, window = hamming_window(frames)

        status = validasi_anggota2(potong, frames, windowed_frames)

        folder_kata = folder_out / nama_kata
        folder_kata.mkdir(parents=True, exist_ok=True)

        tampil = TAMPILKAN_PLOT_DI_LAYAR and (nama_kata == CONTOH_TAMPIL)
        simpan_dan_tampilkan_plot(folder_kata, nama_kata, fs, frames[0], windowed_frames[0], window, tampilkan=tampil)
        simpan_excel_anggota2(
            folder_kata / f"{nama_kata}_khusus_anggota2.xlsx",
            nama_kata,
            fs,
            potong,
            frames,
            windowed_frames,
            ukuran,
            langkah,
        )

        # Bandingkan besar amplitudo sampel paling ujung (n=0) sebelum vs sesudah Hamming
        ujung_awal = abs(float(frames[0, 0]))
        ujung_hamming = abs(float(windowed_frames[0, 0]))

        print(
            f"{nomor:<4}{path_wav.name:<15}{len(potong):<11}{frames.shape[0]:<11}"
            f"{str(windowed_frames.shape):<17}{ujung_awal:<15.6f}{ujung_hamming:<18.6f}{status:<10}"
        )

    print("=" * 112)
    print(f"Semua grafik PNG & file Excel tersimpan di folder: {folder_out}")


if __name__ == "__main__":
    jalankan_semua()