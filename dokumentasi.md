🎮 Ringkasan Fitur & Mekanika yang Diterapkan
1. Integrasi Peta map1safeworld.tmx (Lobby / Safe Zone)
Render 14 Tileset Lengkap: Memuat seluruh layer (Tile Layer 1, padi, jalan, tebing, jembatan, rumah, castle, door, tree) dengan penanganan rotasi & flip tile (horizontal, vertical, diagonal) sesuai spesifikasi format Tiled.
Kamera Halus (Smooth Follow): Kamera mengikuti pergerakan karakter dengan interpolasi (lerp) dan batas clamping pada ukuran map 1280x1280 px.
Sistem Tabrakan (Collision): Otomatis mendeteksi air laut pantai, tebing (kecuali ada jembatan), tembok kastil, rumah, dan batang pohon agar pemain tidak menembus rintangan.
2. Karakter Utama & Pergerakan (Movement & Animasi)
Animasi GIF 4 Arah: Menggunakan sprite GIF Anda di character/main_Char/:
Idle_walk_east.gif (Timur)
Idle_walk_north.gif (Utara)
Idle_walk_south.gif (Selatan)
Idle_walk_west.gif (Barat)
Gerakan 8 Arah Responsif: Kontrol W, A, S, D dengan normalisasi vektor diagonal.
Dodge Roll / Dash (Spasi / Shift): Roll cepat dengan efek jejak bayangan (afterimage ghost trail), biaya stamina 15, dan invincibility frames (i-frames) sesuai aturan GDD.
3. Sistem Tempur (Attack & Skill)
Serangan Pedang Normal (Klik Kiri): Mengayunkan tebasan pedang ke arah kursor mouse (biaya 10 Stamina, efek visual arc slash, dan suara tebasan pedang).
Skill Area 'Ash Cleave' (Klik Kanan): Ledakan energi gelap 360 derajat dengan efek gelombang kejut, getaran layar (screen shake), dan damage 2.2x lipat (biaya 25 Stamina).
Floating Combat Text: Angka damage melayang di atas target (putih untuk normal, oranye-emas untuk Critical Hit, hijau untuk pemulihan HP).
4. NPC di Lobby Sesuai GDD
Api Unggun Oakhaven (Campfire):
Terletak di tengah alun-alun persimpangan (X=544, Y=288).
Tekan [E] untuk memulihkan seluruh HP & Stamina serta menyimpan progres ke savegame.json.
Elara (NPC 1 - Pemandu Quest & Arsiparis):
Menjelaskan narasi Oakhaven dan 4 Suar Kematian.
Memberikan bimbingan quest utama bertahap.
Brog (NPC 2 - Resepsionis Guild / Barman):
Menggunakan sprite animasi character/npc_guild/Idle_breathing-idle_south.gif.
Melayani penukaran Monster Ash (Abu) menjadi Gold (Emas) (Kurs: 10 Abu = 25 Emas).
Pedagang Misterius (NPC 5 - Toko Upgrade):
Toko barang terlarang di sisi selatan untuk membeli Ramuan HP, Tonik Stamina, Batu Asah (+ATK permanen), Cincin Vitalitas (+HP permanen), Sepatu Bayangan (+Speed), dan Zirah (+Armor).
Kapten Penjaga (NPC 4 - Gerbang Ekspedisi Utara):
Menjaga jalan masuk menuju Bab 1: Rawa Kematian & Jenderal Gargantua.
Area Latihan Tempur (Training Yard):
Tersedia Boneka Jerami Latihan dan Monster Rawa (Karak Scout) dengan bar darah di kepala untuk menguji tebasan pedang, mengumpulkan EXP, Abu, dan Koin Emas.
5. Sistem Level, Tas (Backpack), dan Toko
Level & EXP System: Mengalahkan target memberikan EXP. Ketika EXP penuh, karakter naik level (Level Up), memulihkan HP & Stamina secara penuh, dan meningkatkan Max HP, Max Stamina, dan ATK secara permanen.
Tas Penyintas (B / I): Grid slot tas 4x4 dengan tooltip keterangan item, penghitung emas & abu, serta konsumsi ramuan cepat lewat tombol hotkey 1 (HP Potion) dan 2 (Stamina Tonic).
Mekanisme Kematian GDD: Jika HP mencapai 0, pemain gugur dan dapat menekan tombol [R] untuk respawn di Api Unggun dengan konsekuensi kehilangan 30% Abu Monster.
Penyimpanan Game (Save/Load): Tersimpan otomatis di 

savegame.json
.
🕹️ Panduan Tombol Kontrol
Tombol	Fungsi
W / A / S / D	Bergerak 8 arah (Top-Down)
Kursor Mouse	Membidik arah tebasan pedang & skill
Klik Kiri (LMB)	Serangan tebasan pedang (Konsumsi 10 Stamina)
Klik Kanan (RMB)	Skill Area ledakan "Ash Cleave" (Konsumsi 25 Stamina)
Spasi / Shift Kiri	Dodge Roll / Dash cepat (i-frame)
E	Interaksi NPC, Api Unggun & Buka Toko
B / I	Buka / Tutup Tas Penyintas (Backpack)
1 & 2	Konsumsi cepat Ramuan HP & Tonik Stamina
H	Buka panduan bantuan kontrol di dalam game
M	Mute / Unmute Musik & Efek Suara
R	Bangkit kembali di Api Unggun saat gugur
ESC	Menutup menu apa pun yang sedang terbuka
📂 Struktur File Program


main.py
: Game loop utama dan koordinasi semua sistem


src/config.py
: Resolusi layar (1280x720), konstanta, warna tema


src/map_loader.py
: Parser dan renderer peta map1safeworld.tmx + collider


src/player.py
: Logika pemain, animasi GIF 4 arah, dodge roll, status HP/Stamina/EXP


src/combat.py
: Sistem tebasan, skill area, damage calculation, floating text


src/npc.py
: Class Api Unggun, Elara, Brog, Pedagang, Penjaga, dan Boneka Latihan


src/inventory.py
: Sistem tas, item database, tooltip, penggunaan ramuan


src/shop.py
: Toko upgrade Pedagang Misterius dan meja penukaran abu Brog


src/quest.py
: Alur quest dan sistem dialog RPG ber-portrait


src/ui.py
: HUD bar darah/stamina/exp, hotbar quickslots, popup modal


src/audio.py
: Pengelola musik BGM & efek suara (SFX)


src/save_system.py
: Penyimpanan progres game ke format JSON


README.md
: Dokumentasi lengkap tugas proyek
🚀 Cara Menjalankan Game
Buka terminal di folder Codingan_Game dan jalankan:

bash
python main.py
Silakan dicoba jalankan gamenya! Jika ada hal yang ingin ditambahkan (misalnya variasi monster lain, suara tambahan, efek visual baru, atau dialog cerita yang ingin disesuaikan), silakan beri tahu ya!