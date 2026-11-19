"""
Modul Anggota 3 - Pengolahan Sinyal dan Citra
Tugas:
1. Menghitung Fast Fourier Transform (FFT) pada tiap frame
2. Membuat Filter Bank Mel
3. Menghitung koefisien MFCC (Mel-Frequency Cepstral Coefficients)
"""

import numpy as np
from scipy.fft import rfft, rfftfreq, dct
from konfigurasi import JUMLAH_FILTER_MEL, JUMLAH_MFCC


def fft_frames(windowed_frames, fs):
    """
    Menghitung Real Fast Fourier Transform (rFFT) untuk setiap frame.
    
    Parameter:
        windowed_frames (np.ndarray): Matriks 2D (jumlah_frame, N).
        fs (int): Frekuensi sampling audio.
        
    Return:
        frekuensi (np.ndarray): Sumbu frekuensi (0 s.d. fs/2 Hz).
        magnitudo (np.ndarray): Nilai mutlak dari spektrum FFT.
        power (np.ndarray): Power spectrum |FFT|^2 / N.
    """
    nfft = windowed_frames.shape[1]
    spektrum = rfft(windowed_frames, n=nfft, axis=1)
    frekuensi = rfftfreq(nfft, d=1 / fs)
    magnitudo = np.abs(spektrum)
    power = (magnitudo ** 2) / nfft
    return frekuensi, magnitudo, power


def hz_ke_mel(hz):
    """Konversi frekuensi Hertz ke skala Mel."""
    return 2595.0 * np.log10(1.0 + np.asarray(hz) / 700.0)


def mel_ke_hz(mel):
    """Konversi skala Mel kembali ke frekuensi Hertz."""
    return 700.0 * (10.0 ** (np.asarray(mel) / 2595.0) - 1.0)


def filter_bank_mel(frekuensi, fs, banyak_filter=JUMLAH_FILTER_MEL):
    """
    Membuat matriks filter bank Mel berbentuk segitiga beririsan.
    
    Parameter:
        frekuensi (np.ndarray): Array sumbu frekuensi dari rFFT.
        fs (int): Frekuensi sampling.
        banyak_filter (int): Jumlah filter segitiga (default 26).
        
    Return:
        bank (np.ndarray): Matriks filter bank berukuran (banyak_filter, len(frekuensi)).
    """
    batas_mel = np.linspace(hz_ke_mel(0), hz_ke_mel(fs / 2), banyak_filter + 2)
    titik_hz = mel_ke_hz(batas_mel)
    bank = np.zeros((banyak_filter, len(frekuensi)))
    
    for j in range(banyak_filter):
        kiri, tengah, kanan = titik_hz[j : j + 3]
        bank[j] = np.maximum(
            0.0,
            np.minimum(
                (frekuensi - kiri) / (tengah - kiri),
                (kanan - frekuensi) / (kanan - tengah)
            )
        )
    return bank


def hitung_mfcc(power_spectrum, frekuensi, fs, jumlah_filter=JUMLAH_FILTER_MEL, jumlah_mfcc=JUMLAH_MFCC):
    """
    Menghitung koefisien MFCC dari power spectrum.
    
    Langkah:
    1. Filter bank Mel x Power spectrum
    2. Logaritma energi Mel (dengan epsilon)
    3. Discrete Cosine Transform (DCT Type II)
    
    Return:
        koef (np.ndarray): Matriks koefisien MFCC (jumlah_frame, jumlah_mfcc).
        bank (np.ndarray): Matriks filter bank Mel.
        log_mel (np.ndarray): Log energi Mel sebelum DCT.
    """
    bank = filter_bank_mel(frekuensi, fs, banyak_filter=jumlah_filter)
    energi_mel = power_spectrum @ bank.T
    log_mel = np.log(np.maximum(energi_mel, 1e-12))
    koef = dct(log_mel, type=2, axis=1, norm='ortho')[:, :jumlah_mfcc]
    return koef, bank, log_mel
