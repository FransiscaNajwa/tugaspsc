# Tugas 1 Pengolahan Sinyal dan Citra - Anggota 1

Repository ini memuat kode, data rekaman, dan hasil pengolahan audio untuk bagian **Anggota 1**:
- Pembacaan & Validasi Format Audio WAV (16 kHz, PCM 16-bit, Mono)
- Normalisasi Sinyal Diskrit ke Float `[-1.0, 1.0)`
- Level Clipping Berbasis *Short-Time Power*

## Struktur Direktori
```text
tugaspsc/
├── data_wav/                   # 10 Berkas rekaman audio asli (5 pasang kata)
├── hasil_anggota1/             # Hasil Excel (.xlsx) dan grafik (.png) murni Anggota 1
├── kode/
│   ├── konfigurasi.py          # Parameter audio & clipping
│   ├── anggota1.py             # Modul inti baca_wav & clipping_berdasarkan_power
│   ├── uji_anggota1.py         # Skrip evaluasi visual plot 3-panel
│   ├── jalankan_anggota1.py    # Pipeline pembentukan workbook Excel Anggota 1
│   ├── rekam_audio.py          # Skrip perekaman audio standar tugas
│   └── konversi_audio.py       # Utilitas konversi audio ke standar
├── DRAF_LAPORAN_ANGGOTA_1.md   # Naskah laporan BAB I, BAB III.1/2, BAB IV.1
├── requirements.txt            # Dependensi Python (numpy, scipy, matplotlib, openpyxl)
└── README.md
```

## Cara Menjalankan
1. Pasang dependensi:
   ```bash
   pip install -r requirements.txt
   ```
2. Uji langsung modul Anggota 1 di terminal:
   ```bash
   python kode/anggota1.py
   ```
3. Buat workbook Excel dan grafik murni Anggota 1:
   ```bash
   python kode/jalankan_anggota1.py
   ```
