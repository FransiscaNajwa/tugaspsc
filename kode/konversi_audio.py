"""
Utilitas Konversi Audio ke Standar Tugas PSC (16 kHz, Mono, PCM 16-bit)
Gunakan skrip ini jika rekaman dari HP/mic berformat stereo, 44.1/48 kHz, atau float32.
"""

from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly
import math

from konfigurasi import FOLDER_WAV, SAMPLE_RATE


def standarkan_wav(input_path, output_path=None):
    """
    Mengubah file WAV sembarang menjadi 16 kHz, Mono, PCM 16-bit.
    """
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path

    fs, data = wavfile.read(str(input_path))
    perubahan = []

    # 1. Konversi ke Mono jika Stereo / Multi-channel
    if data.ndim > 1:
        data = np.mean(data, axis=1)
        perubahan.append("Konversi Stereo -> Mono")

    # 2. Normalisasi format data ke float rentang [-1.0, 1.0]
    if data.dtype == np.int16:
        sinyal = data.astype(np.float64) / 32768.0
    elif data.dtype == np.int32:
        sinyal = data.astype(np.float64) / 2147483648.0
    elif data.dtype == np.uint8:
        sinyal = (data.astype(np.float64) - 128.0) / 128.0
    elif np.issubdtype(data.dtype, np.floating):
        sinyal = data.astype(np.float64)
        max_val = np.max(np.abs(sinyal))
        if max_val > 1.0:
            sinyal = sinyal / max_val
    else:
        sinyal = data.astype(np.float64)
        sinyal = sinyal / np.max(np.abs(sinyal))

    # 3. Resample ke 16 kHz jika sample rate berbeda
    if fs != SAMPLE_RATE:
        gcd = math.gcd(SAMPLE_RATE, fs)
        up = SAMPLE_RATE // gcd
        down = fs // gcd
        sinyal = resample_poly(sinyal, up, down)
        perubahan.append(f"Resampling {fs} Hz -> {SAMPLE_RATE} Hz")

    # 4. Simpan kembali sebagai PCM 16-bit Mono
    data_int16 = (np.clip(sinyal, -1.0, 1.0) * 32767.0).astype(np.int16)
    wavfile.write(str(output_path), SAMPLE_RATE, data_int16)

    ket = ", ".join(perubahan) if perubahan else "Format sudah sesuai"
    print(f"[{input_path.name}] Selesai distandarkan -> {ket}")


def standarkan_semua():
    wav_files = sorted(FOLDER_WAV.glob('*.wav'))
    if not wav_files:
        print(f"Tidak ada file .wav di {FOLDER_WAV}")
        return

    print("Memeriksa dan menstandarkan semua file di folder data_wav/...")
    for wf in wav_files:
        if wf.name == 'DEMO_BUKAN_REKAMAN.wav':
            continue
        try:
            standarkan_wav(wf)
        except Exception as e:
            print(f"Gagal menstandarkan {wf.name}: {e}")


if __name__ == '__main__':
    standarkan_semua()
