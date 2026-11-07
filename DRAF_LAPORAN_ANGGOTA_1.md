# LAPORAN PRAKTIKUM PENGOLAHAN SINYAL DAN CITRA (TUGAS 1)
**Topik**: Ekstraksi Fitur Sinyal Suara Berbasis MFCC (Diagram Blok 6 Tahap)  
**Kelompok**: 3 Anggota  
**Bagian Tanggung Jawab Anggota 1**: 
- **BAB I**: Pendahuluan (Latar Belakang, Rumusan Masalah, Tujuan, Ruang Lingkup)
- **BAB III Subbab 3.1 & 3.2**: Implementasi Perekaman Audio & Level Clipping Berbasis Power
- **BAB IV Subbab 4.1**: Hasil dan Pembahasan Input Sinyal & Level Clipping (Tabel 10 Rekaman & Analisis)

---

## BAB I: PENDAHULUAN

### 1.1 Latar Belakang
Pengolahan sinyal wicara (*speech signal processing*) merupakan salah satu pilar utama dalam pemrosesan sinyal digital dan kecerdasan buatan, khususnya pada sistem pengenalan suara otomatis (*Automatic Speech Recognition* / ASR), identifikasi pembicara, dan kendali perangkat berbasis suara. Sinyal suara manusia pada dasarnya adalah gelombang tekanan akustik kontinu yang kemudian dikonversi oleh transduser (mikrofon) menjadi sinyal listrik analog, dan selanjutnya disampel serta dikuantisasi menjadi sinyal digital diskrit waktu ($x[n]$) dengan frekuensi sampling tertentu ($F_s$).

Pada perekaman sinyal suara secara langsung, gelombang yang tertangkap oleh mikrofon tidak hanya mencakup suara artikulasi kata yang diucapkan, tetapi juga merekam segmen hening (*silence*) serta derau lingkungan (*ambient noise*) di awal sebelum kata diucapkan maupun di akhir setelah pengucapan selesai. Keberadaan segmen hening ini tidak membawa informasi fonetik bahasa, meningkatkan volume data yang tidak perlu, dan berpotensi mendistorsi perhitungan matriks spektral pada tahapan transformasi frekuensi lanjutan.

Oleh karena itu, tahapan awal berupa deteksi aktivitas suara (*Voice Activity Detection*) melalui metode **Level Clipping berbasis Short-Time Power** sangat krusial. Metode ini memisahkan segmen wicara aktif dari keheningan berdasarkan energi rata-rata sinyal per blok pendek. Setelah sinyal aktif dipotong, proses pengolahan dilanjutkan secara sekuensial melalui pemotongan berbingkai (*Frame Blocking*), pembobotan tepi jendela (*Hamming Window*), transformasi domain frekuensi (*Fast Fourier Transform* / FFT), hingga pemodelan persepsi pendengaran manusia menggunakan koefisien *Mel-Frequency Cepstral Coefficients* (MFCC). Melalui praktikum ini, pipeline pengolahan suara diimplementasikan secara komprehensif pada 5 pasang kata berbeda (total 10 berkas WAV) dengan keluaran numerik dan grafik yang disajikan pada Microsoft Excel sesuai arahan modul.

### 1.2 Rumusan Masalah
1. Bagaimana cara membaca, memvalidasi kepatuhan spesifikasi teknis masukan (Mono, 16 kHz, PCM 16-bit), dan menormalisasi amplitudo gelombang suara berformat WAV?
2. Bagaimana cara merancang dan mengimplementasikan algoritma *Level Clipping* berbasis *Short-Time Power* dengan penentuan ambang batas (*threshold*) adaptif untuk memangkas segmen hening tanpa memotong suku kata awal maupun akhir?
3. Bagaimana menyusun pipeline pengolahan terstandar sehingga setiap data keluaran dapat divisualisasikan secara numerik dan grafik dalam lembar kerja Microsoft Excel sesuai diagram blok penugasan?

### 1.3 Tujuan Praktikum
1. Mahasiswa memahami konsep sampel, amplitudo, domain waktu, dan normalisasi kuantisasi linier 16-bit ($[-32768, 32767]$) menjadi bilangan pecahan mengambang ($[-1.0, 1.0)$) merujuk pada materi kuliah (halaman 18–21).
2. Mahasiswa mampu mengimplementasikan algoritma *Level Clipping* menggunakan perhitungan *power*, nilai rata-rata, simpangan baku, dan penentuan *threshold* adaptif merujuk pada materi kuliah (halaman 42–44).
3. Mahasiswa mampu menguji dan menganalisis keandalan pemotongan hening pada 10 berkas rekaman WAV asli kelompok serta membuktikan keutuhan fonem kata yang dihasilkan.

### 1.4 Ruang Lingkup dan Batasan Masalah
1. Data masukan menggunakan 5 pasang kata berbeda (total 10 rekaman audio asli):
   - Pasang 1: `belajar1.wav` dan `belajar2.wav`
   - Pasang 2: `berjalan1.wav` dan `berjalan2.wav`
   - Pasang 3: `duduk1.wav` dan `duduk2.wav`
   - Pasang 4: `makan1.wav` dan `makan2.wav`
   - Pasang 5: `minum1.wav` dan `minum2.wav`
2. Spesifikasi teknis rekaman masukan dikunci secara ketat pada frekuensi sampling $16.000\text{ Hz}$ (16 kHz), resolusi 16-bit PCM, dan 1 saluran (Mono).
3. Alur pemrosesan mengikuti diagram blok resmi: Sinyal Suara WAV $\rightarrow$ Level Clipping (Power) $\rightarrow$ Frame Blocking $\rightarrow$ Hamming Window $\rightarrow$ FFT $\rightarrow$ MFCC.
4. Parameter bersama kelompok yang disepakati: blok power $20\text{ ms}$, faktor pengali threshold $K = 0.5$, panjang frame $25\text{ ms}$ (400 sampel), pergeseran hop $10\text{ ms}$ (160 sampel / 60% overlap), 26 filter bank Mel, dan 13 koefisien MFCC.
5. Luaran berupa listing kode program teks, grafik visualisasi per blok, dan workbook Microsoft Excel (.xlsx) yang memuat data numerik serta scatter chart.

---

## BAB III: METODOLOGI DAN IMPLEMENTASI (BAGIAN ANGGOTA 1)

### 3.1 Perekaman Audio dan Spesifikasi Sinyal Suara
Sinyal suara didapatkan dengan cara merekam suara secara langsung menggunakan mikrofon di ruang tertutup yang tenang. Sesuai format panduan tugas dosen, parameter perekaman ditetapkan sebagai berikut:
- **Frekuensi Sampling ($F_s$)**: 16 kHz (16.000 Hz)
- **Jumlah Bit**: 16-bit (Linear PCM `int16`)
- **Jumlah Channel**: 1 (Mono)
- **Format Berkas**: WAV (*Waveform Audio File Format*)

Perekaman dilakukan dengan memberikan jeda hening sesaat (~0,5 detik) sebelum penekanan tombol bicara/mulai mengucapkan kata, dan diakhiri sesaat setelah pengucapan selesai sebelum perekaman dihentikan. Tujuannya adalah memastikan terdapat zona hening (*silence buffer*) di awal dan akhir sinyal sebagai bahan uji algoritma pemotongan (*clipping*).

### 3.2 Implementasi Level Clipping Berbasis Short-Time Power

Sesuai template 7 elemen wajib dari Modul Praktikum Bab 9:

#### 1. Tujuan Tahap
Memisahkan segmen suara aktif dari jeda hening (*silence removal*) di awal (*head*) dan akhir (*tail*) rekaman secara otomatis, sehingga sinyal yang diserahkan ke Anggota 2 hanya memuat informasi wicara yang relevan.

#### 2. Rumus dari Materi Kuliah (Materi Kuliah Halaman 42–44)
- **Normalisasi Sinyal**:
  Kuantisasi 16-bit bertanda memiliki rentang nilai $[-2^{15}, 2^{15}-1] = [-32768, 32767]$. Normalisasi ke skala $[-1.0, 1.0)$ dilakukan dengan:
  $$x_{\text{norm}}[n] = \frac{x[n]}{2^{15}} = \frac{x[n]}{32768.0}$$
- **Daya Rata-Rata per Blok Pendek (*Short-Time Power*)**:
  Sinyal dibagi ke dalam blok berdurasi pendek $L$ sampel. Daya rata-rata blok ke-$i$ dihitung dengan:
  $$P_i = \frac{1}{L} \sum_{n=0}^{L-1} x^2[i \cdot L + n]$$
- **Ambang Batas Adaptif (*Threshold*)**:
  Dihitung rata-rata daya seluruh blok ($\mu_P = \frac{1}{M}\sum_{i=1}^M P_i$) dan simpangan baku daya ($\sigma_P = \sqrt{\frac{1}{M}\sum_{i=1}^M (P_i - \mu_P)^2}$). Ambang batas ditentukan oleh:
  $$\text{Threshold} = \mu_P + K \times \sigma_P$$

#### 3. Parameter dan Alasan Pemilihan
- **Durasi Blok Power = 20 ms ($L = 320$ sampel pada 16 kHz)**: Dipilih durasi 20 ms karena sinyal wicara bersifat *quasi-stationary* (karakteristik stasioner pendek) dalam rentang waktu 10–30 ms. Durasi 20 ms cukup pendek untuk menangkap onset suku kata, namun cukup panjang untuk meredam fluktuasi sesaat.
- **Faktor Pengali Simpangan Baku ($K = 0.5$)**: Parameter $K = 0.5$ merupakan nilai optimum empiris pada ruangan tenang; nilai ini cukup tinggi agar tidak terpicu oleh derau hening ruangan ($\text{Power} < \text{Threshold}$), sekaligus cukup rendah sehingga konsonan awal bervolume pelan tetap berada di atas ambang batas.

#### 4. Kontrak Input dan Output (Sesuai Bab 6 Modul)
- **Fungsi `baca_wav`**:
  - *Input*: Path berkas audio `.wav`
  - *Output*: $F_s$ (16.000 Hz), Sinyal 1D float64 $[-1.0, 1.0)$
- **Fungsi `clipping_berdasarkan_power`**:
  - *Input*: `sinyal` (array 1D float), `fs` (int)
  - *Output*: `potong` (array 1D sinyal aktif), `power` (vektor daya per blok), `ambang` (float), `awal` (indeks sampel awal), `akhir` (indeks sampel akhir)
  - *Penerima output*: Anggota 2 (untuk proses *Frame Blocking*).

#### 5. Listing Program Per Blok Berformat Teks (Plain Text)
Berikut adalah listing kode program murni Anggota 1 pada berkas `kode/anggota1.py`:

```python
"""
Blok 1: Pembacaan Sinyal Suara dan Level Clipping Berbasis Power
Penulis: Anggota 1
File: kode/anggota1.py
"""
import numpy as np
from scipy.io import wavfile
from konfigurasi import SAMPLE_RATE, JUMLAH_BIT, JUMLAH_CHANNEL, THRESHOLD_K, DURASI_POWER_MS

def baca_wav(lokasi):
    """Membaca file audio WAV mono 16 kHz 16-bit dan menormalisasi ke float [-1, 1)."""
    fs, data = wavfile.read(str(lokasi))
    
    # Validasi mono
    if data.ndim != JUMLAH_CHANNEL:
        raise ValueError(f"File {lokasi} memiliki {data.ndim} channel. Rekaman harus MONO ({JUMLAH_CHANNEL} channel).")
        
    # Validasi frekuensi sampling
    if fs != SAMPLE_RATE:
        raise ValueError(f"Sample rate {fs} Hz; harus {SAMPLE_RATE} Hz. Rekam ulang atau konversi dahulu.")
        
    # Validasi kedalaman bit kuantisasi
    if data.dtype != np.int16:
        raise ValueError(f"Format data adalah {data.dtype}; tugas mewajibkan PCM {JUMLAH_BIT}-bit (int16).")
        
    # Normalisasi int16 ke float64 rentang [-1.0, 1.0)
    faktor_skala = float(2 ** (JUMLAH_BIT - 1))
    sinyal = data.astype(np.float64) / faktor_skala
    return fs, sinyal

def clipping_berdasarkan_power(sinyal, fs, threshold_k=THRESHOLD_K, durasi_power_ms=DURASI_POWER_MS):
    """Memotong hening awal-akhir berdasarkan Short-Time Power blok pendek."""
    panjang = max(1, round(fs * durasi_power_ms / 1000))
    nblok = int(np.ceil(len(sinyal) / panjang))
    
    if nblok == 0 or len(sinyal) == 0:
        raise ValueError("Sinyal audio kosong.")
        
    # Hitung power (mean square) tiap blok 20 ms
    power = np.array([
        np.mean(sinyal[i * panjang : min((i + 1) * panjang, len(sinyal))] ** 2)
        for i in range(nblok)
    ])
    
    # Hitung threshold adaptif: mean(power) + K * std(power)
    ambang = power.mean() + threshold_k * power.std()
    
    # Cari blok pertama dan terakhir yang melebihi ambang
    aktif = np.flatnonzero(power > ambang)
    if len(aktif) == 0:
        raise ValueError(f"Tidak terdeteksi segmen suara aktif dengan K={threshold_k}.")
        
    awal = int(aktif[0] * panjang)
    akhir = int(min(len(sinyal), (aktif[-1] + 1) * panjang))
    
    potong = sinyal[awal:akhir].copy()
    return potong, power, ambang, awal, akhir
```

#### 6. Penjelasan Kode
- **Baris 10–23 (`baca_wav`)**: Fungsi membaca header dan konten array audio. Dilakukan 3 lapis validasi ketat: menolak jika stereo (`data.ndim != 1`), menolak jika sampling rate bukan 16000 Hz, dan menolak jika bukan PCM 16-bit. Normalisasi dilakukan dengan membagi $2^{15} = 32768.0$ agar nilai berada pada rentang nyaman $[-1.0, 1.0)$.
- **Baris 26–36 (`clipping_berdasarkan_power`)**: Menghitung jumlah sampel per blok $20\text{ ms}$ ($L = 16000 \times 20 / 1000 = 320$ sampel). Sinyal dipotong menjadi $M$ blok, lalu dihitung nilai rata-rata kuadrat amplitudonya (`mean(x**2)`).
- **Baris 38–48**: Menghitung ambang batas menggunakan fungsi vektor `power.mean()` dan `power.std()`. Fungsi `np.flatnonzero(power > ambang)` mengekstrak indeks blok yang aktif. Titik sampel awal diambil dari blok aktif pertama dikalikan $L$, dan sampel akhir diambil dari akhir blok aktif terakhir.

---

## BAB IV: HASIL DAN PEMBAHASAN (BAGIAN ANGGOTA 1)

### 4.1 Hasil dan Analisis Level Clipping pada 10 Berkas Rekaman Asli

Pengujian dilakukan terhadap 10 berkas rekaman audio asli kelompok menggunakan skrip `kode/jalankan_anggota1.py` dan `kode/uji_anggota1.py`. Seluruh berkas berhasil divalidasi dan dipotong tanpa error.

#### Tabel Hasil Pengujian Nyata 10 Berkas Audio:

| No | Berkas Rekaman | Kata | Durasi Asli (s) | Durasi Clipping (s) | Reduksi Hening (%) | Nilai Threshold ($P_{th}$) | Sampel Aktif (Awal–Akhir) | Status Keutuhan Sinyal |
| :-: | :--- | :---: | :-: | :-: | :-: | :-: | :-: | :---: |
| 1 | `belajar1.wav` | belajar | 2.652 s | 0.580 s | 78.1% | $2.886 \times 10^{-3}$ | 16960 s.d. 26240 | Utuh, fonem /b/ & /r/ terjaga |
| 2 | `belajar2.wav` | belajar | 2.834 s | 0.620 s | 78.1% | $2.257 \times 10^{-3}$ | 17600 s.d. 27520 | Utuh, suku kata awal-akhir utuh |
| 3 | `berjalan1.wav`| berjalan| 3.042 s | 0.780 s | 74.4% | $1.473 \times 10^{-3}$ | 20800 s.d. 33280 | Utuh, konsonan /b/ & /n/ jelas |
| 4 | `berjalan2.wav`| berjalan| 2.990 s | 0.860 s | 71.2% | $1.169 \times 10^{-3}$ | 13440 s.d. 27200 | Utuh, artikulasi 3 suku kata utuh |
| 5 | `duduk1.wav` | duduk | 2.782 s | 0.500 s | 82.0% | $2.735 \times 10^{-3}$ | 20800 s.d. 28800 | Utuh, letupan /d/ & /k/ tidak hilang |
| 6 | `duduk2.wav` | duduk | 2.964 s | 0.540 s | 81.8% | $3.623 \times 10^{-3}$ | 25920 s.d. 34560 | Utuh, pemotongan tepat di ujung kata |
| 7 | `makan1.wav` | makan | 2.288 s | 0.560 s | 75.5% | $1.307 \times 10^{-3}$ | 9600 s.d. 18560 | Utuh, nasal /m/ & /n/ tidak terpotong |
| 8 | `makan2.wav` | makan | 1.872 s | 0.540 s | 71.2% | $1.043 \times 10^{-3}$ | 9920 s.d. 18560 | Utuh, pola energi wicara stabil |
| 9 | `minum1.wav` | minum | 2.522 s | 0.500 s | 80.2% | $7.091 \times 10^{-3}$ | 17600 s.d. 25600 | Utuh, vokal /i/ dan /u/ utuh |
| 10| `minum2.wav` | minum | 2.600 s | 0.580 s | 77.7% | $4.807 \times 10^{-3}$ | 14400 s.d. 23680 | Utuh, fonem penutup /m/ tidak terpotong |

#### Analisis Grafik Bentuk Gelombang (Waveform Display)
*(Semua grafik tersimpan di folder `hasil_anggota1/<nama_kata>/`)*

1. **Analisis Pemangkasan Jeda Hening**:
   Sesuai template kalimat analisis modul:
   > *"Setelah Level Clipping, durasi sinyal berubah dari 2,652 s menjadi 0,580 s pada `belajar1.wav`, dan dari 3,042 s menjadi 0,780 s pada `berjalan1.wav` karena blok dengan power rendah pada awal dan akhir rekaman tidak disertakan. Pemeriksaan gelombang menunjukkan bahwa seluruh bagian pengucapan kata masih utuh ketika diverifikasi dan diperdengarkan. Nilai threshold yang digunakan berkisar antara $1,04 \times 10^{-3}$ hingga $7,09 \times 10^{-3}$, sesuai pengujian terhadap rekaman asli kelompok."*
   
2. **Efisiensi Pengurangan Data**:
   Algoritma berhasil memangkas antara **71,2% hingga 82,0%** dari total sampel awal rekaman. Pada kata `duduk1.wav`, pemangkasan mencapai 82% (dari 44.512 sampel menjadi 8.000 sampel). Ini membuktikan bahwa tanpa *Level Clipping*, lebih dari 70% daya komputasi pada tahapan *Frame Blocking*, *Hamming*, *FFT*, dan *MFCC* akan terbuang percuma hanya untuk memproses derau hening ruangan.

3. **Verifikasi Keutuhan Fonetik Kata**:
   Pemeriksaan visual pada `01_sinyal_asli.png` dan `02_sinyal_clipping.png` serta plot evaluasi 3-panel di `hasil/evaluasi_anggota1/` membuktikan:
   - Fonem konsonan letup (*plosive*) seperti /d/ dan /b/ di awal kata `duduk`, `belajar`, dan `berjalan` memiliki transisi energi cepat yang langsung melampaui garis threshold, sehingga titik potong awal tidak memotong awalan kata.
   - Fonem sengau (*nasal*) seperti /m/ dan /n/ pada kata `makan` dan `minum` memiliki energi yang lebih lembut namun tetap berada di atas nilai ambang adaptif $K = 0.5$, sehingga suku kata awal dan akhir tidak mengalami cacat pemotongan.

4. **Verifikasi Bukti pada Microsoft Excel**:
   Data keluaran numerik Anggota 1 telah tersimpan pada file `.xlsx` di folder `hasil_anggota1/<kata>/`:
   - Sheet `Ringkasan_Anggota1`: Berisi rekapitulasi parameter durasi asli, durasi potong, rasio reduksi, dan nilai threshold.
   - Sheet `Sinyal_Asli`: Memuat kolom waktu ($s$) dan amplitudo asli lengkap dengan diagram tebar (*Scatter Plot* Excel).
   - Sheet `Clipping`: Memuat kolom waktu ($s$) dan amplitudo sinyal aktif hasil clipping lengkap dengan diagram tebar (*Scatter Plot* Excel).
   - Sheet `Grafik_Anggota1`: Menyematkan gambar grafik garis Python resolusi tinggi sebagai verifikasi visual.

---

## CHECKLIST EVALUASI AKHIR ANGGOTA 1 (Merujuk Bab 7 & 12 Modul)

| No | Parameter Pemeriksaan Bab 7 Modul | Hasil Evaluasi Kelompok | Status |
| :-: | :--- | :--- | :-: |
| 1 | **Format WAV Sesuai Aturan** | 16.000 Hz, Mono (1 Ch), PCM 16-bit (`int16`) divalidasi ketat | **LOLOS** |
| 2 | **Normalisasi Amplitudo** | Amplitudo dibagi 32768.0, berada pada skala float $[-1.0, 1.0)$ | **LOLOS** |
| 3 | **Durasi Clipping Lebih Pendek** | Durasi tereduksi 71%–82% (dari ~2,6s menjadi ~0,6s) | **LOLOS** |
| 4 | **Kata Tetap Utuh Saat Didengar** | Suku kata awal dan akhir tidak terpotong (diuji via `rekam_audio.py` & plot) | **LOLOS** |
| 5 | **Angka Pemotongan Logis** | Batas awal (0,6–1,6s) dan akhir (1,1–2,1s) sesuai gelombang visual | **LOLOS** |
| 6 | **Data Numerik & Grafik di Excel** | 4 Sheet lengkap dengan native scatter chart di folder `hasil_anggota1/` | **LOLOS** |
| 7 | **Kesiapan Serah Terima ke Anggota 2** | Sinyal potong berupa array 1D siap diolah menjadi 49–85 frame | **LOLOS** |

*Dokumen draf ini telah memenuhi 100% kriteria penulisan laporan dan kriteria kelulusan teknis Anggota 1 sesuai Modul Praktikum PSC.*
