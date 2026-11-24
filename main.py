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
    DEFAULT_WIDTH, DEFAULT_HEIGHT, COLOR_BG, FPS, TITLE, STAGE_CONFIGS,
    KEY_INTERACT, KEY_INVENTORY, KEY_INVENTORY_ALT,
    KEY_POTION_HP, KEY_POTION_STAMINA, KEY_ITEM_3, KEY_ITEM_4,
    KEY_HELP, KEY_MUTE, KEY_MINIMAP,
    compute_logical_size, set_screen_size, get_screen_size, window_to_logical,
)
from src.audio import audio_manager
from src.map_loader import MapLoader
from src.player import Player
from src.combat import CombatManager, FloatingText
from src.npc import (
    Campfire, WhiteFlame, ElaraNPC, BrogNPC, VektorNPC, AellNPC, GaelNPC,
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
            ElaraNPC(x=320, y=192),
            VektorNPC(x=128, y=224),
            BrogNPC(x=192, y=544),
            GaelNPC(x=224, y=704),
            AellNPC(x=928, y=288),
            GatekeeperNPC(x=864, y=120),
            VillagerChildNPC("Leo (Anak Oakhaven)", x=160, y=736, variant="boy"),
            VillagerChildNPC("Aria (Penyintas)", x=800, y=672, variant="girl"),
            MapPortal(
                "Gerbang Ekspedisi (Dungeon 1: Rawa Kematian)",
                x=864, y=96, target_map="stage1_swamp.tmx", target_x=96, target_y=608,
                color=(90, 210, 120),
            ),
        ]
        targets = [
            TrainingTarget("Boneka Latihan A", 480, 832, max_hp=32, defense=1, is_monster=False, can_respawn=True),
            TrainingTarget("Boneka Latihan B", 544, 832, max_hp=32, defense=1, is_monster=False, can_respawn=True),
            TrainingTarget("Karak Rawa (Scout)", 544, 768, max_hp=40, defense=2, is_monster=True, can_respawn=True),
        ]
        return npcs, targets

    if tmx_path == "stage1_swamp.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=864, target_y=144, color=(120, 230, 140)),
            MapPortal("Menuju Dungeon 2: Hutan Spora", x=1216, y=608, target_map="stage2_spore.tmx", target_x=96, target_y=608, color=(190, 100, 240)),
            WhiteFlame(128, 128), WhiteFlame(1120, 128), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            _scaled_enemy("Karak Rawa", 256, 580, 26, 3, 75, 76.0, cfg, sprite_kind="monster1", exp_reward=60),
            _scaled_enemy("Kultis Rawa (Ranged)", 320, 420, 22, 2, 70, 62.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=270.0, proj_color=(120, 185, 85), exp_reward=65),
            _scaled_enemy("Slime Lumpur", 576, 300, 24, 2, 65, 68.0, cfg, sprite_kind="slime", exp_reward=50),
            _scaled_enemy("Karak Penjaga Rawa", 600, 820, 32, 4, 82, 80.0, cfg, sprite_kind="monster1", exp_reward=70),
            _scaled_enemy("Kultis Penembak", 880, 700, 24, 2, 75, 64.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=280.0, proj_color=(120, 185, 85), exp_reward=70),
            BossEntity("gargantua", 1040, 580),
        ]
        return npcs, targets

    if tmx_path == "stage2_spore.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
            WhiteFlame(128, 128), WhiteFlame(1120, 128), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            _scaled_enemy("Karak Spora", 260, 540, 32, 6, 86, 80.0, cfg, sprite_kind="monster1", exp_reward=105),
            _scaled_enemy("Penebar Spora (Ranged)", 320, 360, 28, 5, 78, 66.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=280.0, proj_color=(185, 95, 245), exp_reward=110),
            _scaled_enemy("Karak Pembusuk", 640, 640, 38, 7, 90, 84.0, cfg, sprite_kind="monster1", exp_reward=115),
            _scaled_enemy("Penyihir Spora (Ranged)", 780, 460, 30, 5, 84, 68.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=290.0, proj_color=(185, 95, 245), exp_reward=125),
            BossEntity("vespa", 1020, 580),
        ]
        return npcs, targets

    if tmx_path == "stage3_gehenna.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=32, y=608, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
            WhiteFlame(128, 128), WhiteFlame(1120, 128), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            _scaled_enemy("Prajurit Tungku", 280, 560, 42, 10, 96, 84.0, cfg, sprite_kind="monster1", exp_reward=170),
            _scaled_enemy("Penembak Bara (Ranged)", 360, 460, 34, 8, 90, 70.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=300.0, proj_color=(255, 135, 45), exp_reward=180),
            _scaled_enemy("Algojo Gehenna", 640, 600, 48, 12, 102, 88.0, cfg, sprite_kind="monster1", exp_reward=195),
            _scaled_enemy("Penyihir Api (Ranged)", 840, 720, 36, 9, 92, 72.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=300.0, proj_color=(255, 135, 45), exp_reward=195),
            BossEntity("ignis", 1020, 580),
        ]
        return npcs, targets

    if tmx_path == "stage4_frost.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=608, y=1216, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
            WhiteFlame(128, 128), WhiteFlame(1120, 128), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            _scaled_enemy("Ksatria Salju", 560, 880, 54, 15, 108, 90.0, cfg, sprite_kind="monster1", exp_reward=255),
            _scaled_enemy("Pemanah Es (Ranged)", 320, 720, 44, 12, 98, 74.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=320.0, proj_color=(150, 230, 255), exp_reward=265),
            _scaled_enemy("Penjaga Kristal", 740, 640, 60, 18, 114, 92.0, cfg, sprite_kind="monster1", exp_reward=285),
            _scaled_enemy("Penyihir Salju (Ranged)", 920, 480, 48, 13, 102, 76.0, cfg, sprite_kind="monster_ranged", is_ranged=True, aggro_range=320.0, proj_color=(150, 230, 255), exp_reward=285),
            BossEntity("valerius", 608, 220),
        ]
        return npcs, targets

    if tmx_path == "stage5_throne.tmx":
        npcs = [
            MapPortal("Kembali ke Hub Rusty Anchor", x=608, y=1216, target_map="map1safeworld.tmx", target_x=584, target_y=232, color=(120, 230, 140)),
            WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            BossEntity("ash_lord", 608, 280),
        ]
        return npcs, targets

    if tmx_path == "dungeon1.tmx":
        npcs = [
            MapPortal("Kembali ke Lobby Oakhaven", x=112, y=232, target_map="map1safeworld.tmx", target_x=864, target_y=144, color=(120, 230, 140)),
            MapPortal("Gerbang Takhta Dungeon 2", x=1096, y=128, target_map="dungeon2.tmx", target_x=1120, target_y=288, color=(220, 90, 255)),
            WhiteFlame(128, 128), WhiteFlame(1120, 128), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            Enemy("Slime Beracun", 384, 96, max_hp=30, defense=3, attack_damage=78, speed=70.0, sprite_kind="slime", exp_reward=75),
            Enemy("Karak Pengintai", 384, 416, max_hp=38, defense=4, attack_damage=88, speed=78.0, sprite_kind="monster1", exp_reward=95),
            Enemy("Kultis Labirin (Ranged)", 960, 544, max_hp=30, defense=3, attack_damage=82, speed=68.0, sprite_kind="monster_ranged", is_ranged=True, exp_reward=100),
            Enemy("Slime Rawa Gelap", 320, 864, max_hp=32, defense=3, attack_damage=82, speed=72.0, sprite_kind="slime", exp_reward=80),
            BossEntity("gargantua", 1076, 192),
        ]
        return npcs, targets

    if tmx_path == "dungeon2.tmx":
        npcs = [
            MapPortal("Kembali ke Dungeon 1", x=1120, y=224, target_map="dungeon1.tmx", target_x=1096, target_y=168, color=(120, 230, 140)),
            WhiteFlame(96, 96), WhiteFlame(1152, 96), WhiteFlame(128, 1120), WhiteFlame(1120, 1120),
        ]
        targets = [
            Enemy("Karak Terkutuk", 320, 448, max_hp=68, defense=9, attack_damage=135, speed=86.0, sprite_kind="monster1", exp_reward=145),
            Enemy("Penjaga Ruang Abu (Ranged)", 768, 672, max_hp=54, defense=7, attack_damage=125, speed=76.0, sprite_kind="monster_ranged", is_ranged=True, exp_reward=155),
            Enemy("Slime Obsidian", 192, 864, max_hp=60, defense=8, attack_damage=122, speed=78.0, sprite_kind="slime", exp_reward=130),
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

    if isinstance(nearby_npc, WhiteFlame):
        ui_mgr.show_notification("Api Putih: Tetap di dekat aura cahaya ini untuk memulihkan HP secara bertahap.", duration=3.0)
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
            "Para penyintas tersebar di seluruh kota: Vektor di barat laut (Bengkel Skill), Brog di kedai barat, Gael di pelabuhan barat daya (Toko Boost), dan Aell di pos timur!",
            "Perhatikan Minimap [TAB] di pojok kanan atas untuk melihat ikon mereka. Di dalam Dungeon 1-4, HP tidak pulih otomatis—cari Api Putih di sudut map atau bawa Ramuan dari Gael!"
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


def compute_clamped_camera(target_cx, target_cy, map_w, map_h, view_w, view_h):
    """Membatasi kamera ke batas map, atau memusatkan map jika layar lebih besar."""
    if map_w <= view_w:
        cam_x = -(view_w - map_w) / 2.0
    else:
        cam_x = max(0.0, min(float(map_w - view_w), target_cx))
    if map_h <= view_h:
        cam_y = -(view_h - map_h) / 2.0
    else:
        cam_y = max(0.0, min(float(map_h - view_h), target_cy))
    return cam_x, cam_y


def apply_window_mode(fullscreen, windowed_size=(DEFAULT_WIDTH, DEFAULT_HEIGHT)):
    """Mengalihkan mode tampilan antara Layar Penuh (desktop) dan Jendela Resizable normal."""
    if fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    w = max(640, int(windowed_size[0]))
    h = max(480, int(windowed_size[1]))
    return pygame.display.set_mode((w, h), pygame.RESIZABLE)


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    is_fullscreen = False
    windowed_size = (DEFAULT_WIDTH, DEFAULT_HEIGHT)
    screen = apply_window_mode(False, windowed_size)
    clock = pygame.time.Clock()

    canvas_cache = {"surf": None, "size": None}

    def get_render_canvas(disp_surf):
        ww, wh = disp_surf.get_size()
        lw, lh = compute_logical_size(ww, wh)
        set_screen_size(lw, lh)
        if (lw, lh) == (ww, wh):
            return disp_surf
        if canvas_cache["surf"] is None or canvas_cache["size"] != (lw, lh):
            canvas_cache["surf"] = pygame.Surface((lw, lh))
            canvas_cache["size"] = (lw, lh)
        return canvas_cache["surf"]

    def present_canvas(disp_surf, canvas_surf):
        if canvas_surf is not disp_surf:
            pygame.transform.scale(canvas_surf, disp_surf.get_size(), disp_surf)
        pygame.display.flip()

    def map_mouse_event(event, disp_surf, canvas_surf):
        if canvas_surf is not disp_surf and event.type in (
            pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION
        ):
            mapped = window_to_logical(event.pos, disp_surf.get_size(), canvas_surf.get_size())
            data = dict(event.dict)
            data["pos"] = mapped
            return pygame.event.Event(event.type, data)
        return event

    def toggle_fullscreen():
        nonlocal is_fullscreen, screen, canvas
        is_fullscreen = not is_fullscreen
        screen = apply_window_mode(is_fullscreen, windowed_size)
        canvas = get_render_canvas(screen)

    def handle_display_event(event, notify=False):
        nonlocal screen, canvas, windowed_size
        resize_types = [pygame.VIDEORESIZE]
        if hasattr(pygame, "WINDOWSIZECHANGED"):
            resize_types.append(pygame.WINDOWSIZECHANGED)

        if event.type in resize_types:
            screen = pygame.display.get_surface() or screen
            sw, sh = screen.get_size()
            if not is_fullscreen and sw >= 320 and sh >= 240:
                try:
                    desk_sizes = pygame.display.get_desktop_sizes()
                except Exception:
                    desk_sizes = []
                if not desk_sizes or sw < desk_sizes[0][0] - 40 or sh < desk_sizes[0][1] - 80:
                    windowed_size = (sw, sh)
            canvas = get_render_canvas(screen)
            return True

        if event.type == pygame.KEYDOWN:
            is_f11 = event.key == pygame.K_F11
            is_alt_enter = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and bool(event.mod & pygame.KMOD_ALT)
            if is_f11 or is_alt_enter:
                toggle_fullscreen()
                if notify:
                    ui_mgr.show_notification(
                        "Mode Layar Penuh [F11]" if is_fullscreen else "Mode Jendela Normal [F11]",
                        duration=2.0,
                    )
                return True
        return False

    canvas = get_render_canvas(screen)

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

        vw, vh = get_screen_size(canvas)
        camera_x, camera_y = compute_clamped_camera(
            player.x + 24 - vw / 2,
            player.y + 24 - vh / 2,
            map_loader.map_width_px,
            map_loader.map_height_px,
            vw,
            vh,
        )

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

        vw, vh = get_screen_size(canvas)
        camera_x, camera_y = compute_clamped_camera(
            player.x + 24 - vw / 2,
            player.y + 24 - vh / 2,
            map_loader.map_width_px,
            map_loader.map_height_px,
            vw,
            vh,
        )

        cfg = STAGE_CONFIGS.get(new_tmx, {})
        ui_mgr.show_notification(f"Memasuki {cfg.get('name', new_tmx)}", duration=3.0)
        audio_manager.play_music(cfg.get("bgm", "bgm_dungeon"))

    def respawn_to_lobby():
        if current_map != "map1safeworld.tmx":
            switch_map("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1], reset_stages=True)
        lost_ash = player.respawn(LOBBY_SPAWN[0], LOBBY_SPAWN[1], inventory=inventory)
        ui_mgr.show_notification(f"Bangkit di Api Unggun! (-{lost_ash} Ash, -50% Material)", duration=3.5)

    audio_manager.play_music("bgm_village")

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        canvas = get_render_canvas(screen)
        mouse_pos = window_to_logical(pygame.mouse.get_pos(), screen.get_size(), canvas.get_size())

        # -------------------------------------------------------------
        # SCENE: TITLE SCREEN
        # -------------------------------------------------------------
        if mode == "title":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if handle_display_event(event):
                    continue
                ev = map_mouse_event(event, screen, canvas)
                act = title_scene.handle_event(ev)
                if act == "toggle_fullscreen":
                    toggle_fullscreen()
                elif act == "new_game":
                    prolog_scene = PrologScene()
                    mode = "prolog"
                elif act == "continue":
                    start_gameplay(load_existing=True)
                elif act == "exit":
                    running = False
                    break
            title_scene.update(dt)
            title_scene.draw(canvas, mouse_pos, is_fullscreen=is_fullscreen)
            present_canvas(screen, canvas)
            continue

        # -------------------------------------------------------------
        # SCENE: PROLOG INTERAKTIF
        # -------------------------------------------------------------
        if mode == "prolog":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if handle_display_event(event):
                    continue
                ev = map_mouse_event(event, screen, canvas)
                if prolog_scene.handle_event(ev) == "done":
                    start_gameplay(load_existing=False)
                    break
            if mode == "prolog":
                prolog_scene.update(dt)
                prolog_scene.draw(canvas)
                present_canvas(screen, canvas)
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
                if handle_display_event(event):
                    continue
                ev = map_mouse_event(event, screen, canvas)
                res = ending_scene.handle_event(ev)
                if res == "hub":
                    mode = "playing"
                    switch_map("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1], reset_stages=True)
                elif res == "menu":
                    SaveSystem.save_game(player, inventory, quest_mgr, current_map="map1safeworld.tmx")
                    mode = "title"
                    audio_manager.play_music("bgm_village")
            if mode == "ending":
                ending_scene.update(dt)
                ending_scene.draw(canvas, mouse_pos)
                present_canvas(screen, canvas)
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

            if handle_display_event(event, notify=True):
                continue

            event = map_mouse_event(event, screen, canvas)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    ui_mgr.show_tutorial = not ui_mgr.show_tutorial
                    audio_manager.play_sound("accept")
                    continue

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

                hotbar_keys = {
                    KEY_POTION_HP: 0,
                    KEY_POTION_STAMINA: 1,
                    KEY_ITEM_3: 2,
                    KEY_ITEM_4: 3,
                }
                if event.key in hotbar_keys:
                    idx = hotbar_keys[event.key]
                    item_obj = inventory.get_hotbar_entries()[idx][2]
                    status = inventory.use_hotbar_slot(idx, player, combat_mgr)
                    if status == "full" and item_obj:
                        ui_mgr.show_notification(f"Tidak perlu memakai {item_obj.name} saat stat penuh!")
                    elif status == "missing":
                        ui_mgr.show_notification(f"Slot [{idx + 1}] kosong! Cari drop monster atau beli di Toko Gael.")
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

                if event.button == 1 and ui_mgr.show_tutorial and ui_mgr.get_tutorial_close_rect().collidepoint(mouse_pos):
                    ui_mgr.show_tutorial = False
                    audio_manager.play_sound("cancel")
                    continue

                if event.button == 1:
                    clicked_hotbar = False
                    for hb_idx, hb_rect in ui_mgr.get_hotbar_item_rects(canvas.get_size()):
                        if hb_rect.collidepoint(mouse_pos):
                            item_obj = inventory.get_hotbar_entries()[hb_idx][2]
                            status = inventory.use_hotbar_slot(hb_idx, player, combat_mgr)
                            if status == "full" and item_obj:
                                ui_mgr.show_notification(f"Stat untuk {item_obj.name} sudah penuh!")
                            elif status == "missing":
                                ui_mgr.show_notification(f"Slot [{hb_idx + 1}] kosong!")
                            clicked_hotbar = True
                            break
                    if clicked_hotbar:
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
            if isinstance(npc, WhiteFlame):
                npc.update(dt, player=player, combat_mgr=combat_mgr)
            else:
                npc.update(dt)

        if not ui_blocked:
            for target in training_targets:
                target.update(world_dt, player=player, map_loader=map_loader, combat_mgr=combat_mgr)

        vw, vh = get_screen_size(canvas)
        target_cam_x = player.x + 24 - vw / 2
        target_cam_y = player.y + 24 - vh / 2
        camera_x += (target_cam_x - camera_x) * 0.1
        camera_y += (target_cam_y - camera_y) * 0.1

        camera_x, camera_y = compute_clamped_camera(
            camera_x, camera_y,
            map_loader.map_width_px, map_loader.map_height_px,
            vw, vh,
        )

        shake_ox, shake_oy = combat_mgr.get_shake_offset()
        render_cam_x = camera_x + shake_ox
        render_cam_y = camera_y + shake_oy

        # Render Pipeline ke kanvas logis responsif lalu diskalakan penuh ke layar
        canvas.fill(COLOR_BG)
        map_loader.draw(canvas, render_cam_x, render_cam_y)

        render_entities = [(player.y + 40, player)]
        for npc in all_npcs:
            render_entities.append((npc.y + npc.height, npc))
        for target in training_targets:
            if target.is_alive():
                render_entities.append((target.y + target.height, target))

        render_entities.sort(key=lambda item: item[0])
        for _, entity in render_entities:
            entity.draw(canvas, render_cam_x, render_cam_y)

        combat_mgr.draw(canvas, render_cam_x, render_cam_y)

        ui_mgr.draw_hud(
            canvas, player, combat_mgr, inventory, quest_mgr,
            nearby_npc=nearby_npc, current_map=current_map,
            targets=training_targets, map_loader=map_loader, npcs=all_npcs
        )

        if inventory.is_open:
            inventory.draw(canvas, mouse_pos, player)
        if shop_mgr.is_active():
            shop_mgr.draw(canvas, mouse_pos, player, inventory=inventory)
        if world_map_ui.is_open:
            world_map_ui.draw(canvas, mouse_pos, player)
        if dialogue_sys.is_active:
            dialogue_sys.draw(canvas, mouse_pos)

        present_canvas(screen, canvas)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
