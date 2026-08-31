BUILD THE PROGRESS
==================

Setiap hal yang selesai dibangun ditaruh di sini. Dua berkas, nama sama:

    <nama>.jpg    banner persegi 1080x1080
    <nama>.txt    judul, caption siap posting, lalu penjelasan mekanismenya

Di dalam .txt ada dua pagar pembatas:

    ###  MULAI SALIN DARI SINI  ###
    ...caption...
    ###  SELESAI SALIN          ###

Salin persis semua yang ada di antara dua pagar itu, termasuk tautannya, lalu
lampirkan .jpg-nya. Selesai. Jangan menambah atau mengurangi apa pun.

Semua yang ada di bawah pagar kedua TIDAK diposting. Isinya balasan untuk
digantung di bawah postingan, penjelasan cara kerjanya, dan jawaban siap pakai
untuk pertanyaan yang biasanya muncul.


CARA MENULIS CAPTIONNYA
=======================

Ini bagian yang paling gampang bikin gagal. Tulisan bisa benar semua isinya
tapi tetap terasa dingin, kaku, atau ketahuan buatan mesin. Aturannya:

1.  Jangan buka dengan laporan status.
    Buruk : "The escrow contract is written."
    Benar : "Spent today writing a contract that makes it impossible for us to
             touch the money. On purpose."
    Kalimat pertama tugasnya cuma satu: bikin orang baca kalimat kedua.

2.  Pakai "we". Bukan "Time Vault does X".
    Yang menghindari kata "we" selalu terdengar seperti siaran pers.

3.  Kalimat pendek. Boleh tidak lengkap.
    "Not the buyer, not us." Itu bukan kalimat utuh, dan justru itu yang bikin
    kedengaran seperti orang bicara.

4.  Buang kalimat penunjuk arah.
    Buruk : "Here is the part worth reading." / "A few of the details:"
    Manusia tidak mengumumkan bahwa dia akan menjelaskan. Dia langsung
    menjelaskan.

5.  Jangan ada daftar berpoin di postingan utama.
    Postingan utama satu ide saja. Detail dan angka masuk ke balasan.

6.  Angka dilempar santai, bukan dipamerkan.
    Buruk : "31 tests, all passing. solc 0.8.24, zero warnings."
    Benar : "562 lines, 31 tests, zero warnings, all of it public."

7.  Tutup dengan ajakan, bukan ringkasan.
    "Go break it." / "Go look." Bukan "In summary" atau pengulangan isi.

8.  Jangan pernah menulis "belum", "not yet", "still".
    Bukan untuk menyembunyikan apa pun, tapi karena kata itu terdengar seperti
    minta maaf. Tulis apa yang berikutnya: "Testnet next."
    Yang belum jadi tetap tidak boleh ditulis seolah sudah jalan. Bedanya di
    nada, bukan di kejujuran.

9.  Baca keras-keras sebelum posting.
    Kalau ada kalimat yang tidak akan kamu ucapkan ke teman, ganti.

Ciri tulisan yang ketahuan AI, hindari semua:
    - tiga hal sejajar dalam satu kalimat, terus-menerus
    - setiap kalimat panjangnya mirip
    - "bukan X, melainkan Y" dipakai berulang
    - sopan berlebihan, tidak ada sedikit pun sikap
    - menjelaskan sesuatu yang sebenarnya sudah jelas


ATURAN LAIN
===========

Caption bahasa Inggris, karena itu yang dibaca di X. Penjelasan mekanisme
bahasa Indonesia, karena itu untuk kamu.

Setiap postingan harus membawa sesuatu yang bisa dibuka orang asing: berkas
kode, hash transaksi, kontrak di explorer, halaman yang jalan. Itu yang bikin
orang percaya, dan itu juga yang bikin orang takut ketinggalan.

Angka harus angka asli. Jangan dibulatkan ke atas, jangan dikira-kira. Ada satu
saja yang meleset dan seluruh akun ini kehilangan alasan untuk dipercaya.

Tidak ada hitungan hari. Bukan "Day 3 of 10". Begitu satu hari terlewat,
hitungan itu berubah jadi utang di depan umum.


CARA MEMBUAT BANNER BARU
========================

Buka marketing/progress-banner.html, ubah objek POST di bagian bawah:
slug, eyebrow, judul, subjudul, chip, dan potongan kode aslinya. Lalu:

    python marketing/render_progress.py

Hasilnya langsung masuk ke folder ini, dengan nama sesuai slug.

Potongan kode di banner harus kode asli dari berkas yang benar-benar dikirim,
lengkap dengan nomor barisnya. Bukan kode karangan yang dibuat supaya terlihat
bagus.


SUDAH ADA DI SINI
=================

escrow-written    kontrak escrow ditulis, 562 baris, 31 tes lulus
