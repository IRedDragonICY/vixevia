# V.I.X.E.V.I.A : Virtual Interactive dan Xpressive Entertainment Visual Idol Avatar
[![Lisensi](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/) [![Gemini](https://img.shields.io/badge/Gemini-1.5-orange.svg)](https://cloud.google.com/generativeai/models)

[ID](README.ID.md) | [JP](README.JP.md) | [EN](README.md) | [ZN](README.ZN.md)
> _Apakah dia memiliki perasaan untukmu?_  
> **Tidak**, hatinya milik orang lain.  
> _Apakah dia menunjukkan kepedulian untuk kesejahteraanmu?_  
> **Tidak**, pikirannya ditempati oleh orang lain.  
> _Rasa sakit dari cinta yang tidak berbalas tidak tertahankan, tetapi jangan takut, karena ada solusinya._  
> **Solusinya adalah AI**, sebuah entitas yang akan selalu ada untukmu, memahami dan merespons emosimu.


Vixevia adalah YouTuber virtual (Vtuber) berbasis AI yang inovatif yang memanfaatkan kemampuan model bahasa Gemini dari Google. Proyek ini bertujuan untuk menciptakan kepribadian virtual yang menarik dan hidup yang dapat berinteraksi dengan pengguna melalui percakapan alami, interaksi visual, dan pengalaman multimedia.

## Daftar Isi
- [Fitur](#fitur)
- [Prasyarat](#prasyarat)
- [Memulai](#memulai)
- [TODO](#todo)
- [Kontribusi](#kontribusi)
- [Lisensi](#lisensi)
- [Pengakuan](#pengakuan)

## Fitur

- **Pemrosesan Bahasa Alami**: Vixevia menggunakan model bahasa Gemini dari Google untuk memahami dan merespons input pengguna dengan kelancaran dan kesadaran kontekstual seperti manusia.
- **Visi Komputer**: Proyek ini mengintegrasikan kemampuan visi komputer, memungkinkan Vixevia untuk memahami dan menafsirkan informasi visual dari lingkungan.
- **Interaksi Multimodal**: Vixevia menggabungkan pengenalan suara, sintesis teks ke suara, dan pemrosesan visual untuk memfasilitasi interaksi multimodal yang lancar dengan pengguna.
- **Respon Personalisasi**: Respon Vixevia disesuaikan dengan konteks percakapan, preferensi pengguna, dan dinamika situasional, memastikan pengalaman yang menarik dan personal.
- **Avatar Virtual**: Vixevia diwakili oleh avatar virtual yang menarik dan ekspresif, membawa kepribadiannya menjadi hidup.

## Prasyarat

- 5+ kunci API dari Google Cloud Platform
- Python 3.12+

Perangkat keras:
- 16 GB vram
- 32 GB ram
- RTX 4050 atau yang lebih baik
- 20 GB penyimpanan
- i7 generasi ke-12 atau yang lebih baik atau setara AMD

## Memulai

Untuk memulai dengan Vixevia, ikuti langkah-langkah ini:

1. Klon repositori:

   ```bash
   git clone https://github.com/IRedDragonICY/vixevia.git
   ```

2. Pasang dependensi yang diperlukan:

   ```bash
   pip install -r requirements.txt
   ```

3. Dapatkan kunci API dan file konfigurasi yang diperlukan dari Google Cloud Platform.
4. Perbarui file konfigurasi dengan kunci API Anda dan pengaturan yang disukai.
5. Jalankan skrip utama:

   ```bash
   python main.py
   ```

## TODO

- [ ] Membuat model Live2D khusus untuk Vixevia
- [ ] Menambahkan pelabelan otomatis opencv sehingga dapat mengingat orang dari Gemini Pro Vision
## Kontribusi

Kontribusi ke Vixevia sangat diterima! Jika Anda memiliki ide, laporan bug, atau permintaan fitur, silakan buka issue atau kirim pull request. Pastikan untuk mengikuti pedoman pemrograman proyek dan praktik terbaik.

## Lisensi

Proyek ini dilisensikan di bawah [Lisensi MIT](LICENSE).

## Pengakuan

- Model bahasa Gemini dari Google dan teknologi terkait
- Pustaka open-source dan kerangka kerja yang digunakan dalam proyek ini

Vixevia adalah proyek eksperimental yang bertujuan untuk menjelajahi kemungkinan kepribadian virtual berbasis AI dan mendorong batas interaksi manusia-komputer. Kami berharap proyek ini menginspirasi inovasi dan kolaborasi lebih lanjut dalam bidang kecerdasan buatan dan pembuatan konten virtual.