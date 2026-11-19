"""
Skrip Uji Dengar Manual: Membandingkan Audio Asli vs Audio Setelah Clipping
Gunakan skrip ini untuk memastikan dengan telinga Anda sendiri bahwa kata yang diucapkan
benar-benar utuh dan bagian hening di awal/akhir berhasil dipotong.
"""

import time
from pathlib import Path
from scipy.io import wavfile
import sounddevice as sd

from konfigurasi import FOLDER_WAV, AKAR

FOLDER_HASIL_ANGGOTA1 = AKAR / 'hasil_anggota1'

DAFTAR_KATA = [
    'belajar1', 'belajar2',
    'berjalan1', 'berjalan2',
    'duduk1', 'duduk2',
    'makan1', 'makan2',
    'minum1', 'minum2'
]


def putar_audio(path_file, keterangan):
    path_file = Path(path_file)
    if not path_file.exists():
        print(f"[ERROR] File tidak ditemukan: {path_file}")
        return
    fs, data = wavfile.read(str(path_file))
    durasi = len(data) / fs
    print(f"\n>> Memutar {keterangan} ({path_file.name})")
    print(f"   Durasi: {durasi:.3f} detik | Sample Rate: {fs} Hz")
    sd.play(data, fs)
    sd.wait()
    print("   [Selesai diputar]")


def bandingkan_kata(nama_kata):
    file_asli = FOLDER_WAV / f"{nama_kata}.wav"
    file_clip = FOLDER_HASIL_ANGGOTA1 / nama_kata / f"{nama_kata}_clipping.wav"
    
    if not file_asli.exists() or not file_clip.exists():
        print(f"[PERINGATAN] Berkas untuk '{nama_kata}' belum lengkap.")
        return
        
    fs1, d1 = wavfile.read(str(file_asli))
    fs2, d2 = wavfile.read(str(file_clip))
    dur1 = len(d1) / fs1
    dur2 = len(d2) / fs2
    
    print("\n" + "=" * 60)
    print(f" PEMERIKSAAN AUDIO KATA: {nama_kata}")
    print("=" * 60)
    print(f"1. Audio Asli          : {dur1:.3f} detik (ada jeda hening/diam)")
    print(f"2. Audio Hasil Clipping: {dur2:.3f} detik (jeda hening dibuang {((dur1-dur2)/dur1*100):.1f}%)")
    print("=" * 60)
    
    while True:
        print("\nPilih aksi:")
        print(" [1] Putar Audio ASLI (sebelum dipotong)")
        print(" [2] Putar Audio HASIL CLIPPING (setelah dipotong)")
        print(" [3] Putar KEDUANYA bergantian (Bandingkan langsung)")
        print(" [0] Kembali ke menu daftar kata")
        pilih = input("Pilihan Anda (0-3): ").strip()
        
        if pilih == '1':
            putar_audio(file_asli, "AUDIO ASLI")
        elif pilih == '2':
            putar_audio(file_clip, "AUDIO HASIL CLIPPING")
        elif pilih == '3':
            putar_audio(file_asli, "AUDIO ASLI (Perhatikan jeda heningnya)")
            time.sleep(0.8)
            putar_audio(file_clip, "AUDIO HASIL CLIPPING (Langsung masuk ke kata)")
        elif pilih == '0':
            break
        else:
            print("Pilihan tidak valid.")


def main():
    while True:
        print("\n" + "=" * 55)
        print(" MENU UJI MANUAL DENGAR AUDIO (ANGGOTA 1)")
        print("=" * 55)
        for idx, k in enumerate(DAFTAR_KATA, start=1):
            file_clip = FOLDER_HASIL_ANGGOTA1 / k / f"{k}_clipping.wav"
            status = "[SIAP CEK]" if file_clip.exists() else "[BELUM DIPROSES]"
            print(f" {idx:2d}. {k:<12} {status}")
        print("  0. Keluar")
        print("=" * 55)
        
        input_user = input("Pilih nomor kata yang ingin dicek (1-10, 0 untuk keluar): ").strip()
        if input_user == '0':
            print("Pemeriksaan selesai.")
            break
        elif input_user.isdigit() and 1 <= int(input_user) <= 10:
            target = DAFTAR_KATA[int(input_user) - 1]
            bandingkan_kata(target)
        else:
            print("Nomor pilihan tidak valid.")


if __name__ == '__main__':
    main()
