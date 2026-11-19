"""
Modul Anggota 2 - Pengolahan Sinyal dan Citra
Tugas:
1. Melakukan pemotongan sinyal menjadi frame-frame beririsan (Frame Blocking)
2. Menerapkan Jendela Hamming (Hamming Window) pada tiap frame
"""

import numpy as np
from konfigurasi import FRAME_MS, HOP_MS


def frame_blocking(sinyal, fs, frame_ms=FRAME_MS, hop_ms=HOP_MS):
    """
    Membagi sinyal 1D menjadi matriks 2D frame beririsan dengan zero padding pada frame terakhir.
    
    Parameter:
        sinyal (np.ndarray): Sinyal audio 1D (biasanya hasil clipping).
        fs (int): Frekuensi sampling.
        frame_ms (float): Panjang frame dalam milidetik (misal 25 ms).
        hop_ms (float): Pergeseran antar frame dalam milidetik (misal 10 ms).
        
    Return:
        frames (np.ndarray): Matriks berukuran (jumlah_frame, ukuran_frame).
        ukuran (int): Jumlah sampel per frame (misal 400 sampel).
        langkah (int): Jumlah sampel hop/pergeseran (misal 160 sampel).
    """
    ukuran = round(fs * frame_ms / 1000)
    langkah = round(fs * hop_ms / 1000)
    
    if len(sinyal) == 0:
        raise ValueError("Sinyal setelah clipping kosong.")
    if ukuran < 2 or langkah < 1:
        raise ValueError("Parameter ukuran frame atau hop tidak valid.")
        
    # Hitung jumlah total frame yang dibutuhkan
    if len(sinyal) <= ukuran:
        banyak = 1
    else:
        banyak = int(np.ceil((len(sinyal) - ukuran) / langkah)) + 1
        
    # Zero padding di akhir jika panjang sinyal kurang dari panjang total frame
    total = (banyak - 1) * langkah + ukuran
    padded = np.pad(sinyal, (0, total - len(sinyal)), mode='constant')
    
    # Ambil tiap frame
    frames = np.stack([padded[i * langkah : i * langkah + ukuran] for i in range(banyak)])
    return frames, ukuran, langkah


def hamming_window(frames):
    """
    Mengalikan setiap baris frame dengan jendela Hamming:
    w[n] = 0.54 - 0.46 * cos(2 * pi * n / (N - 1))
    
    Parameter:
        frames (np.ndarray): Matriks 2D frame berukuran (jumlah_frame, N).
        
    Return:
        windowed_frames (np.ndarray): Matriks frame setelah dikalikan window.
        window (np.ndarray): Vektor jendela Hamming 1D sepanjang N.
    """
    ukuran = frames.shape[1]
    window = np.hamming(ukuran)
    windowed_frames = frames * window[None, :]
    return windowed_frames, window
