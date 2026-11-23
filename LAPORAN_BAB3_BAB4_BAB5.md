# BAB III

# IMPLEMENTASI PROGRAM

Bab ini menguraikan implementasi perangkat lunak dari sistem pra-pemrosesan sinyal wicara dan ekstraksi fitur MFCC. Setiap subbab memuat penjelasan masukan, parameter teknis, keluaran, serta listing program asli yang dapat dieksekusi secara independen.

---

### 3.1 Lingkungan Pengembangan dan Konfigurasi

Sistem dikembangkan menggunakan bahasa pemrograman Python 3.10+ pada sistem operasi Windows 64-bit. Pustaka komputasi yang digunakan meliputi NumPy untuk manipulasi matriks dan array multi-dimensi, SciPy untuk pembacaan berkas audio WAV, kalkulasi rFFT, dan Discrete Cosine Transform (DCT), Matplotlib untuk visualisasi grafik gelombang dan spektrum, serta OpenPyXL untuk ekspor otomatis data numerik ke lembar kerja Microsoft Excel.

Daftar dependensi pustaka perangkat lunak didefinisikan sebagai berikut:

```text
numpy>=1.24.0
scipy>=1.10.0
matplotlib>=3.7.0
openpyxl>=3.1.0
```

Seluruh parameter operasional dan jalur direktori diatur secara terpusat pada berkas `kode/konfigurasi.py` guna memastikan konsistensi pemrosesan lintas anggota kelompok.

#### Listing Program 3.0 — Konfigurasi Proyek (`kode/konfigurasi.py`)

```python
from pathlib import Path

# Path folder
AKAR = Path(__file__).resolve().parent.parent
FOLDER_WAV = AKAR / 'data_wav'
FOLDER_HASIL = AKAR / 'hasil'

FOLDER_WAV.mkdir(parents=True, exist_ok=True)
FOLDER_HASIL.mkdir(parents=True, exist_ok=True)

# Parameter Perekaman & Pengolahan Audio (Wajib dari Dosen)
SAMPLE_RATE = 16000          # 16 kHz (Frekuensi sampling)
JUMLAH_BIT = 16              # 16 bit (Kuantisasi linier PCM int16)
JUMLAH_CHANNEL = 1           # 1 (Mono)
DURASI_POWER_MS = 20         # 20 ms per blok untuk deteksi power clipping
THRESHOLD_K = 0.0            # K=0.0 (Threshold = mean(power)) agar konsonan akhir (seperti 'r', 'k') tidak terpotong
MARGIN_AWAL_BLOK = 3         # Margin awalan (lead-in) 3 blok (60 ms)
MARGIN_AKHIR_BLOK = 8        # Margin akhiran (hangover) 8 blok (160 ms) agar konsonan letup/henti ('k', 'r') tuntas

# Parameter Frame & Windowing (Anggota 2)
FRAME_MS = 25                # 25 ms per frame (400 sampel pada 16 kHz)
HOP_MS = 10                  # 10 ms per hop (160 sampel, overlap 60%)

# Parameter FFT & MFCC (Anggota 3)
JUMLAH_FILTER_MEL = 26       # 26 filter bank segitiga
JUMLAH_MFCC = 13             # 13 koefisien MFCC pertama
```

---

### 3.2 Pembacaan Sinyal WAV

Modul pembacaan bertanggung jawab mengambil data gelombang suara diskrit dari berkas `.wav`, melakukan validasi ketat terhadap integritas format (mono, 16.000 Hz, PCM 16-bit), serta menormalisasi nilai amplitudo integer bertanda ke skala pecahan desimal mengambang.

- Masukan: Path berkas audio berekstensi `.wav`.
- Parameter: `SAMPLE_RATE = 16000`, `JUMLAH_BIT = 16`, `JUMLAH_CHANNEL = 1`.
- Keluaran: Frekuensi sampling `fs` (integer) dan array 1D sinyal audio ternormalisasi bertipe `float64` pada rentang [-1.0, 1.0).

#### Listing Program 3.1 — Pembacaan WAV (`kode/anggota1.py`)

```python
import numpy as np
from scipy.io import wavfile
from konfigurasi import SAMPLE_RATE, JUMLAH_BIT, JUMLAH_CHANNEL

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
```

---

### 3.3 Level Clipping Berbasis Power

Modul level clipping memisahkan segmen suara aktif (*voiced/unvoiced speech*) dari keheningan (*silence*) dan derau ruangan di awal maupun akhir rekaman. Daya rata-rata dihitung per blok 20 ms, dibandingkan dengan ambang batas adaptif `Threshold = mean(P) + K * std(P)`, serta dipadukan dengan margin awal (*lead-in*) 60 ms dan margin akhir (*hangover*) 160 ms guna melindungi letupan konsonan akhir seperti /k/ dan /r/.

- Masukan: Array sinyal ternormalisasi 1D dan frekuensi sampling `fs`.
- Parameter: `durasi_power_ms = 20`, `threshold_k = 0.0`, `margin_awal = 3`, `margin_akhir = 8`.
- Keluaran: Array sinyal hasil clipping, array daya per blok `power`, nilai ambang batas `ambang`, indeks sampel awal `awal`, dan indeks sampel akhir `akhir`.

#### Listing Program 3.2 — Level Clipping Berbasis Power (`kode/anggota1.py`)

```python
import numpy as np
from konfigurasi import THRESHOLD_K, DURASI_POWER_MS, MARGIN_AWAL_BLOK, MARGIN_AKHIR_BLOK

def clipping_berdasarkan_power(sinyal, fs, threshold_k=THRESHOLD_K, durasi_power_ms=DURASI_POWER_MS, margin_awal=MARGIN_AWAL_BLOK, margin_akhir=MARGIN_AKHIR_BLOK):
    """
    Melakukan Level Clipping pada sinyal audio dengan memangkas bagian hening di awal dan akhir
    berdasarkan nilai daya (power) tiap blok pendek serta margin keamanan di batas potongan.
  
    Rumus:
        Power per blok: P_i = (1 / L) * sum(x[n]^2)
        Ambang batas (Threshold): Ambang = mean(P) + K * std(P)
        Margin Keamanan: Lead-in di awal dan Hangover di akhir agar konsonan henti/lemah ('k', 'r') tidak terpotong.
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
      
    # Tentukan indeks sampel awal dan akhir segmen aktif dengan margin keamanan
    blok_awal = max(0, aktif[0] - margin_awal)
    blok_akhir = min(nblok, aktif[-1] + 1 + margin_akhir)
    awal = int(blok_awal * panjang)
    akhir = int(min(len(sinyal), blok_akhir * panjang))
  
    potong = sinyal[awal:akhir].copy()
    return potong, power, ambang, awal, akhir


if __name__ == '__main__':
    from konfigurasi import FOLDER_WAV, JUMLAH_BIT, JUMLAH_CHANNEL
  
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
                fs, sinyal = baca_wav(berkas)
                durasi_asli = len(sinyal) / fs
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
```

---

### 3.4 Frame Blocking

Modul pembingkaian (*frame blocking*) membagi sinyal hasil clipping menjadi matriks dua dimensi berukuran `(jumlah_frame, ukuran_frame)`. Bingkai dibuat bertumpang tindih (*overlap*) sebesar 60% dengan menambahkan *zero-padding* pada akhir sinyal jika panjang total tidak habis dibagi pergeseran *hop*.

- Masukan: Sinyal hasil clipping 1D dan frekuensi sampling `fs`.
- Parameter: `frame_ms = 25` (400 sampel) dan `hop_ms = 10` (160 sampel).
- Keluaran: Matriks 2D `frames` bertipe `float64`, integer `ukuran` (400), dan integer `langkah` (160).

#### Listing Program 3.3 — Frame Blocking (`kode/anggota2.py`)

```python
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
```

---

### 3.5 Hamming Window

Fungsi jendela Hamming dikalikan pada setiap baris bingkai untuk menekan efek pemutusan tiba-tiba di tepi frame (*rectangular discontinuity*), sehingga meredam fenomena kebocoran spektral (*spectral leakage*) sebelum operasi FFT dilakukan.

- Masukan: Matriks bingkai 2D `frames` berukuran `(jumlah_frame, N)`.
- Parameter: Ukuran jendela N = 400 sampel.
- Keluaran: Matriks 2D `windowed_frames` berukuran `(jumlah_frame, N)` dan vektor 1D `window` sepanjang N.

#### Listing Program 3.4 — Hamming Window (`kode/anggota2.py`)

```python
import numpy as np

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
```

---

### 3.6 Fast Fourier Transform

Transformasi Fourier Cepat riil (*Real Fast Fourier Transform* / rFFT) diterapkan pada setiap bingkai berjendela untuk mentransformasikan representasi domain waktu ke domain frekuensi. Dari total N = 400 sampel, dihasilkan N/2 + 1 = 201 bin frekuensi diskrit pada rentang frekuensi 0 hingga 8.000 Hz (fs / 2) dengan resolusi frekuensi sebesar 16.000 / 400 = 40 Hz per bin.

- Masukan: Matriks bingkai berjendela `windowed_frames` 2D dan frekuensi sampling `fs`.
- Parameter: Panjang rFFT `nfft = 400`.
- Keluaran: Vektor sumbu frekuensi `frekuensi` (201 titik), matriks magnitudo spektrum `magnitudo` berukuran `(jumlah_frame, 201)`, dan matriks `power` spectrum |X[k]|^2 / N.

#### Listing Program 3.5 — Fast Fourier Transform (`kode/anggota3.py`)

```python
import numpy as np
from scipy.fft import rfft, rfftfreq

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
```

---

### 3.7 Mel-Frequency Cepstral Coefficients

#### 3.7.1 Konversi Hertz–Mel dan Mel Filterbank

Power spectrum setiap bingkai dipetakan ke persepsi pendengaran manusia menggunakan 26 filter bank segitiga yang terdistribusi secara linier di bawah 1.000 Hz dan logaritmik di atas 1.000 Hz.

#### Listing Program 3.6 — Konversi Hertz-Mel & Filterbank (`kode/anggota3.py`)

```python
import numpy as np
from konfigurasi import JUMLAH_FILTER_MEL

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
```

#### 3.7.2 Ekstraksi MFCC

Hasil perkalian matriks power spectrum dengan filterbank Mel menghasilkan energi per pita Mel. Setelah dihitung logaritmanya dengan penambahan konstanta stabilisasi epsilon = 1e-12, Discrete Cosine Transform tipe II ortogonal diterapkan untuk menghasilkan 13 koefisien MFCC pertama per bingkai.

- Masukan: Matriks `power_spectrum`, array `frekuensi`, dan frekuensi sampling `fs`.
- Parameter: `jumlah_filter = 26`, `jumlah_mfcc = 13`, `norm = 'ortho'`.
- Keluaran: Matriks koefisien MFCC `koef` berukuran `(jumlah_frame, 13)`, matriks filter bank `bank`, dan matriks `log_mel`.

#### Listing Program 3.7 — Ekstraksi Koefisien MFCC (`kode/anggota3.py`)

```python
import numpy as np
from scipy.fft import dct
from konfigurasi import JUMLAH_FILTER_MEL, JUMLAH_MFCC

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
```

---

### 3.8 Integrasi Program dan Ekspor Excel

Program pipeline utama menghubungkan seluruh tahapan dari pembacaan berkas audio hingga ekspor lengkap ke format lembar kerja Excel `.xlsx` multi-sheet (`Ringkasan`, `Sinyal_Asli`, `Clipping`, `Frame_1`, `Hamming_1`, `FFT_1`, `MFCC`, dan gambar visualisasi).

#### Listing Program 3.8 — Alur Integrasi Eksekusi (`kode/jalankan.py`)

```python
from anggota1 import baca_wav, clipping_berdasarkan_power
from anggota2 import frame_blocking, hamming_window
from anggota3 import fft_frames, hitung_mfcc

# Eksekusi pipeline terintegrasi
fs, sinyal = baca_wav(file_wav)
potong, power_blok, ambang, awal, akhir = clipping_berdasarkan_power(sinyal, fs)
frames, ukuran, langkah = frame_blocking(potong, fs)
windowed, window = hamming_window(frames)
frek, magnitudo, power_spec = fft_frames(windowed, fs)
mfcc, bank, log_mel = hitung_mfcc(power_spec, frek, fs)
```

#### Listing Program 3.9 — Contoh Ekspor Nilai FFT ke Excel (`kode/jalankan.py`)

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = 'FFT_Frame_1'
ws.append(['Frekuensi (Hz)', 'Magnitudo'])
for f, m in zip(frek, magnitudo[0]):
    ws.append([float(f), float(m)])
wb.save('hasil_fft.xlsx')
```

---

# BAB IV

# HASIL DAN PEMBAHASAN

Pengujian dilakukan secara menyeluruh terhadap seluruh **10 berkas rekaman suara asli kelompok** yang mencakup 5 pasang kata berbeda berbahasa Indonesia (*belajar*, *berjalan*, *duduk*, *makan*, dan *minum*). Seluruh hasil pengujian numerik dan visualisasi grafik lengkap dari masing-masing anggota kelompok disajikan secara komprehensif pada subbab di bawah ini.

---

### 4.1 Hasil Perekaman Sinyal Suara (10 Berkas Audio)

Seluruh berkas audio direkam menggunakan mikrofon dengan parameter standar: frekuensi sampling fs = 16.000 Hz, kuantisasi 16-bit linier PCM, dan 1 saluran (mono).

#### Tabel 4.1 Karakteristik Sinyal Asli 10 Berkas Rekaman Audio

| No | Nama Berkas   | Kata     | Durasi Asli (s) | Jumlah Sampel Asli | Estimasi Hening Awal (s) | Amplitudo Maksimum | Amplitudo Minimum |
| :-: | :------------ | :------- | :-------------: | :----------------: | :----------------------: | :----------------: | :---------------: |
| 1 | belajar1.wav  | belajar  |     2,652 s     |       42.432       |    0,00 s s.d. 1,00 s    |       +0,382       |      -0,412      |
| 2 | belajar2.wav  | belajar  |     2,834 s     |       45.344       |    0,00 s s.d. 1,04 s    |       +0,345       |      -0,389      |
| 3 | berjalan1.wav | berjalan |     3,042 s     |       48.672       |    0,00 s s.d. 1,24 s    |       +0,412       |      -0,435      |
| 4 | berjalan2.wav | berjalan |     2,990 s     |       47.840       |    0,00 s s.d. 0,78 s    |       +0,398       |      -0,402      |
| 5 | duduk1.wav    | duduk    |     2,782 s     |       44.512       |    0,00 s s.d. 1,24 s    |       +0,378       |      -0,392      |
| 6 | duduk2.wav    | duduk    |     2,964 s     |       47.424       |    0,00 s s.d. 1,56 s    |       +0,361       |      -0,375      |
| 7 | makan1.wav    | makan    |     2,288 s     |       36.608       |    0,00 s s.d. 0,54 s    |       +0,425       |      -0,448      |
| 8 | makan2.wav    | makan    |     1,872 s     |       29.952       |    0,00 s s.d. 0,54 s    |       +0,410       |      -0,415      |
| 9 | minum1.wav    | minum    |     2,522 s     |       40.352       |    0,00 s s.d. 1,04 s    |       +0,438       |      -0,452      |
| 10 | minum2.wav    | minum    |     2,600 s     |       41.600       |    0,00 s s.d. 0,84 s    |       +0,421       |      -0,430      |

#### Daftar Grafik Sinyal Suara Asli (10 Grafik):

1. **belajar1**: `hasil/belajar1/01_sinyal_asli.png`
2. **belajar2**: `hasil/belajar2/01_sinyal_asli.png`
3. **berjalan1**: `hasil/berjalan1/01_sinyal_asli.png`
4. **berjalan2**: `hasil/berjalan2/01_sinyal_asli.png`
5. **duduk1**: `hasil/duduk1/01_sinyal_asli.png`
6. **duduk2**: `hasil/duduk2/01_sinyal_asli.png`
7. **makan1**: `hasil/makan1/01_sinyal_asli.png`
8. **makan2**: `hasil/makan2/01_sinyal_asli.png`
9. **minum1**: `hasil/minum1/01_sinyal_asli.png`
10. **minum2**: `hasil/minum2/01_sinyal_asli.png`

**Analisis Hasil Perekaman 10 Berkas:**
Dari visualisasi gelombang ke-10 berkas terlihat bahwa seluruh rekaman memiliki jeda hening alami (*lead silence*) di awal berkisar antara 0,54 detik hingga 1,56 detik serta jeda hening penutup (*trailing silence*) sekitar 0,4 hingga 1,0 detik setelah pengucapan selesai. Amplitudo pada fase hening berada sangat dekat dengan nol (|amplitudo| < 0,005), sedangkan amplitudo pada fase suara aktif berkisar antara 0,34 hingga 0,45. Durasi total rekaman asli berkisar antara 1,872 detik (terpendek pada `makan2`) hingga 3,042 detik (terpanjang pada `berjalan1`). Variasi durasi dipengaruhi oleh jumlah suku kata (kata 3 suku kata *berjalan* dan *belajar* memiliki durasi rata-rata lebih panjang daripada kata 2 suku kata *makan*, *minum*, dan *duduk*) serta tempo bicara alami subjek.

---

### 4.2 Hasil Level Clipping Berbasis Power (10 Berkas Audio)

Tahap level clipping memangkas bagian hening di awal dan akhir rekaman dengan menghitung daya per blok 20 ms (320 sampel), menerapkan ambang batas adaptif K = 0,0 (Threshold = mean(P)), serta memberikan margin awal 3 blok (60 ms) dan margin akhir 8 blok (160 ms).

#### Tabel 4.2 Data Hasil Level Clipping 10 Berkas Audio

| No | Nama Berkas   | Kata     | Durasi Awal (s) | Durasi Potong (s) | Reduksi Hening (%) | Nilai Threshold Power | Sampel Aktif (Awal s.d. Akhir) | Status Keutuhan Fonem                          |
| :-: | :------------ | :------- | :-------------: | :---------------: | :----------------: | :-------------------: | :----------------------------: | :--------------------------------------------- |
| 1 | belajar1.wav  | belajar  |     2,652 s     |      0,900 s      |       66,1%       |     1,307 x 10^-3     |       16.000 s.d. 30.400       | Utuh; fonem akhir getar /r/ tuntas             |
| 2 | belajar2.wav  | belajar  |     2,834 s     |      0,920 s      |       67,5%       |     1,037 x 10^-3     |       16.640 s.d. 31.360       | Utuh; suku kata /be-la-jar/ utuh               |
| 3 | berjalan1.wav | berjalan |     3,042 s     |      1,080 s      |       64,5%       |     6,973 x 10^-4     |       19.840 s.d. 37.120       | Utuh; awalan /b/ dan akhiran nasal /n/ terjaga |
| 4 | berjalan2.wav | berjalan |     2,990 s     |      1,180 s      |       60,5%       |     5,334 x 10^-4     |       12.480 s.d. 31.360       | Utuh; seluruh 3 suku kata terlindungi          |
| 5 | duduk1.wav    | duduk    |     2,782 s     |      0,720 s      |       74,1%       |     1,098 x 10^-3     |       19.840 s.d. 31.360       | Utuh; letupan konsonan /k/ tidak terpotong     |
| 6 | duduk2.wav    | duduk    |     2,964 s     |      0,780 s      |       73,7%       |     1,495 x 10^-3     |       24.960 s.d. 37.440       | Utuh; suku kata /-duk/ terdengar sempurna      |
| 7 | makan1.wav    | makan    |     2,288 s     |      0,820 s      |       64,2%       |     6,118 x 10^-4     |       8.640 s.d. 21.760       | Utuh; konsonan sengau /m/ dan /n/ tuntas       |
| 8 | makan2.wav    | makan    |     1,872 s     |      0,780 s      |       58,3%       |     5,128 x 10^-4     |       8.640 s.d. 21.120       | Utuh; artikulasi kata jelas                    |
| 9 | minum1.wav    | minum    |     2,522 s     |      0,740 s      |       70,7%       |     3,480 x 10^-3     |       16.640 s.d. 28.480       | Utuh; vokal /i/ dan penutup /m/ utuh           |
| 10 | minum2.wav    | minum    |     2,600 s     |      0,800 s      |       69,2%       |     2,304 x 10^-3     |       13.440 s.d. 26.240       | Utuh; nasal bilabial awal-akhir terlindungi    |

#### Daftar Grafik Sinyal Clipping & Kurva Power (10 Grafik):

1. **belajar1**: `hasil/belajar1/02_sinyal_clipping.png`
2. **belajar2**: `hasil/belajar2/02_sinyal_clipping.png`
3. **berjalan1**: `hasil/berjalan1/02_sinyal_clipping.png`
4. **berjalan2**: `hasil/berjalan2/02_sinyal_clipping.png`
5. **duduk1**: `hasil/duduk1/02_sinyal_clipping.png`
6. **duduk2**: `hasil/duduk2/02_sinyal_clipping.png`
7. **makan1**: `hasil/makan1/02_sinyal_clipping.png`
8. **makan2**: `hasil/makan2/02_sinyal_clipping.png`
9. **minum1**: `hasil/minum1/02_sinyal_clipping.png`
10. **minum2**: `hasil/minum2/02_sinyal_clipping.png`

#### Daftar Grafik Evaluasi 3-Panel Anggota 1 (10 Grafik Tambahan Anggota 1):

Grafik evaluasi ini menampilkan 3 panel secara vertikal: (a) Sinyal Suara Asli, (b) Kurva Short-Time Power per Blok 20 ms vs Garis Threshold Adaptif, dan (c) Sinyal Hasil Pemotongan Suara Aktif.

1. **belajar1**: `hasil/evaluasi_anggota1/evaluasi_belajar1.png`
2. **belajar2**: `hasil/evaluasi_anggota1/evaluasi_belajar2.png`
3. **berjalan1**: `hasil/evaluasi_anggota1/evaluasi_berjalan1.png`
4. **berjalan2**: `hasil/evaluasi_anggota1/evaluasi_berjalan2.png`
5. **duduk1**: `hasil/evaluasi_anggota1/evaluasi_duduk1.png`
6. **duduk2**: `hasil/evaluasi_anggota1/evaluasi_duduk2.png`
7. **makan1**: `hasil/evaluasi_anggota1/evaluasi_makan1.png`
8. **makan2**: `hasil/evaluasi_anggota1/evaluasi_makan2.png`
9. **minum1**: `hasil/evaluasi_anggota1/evaluasi_minum1.png`
10. **minum2**: `hasil/evaluasi_anggota1/evaluasi_minum2.png`

**Pembahasan Analisis Level Clipping 10 Berkas:**

1. Efisiensi Pemangkasan Data: Durasi sinyal berhasil dipangkas dari rentang awal 1,87–3,04 detik menjadi 0,72–1,18 detik. Persentase reduksi hening konsisten tinggi antara 58,3% hingga 74,1%, yang membuktikan bahwa algoritma menghemat lebih dari setengah ukuran data sebelum diproses ke tahap FFT.
2. Adaptabilitas Ambang Batas: Nilai threshold secara otomatis menyesuaikan tingkat energi masing-masing rekaman, berada pada rentang 5,13 x 10^-4 (pada `makan2`) hingga 3,48 x 10^-3 (pada `minum1`). Rekaman dengan volume suara lebih lantang menghasilkan nilai ambang batas yang lebih tinggi tanpa konfigurasi manual.
3. Penyelamatan Fonem Kritis:
   - Pada kata *duduk1* dan *duduk2*, penurunan energi tajam saat rongga mulut tertutup untuk melafalkan konsonan henti /k/ berhasil diatasi oleh margin akhir (*hangover*) 8 blok (160 ms), sehingga kata tidak terpenggal menjadi *"dud"*.
   - Pada kata *belajar1* dan *belajar2*, getaran fonem /r/ di akhir kata yang energinya sangat rendah berhasil dipertahankan tuntas dengan penentuan faktor K = 0,0 dan margin akhir 8 blok, mencegah pemotongan kata menjadi *"belaj"*.
   - Pada kata *makan* dan *minum*, margin awal 3 blok (60 ms) melindungi awalan sengau bilabial /m/ yang memiliki energi awal lebih lembut daripada vokal utama.

---

### 4.3 Hasil Frame Blocking (10 Berkas Audio)

Sinyal hasil clipping dipotong menjadi bingkai-bingkai pendek dengan panjang frame N = 400 sampel (25 ms pada 16 kHz) dan pergeseran hop H = 160 sampel (10 ms, menghasilkan overlap 60% atau 240 sampel).

#### Tabel 4.3 Data Frame Blocking 10 Berkas Audio

| No | Nama Berkas   | Kata     | Panjang Sinyal Potong (Sampel) | Sampel per Frame (N) | Hop Sampel (H) | Overlap (%) | Jumlah Frame | Zero Padding Akhir (Sampel) |
| :-: | :------------ | :------- | :----------------------------: | :------------------: | :------------: | :---------: | :----------: | :-------------------------: |
| 1 | belajar1.wav  | belajar  |             14.400             |         400         |      160      |  240 (60%)  |   89 frame   |          80 sampel          |
| 2 | belajar2.wav  | belajar  |             14.720             |         400         |      160      |  240 (60%)  |   91 frame   |         160 sampel         |
| 3 | berjalan1.wav | berjalan |             17.280             |         400         |      160      |  240 (60%)  |  107 frame  |          80 sampel          |
| 4 | berjalan2.wav | berjalan |             18.880             |         400         |      160      |  240 (60%)  |  117 frame  |          80 sampel          |
| 5 | duduk1.wav    | duduk    |             11.520             |         400         |      160      |  240 (60%)  |   71 frame   |          80 sampel          |
| 6 | duduk2.wav    | duduk    |             12.480             |         400         |      160      |  240 (60%)  |   77 frame   |          80 sampel          |
| 7 | makan1.wav    | makan    |             13.120             |         400         |      160      |  240 (60%)  |   81 frame   |          80 sampel          |
| 8 | makan2.wav    | makan    |             12.480             |         400         |      160      |  240 (60%)  |   77 frame   |          80 sampel          |
| 9 | minum1.wav    | minum    |             11.840             |         400         |      160      |  240 (60%)  |   73 frame   |          80 sampel          |
| 10 | minum2.wav    | minum    |             12.800             |         400         |      160      |  240 (60%)  |   79 frame   |          80 sampel          |

#### Daftar Grafik Gelombang Frame Pertama (10 Grafik):

1. **belajar1**: `hasil_anggota2/belajar1/03_frame_pertama.png`
2. **belajar2**: `hasil_anggota2/belajar2/03_frame_pertama.png`
3. **berjalan1**: `hasil_anggota2/berjalan1/03_frame_pertama.png`
4. **berjalan2**: `hasil_anggota2/berjalan2/03_frame_pertama.png`
5. **duduk1**: `hasil_anggota2/duduk1/03_frame_pertama.png`
6. **duduk2**: `hasil_anggota2/duduk2/03_frame_pertama.png`
7. **makan1**: `hasil_anggota2/makan1/03_frame_pertama.png`
8. **makan2**: `hasil_anggota2/makan2/03_frame_pertama.png`
9. **minum1**: `hasil_anggota2/minum1/03_frame_pertama.png`
10. **minum2**: `hasil_anggota2/minum2/03_frame_pertama.png`

**Analisis Frame Blocking 10 Berkas:**
Jumlah frame berkorelasi linier dengan panjang durasi pengucapan kata. Kata terpanjang (*berjalan2*, 1,180 s) menghasilkan 117 frame, sedangkan kata terpendek (*duduk1*, 0,720 s) menghasilkan 71 frame. Overlap sebesar 60% (240 sampel) memastikan tidak ada informasi transisi antarfonem yang terputus di batas bingkai, dan penambahan zero-padding otomatis pada frame terakhir menjamin dimensi matriks selalu konsisten tanpa pemotongan data secara paksa.

---

### 4.4 Hasil Hamming Window (10 Berkas Audio)

Setiap bingkai dikalikan dengan fungsi pembobot Hamming Window:

$$
w[n] = 0,54 - 0,46 \cos\left(\frac{2\pi n}{N - 1}\right), \quad 0 \le n \le N - 1
$$

#### Tabel 4.4 Pengaruh Hamming Window pada Frame Pertama 10 Berkas Audio

| No | Nama Berkas   | Amplitudo Awal (n=0) Sebelum Window | Amplitudo Awal (n=0) Sesudah Window | Amplitudo Akhir (n=399) Sebelum Window | Amplitudo Akhir (n=399) Sesudah Window | Efek Reduksi Spectral Leakage        |
| :-: | :------------ | :---------------------------------: | :---------------------------------: | :------------------------------------: | :------------------------------------: | :----------------------------------- |
| 1 | belajar1.wav  |              -0,000305              |              -0,000024              |               +0,000427               |               +0,000034               | Tepi diredam menuju mendekati nol    |
| 2 | belajar2.wav  |              +0,000244              |              +0,000020              |               -0,000366               |               -0,000029               | Diskontinuitas batas ditiadakan      |
| 3 | berjalan1.wav |              -0,000427              |              -0,000034              |               +0,000183               |               +0,000015               | Transisi batas mulus                 |
| 4 | berjalan2.wav |              +0,000366              |              +0,000029              |               -0,000488               |               -0,000039               | Side-lobe ditekan hingga -43 dB      |
| 5 | duduk1.wav    |              -0,000427              |              -0,000034              |               +0,000305               |               +0,000024               | Bentuk gelombang tengah terjaga      |
| 6 | duduk2.wav    |              +0,000183              |              +0,000015              |               -0,000244               |               -0,000020               | Amplitudo ujung mengecil halus       |
| 7 | makan1.wav    |              -0,000244              |              -0,000020              |               +0,000366               |               +0,000029               | Tepi terdistorsi persegi dieliminasi |
| 8 | makan2.wav    |              +0,000305              |              +0,000024              |               -0,000183               |               -0,000015               | Sinyal siap di-FFT tanpa kebocoran   |
| 9 | minum1.wav    |              -0,000366              |              -0,000029              |               +0,000427               |               +0,000034               | Redaman ujung >90%                   |
| 10 | minum2.wav    |              +0,000427              |              +0,000034              |               -0,000305               |               -0,000024               | Tepi tertekan stabil                 |

#### Daftar Grafik Hamming Window Frame Pertama (10 Grafik):

1. **belajar1**: `hasil_anggota2/belajar1/04_hamming_frame_pertama.png`
2. **belajar2**: `hasil_anggota2/belajar2/04_hamming_frame_pertama.png`
3. **berjalan1**: `hasil_anggota2/berjalan1/04_hamming_frame_pertama.png`
4. **berjalan2**: `hasil_anggota2/berjalan2/04_hamming_frame_pertama.png`
5. **duduk1**: `hasil_anggota2/duduk1/04_hamming_frame_pertama.png`
6. **duduk2**: `hasil_anggota2/duduk2/04_hamming_frame_pertama.png`
7. **makan1**: `hasil_anggota2/makan1/04_hamming_frame_pertama.png`
8. **makan2**: `hasil_anggota2/makan2/04_hamming_frame_pertama.png`
9. **minum1**: `hasil_anggota2/minum1/04_hamming_frame_pertama.png`
10. **minum2**: `hasil_anggota2/minum2/04_hamming_frame_pertama.png`

#### Daftar Grafik Perbandingan Khusus Anggota 2 (10 Grafik Tambahan Anggota 2):

Grafik ini secara khusus menampilkan perbandingan visual langsung antara bentuk gelombang frame sebelum windowing (garis biru) dan setelah dikalikan fungsi jendela Hamming (garis oranye) dalam satu diagram komparasi:

1. **belajar1**: `hasil_anggota2/belajar1/perbandingan_anggota2_belajar1.png`
2. **belajar2**: `hasil_anggota2/belajar2/perbandingan_anggota2_belajar2.png`
3. **berjalan1**: `hasil_anggota2/berjalan1/perbandingan_anggota2_berjalan1.png`
4. **berjalan2**: `hasil_anggota2/berjalan2/perbandingan_anggota2_berjalan2.png`
5. **duduk1**: `hasil_anggota2/duduk1/perbandingan_anggota2_duduk1.png`
6. **duduk2**: `hasil_anggota2/duduk2/perbandingan_anggota2_duduk2.png`
7. **makan1**: `hasil_anggota2/makan1/perbandingan_anggota2_makan1.png`
8. **makan2**: `hasil_anggota2/makan2/perbandingan_anggota2_makan2.png`
9. **minum1**: `hasil_anggota2/minum1/perbandingan_anggota2_minum1.png`
10. **minum2**: `hasil_anggota2/minum2/perbandingan_anggota2_minum2.png`

**Analisis Hamming Window 10 Berkas:**
Pada seluruh 10 rekaman, perkalian dengan nilai bobot Hamming w[0] = w[N-1] = 0,08 berhasil mereduksi amplitudo di batas tepi frame sebesar 92%, membawanya sangat mendekati nol tanpa mengubah karakteristik bentuk gelombang di bagian tengah frame. Hal ini secara efektif mencegah timbulnya frekuensi tinggi palsu (*high-frequency artifacts*) akibat diskontinuitas persegi (*rectangular windowing*).

---

### 4.5 Hasil Fast Fourier Transform (10 Berkas Audio)

Operasi Real Fast Fourier Transform (rFFT) diterapkan pada panjang N = 400 sampel per bingkai, menghasilkan 201 bin frekuensi diskrit pada rentang frekuensi 0 hingga 8.000 Hz dengan resolusi frekuensi sebesar 40 Hz per bin.

#### Tabel 4.5 Hasil Evaluasi Spektral FFT 10 Berkas Audio

| No | Nama Berkas   | Kata     | Dimensi Matriks FFT | Jumlah Bin Frekuensi | Resolusi Frekuensi | Pita Frekuensi Dominan Formant (Hz) | Karakteristik Spektral Dominan         |
| :-: | :------------ | :------- | :-----------------: | :------------------: | :----------------: | :---------------------------------: | :------------------------------------- |
| 1 | belajar1.wav  | belajar  |      89 x 201      |       201 bin       |       40 Hz       |        160 Hz s.d. 1.840 Hz        | Formant vokal /a/ dan /e/ kuat         |
| 2 | belajar2.wav  | belajar  |      91 x 201      |       201 bin       |       40 Hz       |        160 Hz s.d. 1.800 Hz        | Resonansi vokal ganda jelas            |
| 3 | berjalan1.wav | berjalan |      107 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 2.120 Hz        | Energi spektrum terdistribusi lebar    |
| 4 | berjalan2.wav | berjalan |      117 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 2.080 Hz        | Spektrum padat di 3 suku kata          |
| 5 | duduk1.wav    | duduk    |      71 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 1.200 Hz        | Puncak formant vokal /u/ rendah        |
| 6 | duduk2.wav    | duduk    |      77 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 1.240 Hz        | Konsentrasi energi di frekuensi rendah |
| 7 | makan1.wav    | makan    |      81 x 201      |       201 bin       |       40 Hz       |        160 Hz s.d. 1.680 Hz        | Resonansi nasal /m/ & vokal /a/        |
| 8 | makan2.wav    | makan    |      77 x 201      |       201 bin       |       40 Hz       |        160 Hz s.d. 1.720 Hz        | Puncak energi tengah tajam             |
| 9 | minum1.wav    | minum    |      73 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 1.480 Hz        | Formant vokal tinggi /i/ dan /u/       |
| 10 | minum2.wav    | minum    |      79 x 201      |       201 bin       |       40 Hz       |        120 Hz s.d. 1.520 Hz        | Dominasi energi frekuensi bawah        |

#### Daftar Grafik Spektrum FFT Frame Pertama (10 Grafik):

1. **belajar1**: `hasil_anggota3/belajar1/fft_frame_pertama.png`
2. **belajar2**: `hasil_anggota3/belajar2/fft_frame_pertama.png`
3. **berjalan1**: `hasil_anggota3/berjalan1/fft_frame_pertama.png`
4. **berjalan2**: `hasil_anggota3/berjalan2/fft_frame_pertama.png`
5. **duduk1**: `hasil_anggota3/duduk1/fft_frame_pertama.png`
6. **duduk2**: `hasil_anggota3/duduk2/fft_frame_pertama.png`
7. **makan1**: `hasil_anggota3/makan1/fft_frame_pertama.png`
8. **makan2**: `hasil_anggota3/makan2/fft_frame_pertama.png`
9. **minum1**: `hasil_anggota3/minum1/fft_frame_pertama.png`
10. **minum2**: `hasil_anggota3/minum2/fft_frame_pertama.png`

#### Daftar Grafik Spektrum FFT Seluruh Frame (10 Grafik Tambahan Anggota 3):

Grafik spektrogram 2D ini menampilkan kontur sebaran energi seluruh bin frekuensi terhadap sumbu waktu (seluruh frame rekaman):

1. **belajar1**: `hasil_anggota3/belajar1/fft_seluruh_frame.png`
2. **belajar2**: `hasil_anggota3/belajar2/fft_seluruh_frame.png`
3. **berjalan1**: `hasil_anggota3/berjalan1/fft_seluruh_frame.png`
4. **berjalan2**: `hasil_anggota3/berjalan2/fft_seluruh_frame.png`
5. **duduk1**: `hasil_anggota3/duduk1/fft_seluruh_frame.png`
6. **duduk2**: `hasil_anggota3/duduk2/fft_seluruh_frame.png`
7. **makan1**: `hasil_anggota3/makan1/fft_seluruh_frame.png`
8. **makan2**: `hasil_anggota3/makan2/fft_seluruh_frame.png`
9. **minum1**: `hasil_anggota3/minum1/fft_seluruh_frame.png`
10. **minum2**: `hasil_anggota3/minum2/fft_seluruh_frame.png`

**Analisis Spektral FFT 10 Berkas:**
Seluruh 10 berkas rekaman menunjukkan konsentrasi energi terbesar pada frekuensi rendah dan menengah (100 Hz hingga 2.500 Hz), yang merupakan lokasi formant suara manusia (F1, F2, F3). Pada kata *duduk* dan *minum*, energi terpusat pada rentang yang lebih rendah (120–1.400 Hz) akibat pengaruh vokal tertutup /u/ dan /i/, sedangkan kata *belajar*, *berjalan*, dan *makan* memiliki sebaran formant yang lebih tinggi hingga 2.100 Hz akibat keterbukaan artikulasi vokal /a/. Di atas 5.000 Hz, magnitudo spektrum meluruh secara tajam menuju level derau dasar.

---

### 4.6 Hasil Mel Filterbank dan MFCC (10 Berkas Audio)

Power spectrum dipetakan ke dalam 26 filter bank segitiga Mel, dihitung logaritmanya, dan ditransformasikan menggunakan DCT tipe II ortogonal untuk menghasilkan 13 koefisien MFCC per frame.

#### Tabel 4.6 Sampel 13 Koefisien MFCC Frame Pertama (Frame 0) untuk 10 Berkas Audio

| No | Nama Berkas   | MFCC 1 | MFCC 2 | MFCC 3 | MFCC 4 | MFCC 5 | MFCC 6 | MFCC 7 | MFCC 8 | MFCC 9 | MFCC 10 | MFCC 11 | MFCC 12 | MFCC 13 |
| :-: | :------------ | :----: | :----: | :----: | :----: | :----: | :----: | :----: | :----: | :----: | :-----: | :-----: | :-----: | :-----: |
| 1 | belajar1.wav  | -68,14 | +6,12 | +2,45 | +0,72 | +3,85 | -1,95 | -0,12 | +1,45 | -0,52 |  -0,88  |  +0,45  |  +0,95  |  -2,15  |
| 2 | belajar2.wav  | -65,32 | +5,85 | +2,10 | +0,65 | +4,10 | -2,05 | -0,08 | +1,60 | -0,60 |  -1,02  |  +0,52  |  +1,10  |  -2,40  |
| 3 | berjalan1.wav | -71,20 | +4,95 | +1,65 | +0,95 | +3,60 | -1,80 | +0,15 | +1,72 | -0,48 |  -0,95  |  +0,68  |  +1,35  |  -2,60  |
| 4 | berjalan2.wav | -69,85 | +5,20 | +1,80 | +0,88 | +3,75 | -1,92 | +0,10 | +1,65 | -0,55 |  -1,10  |  +0,58  |  +1,28  |  -2,52  |
| 5 | duduk1.wav    | -64,92 | +5,36 | +1,90 | +0,81 | +4,34 | -2,12 | -0,06 | +1,86 | -0,66 |  -1,17  |  +0,61  |  +1,23  |  -2,82  |
| 6 | duduk2.wav    | -66,15 | +5,10 | +1,75 | +0,75 | +4,15 | -2,20 | -0,10 | +1,78 | -0,72 |  -1,25  |  +0,55  |  +1,15  |  -2,70  |
| 7 | makan1.wav    | -67,40 | +5,75 | +2,25 | +0,55 | +3,90 | -2,08 | -0,05 | +1,55 | -0,62 |  -1,05  |  +0,48  |  +1,05  |  -2,35  |
| 8 | makan2.wav    | -65,80 | +5,60 | +2,15 | +0,62 | +4,02 | -1,98 | -0,02 | +1,62 | -0,58 |  -0,98  |  +0,50  |  +1,12  |  -2,28  |
| 9 | minum1.wav    | -63,75 | +5,45 | +1,95 | +0,78 | +4,20 | -2,15 | -0,08 | +1,80 | -0,68 |  -1,20  |  +0,58  |  +1,18  |  -2,75  |
| 10 | minum2.wav    | -64,50 | +5,30 | +1,88 | +0,82 | +4,28 | -2,10 | -0,05 | +1,82 | -0,65 |  -1,15  |  +0,62  |  +1,20  |  -2,68  |

#### Daftar Grafik Visualisasi Mel Filterbank 26 Filter Segitiga (10 Grafik):

1. **belajar1**: `hasil_anggota3/belajar1/mel_filterbank.png`
2. **belajar2**: `hasil_anggota3/belajar2/mel_filterbank.png`
3. **berjalan1**: `hasil_anggota3/berjalan1/mel_filterbank.png`
4. **berjalan2**: `hasil_anggota3/berjalan2/mel_filterbank.png`
5. **duduk1**: `hasil_anggota3/duduk1/mel_filterbank.png`
6. **duduk2**: `hasil_anggota3/duduk2/mel_filterbank.png`
7. **makan1**: `hasil_anggota3/makan1/mel_filterbank.png`
8. **makan2**: `hasil_anggota3/makan2/mel_filterbank.png`
9. **minum1**: `hasil_anggota3/minum1/mel_filterbank.png`
10. **minum2**: `hasil_anggota3/minum2/mel_filterbank.png`

#### Daftar Grafik Heatmap Matriks MFCC (10 Grafik Tambahan Anggota 3):

Grafik heatmap ini memetakan nilai matriks koefisien MFCC berukuran (jumlah_frame x 13) menggunakan gradasi warna:

1. **belajar1**: `hasil_anggota3/belajar1/mfcc_heatmap.png`
2. **belajar2**: `hasil_anggota3/belajar2/mfcc_heatmap.png`
3. **berjalan1**: `hasil_anggota3/berjalan1/mfcc_heatmap.png`
4. **berjalan2**: `hasil_anggota3/berjalan2/mfcc_heatmap.png`
5. **duduk1**: `hasil_anggota3/duduk1/mfcc_heatmap.png`
6. **duduk2**: `hasil_anggota3/duduk2/mfcc_heatmap.png`
7. **makan1**: `hasil_anggota3/makan1/mfcc_heatmap.png`
8. **makan2**: `hasil_anggota3/makan2/mfcc_heatmap.png`
9. **minum1**: `hasil_anggota3/minum1/mfcc_heatmap.png`
10. **minum2**: `hasil_anggota3/minum2/mfcc_heatmap.png`

#### Daftar Grafik Kurva Dinamika Koefisien MFCC (10 Grafik Tambahan Anggota 3):

Grafik kurva garis ini menampilkan trayektori pergerakan nilai 13 koefisien MFCC sepanjang transisi frame:

1. **belajar1**: `hasil_anggota3/belajar1/mfcc_koefisien.png`
2. **belajar2**: `hasil_anggota3/belajar2/mfcc_koefisien.png`
3. **berjalan1**: `hasil_anggota3/berjalan1/mfcc_koefisien.png`
4. **berjalan2**: `hasil_anggota3/berjalan2/mfcc_koefisien.png`
5. **duduk1**: `hasil_anggota3/duduk1/mfcc_koefisien.png`
6. **duduk2**: `hasil_anggota3/duduk2/mfcc_koefisien.png`
7. **makan1**: `hasil_anggota3/makan1/mfcc_koefisien.png`
8. **makan2**: `hasil_anggota3/makan2/mfcc_koefisien.png`
9. **minum1**: `hasil_anggota3/minum1/mfcc_koefisien.png`
10. **minum2**: `hasil_anggota3/minum2/mfcc_koefisien.png`

**Analisis Karakteristik Koefisien MFCC 10 Berkas:**

1. Perilaku Koefisien Orde Pertama (c1): Pada frame pertama (margin lead-in), nilai c1 bernilai negatif besar (-63,75 hingga -71,20) karena c1 berbanding lurus dengan log-energi rata-rata bingkai. Begitu sinyal memasuki fase vokal inti kata, nilai c1 naik tajam mencapai nilai -20 hingga -35, mencerminkan peningkatan energi fonetik yang kuat.
2. Karakteristik Amplop Spektral (c2 s.d. c6): Koefisien c2 hingga c6 menunjukkan variasi unik yang konsisten di antara pasangan kata yang sama. Sebagai contoh, pasangan `makan1` dan `makan2` memiliki kemiripan nilai c2 (+5,75 dan +5,60) serta c3 (+2,25 dan +2,15), sedangkan pasangan `duduk1` dan `duduk2` memiliki nilai c5 yang lebih tinggi (+4,34 dan +4,15). Hal ini membuktikan bahwa koefisien orde rendah berhasil mengisolasi bentuk resonansi saluran vokal (*vocal tract filter*) yang menjadi ciri pembeda antarkata.
3. Penyusutan Koefisien Orde Tinggi (c7 s.d. c13): Nilai koefisien ke-7 hingga ke-13 pada seluruh 10 berkas berosilasi dengan magnitudo kecil di sekitar nol (antara -2,82 hingga +1,86), membuktikan sifat decorrelation dan energy compaction yang sangat baik dari transformasi DCT.

---

### 4.7 Rekapitulasi Komprehensif dan Validasi 10 Rekaman

Tabel 4.7 menyajikan lembar rekapitulasi data menyeluruh dari seluruh tahapan pemrosesan untuk ke-10 berkas rekaman audio kelompok:

#### Tabel 4.7 Rekapitulasi Data Lengkap Pemrosesan 10 Berkas Audio

| No | Nama Berkas   | Kata     | Durasi Asli (s) | Durasi Clipping (s) | Reduksi Hening (%) | Nilai Threshold Power | Jumlah Frame | Dimensi Matriks FFT | Dimensi Matriks MFCC | Status Validasi Sistem |
| :-: | :------------ | :------- | :-------------: | :-----------------: | :----------------: | :-------------------: | :----------: | :-----------------: | :------------------: | :--------------------: |
| 1 | belajar1.wav  | belajar  |     2,652 s     |       0,900 s       |       66,1%       |     1,307 x 10^-3     |   89 frame   |      89 x 201      |       89 x 13       |    BERHASIL (VALID)    |
| 2 | belajar2.wav  | belajar  |     2,834 s     |       0,920 s       |       67,5%       |     1,037 x 10^-3     |   91 frame   |      91 x 201      |       91 x 13       |    BERHASIL (VALID)    |
| 3 | berjalan1.wav | berjalan |     3,042 s     |       1,080 s       |       64,5%       |     6,973 x 10^-4     |  107 frame  |      107 x 201      |       107 x 13       |    BERHASIL (VALID)    |
| 4 | berjalan2.wav | berjalan |     2,990 s     |       1,180 s       |       60,5%       |     5,334 x 10^-4     |  117 frame  |      117 x 201      |       117 x 13       |    BERHASIL (VALID)    |
| 5 | duduk1.wav    | duduk    |     2,782 s     |       0,720 s       |       74,1%       |     1,098 x 10^-3     |   71 frame   |      71 x 201      |       71 x 13       |    BERHASIL (VALID)    |
| 6 | duduk2.wav    | duduk    |     2,964 s     |       0,780 s       |       73,7%       |     1,495 x 10^-3     |   77 frame   |      77 x 201      |       77 x 13       |    BERHASIL (VALID)    |
| 7 | makan1.wav    | makan    |     2,288 s     |       0,820 s       |       64,2%       |     6,118 x 10^-4     |   81 frame   |      81 x 201      |       81 x 13       |    BERHASIL (VALID)    |
| 8 | makan2.wav    | makan    |     1,872 s     |       0,780 s       |       58,3%       |     5,128 x 10^-4     |   77 frame   |      77 x 201      |       77 x 13       |    BERHASIL (VALID)    |
| 9 | minum1.wav    | minum    |     2,522 s     |       0,740 s       |       70,7%       |     3,480 x 10^-3     |   73 frame   |      73 x 201      |       73 x 13       |    BERHASIL (VALID)    |
| 10 | minum2.wav    | minum    |     2,600 s     |       0,800 s       |       69,2%       |     2,304 x 10^-3     |   79 frame   |      79 x 201      |       79 x 13       |    BERHASIL (VALID)    |

**Kesimpulan Evaluasi Menyeluruh 10 Berkas:**

1. Tingkat Keberhasilan 100%: Seluruh 10 rekaman audio berhasil diproses tanpa galat (*zero-error*) dari pembacaan WAV hingga pembentukan matriks fitur MFCC.
2. Keteraturan Struktur Data: Jumlah frame selalu menghasilkan bilangan bulat positif yang proporsional terhadap panjang ucapan (71 s.d. 117 frame). Dimensi kolom matriks FFT selalu konsisten 201 titik dan dimensi kolom matriks MFCC selalu konsisten 13 koefisien sesuai rancangan arsitektur penugasan.
3. Penyimpanan Terverifikasi: Seluruh grafik keluaran dan berkas lembar kerja Microsoft Excel (`.xlsx`) multi-sheet telah diekspor dan diverifikasi kelengkapannya pada folder proyek (`hasil/`, `hasil_anggota1/`, `hasil_anggota2/`, dan `hasil_anggota3/`).

---

# BAB V

# KESIMPULAN DAN SARAN

### 5.1 Kesimpulan

Berdasarkan perancangan, implementasi sistem perangkat lunak, serta pengujian mendalam terhadap seluruh 10 berkas rekaman suara asli kelompok, dapat ditarik kesimpulan sebagai berikut:

1. Modul pembacaan berkas audio berhasil memvalidasi spesifikasi berkas masukan (Mono, frekuensi sampling 16 kHz, PCM 16-bit linier) dan melakukan normalisasi nilai amplitudo integer rentang [-32768, 32767] ke rentang desimal mengambang [-1.0, 1.0) dengan presisi ganda (*float64*).
2. Algoritma Level Clipping berbasis *short-time power* per blok 20 ms dengan ambang batas adaptif (K = 0,0) dan penambahan margin keamanan (margin awal 3 blok / 60 ms dan margin akhir 8 blok / 160 ms) terbukti efektif membuang 58,3% hingga 74,1% segmen hening tanpa merusak keutuhan fonem kata, khususnya konsonan henti lemah /k/ pada kata *duduk* dan konsonan getar /r/ pada kata *belajar*.
3. Pembingkaian (*frame blocking*) dengan panjang frame 25 ms (400 sampel) dan pergeseran *hop* 10 ms (160 sampel, overlap 60%) menghasilkan antara 71 hingga 117 bingkai per kata dengan kontinuitas antarkerangka waktu yang terjaga mulus.
4. Perkalian dengan fungsi Hamming Window berhasil meredam amplitudo pada kedua batas ujung frame secara halus menuju nol (penyusutan amplitudo batas hingga 92%), sehingga efektif menekan diskontinuitas tepi dan meminimalkan fenomena kebocoran spektral (*spectral leakage*).
5. Implementasi Real Fast Fourier Transform (rFFT) menghasilkan 201 bin frekuensi diskrit pada rentang 0 hingga 8.000 Hz dengan resolusi 40 Hz per bin, yang secara akurat memetakan energi formasi pita suara vokal pada daerah frekuensi rendah dan menengah (100 Hz hingga 2.500 Hz).
6. Ekstraksi fitur menggunakan 26 filter bank segitiga Mel dan transformasi DCT tipe II ortogonal berhasil memadatkan informasi spektral suara ke dalam 13 koefisien MFCC per frame. Seluruh data numerik dan grafik dari 10 berkas telah terverifikasi dan terekspor secara otomatis ke dalam berkas Microsoft Excel `.xlsx`.

### 5.2 Saran

Untuk pengembangan dan penyempurnaan sistem pada penelitian atau penugasan selanjutnya, disarankan beberapa hal berikut:

1. Penambahan Fitur Turunan Dinamis: Ekstraksi fitur MFCC dapat ditingkatkan dengan menambahkan koefisien delta (Delta MFCC) dan delta-delta (Delta-Delta MFCC) untuk menangkap dinamika perubahan laju ucapan antar-waktu (*velocity* dan *acceleration*).
2. Kombinasi Algoritma VAD: Algoritma level clipping berbasis daya dapat dipadukan dengan parameter Zero Crossing Rate (ZCR) atau Spectral Entropy agar deteksi suara aktif lebih tangguh (*robust*) terhadap derau latar belakang ruangan yang bersifat fluktuatif.
3. Pengembangan ke Tahap Pengenalan Wicara: Matriks fitur MFCC berdimensi (Jumlah Frame x 13) yang telah dihasilkan pada praktikum ini dapat langsung digunakan sebagai masukan bagi algoritma klasifikasi kata atau pengenal pembicara, seperti Dynamic Time Warping (DTW), Hidden Markov Models (HMM), atau Convolutional Neural Network (CNN).
