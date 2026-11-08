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
THRESHOLD_K = 0.0            # K=0.0 (Threshold = mean(power)) agar konsonan akhir (seperti 'r') tidak terpotong
MARGIN_BLOK = 2              # Margin keamanan 2 blok (40 ms) di awal & akhir sesuai Bab 11 Modul

# Parameter Frame & Windowing (Anggota 2)
FRAME_MS = 25                # 25 ms per frame (400 sampel pada 16 kHz)
HOP_MS = 10                  # 10 ms per hop (160 sampel, overlap 60%)

# Parameter FFT & MFCC (Anggota 3)
JUMLAH_FILTER_MEL = 26       # 26 filter bank segitiga
JUMLAH_MFCC = 13             # 13 koefisien MFCC pertama
