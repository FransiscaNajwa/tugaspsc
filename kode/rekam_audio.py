"""
====================================================================
 SKRIP PEREKAMAN AUDIO RESMI TUGAS 1 PSC
 Sesuai Standar Dosen & Modul Praktikum:
 - Sample Rate: 16.000 Hz (16 kHz)
 - Resolusi   : 16-bit PCM
 - Channel    : 1 (Mono)
 - Format     : WAV
====================================================================
Fitur Unggulan:
1. Rekam manual: Tekan ENTER untuk MULAI -> Ucapkan Kata -> Tekan ENTER untuk SELESAI.
   (Memberi jeda hening alami di awal & akhir sesuai instruksi tugas).
2. Deteksi otomatis level audio (peringatan jika suara terlalu pelan / mic mati).
3. Fitur putar ulang (Playback) untuk mendengarkan hasil rekaman langsung.
4. Opsi rekam ulang jika pengucapan kurang jelas.
5. Pemantau status kelengkapan 10 file tugas.
====================================================================
"""

import sys
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

from konfigurasi import FOLDER_WAV, JUMLAH_BIT, JUMLAH_CHANNEL, SAMPLE_RATE

# Daftar 5 pasang kata resmi (10 rekaman)
DAFTAR_KATA_DEFAULT = [
    'makan1', 'makan2',
    'berjalan1', 'berjalan2',
    'belajar1', 'belajar2',
    'minum1', 'minum2',
    'duduk1', 'duduk2'
]


def daftar_perangkat_input():
    """Menampilkan mikrofon yang aktif di komputer."""
    perangkat = sd.query_devices()
    input_devices = [
        (i, dev) for i, dev in enumerate(perangkat) if dev['max_input_channels'] > 0
    ]
    return input_devices


def rekam_dengan_tombol(nama_file):
    """
    Merekam audio dengan kontrol tombol:
    Tekan Enter untuk mulai -> Ucapkan kata (ada jeda diam) -> Tekan Enter untuk stop.
    """
    print("\n" + "=" * 60)
    print(f" PEREKAMAN UNTUK BERKAS: {nama_file}.wav")
    print("=" * 60)
    print("Panduan cara merekam:")
    print("1. Pastikan Anda berada di ruangan yang tenang.")
    print("2. Tekan [ENTER] untuk mulai merekam.")
    print("3. DIAM SEBENTAR (~0.5 detik), lalu UCAPKAN KATA dengan jelas.")
    print("4. DIAM SEBENTAR (~0.5 detik), lalu Tekan [ENTER] untuk berhenti.")
    print("=" * 60)

    input(">> Tekan [ENTER] jika sudah siap mulai merekam...")

    audio_chunks = []
    stop_event = threading.Event()

    def callback(indata, frames, time_info, status):
        if status:
            print(f"[Peringatan status audio: {status}]", file=sys.stderr)
        audio_chunks.append(indata.copy())

    print("\n>>> SEDANG MEREKAM... [Diam sejenak -> Ucapkan kata -> Diam sejenak] <<<")
    print(">> Tekan [ENTER] untuk MENGAKHIRI rekaman...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=JUMLAH_CHANNEL,
        dtype='int16',
        callback=callback
    ):
        input()  # Menunggu tombol Enter ditekan
        stop_event.set()

    print("[Rekaman Selesai!] Memproses data...")

    if not audio_chunks:
        print("[ERROR] Tidak ada data audio yang tertangkap. Periksa mikrofon Anda.")
        return False

    rekaman = np.concatenate(audio_chunks, axis=0)
    durasi = len(rekaman) / SAMPLE_RATE

    # Evaluasi level sinyal (cek apakah mic mati atau suara terlalu kecil)
    sinyal_float = rekaman.astype(np.float64) / 32768.0
    peak = np.max(np.abs(sinyal_float))
    rms = np.sqrt(np.mean(sinyal_float ** 2))

    print(f"\n--- Ringkasan Rekaman: {nama_file}.wav ---")
    print(f"- Durasi Total : {durasi:.2f} detik ({len(rekaman)} sampel)")
    print(f"- Sample Rate  : {SAMPLE_RATE} Hz")
    print(f"- Format       : {JUMLAH_BIT}-bit PCM, Mono")
    print(f"- Puncak Suara : {peak:.3f} (Skala 0.0 - 1.0)")

    if peak < 0.04:
        print(">> [PERHATIAN] Suara sangat kecil atau mikrofon terlalu jauh/hening!")
        print("   Disarankan untuk rekam ulang lebih dekat dengan mikrofon.")
    elif peak > 0.98:
        print(">> [PERHATIAN] Suara terlalu keras mendekati distorsi (clipping).")
    else:
        print(">> [BAGUS] Kualitas level rekaman optimal.")

    # Opsi Playback & Simpan
    while True:
        print("\nPilihan:")
        print(" [S] Simpan rekaman ini")
        print(" [P] Putar ulang (Dengarkan audio)")
        print(" [U] Rekam Ulang file ini")
        print(" [B] Batal (Kembali ke menu)")
        aksi = input("Pilihan Anda (S/P/U/B): ").strip().upper()

        if aksi == 'P':
            print(">> Memutar rekaman audio...")
            sd.play(rekaman, SAMPLE_RATE)
            sd.wait()
            print(">> Selesai memutar.")
        elif aksi == 'S':
            FOLDER_WAV.mkdir(parents=True, exist_ok=True)
            output_file = FOLDER_WAV / f"{nama_file}.wav"
            wavfile.write(str(output_file), SAMPLE_RATE, rekaman)
            print(f"\n[SUKSES] Berkas tersimpan di: {output_file}")
            return True
        elif aksi == 'U':
            return rekam_dengan_tombol(nama_file)
        elif aksi == 'B':
            print("Perekaman dibatalkan.")
            return False
        else:
            print("Pilihan tidak valid.")


def tampilkan_status(daftar_kata):
    """Menampilkan checklist 10 file audio."""
    print("\n" + "=" * 50)
    print(" STATUS KELENGKAPAN 10 BERKAS AUDIO")
    print("=" * 50)
    lengkap = 0
    for idx, kata in enumerate(daftar_kata, start=1):
        target = FOLDER_WAV / f"{kata}.wav"
        if target.exists():
            fs, data = wavfile.read(str(target))
            durasi = len(data) / fs
            status = f"[OK - {durasi:.2f}s]"
            lengkap += 1
        else:
            status = "[BELUM DIREKAM]"
        print(f" {idx:2d}. {kata:<12} : {status}")
    print("=" * 50)
    print(f" Progres: {lengkap}/10 file sudah siap.")
    print("=" * 50)
    return lengkap


def main():
    FOLDER_WAV.mkdir(parents=True, exist_ok=True)
    daftar_kata = DAFTAR_KATA_DEFAULT

    while True:
        lengkap = tampilkan_status(daftar_kata)

        print("\nMENU PEREKAMAN:")
        print("1. Rekam 10 kata secara berurutan (Satu per satu)")
        print("2. Pilih 1 kata tertentu untuk direkam/rekam ulang")
        print("3. Dengarkan salah satu file yang sudah direkam")
        print("4. Cek daftar mikrofon yang terhubung")
        print("0. Selesai / Keluar")

        pilihan = input("\nMasukkan pilihan menu (0-4): ").strip()

        if pilihan == '1':
            for kata in daftar_kata:
                berhasil = rekam_dengan_tombol(kata)
                if not berhasil:
                    break
                print("\nSiap lanjut ke kata berikutnya?")
                lanjut = input("Tekan [ENTER] untuk lanjut, atau ketik 'x' untuk jeda: ").strip().lower()
                if lanjut == 'x':
                    break
        elif pilihan == '2':
            print("\nPilih nomor kata yang ingin direkam (1-10):")
            for idx, k in enumerate(daftar_kata, start=1):
                print(f"  {idx}. {k}")
            no = input("Nomor (1-10): ").strip()
            if no.isdigit() and 1 <= int(no) <= 10:
                target_kata = daftar_kata[int(no) - 1]
                rekam_dengan_tombol(target_kata)
            else:
                print("Nomor pilihan tidak valid.")
        elif pilihan == '3':
            file_ada = [k for k in daftar_kata if (FOLDER_WAV / f"{k}.wav").exists()]
            if not file_ada:
                print("\n[INFO] Belum ada file yang direkam di folder data_wav/.")
                continue
            print("\nPilih file yang ingin didengarkan:")
            for idx, f in enumerate(file_ada, start=1):
                print(f"  {idx}. {f}.wav")
            pilih_putar = input(f"Pilih nomor (1-{len(file_ada)}): ").strip()
            if pilih_putar.isdigit() and 1 <= int(pilih_putar) <= len(file_ada):
                target_play = FOLDER_WAV / f"{file_ada[int(pilih_putar)-1]}.wav"
                fs, data = wavfile.read(str(target_play))
                print(f">> Sedang memutar: {target_play.name}...")
                sd.play(data, fs)
                sd.wait()
                print(">> Selesai diputar.")
        elif pilihan == '4':
            print("\nDaftar Perangkat Mikrofon Terdeteksi:")
            devices = daftar_perangkat_input()
            for idx, dev in devices:
                default_tag = " (DEFAULT)" if idx == sd.default.device[0] else ""
                print(f"  [ID {idx}] {dev['name']}{default_tag}")
            input("\nTekan [ENTER] untuk kembali ke menu...")
        elif pilihan == '0':
            print("\nProgram perekaman ditutup. Selamat mengerjakan tahapan berikutnya!")
            break
        else:
            print("Pilihan menu tidak valid.")


if __name__ == '__main__':
    main()
