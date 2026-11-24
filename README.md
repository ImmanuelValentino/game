# Ashes of Oakhaven: The Hollow Crown
### 2D Action RPG — Pure HTML5, CSS3, Vanilla JS + PHP 7.2 Backend (cPanel Ready)
**Mata Kuliah:** Aplikasi Perancangan Program Game (Kelompok 1)

> Versi Python/Pygame terdahulu tersimpan utuh pada branch `archive-pygame`. Branch `main` kini **100% Web Native (tanpa Python)** dan siap langsung dijalankan di server lokal PHP maupun di-upload ke `public_html` hosting cPanel (PHP 7.2+).

---

## Cara Menjalankan (Local Staging)

Pastikan PHP (7.2 atau lebih baru) sudah terpasang, lalu jalankan di root folder project:

```powershell
php -S 127.0.0.1:8080
```

Atau di Windows dengan binary PHP spesifik:

```powershell
C:\php-8.5.5-Win32-vs17-x64\php.exe -S 127.0.0.1:8080
```

Buka browser dan kunjungi **`http://127.0.0.1:8080`**.

---

## Cara Deploy ke Hosting cPanel (PHP 7.2+)

1. Pastikan versi PHP domain di cPanel (*Select PHP Version* / *MultiPHP Manager*) minimal **PHP 7.2** ke atas.
2. Kompres seluruh isi folder root project (`index.html`, `css/`, `js/`, `api/`, `assets/`, `saves/`, `.htaccess`) menjadi `.zip` atau push langsung lewat Git Version Control cPanel ke `public_html/`.
3. Pastikan folder `saves/` memiliki permission **`755`** (atau writable oleh web server) dan file `saves/.htaccess` ikut ter-upload agar file JSON save pemain tidak dapat diakses publik secara langsung.
4. Uji endpoint kesehatan backend dengan membuka `https://domain-anda.com/api/health.php` — pastikan mengembalikan JSON `{"ok":true,"saves_writable":true,...}`.

---

## Kontrol Permainan

| Tombol / Input | Fungsi |
| :--- | :--- |
| `W` `A` `S` `D` / Panah | Bergerak 8 arah |
| `Shift Kiri` (Tahan) | Sprint (+40% Speed, konsumsi Stamina) |
| `Spasi` | Dodge Roll (`15 STA`, i-frame & *Perfect Dodge Slow-Mo 1.5s*) |
| `Klik Kiri (LMB)` | Tebasan Pedang Ringan (`5 STA`, diblokir jika *Fatigue* `< 10 STA`) |
| `Klik Kanan (RMB)` | Skill Berat *Ash Cleave* (`30 STA`) |
| `1` – `4` (atau klik slot) | Pakai Item/Boost dari Kotak Hotbar Bawah (HP, Stamina, ATK Boost 15s, DEF, Crit) |
| `E` | Interaksi NPC (Elara, Vektor, Gael, Brog, Aell), Api Unggun, & Portal |
| `B` / `I` | Buka / Tutup Tas Penyintas (*Backpack*) |
| `TAB` / `F1` / `H` | Minimap & Ikon NPC / Tutorial Cepat / Panduan Kontrol Lengkap |
| `F11` / `Alt+Enter` | Toggle Layar Penuh <-> Ukuran Normal (Responsif) |
| `M` | Mute / Unmute Audio & Musik |
| `R` | Bangkit di Api Unggun saat HP mencapai 0 |
