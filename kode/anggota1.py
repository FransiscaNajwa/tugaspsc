"""
Modul Anggota 1 - Pengolahan Sinyal dan Citra
Tugas:
1. Membaca berkas audio WAV (validasi 16 kHz, PCM 16-bit, Mono)
2. Normalisasi amplitudo sinyal ke skala [-1.0, 1.0)
3. Melakukan Level Clipping berbasis Short-Time Power untuk memangkas hening (silence)
"""

import numpy as np
from scipy.io import wavfile
from konfigurasi import SAMPLE_RATE, JUMLAH_BIT, JUMLAH_CHANNEL, THRESHOLD_K, DURASI_POWER_MS


def baca_wav(lokasi):
    """
    Membaca berkas audio format WAV mono 16 kHz 16-bit.
    
    Parameter:
        lokasi (str atau Path): Path menuju file audio .wav.
        
    Return:
        fs (int): Sample rate rekaman (harus 16000 Hz).
        sinyal (np.ndarray): Sinyal audio 1D ternormalisasi dalam tipe float64 [-1.0, 1.0).
    """
    fs, data = wavfile.read(str(lokasi))
    
    # Validasi mono (1 channel)
    if data.ndim != JUMLAH_CHANNEL:
        raise ValueError(f"File {lokasi} memiliki {data.ndim} channel. Rekaman harus MONO ({JUMLAH_CHANNEL} channel).")
        
    # Validasi frekuensi sampling (16 kHz)
    if fs != SAMPLE_RATE:
        raise ValueError(f"Sample rate {fs} Hz; harus {SAMPLE_RATE} Hz. Silakan rekam ulang atau konversi dahulu.")
        
    # Validasi kedalaman bit (PCM 16-bit)
    if data.dtype != np.int16:
        raise ValueError(f"Format data adalah {data.dtype}; tugas mewajibkan PCM {JUMLAH_BIT}-bit (int16).")
        
    # Normalisasi int16 (-32768 s.d. 32767) ke float64 rentang [-1.0, 1.0)
    # 32768 berasal dari 2^(JUMLAH_BIT - 1)
    faktor_skala = float(2 ** (JUMLAH_BIT - 1))
    sinyal = data.astype(np.float64) / faktor_skala
    return fs, sinyal


def clipping_berdasarkan_power(sinyal, fs, threshold_k=THRESHOLD_K, durasi_power_ms=DURASI_POWER_MS):
    """
    Melakukan Level Clipping pada sinyal audio dengan memangkas bagian hening di awal dan akhir
    berdasarkan nilai daya (power) tiap blok pendek.
    
    Rumus:
        Power per blok: P_i = (1 / L) * sum(x[n]^2)
        Ambang batas (Threshold): Ambang = mean(P) + K * std(P)
        
    Parameter:
        sinyal (np.ndarray): Array sinyal audio 1D ternormalisasi.
        fs (int): Sample rate audio.
        threshold_k (float): Nilai pengali standar deviasi untuk menentukan ambang batas.
        durasi_power_ms (float): Durasi tiap blok analisis power dalam milidetik (default 20 ms).
        
    Return:
        potong (np.ndarray): Sinyal setelah dipotong dari blok aktif pertama hingga terakhir.
        power (np.ndarray): Array power untuk setiap blok.
        ambang (float): Nilai ambang batas yang digunakan.
        awal (int): Indeks sampel awal pemotongan.
        akhir (int): Indeks sampel akhir pemotongan.
    """
    panjang = max(1, round(fs * durasi_power_ms / 1000))
    nblok = int(np.ceil(len(sinyal) / panjang))
    
    if nblok == 0 or len(sinyal) == 0:
        raise ValueError("Sinyal audio kosong.")
        
    # Hitung mean square (power) per blok pendek
    power = np.array([
        np.mean(sinyal[i * panjang : min((i + 1) * panjang, len(sinyal))] ** 2)
        for i in range(nblok)
    ])
    
    # Hitung threshold berbasis rata-rata dan simpangan baku power
    ambang = power.mean() + threshold_k * power.std()
    
    # Cari blok yang energinya melebihi ambang batas
    aktif = np.flatnonzero(power > ambang)
    
    if len(aktif) == 0:
        raise ValueError(
            f"Tidak terdeteksi segmen suara aktif dengan K={threshold_k}. "
            "Periksa volume rekaman atau turunkan nilai THRESHOLD_K."
        )
        
    # Tentukan indeks sampel awal dan akhir segmen aktif
    awal = int(aktif[0] * panjang)
    akhir = int(min(len(sinyal), (aktif[-1] + 1) * panjang))
    
    potong = sinyal[awal:akhir].copy()
    return potong, power, ambang, awal, akhir


if __name__ == '__main__':
    from konfigurasi import FOLDER_WAV
    
    print("=" * 65)
    print(" DEMO / PENGUJIAN MANDIRI MODUL ANGGOTA 1")
    print(" (Membaca WAV Mono 16 kHz & Level Clipping Berbasis Power)")
    print("=" * 65)
    
    berkas_wav = sorted(FOLDER_WAV.glob('*.wav'))
    if not berkas_wav:
        print(f"[PERINGATAN] Tidak ditemukan berkas .wav di folder: {FOLDER_WAV}")
        print("Silakan rekam suara terlebih dahulu atau jalankan 'python kode/rekam_audio.py'.")
    else:
        print(f"Ditemukan {len(berkas_wav)} berkas WAV di folder data_wav/.\n")
        for berkas in berkas_wav:
            if berkas.name == 'DEMO_BUKAN_REKAMAN.wav':
                continue
            try:
                # 1. Uji fungsi baca_wav
                fs, sinyal = baca_wav(berkas)
                durasi_asli = len(sinyal) / fs
                
                # 2. Uji fungsi clipping_berdasarkan_power
                potong, power, ambang, awal, akhir = clipping_berdasarkan_power(sinyal, fs)
                durasi_potong = len(potong) / fs
                reduksi = (1.0 - len(potong) / len(sinyal)) * 100.0
                
                print(f"[{berkas.name}]")
                print(f"  - Format       : {fs} Hz, PCM {JUMLAH_BIT}-bit, {JUMLAH_CHANNEL} Channel (Mono)")
                print(f"  - Durasi Asli  : {durasi_asli:.3f} s ({len(sinyal)} sampel)")
                print(f"  - Threshold    : {ambang:.6e}")
                print(f"  - Sampel Aktif : {awal} s.d. {akhir} (detik {awal/fs:.3f} s.d. {akhir/fs:.3f})")
                print(f"  - Durasi Potong: {durasi_potong:.3f} s ({len(potong)} sampel)")
                print(f"  - Hening Dibuang: {reduksi:.1f}%")
                print("-" * 65)
            except Exception as e:
                print(f"[GAGAL {berkas.name}]: {e}")
                print("-" * 65)
        print("\n[SELESAI] Modul anggota1.py berfungsi normal dan siap digunakan!")

