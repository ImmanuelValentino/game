# Implementation Plan — Ashes of Oakhaven: The Hollow Crown

Dokumen ini mencatat rencana pengembangan & verifikasi menyeluruh berdasarkan [GDD/Kelompok 1_GDD_Aplikasi Perancangan Program Game.docx](GDD/Kelompok%201_GDD_Aplikasi%20Perancangan%20Program%20Game.docx) dan [GDD/Dokumen Desain Naratif RPG - Hujan Abu di Oakhaven.docx](GDD/Dokumen%20Desain%20Naratif%20RPG%20-%20Hujan%20Abu%20di%20Oakhaven.docx).

---

## Phase 1 — Perbaikan Bug Kritis & Stabilitas Inti (P0) — SELESAI

- [x] **Save/Load Atomik ([src/save_system.py](src/save_system.py)):** Perbaikan impor `ITEM_DATABASE`, validasi sebelum mutasi, penyimpanan `weapon_id`, `karma`, `skill_points`, `skill_levels`, `beacons_cleared`, `current_map`, serta `.gitignore` untuk mengisolasi `savegame.json` & `__pycache__/`.
- [x] **Inventory & Shop ([src/inventory.py](src/inventory.py), [src/shop.py](src/shop.py)):** Perbaikan crash `FloatingText`, `remove_item()` mengosongkan slot menjadi `None`, `can_add_item()` sebelum pemotongan emas, equip senjata langsung dari tas, dan sinkronisasi layout klik vs gambar.
- [x] **MapLoader & Dungeon Klasik ([src/map_loader.py](src/map_loader.py), [dungeon2.tmx](dungeon2.tmx)):** Penghapusan tag tileset unused yang hilang di `dungeon2.tmx`, collider untuk `wall`, `atas tembok`, `pillars`, properti dungeon, celah `pintu`/`door`, serta spatial grid lookup $O(1)$.

---

## Phase 2 — Realisasi Penuh Alur Cerita, Hub, & 5 Bioma GDD — SELESAI

### 2.1 Splash / Main Menu, Prolog Hujan Abu, & Klimaks Ending ([src/scenes.py](src/scenes.py))
- [x] **Title Screen (`TitleScreenScene`):** Ilustrasi latar `assets/ui/title_bg.png`, efek hujan abu & bara, tombol Permainan Baru / Lanjutkan / Panduan Kontrol / Keluar.
- [x] **Prolog Interaktif (`PrologScene`):** Narasi *Hujan Abu di Oakhaven*, bisikan Roh Leluhur, adegan *Dinding Keputusasaan* melawan Gargantua hingga diselamatkan Aell ke Hub *Rusty Anchor*.
- [x] **Klimaks & 2 Ending + QTE (`EndingScene`):** Evaluasi `Karma` (`<= -30` Bad Ending *Raja Iblis Baru*; `>= 20` QTE Good Ending membelah Mahkota bersama siluet Vektor, Aell, dan Gael; `-29..19` pilihan krusial terakhir) + layar Credits.

### 2.2 Hub Oakhaven ("Rusty Anchor") & NPC Sesuai GDD ([src/npc.py](src/npc.py), [src/shop.py](src/shop.py), [src/quest.py](src/quest.py))
- [x] **Vektor (Guildmaster & Bengkel Skill):** Konversi material monster 4 rarity menjadi Gold & Poin Skill (`SKL`), pelatihan skill tempur (`+ATK`, `+STA/Regen`, `+HP/DEF`), serta tempa *Bilah Penebusan* (`+20 Karma`).
- [x] **Aell (Map Reader):** Layar Kartografi Dinamis (`CartographyMapUI`) menampilkan 5 bioma + 2 dungeon klasik dengan pembukaan akses bertahap seiring bos yang ditumbangkan.
- [x] **Gael (Former Adventurer & Pedagang Senjata):** Penjualan ramuan, armor, *Bilah Penebusan*, dan senjata terlarang *Pedang Haus Darah* (`ATK +320`, `Drop x1.5`, `-50 Karma`).
- [x] **Elara, Brog, Penjaga Gerbang, Leo & Aria:** Seluruh NPC Lobby menggunakan sprite animasi tepat arah + dialog terintegrasi.

### 2.3 Generasi Aset, 5 Stage Bioma, Hazard, & 5 Bos GDD ([tools/generate_gdd_assets.py](tools/generate_gdd_assets.py))
- [x] **Tileset & 5 Peta Bioma `.tmx`:** `assets/tilesets/biome_tiles.png/.tsx`, `stage1_swamp.tmx` (Rawa Kematian), `stage2_spore.tmx` (Hutan Spora), `stage3_gehenna.tmx` (Tungku Gehenna), `stage4_frost.tmx` (Benteng Salju Hitam), dan `stage5_throne.tmx` (Ruang Takhta Obsidian).
- [x] **Mekanika Hazard Lingkungan:** Lumpur pekat (`-30% SPD`, `2x Sprint drain`), Jebakan hisap, Kabut Racun (`DoT` & `+15% DMG masuk`), Spora Peledak (`SporeTrap`), Conveyor Belt mendorong posisi, Lahar panas, dan Lantai Es Licin (inersia momentum).
- [x] **Sprite Monster Ranged & 5 Bos (`character/`):** `monster_ranged`, `boss_gargantua`, `boss_vespa`, `boss_ignis`, `boss_valerius`, `boss_demonKing` (Fase 1), dan `boss_hollow_crown` (Fase 2) lengkap dengan serangan proyektil bullet-hell yang terblokir pilar/dinding.
- [x] **Audio Procedural (`assets/audio/`):** `projectile.wav`, `explosion.wav`, `parry.wav`, `bgm_dungeon.wav`, `bgm_boss.wav`, `bgm_throne.wav` (detak jantung Ruang Takhta), `ending_good.wav`, `ending_bad.wav`.

---

## Phase 3 — Formula Combat GDD, Drop Table, & Verifikasi — SELESAI

- [x] **Formula Damage & Progresi GDD ([src/config.py](src/config.py), [src/player.py](src/player.py), [src/combat.py](src/combat.py)):** Rasio `((BaseATK + WeaponATK) / (EnemyDEF*0.5 + 10)) * PLAYER_DAMAGE_SCALING * Mod`, rasio `EnemyATK / (PlayerDEF*0.5 + 10) * HazardPenalty * FatiguePenalty`, tabel progresi Lv 1–70, konsumsi stamina seimbang (Basic Attack `5 STA`, Skill `Ash Cleave` tetap `30 STA`, Roll `15 STA`) + jeda regen `0.6s` (`24 STA/s`), *Fatigue* (`STA < 10`), dan *Perfect Dodge Slow-Mo 1.5s* (`+15 STA` & `150% Crit`).
- [x] **Weighted RNG Drop 4 Tier Rarity & Penalti Kematian:** Drop material `Common 70%`, `Uncommon 20%`, `Rare 8%`, `Epic/Boss 2% (100% bos)`, serta pengurangan `30% Abu` & `50% material belum terjual` saat gugur.
- [x] **Tampilan Layar Responsif, Resizable, & Fullscreen ([src/config.py](src/config.py), [main.py](main.py), [src/ui.py](src/ui.py), [src/scenes.py](src/scenes.py), [src/inventory.py](src/inventory.py), [src/shop.py](src/shop.py), [src/quest.py](src/quest.py)):** Jendela mendukung tarik tepi / Maximize (`pygame.RESIZABLE`), toggle Layar Penuh <-> Ukuran Normal (`F11`, `Alt+Enter`, atau tombol di Menu Utama), pemetaan koordinat mouse (`window_to_logical`), kamera terpusat otomatis saat viewport melebihi peta, dan layout HUD/modal dinamis berbasis `get_screen_size()`.
- [x] **Pengembangan Fitur Kelompok (NPC Spread, Minimap Icons, Story Animasi, Audio Suasana, Skull Laser, Dungeon 1–4, Api Putih, & Hotbar):**
  - **NPC Hub & Minimap Icons ([main.py](main.py), [src/ui.py](src/ui.py), [src/npc.py](src/npc.py)):** NPC tersebar ke seluruh distrik Kota Oakhaven lengkap dengan ikon khusus (`shop`, `skill`, `map`, `quest`, `bar`, `campfire`, `white_fire`, `portal`, `boss`) dan legenda pada minimap.
  - **Tutorial & Story Beranimasi ([src/ui.py](src/ui.py), [src/scenes.py](src/scenes.py), [src/quest.py](src/quest.py)):** Banner tutorial cepat `[F1]` + dialog animasi slide/bobbing portrait + `PrologScene` diorama karakter bergerak (`Ethan`, `Gargantua`, `Aell`, `Vektor`, `Gael`) & `EndingScene` beranimasi.
  - **Audio Suasana ([tools/generate_gdd_assets.py](tools/generate_gdd_assets.py), [src/audio.py](src/audio.py)):** Musik tema tenang ala Zelda untuk Lobby (`bgm_village.wav`), musik battle antusias untuk Dungeon (`bgm_dungeon.wav`/`bgm_boss.wav`), dan tema intens/tertekan untuk Final Boss Domain (`bgm_throne.wav`).
  - **Mekanik Final Boss Domain & Dungeon 1–4 ([src/combat.py](src/combat.py), [src/npc.py](src/npc.py), [src/config.py](src/config.py)):** 6 Kepala Tengkorak Laser invincible (`SkullLaserBarrage` formasi 3 atas+3 bawah & 3 kiri+3 kanan), progresi musuh tajam Dungeon 1–4 yang mendorong pembelian boost/upgrade, tanpa regen HP otomatis + **Api Putih** (`WhiteFlame`) di sudut dungeon, serta **Hotbar Item Bawah `[1–4]`** untuk Ramuan HP, Attack Boost (15 detik), Defense Boost, Crit Focus, & Stamina Tonic.
- [x] **Automated Test Suite ([tests/test_game.py](tests/test_game.py)):** Verifikasi penuh seluruh 8 peta `.tmx`, konektivitas BFS, mekanika stamina/fatigue/slow-mo/hazard/boss 2-fase, ekonomi Vektor/Gael/Karma, save/load, seluruh ikon inventory, layar responsif, NPC spread, Api Putih, Skull Laser, dan Hotbar boost (`python -B -m unittest discover -s tests -v`).
