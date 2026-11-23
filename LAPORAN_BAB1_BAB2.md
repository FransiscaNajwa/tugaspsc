# LAPORAN PRAKTIKUM PENGOLAHAN SINYAL MULTIDIMENSI
## Pra-pemrosesan Sinyal Suara dan Ekstraksi Fitur Wicara Berbasis Mel-Frequency Cepstral Coefficients (MFCC)

---

# BAB I
# PENDAHULUAN

## 1.1 Latar Belakang

Suara adalah medium komunikasi paling alami yang digunakan manusia sehari-hari. Seiring perkembangan teknologi, kemampuan komputer untuk memahami dan mengolah sinyal suara menjadi kebutuhan yang semakin mendasar, mulai dari sistem pengenalan suara (*automatic speech recognition*), asisten virtual, hingga identifikasi pembicara. Namun, sinyal suara yang direkam langsung melalui mikrofon tidak serta-merta siap digunakan. Hampir setiap rekaman memiliki segmen hening (*silence*) di awal, sebelum pengucapan dimulai, dan di akhir, setelah pengucapan selesai. Segmen ini tidak membawa informasi fonetik apa pun, tetapi tetap ikut dihitung dan dapat memperburuk akurasi analisis spektral pada tahap pemrosesan selanjutnya.

Oleh karena itu, pra-pemrosesan sinyal menjadi tahap yang tidak bisa dilewatkan. Salah satu pendekatan yang paling umum dan terbukti efektif adalah deteksi titik awal dan akhir ucapan (*endpoint detection*) berbasis daya jangka pendek (*short-time power*). Metode ini membandingkan daya tiap segmen kecil sinyal terhadap ambang batas adaptif yang dihitung dari statistik rekaman itu sendiri, sehingga secara otomatis menyesuaikan diri dengan volume dan kondisi derau pada setiap berkas rekaman [5][6].

Setelah bagian aktif sinyal dipisahkan dari keheningan, sinyal diteruskan melalui serangkaian tahap pemrosesan lebih lanjut. Sinyal dipotong menjadi bingkai-bingkai pendek (*frame blocking*) berdurasi sekitar 25 ms, kemudian dikalikan dengan fungsi jendela Hamming (*Hamming window*) untuk meredam diskontinuitas di tepi setiap bingkai dan mengurangi kebocoran spektral. Transformasi Fourier Cepat (*Fast Fourier Transform* / FFT) kemudian digunakan untuk mengubah sinyal dari domain waktu ke domain frekuensi, sehingga kandungan spektral tiap bingkai dapat diekstraksi. Tahap akhir adalah perhitungan koefisien *Mel-Frequency Cepstral Coefficients* (MFCC), yaitu representasi kompak dari spektrum suara yang menggunakan skala mel — skala frekuensi yang meniru cara telinga manusia merespons bunyi secara perseptual [1][4].

Praktikum ini mengimplementasikan seluruh rangkaian tahap pra-pemrosesan tersebut pada 10 berkas rekaman kata berbahasa Indonesia yang diucapkan sendiri oleh anggota kelompok, yaitu kata *belajar*, *berjalan*, *duduk*, *makan*, dan *minum*, masing-masing direkam sebanyak dua kali. Dalam proses pengerjaan, ditemukan tantangan nyata pada tahap awal. Pada kata seperti *duduk*, energi sinyal turun drastis saat rongga mulut menutup untuk membentuk konsonan henti /k/ di akhir kata. Jika ambang batas clipping dipasang terlalu tinggi, sistem akan mengira fase penutupan itu sebagai akhir ucapan, sehingga kata terpotong prematur menjadi *"dud"*. Hal serupa juga terjadi pada kata *belajar* yang terpotong menjadi *"belaj"* saat parameter belum disesuaikan. Masalah ini diatasi dengan menggunakan ambang batas adaptif yang lebih konservatif (K = 0,0) dan menambahkan margin pengaman berupa *lead-in* di awal serta *hangover time* di akhir segmen aktif, sehingga seluruh fonem — termasuk konsonan lemah di ujung kata — tetap terjaga [5][7].

## 1.2 Tujuan

Berdasarkan latar belakang di atas, tujuan praktikum ini adalah:

1. Membaca dan memvalidasi berkas WAV kelompok (format mono, 16 kHz, PCM 16-bit), kemudian menormalisasi nilai amplitudonya ke rentang [-1,0 ; 1,0).
2. Mengimplementasikan algoritma level clipping berbasis *short-time power* dengan ambang batas adaptif serta margin pengaman (*lead-in* dan *hangover*) untuk membuang segmen hening tanpa merusak fonem di awal maupun akhir kata.
3. Menerapkan frame blocking dan Hamming window pada sinyal hasil clipping agar sinyal siap dianalisis secara spektral.
4. Mengubah setiap bingkai sinyal ke domain frekuensi menggunakan FFT.
5. Mengekstraksi 13 koefisien MFCC dari spektrum setiap bingkai sebagai representasi fitur wicara.
6. Mengevaluasi hasil setiap tahap pemrosesan pada 10 berkas rekaman asli kelompok dan menyajikannya dalam bentuk tabel numerik serta grafik.

## 1.3 Batasan Masalah

Agar pembahasan tetap terfokus, praktikum ini membatasi ruang lingkupnya sebagai berikut:

1. Data yang digunakan adalah 10 berkas WAV hasil rekaman suara sendiri, terdiri atas 5 kata berbahasa Indonesia — *belajar*, *berjalan*, *duduk*, *makan*, dan *minum* — yang masing-masing direkam dua kali (belajar1.wav, belajar2.wav, dst.).
2. Seluruh berkas rekaman menggunakan format standar: frekuensi sampling 16.000 Hz (16 kHz), resolusi kuantisasi 16-bit Linear PCM, dan satu kanal audio (mono).
3. Perekaman dilakukan di ruangan tertutup yang relatif tenang, menghasilkan jeda hening alami sekitar 0,3–0,5 detik di bagian awal dan akhir setiap rekaman.
4. Alur pemrosesan dibatasi pada enam tahap berurutan: (1) pembacaan sinyal WAV, (2) level clipping, (3) frame blocking, (4) Hamming window, (5) FFT, dan (6) MFCC.
5. Parameter tetap yang digunakan selama praktikum:
   - Durasi blok power: 20 ms (320 sampel pada 16 kHz)
   - Faktor threshold adaptif: K = 0,0
   - Margin awal (lead-in): 3 blok (60 ms)
   - Margin akhir (hangover): 8 blok (160 ms)
   - Panjang frame: 25 ms (400 sampel), hop 10 ms (160 sampel), overlap 60%
   - Jumlah filter bank mel: 26 filter
   - Jumlah koefisien MFCC yang diambil: 13 koefisien
6. Laporan ini tidak mencakup tahap klasifikasi atau pengenalan kata; pemrosesan berhenti pada tahap ekstraksi fitur MFCC.

## 1.4 Rumusan Masalah

Berdasarkan latar belakang dan batasan yang telah diuraikan, rumusan masalah yang akan dijawab dalam praktikum ini adalah:

1. Bagaimana cara membaca, memvalidasi, dan menormalisasi sinyal suara berformat WAV mono 16 kHz PCM 16-bit sehingga siap diproses secara numerik?
2. Bagaimana menerapkan level clipping berbasis *short-time power* dengan ambang batas adaptif dan margin pengaman agar segmen hening terbuang secara efektif tanpa memutus fonem — khususnya konsonan akhir yang energinya rendah?
3. Bagaimana sinyal hasil clipping diproses lebih lanjut melalui frame blocking, Hamming window, dan FFT sebelum diekstraksi menjadi fitur?
4. Bagaimana menghitung koefisien MFCC dari spektrum setiap bingkai sinyal?
5. Bagaimana menyajikan hasil numerik dan grafik dari setiap tahap pemrosesan secara terstruktur?

---

# BAB II
# DASAR TEORI

## 2.1 Sinyal Suara Digital

Suara pada dasarnya adalah gelombang tekanan udara yang merambat secara kontinu terhadap waktu. Agar dapat diolah oleh komputer, sinyal analog ini perlu diubah menjadi representasi digital melalui dua proses utama: *sampling* (diskretisasi waktu) dan kuantisasi (diskretisasi amplitudo) [6].

*Sampling* adalah proses pengambilan nilai amplitudo sinyal pada interval waktu tetap sebesar 1/fs, di mana fs adalah frekuensi sampling. Menurut teorema Nyquist-Shannon, frekuensi sampling harus paling sedikit dua kali frekuensi tertinggi yang terkandung dalam sinyal, agar tidak terjadi aliasing. Untuk keperluan pemrosesan wicara, frekuensi sampling sebesar 16.000 Hz (16 kHz) sudah mencukupi karena mampu merepresentasikan komponen frekuensi hingga 8 kHz — rentang yang sudah mencakup hampir seluruh informasi fonetik yang dibutuhkan [1].

Kuantisasi adalah proses pemetaan nilai amplitudo kontinu ke bilangan bulat berdiskrit sesuai resolusi bit yang digunakan. Pada format PCM 16-bit, tersedia 2^16 = 65.536 level kuantisasi, dengan nilai sampel yang dapat berkisar antara -32.768 hingga 32.767. Agar hasil tidak bergantung pada skala perangkat keras perekam yang berbeda-beda, nilai integer ini dinormalisasi ke rentang desimal mengambang:

```
x_norm[n] = x[n] / 32768
```

Setelah normalisasi, seluruh nilai amplitudo berada dalam rentang [-1,0 ; 1,0). Format mono berarti hanya terdapat satu deret sampel tanpa pemisahan kanal kiri-kanan, sehingga setiap elemen array langsung merepresentasikan tekanan suara pada saat itu.

Satu sifat penting sinyal wicara adalah *quasi-stationarity*, yaitu meskipun sifat statistiknya berubah seiring waktu sesuai fonem yang diucapkan, dalam jendela waktu yang sangat pendek (sekitar 10–30 ms) sinyal dapat dianggap stasioner. Asumsi ini menjadi landasan bagi seluruh pemrosesan berbasis frame yang akan dijelaskan pada subbab berikutnya [1][6].

## 2.2 Level Clipping Berbasis Power

Level clipping adalah teknik pra-pemrosesan yang bertujuan memisahkan segmen ucapan aktif dari segmen hening di awal dan akhir rekaman. Pendekatan yang digunakan dalam praktikum ini adalah deteksi aktivitas suara (*Voice Activity Detection* / VAD) berbasis *short-time power* — salah satu metode VAD paling umum karena implementasinya sederhana namun cukup andal di lingkungan dengan derau rendah [5][6].

Langkah-langkah algoritmanya adalah sebagai berikut:

**Langkah 1 — Pembagian blok pendek.**
Sinyal dibagi menjadi blok-blok pendek berdurasi 20 ms. Pada frekuensi sampling 16 kHz, durasi ini setara dengan 320 sampel per blok. Pemilihan 20 ms mengacu pada sifat quasi-stationarity sinyal wicara sehingga daya di dalam satu blok dapat dianggap merepresentasikan kondisi fonem saat itu.

**Langkah 2 — Perhitungan daya per blok.**
Untuk setiap blok ke-i, dihitung daya rata-rata (*mean square*):

```
P_i = (1 / L) * Σ x²[n],   n dari awal blok hingga akhir blok
```

dengan L adalah jumlah sampel dalam blok tersebut.

**Langkah 3 — Penentuan ambang batas adaptif.**
Nilai daya semua blok dikumpulkan, lalu ambang batas dihitung dari statistiknya:

```
Threshold = mean(P) + K * std(P)
```

Karena ambang batas dihitung dari rekaman itu sendiri, nilainya secara otomatis menyesuaikan diri dengan volume dan derau latar pada masing-masing berkas. Dalam praktikum ini, nilai K ditetapkan K = 0,0 — artinya ambang batas sama dengan rata-rata daya seluruh blok — agar fonem berenergi rendah seperti konsonan frikatif dan henti tidak ikut terbuang [5].

**Langkah 4 — Penetapan margin pengaman.**
Blok yang dayanya melebihi ambang batas dianggap aktif. Namun, ada fenomena akustik yang perlu ditangani: konsonan henti (*stop consonant*) seperti /k/ pada kata *duduk* memiliki fase penutupan (*closure*) di mana energi turun mendekati nol sebelum letupan akhir dilepas. Tanpa margin pengaman, sistem akan mengira fase penutupan itu sebagai akhir ucapan dan memotong kata sebelum waktunya. Untuk mengatasinya, ditambahkan:

- Margin awal (*lead-in*) = 3 blok (60 ms) sebelum blok aktif pertama
- Margin akhir (*hangover time*) = 8 blok (160 ms) setelah blok aktif terakhir

Sinyal kemudian dipotong dari batas margin awal hingga batas margin akhir, sehingga seluruh fonem — termasuk konsonan lemah di ujung kata — terjaga keutuhannya [5][7].

Keterbatasan utama metode berbasis energi ini adalah sensitivitasnya terhadap derau latar yang fluktuatif. Jika lingkungan rekaman bising, nilai daya derau dapat mendekati daya suara aktif, sehingga ambang batas menjadi tidak efektif [7].

## 2.3 Frame Blocking

Karena sifat quasi-stationarity sinyal wicara hanya berlaku dalam jendela waktu yang sangat pendek, sinyal hasil clipping dipecah menjadi bingkai-bingkai (*frame*) berdurasi pendek sebelum dianalisis secara spektral [1][2].

Panjang frame yang umum digunakan berkisar antara 20–30 ms. Bingkai yang berurutan dibuat saling tumpang tindih (*overlap*) agar informasi akustik yang terdapat di dekat batas dua bingkai yang bersebelahan tidak hilang. Jika panjang frame adalah N sampel dan pergeseran antar-bingkai (*hop*) adalah H sampel, maka jumlah total bingkai yang dihasilkan dari sinyal sepanjang Ns sampel adalah:

```
Jumlah frame = 1 + floor((Ns - N) / H)
```

Dalam praktikum ini digunakan parameter:
- Panjang frame: 25 ms = 400 sampel
- Hop (pergeseran): 10 ms = 160 sampel
- Overlap: 400 - 160 = 240 sampel (60%)

Nilai overlap 60% dipilih agar bingkai yang bersebelahan memiliki cukup banyak irisan sehingga perubahan fitur antar-bingkai berlangsung secara mulus. Pemotongan mendadak di tepi bingkai tanpa windowing akan menimbulkan diskontinuitas yang mengotori spektrum, dan inilah yang membuat tahap Hamming window menjadi perlu [3].

## 2.4 Hamming Window

Ketika sebuah bingkai dipotong dari sinyal yang lebih panjang, tepi bingkai mengalami transisi mendadak dari nilai amplitudo tertentu ke nol. Jika DFT/FFT diterapkan langsung pada bingkai tersebut, transisi mendadak itu memunculkan artefak spektral yang dikenal sebagai *spectral leakage* — energi dari satu komponen frekuensi "bocor" ke komponen frekuensi tetangganya dan mengaburkan spektrum yang sesungguhnya [1][3].

Windowing mengatasi masalah ini dengan mengalikan setiap bingkai dengan fungsi pembobot yang nilainya tinggi di tengah dan menurun halus ke nol di kedua tepi. Fungsi Hamming window didefinisikan sebagai:

```
w(n) = 0,54 - 0,46 * cos(2π * n / (N - 1)),    untuk 0 ≤ n ≤ N - 1
```

Sinyal berjendela diperoleh dengan perkalian sampel demi sampel:

```
y[n] = x[n] * w(n)
```

Jendela Hamming menjadi pilihan standar dalam pengolahan wicara karena memberikan keseimbangan yang baik antara resolusi frekuensi (kemampuan membedakan dua komponen frekuensi yang berdekatan) dan penekanan kebocoran spektral. Dibandingkan jendela persegi panjang (*rectangular window*) yang setara dengan tidak melakukan windowing sama sekali, jendela Hamming mampu menekan *sidelobe* spektral secara signifikan [1][8].

## 2.5 Fast Fourier Transform

Setelah bingkai dijendela, langkah selanjutnya adalah mengubah representasi sinyal dari domain waktu ke domain frekuensi menggunakan Discrete Fourier Transform (DFT). Secara matematis, DFT dari sinyal x[n] berdurasi N sampel didefinisikan sebagai:

```
X[k] = Σ x[n] * e^(-j2π*k*n/N),    k = 0, 1, ..., N-1
       n=0 sampai N-1
```

X[k] adalah koefisien kompleks yang merepresentasikan kontribusi komponen frekuensi ke-k terhadap sinyal. Dari X[k] dapat diperoleh:
- Spektrum magnitudo: |X[k]|
- Power spectrum: |X[k]|²

Komputasi DFT secara langsung membutuhkan operasi perkalian dan penjumlahan kompleks sebanyak O(N²) — sangat tidak efisien ketika N besar atau banyak bingkai yang harus diproses. *Fast Fourier Transform* (FFT) mempercepat perhitungan ini menjadi O(N log N) dengan memanfaatkan simetri dan periodisitas faktor eksponensial. Algoritma yang paling banyak digunakan adalah Cooley-Tukey (1965), yang bekerja paling efisien ketika N adalah pangkat dua [1][4].

Dalam praktikum ini, panjang FFT dipilih sama dengan panjang frame (N = 400 sampel), atau dibulatkan ke pangkat dua terdekat untuk efisiensi komputasi jika diperlukan. Karena sinyal wicara adalah sinyal riil, spektrum FFT bersifat simetris konjugat: hanya separuh pertama dari N titik frekuensi (dari 0 hingga fs/2 = 8.000 Hz) yang membawa informasi unik. Bagian inilah yang akan menjadi masukan bagi filter bank mel pada tahap MFCC [1][4].

## 2.6 Mel-Frequency Cepstral Coefficients

MFCC adalah salah satu representasi fitur sinyal wicara yang paling banyak digunakan dalam sistem pengenalan ucapan dan identifikasi pembicara. Keunggulan utamanya terletak pada penggunaan skala mel (*mel scale*) yang meniru cara telinga manusia merespons frekuensi secara perseptual: pendengaran manusia lebih sensitif terhadap perbedaan di frekuensi rendah dibandingkan frekuensi tinggi [1][4][8].

**Skala Mel** mendefinisikan hubungan antara frekuensi fisik f (dalam Hz) dan frekuensi perseptual m (dalam mel):

```
m = 2595 * log10(1 + f / 700)
```

Proses perhitungan MFCC dari spektrum FFT dilakukan melalui empat tahap berikut:

**Tahap 1 — Filter bank mel.**
Power spectrum setiap bingkai dilewatkan melalui serangkaian filter segitiga yang tersusun sesuai skala mel. Dalam praktikum ini digunakan 26 filter. Filter-filter ini saling tumpang tindih, tersusun rapat di frekuensi rendah dan melebar seiring kenaikan frekuensi — mencerminkan resolusi frekuensi pendengaran manusia. Energi keluaran filter ke-m diperoleh dengan menjumlahkan power spectrum yang tertimbang oleh fungsi segitiga filter tersebut [1][4].

**Tahap 2 — Log energi.**
Energi keluaran setiap filter diambil logaritmanya:

```
S_m = log(Energi filter ke-m),    m = 1, 2, ..., M
```

Transformasi logaritmik ini meniru cara telinga manusia merespons intensitas bunyi secara logaritmik (hukum Weber-Fechner) dan sekaligus membantu menstabilkan variansi fitur [4].

**Tahap 3 — Discrete Cosine Transform (DCT).**
DCT diterapkan pada vektor log-energi dari seluruh filter untuk mendekorelasinya dan memadatkan informasi ke koefisien-koefisien awal:

```
c_n = Σ S_m * cos(π * n * (m - 0,5) / M),    m = 1 hingga M
```

DCT memiliki sifat memadatkan energi sinyal ke koefisien orde rendah, sehingga sebagian besar informasi akustik tersimpan dalam beberapa koefisien pertama saja [4][8].

**Tahap 4 — Pengambilan 13 koefisien pertama.**
Dari M = 26 koefisien hasil DCT, diambil 13 koefisien pertama (c_1 hingga c_13) sebagai fitur representasi setiap bingkai. Penelitian menunjukkan bahwa koefisien orde tinggi umumnya mengandung derau dan tidak membawa informasi fonetik yang signifikan [1].

Hasil akhir dari tahap MFCC adalah matriks fitur berukuran (jumlah bingkai) × 13 untuk setiap rekaman. Matriks ini yang selanjutnya dapat digunakan sebagai masukan pada sistem pengenalan suara, pengelompokan, atau keperluan analisis lanjut lainnya.

---

# REFERENSI JURNAL

| No | Subbab | Judul / Sumber | Link |
|:---:|:---|:---|:---|
| [1] | 2.1, 2.3, 2.4, 2.5, 2.6 | Muda, A.K., Yusoff, M., & Hafizan, I. (2010). **Voice Recognition Algorithms using Mel Frequency Cepstral Coefficient (MFCC) and Dynamic Time Warping (DTW) Techniques**. *Journal of Computing*, 2(3). | https://arxiv.org/pdf/1003.4083 |
| [2] | 2.3 | Rabiner, L. & Juang, B.H. (1993). **Fundamentals of Speech Recognition**. Prentice-Hall. *(teori frame blocking, overlap)* | *(buku teks — lihat perpustakaan kampus)* |
| [3] | 2.3, 2.4 | Hossain, M.S., et al. (2020). **Evaluation of biometric user authentication using an ensemble classifier with face and voice recognition**. *arXiv preprint*. | https://arxiv.org/pdf/2006.00548 |
| [4] | 2.5, 2.6 | Sahidullah, M. & Saha, G. (2012). **Design, Analysis and Experimental Evaluation of Block Based Transformation in MFCC Computation for Speaker Recognition**. *(Modified Mel Filter Bank to Compute MFCC of Subsampled Speech)* *arXiv preprint*. | https://arxiv.org/pdf/1410.7382 |
| [5] | 2.2 | Ajmera, P.K., Holambe, R.S., & Basu, T.K. (2014). **Silence Removal and Endpoint Detection of Speech Signal for Text Independent Speaker Identification**. *International Journal of Image, Graphics and Signal Processing (IJIGSP)*, 6(6), 27-33. | https://typeset.io/pdf/silence-removal-and-endpoint-detection-of-speech-signal-for-42808sqc38.pdf |
| [6] | 2.1, 2.2 | Ko, T. & Peddinti, V. (2013). **Audio preprocessing and feature extraction for speech recognition** *(Short-time energy based preprocessing)*. *arXiv preprint*. | https://arxiv.org/pdf/1305.2352 |
| [7] | 2.2 | Zhang, X., et al. (2018). **Wavelet Convolution Based Speech Endpoint Detection**. *arXiv preprint*. *(keterbatasan endpoint detection berbasis energi)* | https://arxiv.org/pdf/1804.06159v1 |
| [8] | 2.4, 2.6 | Proksa, M. (2009). **Visualization of Stages of Determining Cepstral Factors in Speech**. *Journal of Medical Informatics & Technologies*, Vol. 13. | https://yadda.icm.edu.pl/baztech/element/bwmeta1.element.baztech-article-PWA4-0002-0022/c/2009_v13_Proksa.pdf |

> **Catatan penting:**
> - Referensi [2] adalah buku teks standar untuk teori frame blocking dan Hamming window; pastikan tersedia di perpustakaan atau modul dosen.
> - Untuk referensi [1], [3], [4], [6], [7]: buka link-nya, salin judul lengkap, nama penulis, dan tahun yang tertulis di halaman pertama PDF untuk menyusun daftar pustaka dengan format IEEE atau APA yang diminta dosen.
> - Teorema Nyquist-Shannon (Subbab 2.1) dan algoritma FFT Cooley-Tukey (Subbab 2.5) sebaiknya juga dikutip dari buku teks mata kuliah atau modul dosen.

**Pemetaan referensi ke subbab:**
- 2.1 Sinyal Suara Digital → [1][6]
- 2.2 Level Clipping Berbasis Power → [5][6][7]
- 2.3 Frame Blocking → [1][2][3]
- 2.4 Hamming Window → [1][3][8]
- 2.5 Fast Fourier Transform → [1][4]
- 2.6 MFCC → [1][4][8]
