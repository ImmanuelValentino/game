"""
=============================================================================
Ashes of Oakhaven: The Hollow Crown
Main Game Entry Point - Pygame 2D Top-Down Action RPG
Terintegrasi penuh sesuai GDD Kelompok 1:
- Main Menu & Prolog Interaktif (Hujan Abu)
- Hub Oakhaven ("Rusty Anchor"): Vektor, Aell, Gael, Elara, Brog, & Penjaga
- 5 Stage/Bioma GDD + Hazard Lingkungan + 5 Jenderal/Bos (2-Fase Final Boss)
- Perfect Dodge Slow-Mo, Fatigue, Formula ATK/DEF, Weighted RNG Drop, & 2 Ending + QTE
=============================================================================
"""
import sys
import pygame

from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, STAGE_CONFIGS,
    KEY_INTERACT, KEY_INVENTORY, KEY_INVENTORY_ALT,
    KEY_POTION_HP, KEY_POTION_STAMINA, KEY_HELP, KEY_MUTE, KEY_MINIMAP,
)
from src.audio import audio_manager
from src.map_loader import MapLoader
from src.player import Player
from src.combat import CombatManager, FloatingText
from src.npc import (
    Campfire, ElaraNPC, BrogNPC, VektorNPC, AellNPC, GaelNPC,
    GatekeeperNPC, VillagerChildNPC, MapPortal,
    TrainingTarget, Enemy, BossEntity,
)
from src.inventory import Inventory
from src.shop import ShopManager
from src.quest import QuestManager, DialogueSystem, CartographyMapUI
from src.ui import UIManager
from src.save_system import SaveSystem
from src.scenes import TitleScreenScene, PrologScene, EndingScene

LOBBY_SPAWN = (584, 232)


def _scaled_enemy(name, x, y, base_hp, base_def, base_atk, base_spd, cfg, **kwargs):
    """Membuat musuh dengan skala Multiplier Kesulitan GDD (HP / DMG / SPD)."""
    return Enemy(
        name=name, x=x, y=y,
        max_hp=int(round(base_hp * cfg["hp_mult"])),
        defense=base_def,
        attack_damage=int(round(base_atk * cfg["dmg_mult"])),
        speed=base_spd * min(1.85, cfg["spd_mult"]),
        **kwargs,
    )


def create_map_entities(tmx_path):
    """Membangun daftar NPC, Portal, dan Monster/Bos sesuai peta aktif."""
    cfg = STAGE_CONFIGS.get(tmx_path, STAGE_CONFIGS["map1safeworld.tmx"])

    if tmx_path == "map1safeworld.tmx":
        npcs = [
            Campfire(x=544, y=256),
            ElaraNPC(x=440, y=250),
            BrogNPC(x=650, y=250),
            GaelNPC(x=584, y=364),
            GatekeeperNPC(x=864, y=120),
            VektorNPC(x=352, y=240),
            AellNPC(x=352, y=320),
            VillagerChildNPC("Leo (Anak Oakhaven)", x=640, y=320, variant="boy"),
            VillagerChildNPC("Aria (Penyintas)", x=704, y=320, variant="girl"),
            MapPortal(
                "Gerbang Ekspedisi (Stage 1: Rawa Kematian)",
                x=864, y=96, target_map="stage1_swamp.tmx", target_x=96, target_y=608,
                color=(90, 210, 120),
            ),
        ]
        targets = [
            TrainingTarget("Boneka Latihan A", 780, 360, max_hp=32, defense=1, is_monster=False, can_respawn=True),
            TrainingTarget("Boneka Latihan B", 840, 360, max_hp=32, defense=1, is_monster=False, can_respawn=True),
            TrainingTarget("Karak Rawa (Scout)", 788, 408, max_hp=40, defense=2, is_monster=True, can_respawn=True),
        ]
        return npcs, targets

    if tmx_path == "stage1_swamp.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=864, target_y=144, color=(120, 230, 140)),
            MapPortal("Menuju Stage 2: Hutan Spora", x=1216, y=608, target_map="stage2_spore.tmx", target_x=96, target_y=608, color=(190, 100, 240)),
        ]
        targets = [
            _scaled_enemy("Karak Rawa", 256, 580, 24, 3, 75, 76.0, cfg, sprite_kind="monster1", exp_reward=60),
            _scaled_enemy("Kultis Rawa (Ranged)", 320, 420, 20, 2, 70, 62.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=270.0, proj_color=(120, 185, 85), exp_reward=65),
            _scaled_enemy("Slime Lumpur", 576, 300, 22, 2, 65, 68.0, cfg, sprite_kind="slime", exp_reward=50),
            _scaled_enemy("Karak Penjaga Rawa", 600, 820, 30, 4, 80, 80.0, cfg, sprite_kind="monster1", exp_reward=70),
            _scaled_enemy("Kultis Penembak", 880, 700, 22, 2, 75, 64.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=280.0, proj_color=(120, 185, 85), exp_reward=70),
            BossEntity("gargantua", 1040, 580),
        ]
        return npcs, targets

    if tmx_path == "stage2_spore.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
        ]
        targets = [
            _scaled_enemy("Karak Spora", 260, 540, 28, 5, 82, 80.0, cfg, sprite_kind="monster1", exp_reward=95),
            _scaled_enemy("Penebar Spora (Ranged)", 320, 360, 24, 4, 75, 66.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=280.0, proj_color=(185, 95, 245), exp_reward=100),
            _scaled_enemy("Karak Pembusuk", 640, 640, 32, 6, 86, 84.0, cfg, sprite_kind="monster1", exp_reward=105),
            _scaled_enemy("Penyihir Spora (Ranged)", 780, 460, 26, 4, 80, 68.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=290.0, proj_color=(185, 95, 245), exp_reward=115),
            BossEntity("vespa", 1020, 580),
        ]
        return npcs, targets

    if tmx_path == "stage3_gehenna.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
        ]
        targets = [
            _scaled_enemy("Prajurit Tungku", 280, 560, 34, 8, 88, 84.0, cfg, sprite_kind="monster1", exp_reward=150),
            _scaled_enemy("Penembak Bara (Ranged)", 360, 460, 28, 6, 82, 70.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=300.0, proj_color=(255, 135, 45), exp_reward=160),
            _scaled_enemy("Algojo Gehenna", 640, 600, 38, 10, 92, 88.0, cfg, sprite_kind="monster1", exp_reward=175),
            _scaled_enemy("Penyihir Api (Ranged)", 840, 720, 30, 7, 85, 72.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=300.0, proj_color=(255, 135, 45), exp_reward=175),
            BossEntity("ignis", 1020, 580),
        ]
        return npcs, targets

    if tmx_path == "stage4_frost.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=608, y=1216, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
        ]
        targets = [
            _scaled_enemy("Ksatria Salju", 560, 880, 42, 12, 95, 90.0, cfg, sprite_kind="monster1", exp_reward=220),
            _scaled_enemy("Pemanah Es (Ranged)", 320, 720, 34, 9, 88, 74.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=320.0, proj_color=(150, 230, 255), exp_reward=230),
            _scaled_enemy("Penjaga Kristal", 740, 640, 46, 14, 98, 92.0, cfg, sprite_kind="monster1", exp_reward=245),
            _scaled_enemy("Penyihir Salju (Ranged)", 920, 480, 36, 10, 90, 76.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=320.0, proj_color=(150, 230, 255), exp_reward=245),
            BossEntity("valerius", 608, 220),
        ]
        return npcs, targets

    if tmx_path == "stage5_throne.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=608, y=1216, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
        ]
        targets = [
            BossEntity("ash_lord", 608, 280),
        ]
        return npcs, targets

    if tmx_path == "dungeon1.tmx":
        npcs = [
            MapPortal("Kembali ke Lobby Oakhaven", x=112, y=232, target_map="map1safeworld.tmx", target_x=864, target_y=144, color=(120, 230, 140)),
            MapPortal("Gerbang Takhta Dungeon 2", x=1096, y=128, target_map="dungeon2.tmx", target_x=1120, target_y=288, color=(220, 90, 255)),
        ]
        targets = [
            Enemy("Slime Beracun", 384, 96, max_hp=28, defense=3, attack_damage=75, speed=70.0, sprite_kind="slime", exp_reward=70),
            Enemy("Karak Pengintai", 384, 416, max_hp=34, defense=4, attack_damage=85, speed=78.0, sprite_kind="monster1", exp_reward=90),
            Enemy("Kultis Labirin (Ranged)", 960, 544, max_hp=28, defense=3, attack_damage=78, speed=68.0, sprite_kind="monster_ranged", is_ranged=True, exp_reward=95),
            Enemy("Slime Rawa Gelap", 320, 864, max_hp=30, defense=3, attack_damage=78, speed=72.0, sprite_kind="slime", exp_reward=75),
            BossEntity("gargantua", 1076, 192),
        ]
        return npcs, targets

    if tmx_path == "dungeon2.tmx":
        npcs = [
            MapPortal("Kembali ke Dungeon 1", x=1120, y=224, target_map="dungeon1.tmx", target_x=1096, target_y=168, color=(120, 230, 140)),
        ]
        targets = [
            Enemy("Karak Terkutuk", 320, 448, max_hp=42, defense=6, attack_damage=100, speed=84.0, sprite_kind="monster1", exp_reward=125),
            Enemy("Penjaga Ruang Abu (Ranged)", 768, 672, max_hp=34, defense=5, attack_damage=95, speed=74.0, sprite_kind="monster_ranged", is_ranged=True, exp_reward=135),
            Enemy("Slime Obsidian", 192, 864, max_hp=38, defense=5, attack_damage=92, speed=76.0, sprite_kind="slime", exp_reward=110),
            BossEntity("demon_king", 640, 160),
        ]
        return npcs, targets

    return [], []


def handle_npc_interaction(
    nearby_npc, player, inventory, shop_mgr, quest_mgr,
    dialogue_sys, combat_mgr, ui_mgr, targets, world_map_ui, switch_map_fn
):
    """Menangani interaksi tombol [E] terhadap Portal, Api Unggun, dan seluruh NPC Hub."""
    if isinstance(nearby_npc, MapPortal):
        if nearby_npc.target_map in ("stage2_spore.tmx", "dungeon2.tmx"):
            boss_alive = any(getattr(t, "is_boss", False) and t.is_alive() for t in targets)
            if boss_alive:
                ui_mgr.show_notification("Kalahkan bos area ini terlebih dahulu untuk membuka portal lanjut!", duration=3.0)
                audio_manager.play_sound("cancel")
                return
        audio_manager.play_sound("accept")
        switch_map_fn(nearby_npc.target_map, nearby_npc.target_x, nearby_npc.target_y)
        return

    name = nearby_npc.name
    if name == "Api Unggun Oakhaven":
        player.heal(player.max_hp)
        player.restore_stamina(player.max_stamina)
        audio_manager.play_sound("heal")
        SaveSystem.save_game(player, inventory, quest_mgr, current_map="map1safeworld.tmx")
        ui_mgr.show_notification("HP & Stamina pulih! Progress disimpan di Api Unggun.", duration=3.0)
        return

    if name.startswith("Vektor"):
        shop_mgr.open_vektor()
        return

    if name.startswith("Aell"):
        world_map_ui.open()
        return

    if name.startswith("Gael"):
        shop_mgr.open_gael()
        return

    if name.startswith("Brog"):
        shop_mgr.open_brog()
        return

    if name.startswith("Elara"):
        pages = [
            "Ethan... Syukurlah Aell berhasil membawamu keluar dari Rawa Kematian.",
            "Empat Jenderal menjaga empat Suar Kematian: Gargantua (Selatan), Vespa (Timur), Ignis (Barat), dan Valerius (Utara).",
            "Berbicaralah dengan Vektor untuk melatih skill & menempa Bilah Penebusan, atau buka peta dinamis milik Aell untuk berangkat!"
        ]

        def on_quest_talk():
            quest_mgr.advance_progress("q1_awaken", 1, player, combat_mgr)
            dialogue_sys.close()
            ui_mgr.show_notification("Quest selesai! Buka Peta Aell atau kunjungi Vektor/Gael.")

        def on_aid_villagers():
            if not getattr(player, "_helped_elara", False):
                player._helped_elara = True
                player.karma += 15
                ui_mgr.show_notification("Kau berjanji melindungi para penyintas Oakhaven (+Karma)!", duration=3.0)
            quest_mgr.advance_progress("q1_awaken", 1, player, combat_mgr)
            dialogue_sys.close()

        choices = [
            ("Terima Petunjuk Misi", on_quest_talk),
            ("Janji Lindungi Warga (+Karma)", on_aid_villagers),
        ]
        dialogue_sys.start_dialogue(nearby_npc.name, pages, nearby_npc.portrait, choices)
        return

    if name == "Kapten Penjaga Gerbang":
        pages = [
            "Gerbang Ekspedisi ini menuju Stage 1: Rawa Kematian tempat Jenderal Gargantua menunggu.",
            "Manfaatkan pohon mati/pilar untuk berlindung dari proyektil musuh, dan gunakan [Spasi] untuk Perfect Dodge Slow-Mo!",
            "Kau juga bisa menggunakan Peta Kartografi Aell untuk melompat cepat ke bioma yang sudah terbuka."
        ]

        def on_gate_talk():
            dialogue_sys.close()
            switch_map_fn("stage1_swamp.tmx", 96, 608)

        choices = [
            ("Masuk Stage 1: Rawa Kematian", on_gate_talk),
            ("Tutup", dialogue_sys.close),
        ]
        dialogue_sys.start_dialogue(nearby_npc.name, pages, nearby_npc.portrait, choices)
        return

    if name.startswith("Leo"):
        pages = [
            "Kak Ethan! Api Unggun di alun-alun itu selalu menghangatkan kami sejak desa terbakar.",
            "Kalau stamina kakak habis di bawah 10, serangan bakal tertahan (Fatigue)! Tekan [2] buat minum Tonik Stamina cepat."
        ]
        dialogue_sys.start_dialogue(nearby_npc.name, pages, nearby_npc.portrait)
        return

    if name.startswith("Aria"):
        pages = [
            "Desa Oakhaven hancur saat hujan abu turun... Tolong padamkan empat Suar Kematian agar kami bisa pulang.",
            "Vektor bilang jika kau memilih jalan Penebusan tanpa tergoda senjata terlarang Gael, fajar baru akan kembali."
        ]
        dialogue_sys.start_dialogue(nearby_npc.name, pages, nearby_npc.portrait)


def _process_kill_quests(current_map, killed_targets, player, quest_mgr, combat_mgr, ui_mgr):
    """Memperbarui progres quest & status Suar Kematian saat musuh/bos dikalahkan."""
    for target in killed_targets:
        if current_map == "map1safeworld.tmx":
            quest_mgr.advance_progress("q2_training", 1, player, combat_mgr)
        elif getattr(target, "is_boss", False):
            player.beacons_cleared.add(current_map)
            if current_map == "stage1_swamp.tmx":
                quest_mgr.advance_progress("q4_stage1", 1, player, combat_mgr)
                ui_mgr.show_notification("Suar Kematian 1 Padam! Stage 2: Hutan Spora kini terbuka di Peta Aell!", duration=4.5)
            elif current_map == "stage2_spore.tmx":
                quest_mgr.advance_progress("q5_stage2", 1, player, combat_mgr)
                ui_mgr.show_notification("Suar Kematian 2 Padam! Stage 3: Tungku Gehenna terbuka di Peta Aell!", duration=4.5)
            elif current_map == "stage3_gehenna.tmx":
                quest_mgr.advance_progress("q6_stage3", 1, player, combat_mgr)
                ui_mgr.show_notification("Suar Kematian 3 Padam! Stage 4: Benteng Salju Hitam terbuka!", duration=4.5)
            elif current_map == "stage4_frost.tmx":
                quest_mgr.advance_progress("q7_stage4", 1, player, combat_mgr)
                ui_mgr.show_notification("Suar Kematian 4 Padam! Gerbang Ruang Takhta Obsidian terbuka!", duration=4.5)
            elif current_map == "stage5_throne.tmx":
                quest_mgr.advance_progress("q8_stage5", 1, player, combat_mgr)
                return "trigger_ending"
            elif current_map == "dungeon1.tmx":
                ui_mgr.show_notification("Bos Dungeon 1 tumbang! Gerbang ke Dungeon 2 terbuka!", duration=4.0)
            elif current_map == "dungeon2.tmx":
                ui_mgr.show_notification("Raja Iblis Dungeon 2 berhasil dikalahkan!", duration=4.0)
    return None


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    print("[Main] Menginisialisasi sistem game...")

    # Mode scene: "title" | "prolog" | "playing" | "ending"
    mode = "title"
    title_scene = TitleScreenScene()
    prolog_scene = PrologScene()
    ending_scene = None

    current_map = "map1safeworld.tmx"
    map_loaders = {}
    map_entities = {}

    player = Player(x=LOBBY_SPAWN[0], y=LOBBY_SPAWN[1])
    combat_mgr = CombatManager()
    inventory = Inventory()
    shop_mgr = ShopManager()
    quest_mgr = QuestManager()
    dialogue_sys = DialogueSystem()
    world_map_ui = CartographyMapUI()
    ui_mgr = UIManager()

    all_npcs = []
    training_targets = []
    map_loader = None
    camera_x = 0.0
    camera_y = 0.0

    def start_gameplay(load_existing=False):
        nonlocal current_map, map_loader, all_npcs, training_targets, camera_x, camera_y, mode
        player.__init__(x=LOBBY_SPAWN[0], y=LOBBY_SPAWN[1])
        inventory.__init__()
        quest_mgr.__init__()
        combat_mgr.clear_world_effects()
        map_entities.clear()
        current_map = "map1safeworld.tmx"

        if load_existing and SaveSystem.load_game(player, inventory, quest_mgr):
            saved_map = getattr(player, "saved_map", "map1safeworld.tmx")
            if saved_map in STAGE_CONFIGS:
                current_map = saved_map

        if current_map not in map_loaders:
            map_loaders[current_map] = MapLoader(current_map)
        map_loader = map_loaders[current_map]

        if map_loader.is_blocked(player.get_hitbox()):
            current_map = "map1safeworld.tmx"
            if current_map not in map_loaders:
                map_loaders[current_map] = MapLoader(current_map)
            map_loader = map_loaders[current_map]
            player.x, player.y = float(LOBBY_SPAWN[0]), float(LOBBY_SPAWN[1])

        all_npcs, training_targets = create_map_entities(current_map)
        map_entities[current_map] = (all_npcs, training_targets)

        camera_x = max(0.0, min(float(max(0, map_loader.map_width_px - SCREEN_WIDTH)), player.x + 24 - SCREEN_WIDTH / 2))
        camera_y = max(0.0, min(float(max(0, map_loader.map_height_px - SCREEN_HEIGHT)), player.y + 24 - SCREEN_HEIGHT / 2))

        mode = "playing"
        bgm = STAGE_CONFIGS.get(current_map, {}).get("bgm", "bgm_lobby")
        audio_manager.play_music(bgm)
        ui_mgr.show_notification("Selamat datang di Hub Rusty Anchor! Tekan [H] untuk panduan.", duration=4.0)

    def switch_map(new_tmx, spawn_x, spawn_y, reset_stages=False):
        nonlocal current_map, map_loader, all_npcs, training_targets, camera_x, camera_y
        if reset_stages:
            for k in list(map_entities.keys()):
                if k != "map1safeworld.tmx":
                    map_entities.pop(k, None)

        map_entities[current_map] = (all_npcs, training_targets)
        current_map = new_tmx
        if new_tmx not in map_loaders:
            map_loaders[new_tmx] = MapLoader(new_tmx)
        map_loader = map_loaders[new_tmx]

        if new_tmx not in map_entities or reset_stages:
            map_entities[new_tmx] = create_map_entities(new_tmx)
        all_npcs, training_targets = map_entities[new_tmx]

        player.x = float(spawn_x)
        player.y = float(spawn_y)
        player.vel_x = 0.0
        player.vel_y = 0.0
        player.knockback_vx = 0.0
        player.knockback_vy = 0.0
        combat_mgr.clear_world_effects()

        max_cx = max(0, map_loader.map_width_px - SCREEN_WIDTH)
        max_cy = max(0, map_loader.map_height_px - SCREEN_HEIGHT)
        camera_x = max(0.0, min(float(max_cx), player.x + 24 - SCREEN_WIDTH / 2))
        camera_y = max(0.0, min(float(max_cy), player.y + 24 - SCREEN_HEIGHT / 2))

        cfg = STAGE_CONFIGS.get(new_tmx, {})
        ui_mgr.show_notification(f"Memasuki {cfg.get('name', new_tmx)}", duration=3.0)
        audio_manager.play_music(cfg.get("bgm", "bgm_dungeon"))

    def respawn_to_lobby():
        if current_map != "map1safeworld.tmx":
            switch_map("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1], reset_stages=True)
        lost_ash = player.respawn(LOBBY_SPAWN[0], LOBBY_SPAWN[1], inventory=inventory)
        ui_mgr.show_notification(f"Bangkit di Api Unggun! (-{lost_ash} Ash, -50% Material)", duration=3.5)

    audio_manager.play_music("bgm_lobby")

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        mouse_pos = pygame.mouse.get_pos()

        # -------------------------------------------------------------
        # SCENE: TITLE SCREEN
        # -------------------------------------------------------------
        if mode == "title":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                act = title_scene.handle_event(event)
                if act == "new_game":
                    prolog_scene = PrologScene()
                    mode = "prolog"
                elif act == "continue":
                    start_gameplay(load_existing=True)
                elif act == "exit":
                    running = False
                    break
            title_scene.update(dt)
            title_scene.draw(screen, mouse_pos)
            pygame.display.flip()
            continue

        # -------------------------------------------------------------
        # SCENE: PROLOG INTERAKTIF
        # -------------------------------------------------------------
        if mode == "prolog":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if prolog_scene.handle_event(event) == "done":
                    start_gameplay(load_existing=False)
                    break
            if mode == "prolog":
                prolog_scene.update(dt)
                prolog_scene.draw(screen)
                pygame.display.flip()
            continue

        # -------------------------------------------------------------
        # SCENE: ENDING & QTE KLIMAKS
        # -------------------------------------------------------------
        if mode == "ending":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    SaveSystem.save_game(player, inventory, quest_mgr, current_map="map1safeworld.tmx")
                    running = False
                    break
                res = ending_scene.handle_event(event)
                if res == "hub":
                    mode = "playing"
                    switch_map("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1], reset_stages=True)
                elif res == "menu":
                    SaveSystem.save_game(player, inventory, quest_mgr, current_map="map1safeworld.tmx")
                    mode = "title"
                    audio_manager.play_music("bgm_lobby")
            if mode == "ending":
                ending_scene.update(dt)
                ending_scene.draw(screen, mouse_pos)
                pygame.display.flip()
            continue

        # -------------------------------------------------------------
        # SCENE: GAMEPLAY UTAMA
        # -------------------------------------------------------------
        keys = pygame.key.get_pressed()
        nearby_npc = next((npc for npc in all_npcs if npc.is_player_near(player)), None)
        stage_cfg = STAGE_CONFIGS.get(current_map, STAGE_CONFIGS["map1safeworld.tmx"])
        tier_mult = stage_cfg.get("tier_mult", 1.0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                SaveSystem.save_game(player, inventory, quest_mgr, current_map=current_map)
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                if event.key == KEY_HELP:
                    ui_mgr.show_help = not ui_mgr.show_help
                    audio_manager.play_sound("accept")
                    continue

                if event.key == KEY_MUTE:
                    is_muted = audio_manager.toggle_mute()
                    ui_mgr.show_notification("Audio DINONAKTIFKAN" if is_muted else "Audio DIAKTIFKAN", duration=1.5)
                    continue

                if event.key == KEY_MINIMAP and not player.is_dead:
                    ui_mgr.show_minimap = not ui_mgr.show_minimap
                    audio_manager.play_sound("accept")
                    continue

                if event.key == pygame.K_ESCAPE:
                    if ui_mgr.show_help:
                        ui_mgr.show_help = False
                    elif world_map_ui.is_open:
                        world_map_ui.close()
                    elif dialogue_sys.is_active:
                        dialogue_sys.close()
                    elif inventory.is_open:
                        inventory.toggle()
                    elif shop_mgr.is_active():
                        shop_mgr.close_all()
                    continue

                if player.is_dead:
                    if event.key == pygame.K_r:
                        respawn_to_lobby()
                    continue

                if ui_mgr.show_help:
                    continue

                if world_map_ui.is_open:
                    if event.key == KEY_INTERACT:
                        world_map_ui.close()
                    continue

                if dialogue_sys.is_active:
                    dialogue_sys.handle_key(event.key)
                    continue

                if shop_mgr.is_active():
                    if event.key == KEY_INTERACT:
                        shop_mgr.close_all()
                    continue

                if event.key in (KEY_INVENTORY, KEY_INVENTORY_ALT):
                    inventory.toggle()
                    continue

                if inventory.is_open:
                    continue

                if event.key == KEY_POTION_HP:
                    status = inventory.use_item_by_id("hp_potion", player, combat_mgr)
                    if status == "full":
                        ui_mgr.show_notification("HP sudah penuh!")
                    elif status == "missing":
                        ui_mgr.show_notification("Tidak ada Ramuan HP di Tas!")
                    continue

                if event.key == KEY_POTION_STAMINA:
                    status = inventory.use_item_by_id("stamina_tonic", player, combat_mgr)
                    if status == "full":
                        ui_mgr.show_notification("Stamina sudah penuh!")
                    elif status == "missing":
                        ui_mgr.show_notification("Tidak ada Tonik Stamina di Tas!")
                    continue

                if event.key == KEY_INTERACT and nearby_npc:
                    handle_npc_interaction(
                        nearby_npc, player, inventory, shop_mgr, quest_mgr,
                        dialogue_sys, combat_mgr, ui_mgr, training_targets, world_map_ui, switch_map
                    )

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ui_mgr.show_help:
                    ui_mgr.show_help = False
                    continue

                if player.is_dead:
                    if event.button == 1 and ui_mgr.get_respawn_button_rect().collidepoint(mouse_pos):
                        respawn_to_lobby()
                    continue

                if world_map_ui.is_open:
                    world_map_ui.handle_click(mouse_pos, player, switch_map, ui_mgr)
                    continue

                if dialogue_sys.is_active:
                    dialogue_sys.handle_click(mouse_pos)
                    continue

                if shop_mgr.is_active():
                    shop_mgr.handle_click(mouse_pos, player, inventory, combat_mgr, quest_mgr)
                    continue

                if inventory.is_open:
                    inventory.handle_click(mouse_pos, player, combat_mgr)
                    continue

                if event.button == 1:
                    alive_before = [t for t in training_targets if t.is_alive()]
                    if combat_mgr.perform_attack(player, mouse_pos, camera_x, camera_y, training_targets, inventory=inventory, tier_mult=tier_mult):
                        killed = [t for t in alive_before if not t.is_alive()]
                        if _process_kill_quests(current_map, killed, player, quest_mgr, combat_mgr, ui_mgr) == "trigger_ending":
                            ending_scene = EndingScene(player)
                            mode = "ending"
                            break

                elif event.button == 3:
                    alive_before = [t for t in training_targets if t.is_alive()]
                    if combat_mgr.perform_skill(player, mouse_pos, camera_x, camera_y, training_targets, inventory=inventory, tier_mult=tier_mult):
                        killed = [t for t in alive_before if not t.is_alive()]
                        if _process_kill_quests(current_map, killed, player, quest_mgr, combat_mgr, ui_mgr) == "trigger_ending":
                            ending_scene = EndingScene(player)
                            mode = "ending"
                            break

        if mode != "playing":
            continue

        # Update Gameplay dengan Slow-Mo Perfect Dodge (0.45x pada musuh/proyektil selama 1.5s)
        ui_blocked = (
            dialogue_sys.is_active or shop_mgr.is_active()
            or inventory.is_open or ui_mgr.show_help or world_map_ui.is_open
        )
        move_dir = None
        if not ui_blocked and not player.is_dead:
            move_dir = player.handle_input(keys, dt)

        player.update(dt, map_loader, move_dir, combat_mgr=combat_mgr)
        world_dt = dt * (0.45 if player.perfect_dodge_slowmo_timer > 0 else 1.0)
        combat_mgr.update(world_dt, player=player, map_loader=map_loader)
        ui_mgr.update(dt)
        dialogue_sys.update(dt)

        for npc in all_npcs:
            npc.update(dt)

        if not ui_blocked:
            for target in training_targets:
                target.update(world_dt, player=player, map_loader=map_loader, combat_mgr=combat_mgr)

        target_cam_x = player.x + 24 - SCREEN_WIDTH / 2
        target_cam_y = player.y + 24 - SCREEN_HEIGHT / 2
        camera_x += (target_cam_x - camera_x) * 0.1
        camera_y += (target_cam_y - camera_y) * 0.1

        max_cam_x = max(0, map_loader.map_width_px - SCREEN_WIDTH)
        max_cam_y = max(0, map_loader.map_height_px - SCREEN_HEIGHT)
        camera_x = max(0.0, min(float(max_cam_x), camera_x))
        camera_y = max(0.0, min(float(max_cam_y), camera_y))

        shake_ox, shake_oy = combat_mgr.get_shake_offset()
        render_cam_x = camera_x + shake_ox
        render_cam_y = camera_y + shake_oy

        # Render Pipeline
        screen.fill((0, 0, 0))
        map_loader.draw(screen, render_cam_x, render_cam_y)

        render_entities = [(player.y + 40, player)]
        for npc in all_npcs:
            render_entities.append((npc.y + npc.height, npc))
        for target in training_targets:
            if target.is_alive():
                render_entities.append((target.y + target.height, target))

        render_entities.sort(key=lambda item: item[0])
        for _, entity in render_entities:
            entity.draw(screen, render_cam_x, render_cam_y)

        combat_mgr.draw(screen, render_cam_x, render_cam_y)

        ui_mgr.draw_hud(
            screen, player, combat_mgr, inventory, quest_mgr,
            nearby_npc=nearby_npc, current_map=current_map,
            targets=training_targets, map_loader=map_loader, npcs=all_npcs
        )

        if inventory.is_open:
            inventory.draw(screen, mouse_pos, player)
        if shop_mgr.is_active():
            shop_mgr.draw(screen, mouse_pos, player, inventory=inventory)
        if world_map_ui.is_open:
            world_map_ui.draw(screen, mouse_pos, player)
        if dialogue_sys.is_active:
            dialogue_sys.draw(screen, mouse_pos)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
