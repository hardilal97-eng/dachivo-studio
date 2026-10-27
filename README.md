# Dachivo Studio v1

Prototype lokal untuk menyusun storyboard animasi 3 menit, prompt per klip, upload klip Google Flow, dan merender MP4 dengan FFmpeg.

**Status:** integrasi Google Flow otomatis, audio, pengecekan transisi/karakter dan trimming tepat 180 detik **belum tersedia**. Versi ini menghasilkan draft video tanpa audio.

## Instalasi InstaBox / Debian / Ubuntu

Jalankan di terminal mesin InstaBox yang menyediakan `sudo` dan penyimpanan permanen `/data`:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip ffmpeg
cd /data
git clone https://github.com/hardilal97-eng/dachivo-studio.git
cd dachivo-studio
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8787
```

Buka port 8787 hanya melalui private port-forward/SSH tunnel. **Jangan publish port tanpa autentikasi:** versi ini belum memiliki login dan membolehkan upload file.

## Penggunaan
1. Buat storyboard dan periksa prompt setiap shot.
2. Generate klip menggunakan Google Flow secara manual; gunakan Extend/frame referensi untuk konsistensi.
3. Simpan klip sebagai `001.mp4`, `002.mp4`, dst., lalu upload sesuai urutan.
4. Klik **Gabungkan MP4** untuk menghasilkan draft. Tambahkan audio dan tinjau sambungan sebelum dipublikasikan.

## Batasan
- Tidak memanggil API Google Flow dan belum melakukan Playwright automation.
- Upload/render tidak mempunyai pembatas ukuran/quota dan tidak layak diekspos publik.
- Merender ulang setiap klip ke 720p/24fps dan menghapus audio.
- Belum memvalidasi jumlah shot, durasi final, ataupun konsistensi karakter.
- Gunakan penyimpanan `/data` untuk menjaga file saat lingkungan menghapus filesystem sementara.
