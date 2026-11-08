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
2. Mampu merancang dan mengimplementasikan algoritma Level Clipping menggunakan perhitungan Short-Time Power per blok 20 ms dengan ambang batas adaptif dan margin keamanan (hangover time).
3. Mampu mengevaluasi efektivitas pemangkasan jeda hening dan membuktikan keutuhan fonem pada 10 berkas rekaman audio asli kelompok.

### 1.4 Ruang Lingkup
1. Data masukan terdiri dari 5 pasang kata berbeda (total 10 berkas WAV asli kelompok): belajar1/2, berjalan1/2, duduk1/2, makan1/2, dan minum1/2.
2. Format perekaman ditetapkan pada frekuensi sampling 16 kHz (16.000 Hz), resolusi 16-bit PCM, dan 1 saluran (Mono).
3. Diagram alir pemrosesan mencakup 6 tahapan: Sinyal WAV -> Level Clipping (Power) -> Frame Blocking -> Hamming Window -> FFT -> MFCC.
4. Parameter yang digunakan: durasi blok power 20 ms, faktor pengali threshold K = 0.0 dengan margin awal 3 blok (60 ms) dan margin akhir 8 blok (160 ms), frame 25 ms, hop 10 ms (overlap 60%), 26 filter bank Mel, dan 13 koefisien MFCC.

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
   Berdasarkan evaluasi fonetik, nilai K dipilih sebesar 0.0 (ambang batas sama dengan rata-rata daya blok) agar konsonan getar yang energinya lebih lembut di akhir kata tidak terpotong.

5. Margin Keamanan dan Hangover Time: Pada konsonan henti/letup seperti fonem /k/ di akhir kata (misal kata duduk), energi suara turun tajam saat fase penutupan mulut (closure) sebelum letupan akhir dilepas. Untuk mencegah kata terpotong menjadi "dud", diterapkan sistem margin keamanan:
   - Margin awal (lead-in) = 3 blok (60 ms)
   - Margin akhir (hangover time) = 8 blok (160 ms)
   Sinyal kemudian dipotong dari batas margin awal hingga batas margin akhir.

#### Listing Program (Plain Text):
```python
"""
Blok 1: Pembacaan Sinyal Suara dan Level Clipping Berbasis Power
Penulis: Anggota 1
File: kode/anggota1.py
"""
import numpy as np
from scipy.io import wavfile
from konfigurasi import SAMPLE_RATE, JUMLAH_BIT, JUMLAH_CHANNEL, THRESHOLD_K, DURASI_POWER_MS, MARGIN_AWAL_BLOK, MARGIN_AKHIR_BLOK

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

def clipping_berdasarkan_power(sinyal, fs, threshold_k=THRESHOLD_K, durasi_power_ms=DURASI_POWER_MS, margin_awal=MARGIN_AWAL_BLOK, margin_akhir=MARGIN_AKHIR_BLOK):
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
        
    blok_awal = max(0, aktif[0] - margin_awal)
    blok_akhir = min(nblok, aktif[-1] + 1 + margin_akhir)
    awal = int(blok_awal * panjang)
    akhir = int(min(len(sinyal), blok_akhir * panjang))
    
    potong = sinyal[awal:akhir].copy()
    return potong, power, ambang, awal, akhir
```

#### Penjelasan Fungsi Program:
- Fungsi baca_wav membaca berkas audio WAV serta memastikan masukan tepat mono, 16 kHz, dan PCM 16-bit. Normalisasi membagi data terhadap 32768.0 sehingga berada pada rentang float [-1.0, 1.0).
- Fungsi clipping_berdasarkan_power menghitung daya per blok 20 ms, menetapkan ambang batas rata-rata daya, menambahkan margin awal 60 ms dan margin akhir 160 ms untuk melindungi letupan konsonan akhir, lalu memotong bagian hening di luar rentang wicara aktif.

---

# BAB IV
# HASIL DAN PEMBAHASAN

### 4.1 Hasil dan Pembahasan Level Clipping

Pengujian dilakukan terhadap 10 berkas rekaman suara asli kelompok. Seluruh berkas berhasil dibaca dan dipotong secara optimal.

#### Tabel 4.1 Data Hasil Level Clipping 10 Berkas Audio:
| No | Nama Berkas | Kata | Durasi Awal (s) | Durasi Potong (s) | Reduksi Hening (%) | Nilai Threshold Power | Sampel Aktif (Awal–Akhir) | Status Keutuhan Kata |
| :-: | :--- | :---: | :-: | :-: | :-: | :-: | :-: | :---: |
| 1 | belajar1.wav | belajar | 2.652 s | 0.900 s | 66.1% | 1,307 × 10^-3 | 16000 s.d. 30400 | Utuh, akhiran /ar/ terdengar jelas |
| 2 | belajar2.wav | belajar | 2.834 s | 0.920 s | 67.5% | 1,037 × 10^-3 | 16640 s.d. 31360 | Utuh, suku kata awal-akhir utuh |
| 3 | berjalan1.wav| berjalan| 3.042 s | 1.080 s | 64.5% | 6,973 × 10^-4 | 19840 s.d. 37120 | Utuh, konsonan /b/ dan /n/ terjaga |
| 4 | berjalan2.wav| berjalan| 2.990 s | 1.180 s | 60.5% | 5,334 × 10^-4 | 12480 s.d. 31360 | Utuh, artikulasi kata jelas |
| 5 | duduk1.wav | duduk | 2.782 s | 0.720 s | 74.1% | 1,098 × 10^-3 | 19840 s.d. 31360 | Utuh, letupan akhir /k/ terdengar sempurna |
| 6 | duduk2.wav | duduk | 2.964 s | 0.780 s | 73.7% | 1,495 × 10^-3 | 24960 s.d. 37440 | Utuh, suku kata kedua tidak terpenggal |
| 7 | makan1.wav | makan | 2.288 s | 0.820 s | 64.2% | 6,118 × 10^-4 | 8640 s.d. 21760 | Utuh, fonem sengau /m/ & /n/ utuh |
| 8 | makan2.wav | makan | 1.872 s | 0.780 s | 58.3% | 5,128 × 10^-4 | 8640 s.d. 21120 | Utuh, artikulasi jelas |
| 9 | minum1.wav | minum | 2.522 s | 0.740 s | 70.7% | 3,480 × 10^-3 | 16640 s.d. 28480 | Utuh, vokal /i/ dan /u/ utuh |
| 10| minum2.wav | minum | 2.600 s | 0.800 s | 69.2% | 2,304 × 10^-3 | 13440 s.d. 26240 | Utuh, fonem penutup /m/ tidak terpotong |

(Sisipkan gambar 01_sinyal_asli.png dan 02_sinyal_clipping.png dari folder hasil_anggota1/duduk1/ sebagai contoh grafik perwakilan di bawah tabel ini).

#### Pembahasan Analisis Hasil:
Setelah proses Level Clipping, durasi sinyal berubah dari rata-rata 1,87–3,04 detik menjadi 0,72–1,18 detik karena blok dengan power rendah pada awal dan akhir rekaman tidak disertakan. Algoritma berhasil mereduksi rata-rata 58% hingga 74% panjang sinyal awal yang didominasi oleh fase hening dan derau udara ruangan.

Pada evaluasi pengujian secara kritis, ditemukan fenomena akustik pada kata yang memiliki konsonan akhir lemah atau konsonan henti (stop consonant), seperti getaran /r/ pada kata belajar dan letupan /k/ pada kata duduk. Pada kata duduk, saat pembicara menutup rongga mulut untuk melafalkan konsonan /k/ di akhir suku kata kedua, energi sinyal mengalami penurunan tajam (fase closure) sebelum hembusan udara rilis dilepaskan. Apabila pemotongan hanya mengandalkan ambang batas daya biasa dengan margin sempit, sistem menganggap fase henti tersebut sebagai akhir rekaman, sehingga kata terpotong secara prematur menjadi "dud".

Sesuai panduan penanganan masalah (troubleshooting) pada Bab 11 Modul Praktikum, nilai K disesuaikan menjadi K = 0.0 (ambang batas setara dengan rata-rata daya blok) serta ditambahkan waktu tunda (hangover time) melalui margin akhir sebesar 8 blok (160 ms). Penambahan margin akhir ini memberi ruang yang cukup bagi rilis akustik konsonan /k/ dan /r/ untuk teredam secara alami hingga tuntas.

Setelah penyempurnaan parameter tersebut, pengujian ulang menunjukkan bahwa seluruh kata (belajar, berjalan, duduk, makan, minum) terdengar utuh dan natural dari fonem awal hingga desah fonem penutup. Nilai threshold yang diperoleh berada pada rentang 5,13 × 10^-4 hingga 3,48 × 10^-3. Hasil ini membuktikan bahwa Level Clipping dengan margin lead-in dan hangover mampu mempertahankan integritas fonetik wicara manusia secara adaptif sekaligus menghemat lebih dari 60% pemrosesan data hening. Seluruh keluaran numerik dan diagram tebar telah diverifikasi dan tersimpan pada berkas Excel di masing-masing folder kata.
