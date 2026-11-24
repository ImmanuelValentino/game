# Implementation Plan — Ashes of Oakhaven: The Hollow Crown

Dokumen ini mencatat arsitektur & rencana implementasi menyeluruh versi **Web Pure HTML5 + CSS3 + Vanilla JavaScript + PHP 7.2 Backend** (*cPanel-ready*), berlandaskan GDD Kelompok 1 ([GDD/](GDD/)).

> **Catatan Arsip:** Versi Python/Pygame original telah diarsipkan utuh di branch `archive-pygame` pada repository GitHub sebelum migrasi bersih branch `main` ke arsitektur Web + PHP 7.2.

---

## Phase 1–3 (Python Heritage — Diarsipkan di `archive-pygame`) — SELESAI

Seluruh fitur GDD inti (5 bioma & 5 bos, 2-fase Final Boss, NPC Vektor/Aell/Gael/Elara/Brog, formula damage GDD, Perfect Dodge Slow-Mo, 4 rarity drop table, layar responsif `[F11]`, NPC spread & minimap icons, story beranimasi, musik suasana Zelda/Battle/Throne, 6 Skull Laser Barrage, progresi Dungeon 1–4, Api Putih regen, dan Hotbar Item `[1–4]`) telah divalidasi di versi desktop sebelum diekspor ke pipeline Web.

---

## Phase 4 — Migrasi Bersih ke Pure HTML5/CSS3/JS + PHP 7.2 cPanel — SELESAI

### 4.1 Ekspor Aset Web 60fps (`assets/data/`, `assets/sprites_web/`, `assets/items_web/`)
- [x] **Bake Peta TMX/TSX -> PNG & JSON ([assets/data/maps/](assets/data/maps/)):** Seluruh 8 peta (`map1safeworld`, `stage1_swamp`, `stage2_spore`, `stage3_gehenna`, `stage4_frost`, `stage5_throne`, `dungeon1`, `dungeon2`) diekspor menjadi sprite latar `1280x1280.png` + data `colliders` & `hazards` JSON berkecepatan tinggi.
- [x] **Ekspor Strip Sprite PNG (`assets/sprites_web/` & [assets/data/sprites.json](assets/data/sprites.json)):** Seluruh `.gif` animasi & faceset karakter/monster/bos/Skull Laser/Api Putih dikonversi menjadi horizontal PNG strip bebas bug *freeze* frame-0 pada Canvas.
- [x] **Crop Ikon Item Bersih ([assets/items_web/](assets/items_web/)):** Seluruh ikon senjata (`Katana.png`, `Hammer.png`, `Axe.png` dari grid 4x4), material, dan potion/boost diekspor ke resolusi tajam `36x36`.

### 4.2 Engine Game Pure HTML5 + CSS3 + Vanilla JS ([index.html](index.html), [css/style.css](css/style.css), [js/](js/))
- [x] **Core Loop, Viewport Responsif, & Input ([js/main.js](js/main.js), [js/config.js](js/config.js)):** Canvas responsif (`computeLogicalSize`), Fullscreen API `[F11]` / `[Alt+Enter]`, pemetaan presisi koordinat mouse, pencegahan menu konteks klik kanan (`RMB` *Ash Cleave*), dan loop `requestAnimationFrame` 60fps dengan *Slow-Mo* `0.38x`.
- [x] **Web Audio & Musik Suasana ([js/audio.js](js/audio.js)):** Auto-unlock AudioContext + BGM streaming (`bgm_village.wav`, `bgm_dungeon.wav`, `bgm_boss.wav`, `bgm_throne.wav`), mute toggle `[M]`, dan Web Audio buffer SFX instan.
- [x] **Combat, Hazards, Api Putih, & 6 Skull Laser ([js/combat.js](js/combat.js), [js/entities.js](js/entities.js)):** Implementasi penuh `Player` (tanpa auto-HP regen), `WhiteFlame` di sudut dungeon, `SkullLaserBarrage` (6 tengkorak invincible), `SporeTrap`, proyektil bullet-hell, dan progresi Dungeon 1–4.
- [x] **Inventory Hotbar, Shop, Quest, UI, & Story Animasi ([js/inventory.js](js/inventory.js), [js/shop.js](js/shop.js), [js/quest.js](js/quest.js), [js/ui.js](js/ui.js), [js/scenes.js](js/scenes.js)):** Kotak Hotbar bawah `[1–4]` otomatis terisi item drop/shop, toko Gael 2 kolom, Bengkel Vektor, Kartografi Aell, Minimap custom icons + legenda, tutorial cepat `[F1]`, `PrologScene` diorama beranimasi, serta `EndingScene` QTE & 2 ending.

### 4.3 Backend PHP 7.2 & Konfigurasi Hosting cPanel ([api/](api/), [.htaccess](.htaccess), [saves/.htaccess](saves/.htaccess))
- [x] **REST Save API Strict PHP 7.2:** `api/health.php`, `api/save.php` (`POST` JSON ter-sanitasi `player_id` dengan `LOCK_EX`), dan `api/load.php` (`GET`) menggunakan sintaks ketat PHP 7.2 (tanpa MySQL, siap upload ke `public_html` cPanel) + sinkronisasi otomatis `localStorage` di [js/storage.js](js/storage.js).
- [x] **Keamanan cPanel:** Proteksi langsung folder [saves/](saves/) via [saves/.htaccess](saves/.htaccess) (`Require all denied`), penonaktifan *directory listing* via [.htaccess](.htaccess), dan isolasi file save runtime di [.gitignore](.gitignore).

### 4.4 Pembersihan & Verifikasi Staging
- [x] **Bersihkan File Python & TMX dari `main`:** Menghapus `main.py`, `src/`, `tests/`, `tools/`, `.tmx/.tsx`, dan aset mentah yang sudah di-bake agar branch `main` murni siap hosting web.
- [x] **Verifikasi Teknis & Live Staging:** Validasi `php -l` seluruh skrip PHP, `node --check` seluruh modul JS, uji HTTP save/load pada server staging `php -S 127.0.0.1:8080`, dan uji visual interaktif di browser langsung.
