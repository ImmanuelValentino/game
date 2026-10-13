"""
=============================================================================
Ashes of Oakhaven: The Hollow Crown
Main Game Entry Point - Pygame 2D Top-Down Action RPG
Disusun sesuai GDD (Game Design Document) & map1safeworld.tmx
=============================================================================
"""
import sys
import pygame

from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    KEY_INTERACT, KEY_INVENTORY, KEY_INVENTORY_ALT,
    KEY_POTION_HP, KEY_POTION_STAMINA, KEY_HELP, KEY_MUTE,
    MAP_WIDTH_PX, MAP_HEIGHT_PX, COLOR_GOLD
)
from src.audio import audio_manager
from src.map_loader import MapLoader
from src.player import Player
from src.combat import CombatManager, FloatingText
from src.npc import Campfire, ElaraNPC, BrogNPC, MerchantNPC, GatekeeperNPC, TrainingTarget
from src.inventory import Inventory
from src.shop import ShopManager
from src.quest import QuestManager, DialogueSystem
from src.ui import UIManager
from src.save_system import SaveSystem

def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    print("[Main] Menginisialisasi sistem game...")

    # Inisialisasi Sistem Inti
    map_loader = MapLoader("map1safeworld.tmx")
    # Spawn player di jalan utama yang bebas hambatan (X=544, Y=210)
    player = Player(x=544, y=210)
    combat_mgr = CombatManager()
    inventory = Inventory()
    shop_mgr = ShopManager()
    quest_mgr = QuestManager()
    dialogue_sys = DialogueSystem()
    ui_mgr = UIManager()

    # Inisialisasi NPC & Objek Interaktif di Lobby
    campfire = Campfire(x=544, y=256)
    elara = ElaraNPC(x=440, y=250)
    brog = BrogNPC(x=650, y=250)
    merchant = MerchantNPC(x=480, y=440)
    gatekeeper = GatekeeperNPC(x=864, y=120)

    # Objek Latihan Tempur di Halaman Timur
    training_targets = [
        TrainingTarget("Boneka Latihan A", 780, 360, max_hp=100, is_monster=False),
        TrainingTarget("Boneka Latihan B", 840, 360, max_hp=100, is_monster=False),
        TrainingTarget("Karak Rawa (Scout)", 810, 420, max_hp=140, is_monster=True),
    ]

    all_npcs = [campfire, elara, brog, merchant, gatekeeper]

    # Coba memuat save file yang ada
    SaveSystem.load_game(player, inventory, quest_mgr)

    # Putar musik latar Lobby Safe Zone
    audio_manager.play_music("bgm_lobby")

    # Inisialisasi Posisi Kamera
    camera_x = float(player.x - SCREEN_WIDTH / 2)
    camera_y = float(player.y - SCREEN_HEIGHT / 2)

    ui_mgr.show_notification("Selamat datang di Oakhaven! Tekan [H] untuk panduan kontrol.", duration=4.0)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05) # Batas delta time agar tidak tunneling saat lag

        mouse_pos = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        # Deteksi NPC terdekat untuk interaksi [E]
        nearby_npc = None
        for npc in all_npcs:
            if npc.is_player_near(player):
                nearby_npc = npc
                break

        # -------------------------------------------------------------
        # EVENT HANDLING
        # -------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                SaveSystem.save_game(player, inventory, quest_mgr)
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                # Toggle Help Overlay
                if event.key == KEY_HELP:
                    ui_mgr.show_help = not ui_mgr.show_help
                    audio_manager.play_sound("accept")
                    continue

                # Toggle Audio Mute
                if event.key == KEY_MUTE:
                    is_muted = audio_manager.toggle_mute()
                    status = "Audio DINONAKTIFKAN" if is_muted else "Audio DIAKTIFKAN"
                    ui_mgr.show_notification(status, duration=1.5)
                    continue

                # ESC menutup menu apa pun yang terbuka
                if event.key == pygame.K_ESCAPE:
                    if ui_mgr.show_help:
                        ui_mgr.show_help = False
                    elif dialogue_sys.is_active:
                        dialogue_sys.close()
                    elif inventory.is_open:
                        inventory.toggle()
                    elif shop_mgr.is_active():
                        shop_mgr.close_all()
                    continue

                # Respawn saat mati dengan tombol R
                if player.is_dead and event.key == pygame.K_r:
                    lost_ash = player.respawn(544, 210)
                    ui_mgr.show_notification(f"Bangkit di Api Unggun! (-{lost_ash} Monster Ash)", duration=3.0)
                    continue

                # Jika ada dialog atau shop terbuka, tombol kontrol game dinonaktifkan
                if dialogue_sys.is_active or shop_mgr.is_active() or ui_mgr.show_help:
                    continue

                # Toggle Inventory (B / I)
                if event.key in (KEY_INVENTORY, KEY_INVENTORY_ALT):
                    inventory.toggle()
                    continue

                # Quick Potion 1 (HP)
                if event.key == KEY_POTION_HP:
                    if inventory.get_count("hp_potion") > 0:
                        if player.hp < player.max_hp:
                            healed = player.heal(50)
                            inventory.remove_item("hp_potion", 1)
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 20, f"+{healed} HP", (100, 255, 120), is_crit=True)
                            )
                        else:
                            ui_mgr.show_notification("HP sudah penuh!")
                    else:
                        ui_mgr.show_notification("Tidak ada Ramuan HP di Tas!")
                    continue

                # Quick Potion 2 (Stamina)
                if event.key == KEY_POTION_STAMINA:
                    if inventory.get_count("stamina_tonic") > 0:
                        if player.stamina < player.max_stamina:
                            player.restore_stamina(50)
                            audio_manager.play_sound("heal")
                            inventory.remove_item("stamina_tonic", 1)
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 20, "+50 Stamina", (120, 220, 255))
                            )
                        else:
                            ui_mgr.show_notification("Stamina sudah penuh!")
                    else:
                        ui_mgr.show_notification("Tidak ada Tonik Stamina di Tas!")
                    continue

                # Interaksi Tombol [E]
                if event.key == KEY_INTERACT:
                    if nearby_npc:
                        if nearby_npc == campfire:
                            # Istirahat di Api Unggun
                            player.heal(player.max_hp)
                            player.restore_stamina(player.max_stamina)
                            audio_manager.play_sound("heal")
                            SaveSystem.save_game(player, inventory, quest_mgr)
                            ui_mgr.show_notification("HP & Stamina pulih! Progress disimpan di Api Unggun.", duration=3.0)

                        elif nearby_npc == elara:
                            # Dialog Elara
                            pages = [
                                "Penyintas... Akhirnya kau sadar. Desa Oakhaven telah luluh lantak oleh Sang Penguasa Abu.",
                                "Empat Suar Kematian menyegel tanah ini. Jenderal Gargantua kini berkuasa di Rawa Kematian di utara.",
                                "Kuatkan dirimu, latihlah tebasan pedangmu, dan persiapkan bekal sebelum melangkah ke gerbang ekspedisi!"
                            ]
                            def on_quest_talk():
                                quest_mgr.advance_progress("q1_awaken", 1, player, combat_mgr)
                                dialogue_sys.close()
                                ui_mgr.show_notification("Quest diperbarui: Bangkit dari Abu selesai!")

                            choices = [
                                ("Terima Petunjuk Quest", on_quest_talk),
                                ("Tutup Percakapan", dialogue_sys.close)
                            ]
                            dialogue_sys.start_dialogue(elara.name, pages, elara.portrait, choices)

                        elif nearby_npc == brog:
                            # Menu Brog
                            shop_mgr.open_brog()

                        elif nearby_npc == merchant:
                            # Toko Pedagang Misterius
                            shop_mgr.open_merchant()

                        elif nearby_npc == gatekeeper:
                            # Dialog Penjaga Gerbang
                            pages = [
                                "Hentikan langkahmu, pengembara! Gerbang Utara mengarah langsung ke Bab 1: Rawa Kematian.",
                                "Tanah di sana beracun dan dipenuhi monster Karak berduri yang dipimpin raksasa Gargantua.",
                                "Pastikan kau telah meningkatkan senjatamu dan membawa banyak ramuan pemulih sebelum melangkah keluar!"
                            ]
                            def on_gate_talk():
                                quest_mgr.advance_progress("q4_gate", 1, player, combat_mgr)
                                dialogue_sys.close()
                                ui_mgr.show_notification("Quest Selesai: Lapor ke Penjaga Gerbang!")

                            choices = [
                                ("Siap untuk Ekspedisi", on_gate_talk),
                                ("Kembali ke Lobby", dialogue_sys.close)
                            ]
                            dialogue_sys.start_dialogue(gatekeeper.name, pages, gatekeeper.portrait, choices)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 1. Jika Help Overlay aktif, klik mana saja menutup
                if ui_mgr.show_help:
                    ui_mgr.show_help = False
                    continue

                # 2. Jika Dialog aktif, klik dialog
                if dialogue_sys.is_active:
                    dialogue_sys.handle_click(mouse_pos)
                    continue

                # 3. Jika Toko aktif, klik toko
                if shop_mgr.is_active():
                    shop_mgr.handle_click(mouse_pos, player, inventory, combat_mgr)
                    continue

                # 4. Jika Tas/Inventory aktif, klik tas
                if inventory.is_open:
                    inventory.handle_click(mouse_pos, player, combat_mgr)
                    continue

                # 5. Serangan Normal (Klik Kiri)
                if event.button == 1:
                    alive_targets_before = [t for t in training_targets if t.is_alive()]
                    hit = combat_mgr.perform_attack(player, mouse_pos, camera_x, camera_y, training_targets)
                    if hit:
                        # Cek apakah ada target yang baru saja kalah untuk progres quest
                        for t in alive_targets_before:
                            if not t.is_alive():
                                quest_mgr.advance_progress("q2_training", 1, player, combat_mgr)

                # 6. Skill Khusus Area (Klik Kanan)
                elif event.button == 3:
                    alive_targets_before = [t for t in training_targets if t.is_alive()]
                    hit = combat_mgr.perform_skill(player, mouse_pos, camera_x, camera_y, training_targets)
                    if hit:
                        for t in alive_targets_before:
                            if not t.is_alive():
                                quest_mgr.advance_progress("q2_training", 1, player, combat_mgr)

        # -------------------------------------------------------------
        # GAME UPDATE
        # -------------------------------------------------------------
        move_dir = None
        if not dialogue_sys.is_active and not shop_mgr.is_active() and not inventory.is_open and not ui_mgr.show_help:
            move_dir = player.handle_input(keys, dt)

        player.update(dt, map_loader, move_dir)
        combat_mgr.update(dt)
        ui_mgr.update(dt)
        dialogue_sys.update(dt)

        for npc in all_npcs:
            npc.update(dt)

        for target in training_targets:
            target.update(dt)

        # Update Smooth Camera Mengikuti Pemain
        target_cam_x = player.x + 24 - SCREEN_WIDTH / 2
        target_cam_y = player.y + 24 - SCREEN_HEIGHT / 2

        camera_x += (target_cam_x - camera_x) * 0.1
        camera_y += (target_cam_y - camera_y) * 0.1

        # Batasi kamera di dalam batas peta 1280x1280 px
        max_cam_x = max(0, MAP_WIDTH_PX - SCREEN_WIDTH)
        max_cam_y = max(0, MAP_HEIGHT_PX - SCREEN_HEIGHT)
        camera_x = max(0.0, min(float(max_cam_x), camera_x))
        camera_y = max(0.0, min(float(max_cam_y), camera_y))

        # Tambahkan screen shake dari skill / critical hit
        shake_ox, shake_oy = combat_mgr.get_shake_offset()
        render_cam_x = camera_x + shake_ox
        render_cam_y = camera_y + shake_oy

        # -------------------------------------------------------------
        # RENDER PIPELINE
        # -------------------------------------------------------------
        # 1. Gambar Base Map (Ground, Jalan, Tebing, Jembatan, Kastil)
        map_loader.draw(screen, render_cam_x, render_cam_y)

        # 2. Depth Sorting (Y-Sorting) untuk Entity & NPC
        render_entities = []
        render_entities.append((player.y + 40, player))
        for npc in all_npcs:
            render_entities.append((npc.y + npc.height, npc))
        for target in training_targets:
            if target.is_alive():
                render_entities.append((target.y + target.height, target))

        render_entities.sort(key=lambda item: item[0])

        for _, entity in render_entities:
            entity.draw(screen, render_cam_x, render_cam_y)

        # 3. Gambar Efek Tebasan & Floating Damage
        combat_mgr.draw(screen, render_cam_x, render_cam_y)

        # 4. Gambar HUD & UI
        ui_mgr.draw_hud(screen, player, combat_mgr, inventory, quest_mgr, nearby_npc)

        # 5. Gambar Modal UI (Tas, Toko, Dialog)
        if inventory.is_open:
            inventory.draw(screen, mouse_pos, player)

        if shop_mgr.is_active():
            shop_mgr.draw(screen, mouse_pos, player)

        if dialogue_sys.is_active:
            dialogue_sys.draw(screen, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
