import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from openpyxl import Workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.styles import Font, PatternFill

from konfigurasi import (
    AKAR,
    FOLDER_WAV,
    FRAME_MS,
    HOP_MS,
    JUMLAH_FILTER_MEL,
    JUMLAH_MFCC
)

from anggota1 import baca_wav, clipping_berdasarkan_power
from anggota2 import frame_blocking, hamming_window
from anggota3 import fft_frames, hitung_mfcc


FOLDER_HASIL = AKAR / "hasil_anggota3"


def validasi_hasil(frekuensi, magnitudo, power, mfcc,
                   bank, log_mel, jumlah_frame, fs):

    jumlah_bin = len(frekuensi)

    if magnitudo.shape != (jumlah_frame, jumlah_bin):
        raise ValueError("Ukuran matriks FFT tidak sesuai")

    if power.shape != magnitudo.shape:
        raise ValueError("Ukuran Power Spectrum tidak sesuai")

    if mfcc.shape != (jumlah_frame, JUMLAH_MFCC):
        raise ValueError("Ukuran matriks MFCC tidak sesuai")

    if bank.shape != (JUMLAH_FILTER_MEL, jumlah_bin):
        raise ValueError("Ukuran Mel Filterbank tidak sesuai")

    if log_mel.shape != (jumlah_frame, JUMLAH_FILTER_MEL):
        raise ValueError("Ukuran Log Mel tidak sesuai")

    if not np.isclose(frekuensi[0], 0):
        raise ValueError("Frekuensi awal FFT harus 0 Hz")

    if not np.isclose(frekuensi[-1], fs / 2):
        raise ValueError("Frekuensi akhir FFT tidak sesuai Nyquist")

    data = {
        "Frekuensi": frekuensi,
        "Magnitudo": magnitudo,
        "Power Spectrum": power,
        "MFCC": mfcc,
        "Mel Filterbank": bank,
        "Log Mel": log_mel
    }

    for nama, nilai in data.items():
        if not np.isfinite(nilai).all():
            raise ValueError(f"{nama} mengandung NaN atau Inf")

    return True


def simpan_grafik(x, y, judul, xlabel, ylabel, lokasi):

    plt.figure(figsize=(10, 4))
    plt.plot(x, y)

    plt.title(judul)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)

    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(lokasi, dpi=150)
    plt.close()


def grafik_fft(folder, nama, frekuensi, magnitudo, fs, hop):

    simpan_grafik(
        frekuensi,
        magnitudo[0],
        f"FFT Frame Pertama - {nama}",
        "Frekuensi (Hz)",
        "Magnitudo",
        folder / "fft_frame_pertama.png"
    )

    waktu = np.arange(len(magnitudo)) * hop / fs

    spectrum_db = 10 * np.log10(
        np.maximum(magnitudo ** 2, 1e-12)
    )

    plt.figure(figsize=(11, 5))

    plt.imshow(
        spectrum_db.T,
        origin="lower",
        aspect="auto",
        extent=[
            0,
            waktu[-1] + hop / fs,
            frekuensi[0],
            frekuensi[-1]
        ],
        cmap="viridis"
    )

    plt.title(f"Spektrum FFT Seluruh Frame - {nama}")
    plt.xlabel("Waktu (s)")
    plt.ylabel("Frekuensi (Hz)")

    plt.colorbar(label="Magnitudo Kuadrat (dB)")
    plt.tight_layout()

    plt.savefig(folder / "fft_seluruh_frame.png", dpi=150)
    plt.close()


def grafik_mel_filterbank(folder, frekuensi, bank):

    plt.figure(figsize=(10, 4))

    for filter_mel in bank:
        plt.plot(frekuensi, filter_mel)

    plt.title("Mel Filterbank")
    plt.xlabel("Frekuensi (Hz)")
    plt.ylabel("Bobot Filter")

    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(folder / "mel_filterbank.png", dpi=150)
    plt.close()


def grafik_mfcc(folder, nama, mfcc):

    jumlah_frame = mfcc.shape[0]

    simpan_grafik(
        np.arange(1, jumlah_frame + 1),
        mfcc[:, 0],
        f"MFCC Koefisien Pertama - {nama}",
        "Indeks Frame",
        "Nilai MFCC",
        folder / "mfcc_koefisien.png"
    )

    plt.figure(figsize=(11, 5))

    plt.imshow(
        mfcc.T,
        origin="lower",
        aspect="auto",
        cmap="viridis",
        extent=[
            0.5,
            jumlah_frame + 0.5,
            0.5,
            mfcc.shape[1] + 0.5
        ]
    )

    plt.title(f"MFCC Heatmap - {nama}")
    plt.xlabel("Indeks Frame")
    plt.ylabel("Koefisien MFCC")

    plt.yticks(np.arange(1, mfcc.shape[1] + 1))

    plt.colorbar(label="Nilai Koefisien")
    plt.tight_layout()

    plt.savefig(folder / "mfcc_heatmap.png", dpi=150)
    plt.close()


def buat_sheet(wb, nama, header, data):

    ws = wb.create_sheet(nama)

    ws.append(header)

    for baris in data:
        ws.append([
            float(nilai) if isinstance(
                nilai, (np.integer, np.floating)
            ) else nilai
            for nilai in baris
        ])

    ws.freeze_panes = "B2"

    for cell in ws[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF"
        )
        cell.fill = PatternFill(
            "solid",
            fgColor="17365D"
        )

    ws.column_dimensions["A"].width = 24

    return ws


def tambah_grafik_excel(ws, kolom_x, kolom_y, judul, posisi):

    chart = LineChart()

    chart.title = judul
    chart.x_axis.title = ws.cell(1, kolom_x).value
    chart.y_axis.title = ws.cell(1, kolom_y).value

    data = Reference(
        ws,
        min_col=kolom_y,
        min_row=1,
        max_row=ws.max_row
    )

    kategori = Reference(
        ws,
        min_col=kolom_x,
        min_row=2,
        max_row=ws.max_row
    )

    chart.add_data(data, titles_from_data=True)
    chart.set_categories(kategori)

    chart.width = 18
    chart.height = 9

    ws.add_chart(chart, posisi)


def ekspor_excel(
    folder, nama, fs, jumlah_frame, ukuran, hop,
    frekuensi, magnitudo, power, bank, log_mel, mfcc
):

    wb = Workbook()
    ws = wb.active
    ws.title = "Ringkasan"

    ringkasan = [
        ["Parameter", "Nilai"],
        ["Nama Rekaman", nama],
        ["Sampling Rate", fs],
        ["Frame (ms)", FRAME_MS],
        ["Hop (ms)", HOP_MS],
        ["Jumlah Frame", jumlah_frame],
        ["Sampel per Frame", ukuran],
        ["Sampel Hop", hop],
        ["Jumlah Bin FFT", len(frekuensi)],
        ["Jumlah Filter Mel", JUMLAH_FILTER_MEL],
        ["Jumlah Koefisien MFCC", JUMLAH_MFCC],
        ["Status Validasi", "BERHASIL"]
    ]

    for baris in ringkasan:
        ws.append(baris)

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 25

    header_fft = ["Frekuensi (Hz)"] + [
        f"Frame {i + 1}"
        for i in range(jumlah_frame)
    ]

    data_fft = [
        [frekuensi[k]] + magnitudo[:, k].tolist()
        for k in range(len(frekuensi))
    ]

    buat_sheet(
        wb,
        "FFT_Semua_Frame",
        header_fft,
        data_fft
    )

    data_fft_pertama = [
        [frekuensi[k], magnitudo[0, k]]
        for k in range(len(frekuensi))
    ]

    ws_fft = buat_sheet(
        wb,
        "FFT_Frame_1",
        ["Frekuensi (Hz)", "Magnitudo"],
        data_fft_pertama
    )

    tambah_grafik_excel(
        ws_fft,
        1,
        2,
        "FFT Frame Pertama",
        "D2"
    )

    data_power = [
        [frekuensi[k]] + power[:, k].tolist()
        for k in range(len(frekuensi))
    ]

    buat_sheet(
        wb,
        "Power_Spectrum",
        header_fft,
        data_power
    )

    header_mel = ["Frekuensi (Hz)"] + [
        f"Mel {i + 1}"
        for i in range(bank.shape[0])
    ]

    data_mel = [
        [frekuensi[k]] + bank[:, k].tolist()
        for k in range(len(frekuensi))
    ]

    buat_sheet(
        wb,
        "Mel_Filterbank",
        header_mel,
        data_mel
    )

    header_log = ["Frame"] + [
        f"Log Mel {i + 1}"
        for i in range(log_mel.shape[1])
    ]

    data_log = [
        [i + 1] + log_mel[i].tolist()
        for i in range(jumlah_frame)
    ]

    buat_sheet(
        wb,
        "Log_Mel",
        header_log,
        data_log
    )

    header_mfcc = ["Frame"] + [
        f"MFCC {i + 1}"
        for i in range(mfcc.shape[1])
    ]

    data_mfcc = [
        [i + 1] + mfcc[i].tolist()
        for i in range(jumlah_frame)
    ]

    ws_mfcc = buat_sheet(
        wb,
        "MFCC",
        header_mfcc,
        data_mfcc
    )

    tambah_grafik_excel(
        ws_mfcc,
        1,
        2,
        "MFCC Koefisien Pertama",
        "Q2"
    )

    lokasi = folder / f"{nama}_hasil_anggota3.xlsx"

    wb.save(lokasi)

    return lokasi


def proses_rekaman(file):

    print(f"\nMemproses: {file.name}")

    fs, sinyal = baca_wav(file)

    potong, _, _, _, _ = clipping_berdasarkan_power(
        sinyal, fs
    )

    frames, ukuran, hop = frame_blocking(
        potong, fs
    )

    windowed_frames, _ = hamming_window(frames)

    frekuensi, magnitudo, power = fft_frames(
        windowed_frames, fs
    )

    mfcc, bank, log_mel = hitung_mfcc(
        power, frekuensi, fs
    )

    jumlah_frame = len(frames)

    validasi_hasil(
        frekuensi,
        magnitudo,
        power,
        mfcc,
        bank,
        log_mel,
        jumlah_frame,
        fs
    )

    folder = FOLDER_HASIL / file.stem
    folder.mkdir(parents=True, exist_ok=True)

    grafik_fft(
        folder,
        file.stem,
        frekuensi,
        magnitudo,
        fs,
        hop
    )

    grafik_mel_filterbank(
        folder,
        frekuensi,
        bank
    )

    grafik_mfcc(
        folder,
        file.stem,
        mfcc
    )

    lokasi_excel = ekspor_excel(
        folder,
        file.stem,
        fs,
        jumlah_frame,
        ukuran,
        hop,
        frekuensi,
        magnitudo,
        power,
        bank,
        log_mel,
        mfcc
    )

    print(f"Jumlah Frame : {jumlah_frame}")
    print(f"Ukuran FFT   : {magnitudo.shape}")
    print(f"Ukuran MFCC  : {mfcc.shape}")
    print(f"Status       : BERHASIL")
    print(f"Excel        : {lokasi_excel}")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--file",
        help="Nama rekaman WAV yang akan diproses"
    )

    args = parser.parse_args()

    if args.file:
        daftar_file = [FOLDER_WAV / args.file]
    else:
        daftar_file = sorted(FOLDER_WAV.glob("*.wav"))

    daftar_file = [
        file for file in daftar_file
        if file.name != "DEMO_BUKAN_REKAMAN.wav"
    ]

    if not daftar_file:
        print("Tidak ada file WAV ditemukan")
        return

    berhasil = 0
    gagal = 0

    for file in daftar_file:

        try:
            proses_rekaman(file)
            berhasil += 1

        except Exception as error:
            print(f"GAGAL: {file.name}")
            print(f"Error: {error}")
            gagal += 1

    print("\n========== HASIL PENGUJIAN ==========")
    print(f"Total Rekaman : {len(daftar_file)}")
    print(f"Berhasil      : {berhasil}")
    print(f"Gagal         : {gagal}")
    print("=====================================")

    if gagal:
        raise SystemExit(1)


if __name__ == "__main__":
    main()