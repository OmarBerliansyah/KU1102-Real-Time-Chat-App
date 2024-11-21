# Aplikasi Chat Real-time

Aplikasi chat real-time sederhana yang memungkinkan komunikasi antar pengguna dalam jaringan yang sama.

## Prasyarat

- Python 3.6 atau lebih baru
- Pustaka customtkinter: `pip install customtkinter`


## Cara Penggunaan

### 1. Menjalankan Server
Masukkan perintah berikut ke dalam terminal python anda (pastikan directory folder benar):
    python server.py

Server akan menampilkan IP dan port yang digunakan (default port: 8000)

### 2. Menjalankan Client
Masukkan perintah berikut ke dalam terminal python anda (pastikan directory folder benar):
    python client.py


Setelah menjalankan client:

1. Pilih alamat IP server dari daftar atau masukkan manual.
2. Masukkan nama panggilan Anda.
3. Mulai chat!

### 3. Koneksi dalam Jaringan WiFi yang Sama

1. Satu orang harus menjalankan `server.py` terlebih dahulu.
2. Server akan menampilkan IP lokal (biasanya 192.168.xxx.xxx, kalau berbeda tidak apa, disesuaikan saja).
3. Pengguna lain dapat menjalankan `client.py` dan memasukkan IP server tersebut.
4. Pastikan semua komputer terhubung ke jaringan WiFi yang sama.
5. Pastikan tidak ada firewall yang memblokir koneksi.
6. Gunakan port default 8000.

### Fitur-fitur

- Format teks: 
  - Bold: Ctrl+B
  - Italic: Ctrl+I
  - Underline: Ctrl+U
- Kirim pesan: Ctrl+Enter atau tombol Send
- Berbagi file: klik tombol paperclip
- Layar penuh: F11

### Informasi Tambahan

- **File sementara**: Server menyimpan file yang diterima dalam folder `temp_files` sebelum mengirimkannya ke klien lain. File ini akan dihapus secara otomatis setelah transfer selesai.
- **Log aktivitas**: Semua aktivitas server dicatat dalam folder `logs`, termasuk pesan masuk dan transfer file.
- **UUID untuk file**: Setiap file yang ditransfer diberi nama unik untuk menghindari konflik.

### Troubleshooting

1. Server tidak bisa dijalankan:
   - Periksa apakah port 8000 sudah digunakan.
   - Periksa firewall.

2. Client tidak bisa connect:
   - Pastikan IP server benar.
   - Pastikan server sudah running.
   - Pastikan terhubung ke WiFi yang sama.
