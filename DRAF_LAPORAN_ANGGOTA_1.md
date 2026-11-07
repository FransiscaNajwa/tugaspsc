# BAGIAN LAPORAN ANGGOTA 1 (SIAP COPY KE WORD)

---

# BAB I
# PENDAHULUAN

### 1.1 Latar Belakang
Pengolahan sinyal wicara merupakan bagian penting dari interaksi manusia dan komputer. Sinyal suara yang direkam secara langsung melalui mikrofon pada umumnya merekam kondisi lingkungan sekitar, sehingga menghasilkan segmen hening (silence) atau derau latar belakang (background noise) di awal sebelum pengucapan dimulai maupun di akhir setelah pengucapan selesai.

Keberadaan segmen hening yang tidak memiliki informasi fonetik tersebut meningkatkan volume data yang tidak perlu dan dapat mendistorsi perhitungan matriks spektral pada tahapan pengolahan lanjutan. Oleh karena itu, tahapan pra-pemrosesan awal berupa deteksi suara aktif dan pemangkasan hening (Level Clipping berbasis Short-Time Power) menjadi tahapan penentu. Setelah sinyal aktif dipisahkan dari keheningan, sinyal tersebut diproses lebih lanjut melalui pemotongan berbingkai (Frame Blocking), pembobotan jendela (Hamming Window), transformasi domain frekuensi (Fast Fourier Transform / FFT), hingga ekstraksi fitur Mel-Frequency Cepstral Coefficients (MFCC).

### 1.2 Rumusan Masalah
1. Bagaimana cara membaca, memvalidasi spesifikasi masukan (Mono, 16 kHz, PCM 16-bit), dan menormalisasi amplitudo gelombang suara berformat WAV?
2. Bagaimana cara mengimplementasikan metode Level Clipping berbasis Short-Time Power dengan penentuan ambang batas (threshold) adaptif untuk membuang segmen hening tanpa memotong suku kata?
3. Bagaimana menyajikan data numerik dan grafik dari hasil pemrosesan ke dalam lembar kerja Microsoft Excel sesuai diagram alir penugasan?

### 1.3 Tujuan Praktikum
1. Mampu membaca dan menginterpretasikan data sampel suara diskrit berformat WAV mono 16 kHz serta melakukan normalisasi kuantisasi 16-bit ke bilangan pecahan desimal.
2. Mampu merancang dan mengimplementasikan algoritma Level Clipping menggunakan perhitungan Short-Time Power per blok 20 ms dengan ambang batas adaptif.
3. Mampu mengevaluasi efektivitas pemangkasan jeda hening dan membuktikan keutuhan fonem pada 10 berkas rekaman audio asli kelompok.

### 1.4 Ruang Lingkup
1. Data masukan terdiri dari 5 pasang kata berbeda (total 10 berkas WAV asli kelompok): belajar1/2, berjalan1/2, duduk1/2, makan1/2, dan minum1/2.
2. Format perekaman ditetapkan pada frekuensi sampling 16 kHz (16.000 Hz), resolusi 16-bit PCM, dan 1 saluran (Mono).
3. Diagram alir pemrosesan mencakup 6 tahapan: Sinyal WAV -> Level Clipping (Power) -> Frame Blocking -> Hamming Window -> FFT -> MFCC.
4. Parameter yang digunakan: durasi blok power 20 ms, faktor pengali threshold K = 0.5, frame 25 ms, hop 10 ms (overlap 60%), 26 filter bank Mel, dan 13 koefisien MFCC.

---

# BAB III
# METODOLOGI DAN IMPLEMENTASI

### 3.1 Perekaman Sinyal Suara
Sinyal suara diperoleh dengan cara merekam pengucapan kata secara langsung menggunakan mikrofon di ruangan tertutup yang tenang. Parameter perekaman yang digunakan adalah:
- Frekuensi sampling (sample rate) = 16 kHz (16.000 Hz)
- Resolusi kuantisasi = 16-bit (Linear PCM)
- Jumlah saluran (channel) = 1 (Mono)
- Format berkas = .wav

Perekaman dilakukan sesaat setelah tombol rekam ditekan dan diakhiri sebelum tombol rekam dihentikan. Hal ini memberikan jeda hening alami sekitar 0,3–0,5 detik di awal dan akhir rekaman untuk menguji keandalan algoritma pemotongan hening (clipping).

### 3.2 Implementasi Level Clipping Berbasis Short-Time Power
Tahap Level Clipping bertujuan memisahkan segmen suara aktif dari keheningan (silence removal). Langkah-langkah matematis yang diterapkan adalah:

1. Normalisasi Amplitudo: Data mentah bertipe integer 16-bit (rentang -32768 s.d. 32767) dinormalisasi ke skala pecahan mengambang pada rentang [-1.0, 1.0) dengan membagi sampel terhadap faktor skala 32768.0:
   x_norm[n] = x[n] / 32768.0

2. Pembagian Blok Pendek: Sinyal dibagi menjadi blok-blok pendek berdurasi 20 ms (320 sampel pada frekuensi 16 kHz). Durasi 20 ms dipilih karena sinyal wicara bersifat stasioner pendek (quasi-stationary) pada interval 10–30 ms.

3. Perhitungan Daya per Blok (Short-Time Power): Untuk setiap blok ke-i, dihitung daya rata-rata (mean square) menggunakan rumus:
   P_i = (1 / L) * sum(x^2[n])

4. Penentuan Ambang Batas Adaptif (Threshold): Dihitung nilai rata-rata daya seluruh blok (mean) dan simpangan baku daya (std). Ambang batas dihitung melalui rumus:
   Threshold = mean(P) + K * std(P)
   Nilai K yang disepakati adalah 0.5. Nilai ini cukup tinggi agar tidak terpicu oleh derau ruangan, sekaligus cukup rendah sehingga tidak memotong fonem wicara yang berenergi pelan.

5. Pemotongan Sinyal: Dicari indeks blok aktif pertama dan terakhir yang memiliki daya melebihi ambang batas (Power > Threshold). Sinyal dipotong dari sampel awal blok aktif pertama hingga sampel akhir blok aktif terakhir.

#### Listing Program (Plain Text):
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
    fs, data = wavfile.read(str(lokasi))
    if data.ndim != JUMLAH_CHANNEL:
        raise ValueError(f"File harus MONO ({JUMLAH_CHANNEL} channel).")
    if fs != SAMPLE_RATE:
        raise ValueError(f"Sample rate {fs} Hz; harus {SAMPLE_RATE} Hz.")
    if data.dtype != np.int16:
        raise ValueError(f"Format data wajib PCM {JUMLAH_BIT}-bit (int16).")
    
    faktor_skala = float(2 ** (JUMLAH_BIT - 1))
    sinyal = data.astype(np.float64) / faktor_skala
    return fs, sinyal

def clipping_berdasarkan_power(sinyal, fs, threshold_k=THRESHOLD_K, durasi_power_ms=DURASI_POWER_MS):
    panjang = max(1, round(fs * durasi_power_ms / 1000))
    nblok = int(np.ceil(len(sinyal) / panjang))
    if nblok == 0 or len(sinyal) == 0:
        raise ValueError("Sinyal audio kosong.")
        
    power = np.array([
        np.mean(sinyal[i * panjang : min((i + 1) * panjang, len(sinyal))] ** 2)
        for i in range(nblok)
    ])
    
    ambang = power.mean() + threshold_k * power.std()
    aktif = np.flatnonzero(power > ambang)
    if len(aktif) == 0:
        raise ValueError(f"Tidak terdeteksi segmen suara aktif dengan K={threshold_k}.")
        
    awal = int(aktif[0] * panjang)
    akhir = int(min(len(sinyal), (aktif[-1] + 1) * panjang))
    return sinyal[awal:akhir].copy(), power, ambang, awal, akhir
```

#### Penjelasan Fungsi Program:
- Fungsi baca_wav bertugas membaca berkas .wav serta melakukan validasi ketat agar masukan sesuai standar praktikum (mono, 16 kHz, PCM 16-bit). Data integer dinormalisasi dengan membaginya terhadap 32768.0 sehingga berada pada rentang float [-1.0, 1.0).
- Fungsi clipping_berdasarkan_power membagi sinyal menjadi blok-blok 20 ms, menghitung nilai mean kuadrat (daya) tiap blok, menentukan batas ambang adaptif berbasis mean dan standar deviasi daya, lalu memotong sinyal dari blok aktif pertama hingga blok aktif terakhir.

---

# BAB IV
# HASIL DAN PEMBAHASAN

### 4.1 Hasil dan Pembahasan Level Clipping

Pengujian dilakukan terhadap 10 berkas rekaman suara asli kelompok. Seluruh berkas berhasil dibaca dan dipotong secara otomatis.

#### Tabel 4.1 Data Hasil Level Clipping 10 Berkas Audio:
| No | Nama Berkas | Kata | Durasi Awal (s) | Durasi Potong (s) | Reduksi Hening (%) | Nilai Threshold Power | Sampel Aktif (Awal–Akhir) | Status Keutuhan Kata |
| :-: | :--- | :---: | :-: | :-: | :-: | :-: | :-: | :---: |
| 1 | belajar1.wav | belajar | 2.652 s | 0.580 s | 78.1% | 2,886 × 10^-3 | 16960 s.d. 26240 | Utuh, fonem /b/ dan /r/ sempurna |
| 2 | belajar2.wav | belajar | 2.834 s | 0.620 s | 78.1% | 2,257 × 10^-3 | 17600 s.d. 27520 | Utuh, suku kata awal-akhir utuh |
| 3 | berjalan1.wav| berjalan| 3.042 s | 0.780 s | 74.4% | 1,473 × 10^-3 | 20800 s.d. 33280 | Utuh, konsonan /b/ dan /n/ terjaga |
| 4 | berjalan2.wav| berjalan| 2.990 s | 0.860 s | 71.2% | 1,169 × 10^-3 | 13440 s.d. 27200 | Utuh, artikulasi kata jelas |
| 5 | duduk1.wav | duduk | 2.782 s | 0.500 s | 82.0% | 2,735 × 10^-3 | 20800 s.d. 28800 | Utuh, fonem /d/ dan /k/ tidak terpotong |
| 6 | duduk2.wav | duduk | 2.964 s | 0.540 s | 81.8% | 3,623 × 10^-3 | 25920 s.d. 34560 | Utuh, tidak ada distorsi ujung |
| 7 | makan1.wav | makan | 2.288 s | 0.560 s | 75.5% | 1,307 × 10^-3 | 9600 s.d. 18560 | Utuh, fonem sengau /m/ & /n/ utuh |
| 8 | makan2.wav | makan | 1.872 s | 0.540 s | 71.2% | 1,043 × 10^-3 | 9920 s.d. 18560 | Utuh, artikulasi jelas |
| 9 | minum1.wav | minum | 2.522 s | 0.500 s | 80.2% | 7,091 × 10^-3 | 17600 s.d. 25600 | Utuh, vokal /i/ dan /u/ utuh |
| 10| minum2.wav | minum | 2.600 s | 0.580 s | 77.7% | 4,807 × 10^-3 | 14400 s.d. 23680 | Utuh, fonem penutup /m/ tidak terpotong |

(Sisipkan gambar 01_sinyal_asli.png dan 02_sinyal_clipping.png dari folder hasil_anggota1/makan1/ sebagai contoh grafik perwakilan di bawah tabel ini).

#### Pembahasan Analisis Hasil:
Setelah proses Level Clipping, durasi sinyal berubah dari rata-rata 2,2–3,0 detik menjadi 0,50–0,86 detik karena blok dengan power rendah pada awal dan akhir rekaman tidak disertakan. Algoritma berhasil mereduksi rata-rata 71% hingga 82% panjang sinyal awal yang didominasi oleh fase hening dan derau udara ruangan.

Pemeriksaan gelombang sinyal dan uji pendengaran menunjukkan bahwa seluruh bagian pengucapan kata masih utuh. Fonem konsonan letup (/b/ dan /d/) pada kata belajar, berjalan, dan duduk memiliki lonjakan energi yang terdeteksi dengan tepat pada awal batas potong. Begitu pula pada fonem sengau (/m/) pada kata makan dan minum, energi suara tetap melampaui garis ambang batas sehingga suku kata awal tidak terpotong. 

Nilai threshold yang diperoleh berada pada rentang 1,04 × 10^-3 hingga 7,09 × 10^-3 (atau 0,00104 hingga 0,00709), sesuai dengan tingkat energi rekaman masing-masing kata. Penggunaan durasi blok 20 ms dengan parameter K = 0.5 terbukti adaptif dan optimal dalam memisahkan sinyal wicara aktif terhadap derau latar belakang. Hasil keluaran ini juga telah diverifikasi secara numerik dan grafik pada lembar kerja Microsoft Excel di setiap berkas rekaman.
