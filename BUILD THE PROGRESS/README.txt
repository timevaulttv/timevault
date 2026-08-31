BUILD THE PROGRESS
==================

Setiap hal yang selesai dibangun ditaruh di sini. Dua berkas, nama sama:

    <nama>.jpg    banner persegi 1080x1080
    <nama>.txt    judul, caption siap posting, lalu penjelasan mekanismenya

Tinggal buka .txt-nya, salin bagian caption, lampirkan .jpg-nya. Selesai.

Bagian bawah .txt bukan untuk diposting. Itu penjelasan cara kerjanya dalam
bahasa Indonesia, supaya kalau ada yang bertanya di kolom balasan, jawabannya
sudah ada dan tidak perlu menebak.

Aturan yang berlaku untuk semuanya
----------------------------------

Caption bahasa Inggris, karena itu yang dibaca di X. Penjelasan mekanisme
bahasa Indonesia, karena itu untuk kamu.

Ringkas. Judul satu baris, caption beberapa baris, lalu tautan yang bisa
dibuka orang asing. Setiap postingan harus membawa sesuatu yang bisa dicek:
berkas kode, hash transaksi, kontrak di explorer, halaman yang terbuka.

Tidak ada hitungan hari. Bukan "Day 3 of 10". Begitu satu hari terlewat,
hitungan itu berubah jadi utang di depan umum.

Jangan pernah menulis sesuatu yang belum jadi seolah sudah jalan. Kalau belum
di-deploy, tulis apa adanya. Reputasi akun ini bertumpu pada itu.

Cara membuat banner baru
------------------------

Buka marketing/progress-banner.html, ubah objek POST di bagian bawah:
slug, eyebrow, judul, subjudul, chip, dan potongan kode aslinya. Lalu:

    python marketing/render_progress.py

Hasilnya langsung masuk ke folder ini, dengan nama sesuai slug.

Potongan kode di banner harus kode asli dari berkas yang benar-benar dikirim,
lengkap dengan nomor barisnya. Bukan kode karangan yang dibuat supaya terlihat
bagus.

Sudah ada di sini
-----------------

escrow-written    kontrak escrow ditulis, 31 tes lulus, belum di-deploy
