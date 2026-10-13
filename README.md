# Ashes of Oakhaven: The Hollow Crown
### Game RPG 2D Top-Down Berbasis Pygame
**Mata Kuliah:** Aplikasi Perancangan Program Game (Kelompok 1)

---

## 📖 Deskripsi Game
Game ini dikembangkan berdasarkan **Game Design Document (GDD)** bertajuk *"Ashes of Oakhaven: The Hollow Crown"*, dengan mengintegrasikan peta resmi **`map1safeworld.tmx`** sebagai **Safe Zone / Guild Lobby ("Rusty Anchor")**.

Pada tahap ini, pemain memulai petualangan di area Lobby (Hub Oakhaven) dengan seluruh mekanisme dasar yang sudah aktif dan dapat dimainkan.

---

## 🎮 Kontrol Permainan (Keyboard & Mouse)
| Aksi | Tombol / Input | Keterangan |
| :--- | :--- | :--- |
| **Gerakan (8 Arah)** | `W` / `A` / `S` / `D` | Bergerak ke segala arah mata angin secara halus (Top-Down). |
| **Bidikan (Aiming)** | Kursor Mouse | Arah tebasan pedang dan skill mengarah presisi ke kursor. |
| **Serangan Pedang (Normal)** | `Klik Kiri (LMB)` | Menebas pedang ke arah mouse (Konsumsi 10 Stamina). |
| **Skill Area (Ash Cleave)** | `Klik Kanan (RMB)` | Ledakan energi area dengan efek getar layar (Konsumsi 25 Stamina). |
| **Dodge Roll / Dash** | `Spasi` / `Shift Kiri` | Menghindar cepat dengan *invincibility frames (i-frames)*. |
| **Interaksi NPC / Benda** | `E` | Berbicara dengan NPC, istirahat di Api Unggun, membuka Toko. |
| **Tas Penyintas (Backpack)**| `B` atau `I` | Buka/tutup inventory, klik ramuan untuk mengonsumsi. |
| **Quick Potion HP** | `1` | Mengonsumsi Ramuan Pemulih HP seketika (+50 HP). |
| **Quick Potion Stamina** | `2` | Mengonsumsi Tonik Stamina seketika (+50 Stamina). |
| **Bantuan Kontrol** | `H` | Menampilkan overlay panduan kontrol di dalam game. |
| **Mute / Unmute Audio** | `M` | Menyalakan atau mematikan musik & efek suara. |
| **Respawn** | `R` | Bangkit kembali di Api Unggun saat HP mencapai 0. |
| **Tutup Menu / Batal** | `ESC` | Menutup dialog, toko, atau tas. |

---

## 🏛️ Fitur & NPC di Lobby Oakhaven
1. **Api Unggun Oakhaven (Campfire):**
   - Terletak di pusat alun-alun persimpangan jalan (X=544, Y=288).
   - Efek visual api menyala dan partikel percikan.
   - Interaksi `[E]`: Memulihkan HP & Stamina secara penuh, serta menyimpan progres pemain ke `savegame.json`.
2. **Elara (NPC 1 - Pemandu Quest & Arsiparis):**
   - Menjelaskan narasi kehancuran Oakhaven akibat Sang Penguasa Abu dan 4 Suar Kematian.
   - Memberikan bimbingan quest utama bertahap.
3. **Brog (NPC 2 - Resepsionis Guild / Barman):**
   - Menggunakan sprite animasi khusus `character/npc_guild`.
   - Melayani penukaran **Monster Ash (Abu)** menjadi **Gold (Emas)** (Kurs: 10 Abu = 25 Emas atau tukar sekaligus).
4. **Pedagang Misterius (NPC 5 - Toko Upgrade Senjata):**
   - Berada di sisi selatan dekat lorong gorong-gorong.
   - Membuka Toko Perlengkapan Gelap: Beli Ramuan HP, Tonik Stamina, Batu Asah (+ATK permanen), Cincin Vitalitas (+HP permanen), Sepatu Bayangan (+Speed), dan Zirah (+Armor).
5. **Kapten Penjaga (NPC 4 - Gerbang Ekspedisi Utara):**
   - Berjaga di depan gerbang kastil utara.
   - Menjelaskan bahaya Bab 1: Rawa Kematian dan Jenderal Gargantua.
6. **Area Latihan Tempur (Training Yard):**
   - Disediakan **Boneka Latihan (Training Dummies)** dan **Karak Scout (Monster Rawa)**.
   - Memiliki bar darah di atas kepala, menerima damage tebasan dan skill, memunculkan angka damage melayang (*Floating Combat Text*), serta menjatuhkan EXP, Abu Monster, dan Emas saat dikalahkan.

---

## ⚙️ Sistem & Mekanika Dasar
- **Level & EXP System:** Mengalahkan monster/target memberikan EXP. Saat EXP penuh, karakter naik level (*Level Up*), memulihkan HP & Stamina penuh, serta meningkatkan statistik dasar secara permanen.
- **Sistem Stamina & HP:** Bar HP dengan efek *smooth trailing decay*, serta Stamina yang berkurang saat menyerang/dash dan terisi ulang secara otomatis saat jeda.
- **Backpack System:** Grid slot tas 4x4 dengan info tooltip detail, penghitung koin emas & abu, serta konsumsi ramuan yang responsif.
- **Sistem Kematian Sesuai GDD:** Jika HP mencapai 0, pemain gugur dan dapat bangkit di Api Unggun dengan konsekuensi kehilangan 30% Abu Monster yang dikumpulkan.
- **Sistem Penyimpanan (Save/Load):** Progres level, EXP, emas, abu, inventory, dan quest tersimpan secara otomatis di `savegame.json`.

---

## 🚀 Cara Menjalankan Game
Pastikan Python dan modul `pygame` serta `Pillow` sudah terinstal:
```bash
pip install pygame pillow
```

Jalankan game dengan perintah:
```bash
python main.py
```
