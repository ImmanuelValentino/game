import os
import tempfile
import unittest
from collections import deque

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from main import LOBBY_SPAWN, apply_window_mode, compute_clamped_camera, create_map_entities
from src.combat import CombatManager, Projectile, SkullLaserBarrage, SporeTrap, roll_material_drop
from src.config import (
    STAGE_CONFIGS, BASIC_ATTACK_STAMINA, SKILL_ATTACK_STAMINA, DODGE_ROLL_STAMINA,
    DEFAULT_WIDTH, DEFAULT_HEIGHT, ATTACK_BOOST_MULT, compute_logical_size,
    set_screen_size, get_screen_size, window_to_logical,
)
from src.inventory import Inventory, ITEM_DATABASE
from src.map_loader import MapLoader
from src.npc import BossEntity, Enemy, TrainingTarget, WhiteFlame
from src.player import Player
from src.quest import CartographyMapUI, DialogueSystem, QuestManager
from src.save_system import SaveSystem
from src.scenes import EndingScene, PrologScene, TitleScreenScene
from src.shop import ShopManager
from src.ui import UIManager


class TestMapsAndEntities(unittest.TestCase):
    def test_all_8_maps_load_with_colliders_hazards_and_walkable_entities(self):
        for tmx_path, cfg in STAGE_CONFIGS.items():
            ml = MapLoader(tmx_path)
            self.assertGreater(len(ml.colliders), 0, f"{tmx_path} should have colliders")
            spawn = cfg["spawn"]
            spawn_hb = pygame.Rect(spawn[0] + 17, spawn[1] + 36, 14, 10)
            self.assertFalse(ml.is_blocked(spawn_hb), f"Spawn {spawn} in {tmx_path} is blocked")

            if tmx_path in ("stage1_swamp.tmx", "stage2_spore.tmx", "stage3_gehenna.tmx", "stage4_frost.tmx"):
                self.assertGreater(len(ml.hazard_grid), 0, f"{tmx_path} should have environmental hazards")

            npcs, targets = create_map_entities(tmx_path)
            self.assertGreater(len(npcs), 0)
            self.assertGreater(len(targets), 0)

            for npc in npcs:
                rect = pygame.Rect(int(npc.x), int(npc.y), npc.width, npc.height)
                self.assertFalse(ml.is_blocked(rect), f"NPC/Portal {npc.name} blocked in {tmx_path}")

            for target in targets:
                rect = (
                    target.get_hitbox()
                    if hasattr(target, "get_hitbox")
                    else pygame.Rect(int(target.x), int(target.y), target.width, target.height)
                )
                self.assertFalse(ml.is_blocked(rect), f"Target {target.name} blocked in {tmx_path}")

    def test_all_stage_and_dungeon_bfs_connectivity(self):
        for tmx_path in (
            "stage1_swamp.tmx", "stage2_spore.tmx", "stage3_gehenna.tmx",
            "stage4_frost.tmx", "stage5_throne.tmx", "dungeon1.tmx", "dungeon2.tmx"
        ):
            ml = MapLoader(tmx_path)
            spawn = STAGE_CONFIGS[tmx_path]["spawn"]
            start_cell = (spawn[0] // ml.tile_width, spawn[1] // ml.tile_height)
            visited = {start_cell}
            queue = deque([start_cell])
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) in visited or not (0 <= nx < ml.map_width_tiles and 0 <= ny < ml.map_height_tiles):
                        continue
                    cell_hb = pygame.Rect(nx * ml.tile_width + 9, ny * ml.tile_height + 11, 14, 10)
                    if not ml.is_blocked(cell_hb):
                        visited.add((nx, ny))
                        queue.append((nx, ny))

            npcs, targets = create_map_entities(tmx_path)
            for entity in [*npcs, *targets]:
                ecx, ecy = entity.get_center()
                cell = (int(ecx) // ml.tile_width, int(ecy) // ml.tile_height)
                self.assertIn(cell, visited, f"{entity.name} in {tmx_path} is unreachable from spawn")


class TestGDDCombatAndMechanics(unittest.TestCase):
    def test_stamina_delay_fatigue_and_perfect_dodge_slowmo(self):
        ml = MapLoader("stage1_swamp.tmx")
        player = Player(x=96, y=608)
        combat = CombatManager()
        target = TrainingTarget("Dummy", 126, 608, max_hp=100)

        # Serangan normal ringan (-5 STA) dan jeda pemulihan 0.6 detik
        self.assertEqual(BASIC_ATTACK_STAMINA, 5.0)
        self.assertEqual(SKILL_ATTACK_STAMINA, 30.0)
        self.assertTrue(combat.perform_attack(player, (140, 620), 0, 0, [target]))
        self.assertEqual(player.stamina, 45.0)
        player.update(0.3, ml)
        self.assertEqual(player.stamina, 45.0, "Stamina must pause during 0.6s recovery delay")
        player.update(0.6, ml)
        self.assertGreater(player.stamina, 45.0, "Stamina must regenerate after 0.6s delay")

        # Skill RMB tetap memakai 30 STA sesuai permintaan tim
        player.stamina = 45.0
        player.stagger_timer = 0.0
        combat.skill_cd_timer = 0.0
        self.assertTrue(combat.perform_skill(player, (140, 620), 0, 0, [target]))
        self.assertEqual(player.stamina, 15.0)

        # Uji Fatigue (<10 STA) menolak serangan dan memberi stagger
        player.stamina = 8.0
        combat.attack_cd_timer = 0.0
        self.assertFalse(combat.perform_attack(player, (140, 620), 0, 0, [target]))
        self.assertGreater(player.stagger_timer, 0.0)

        # Uji Perfect Dodge: -15 STA roll + +15 STA parry = net stabil, Slow-Mo 1.5s, & Crit 150% buff
        player.stamina = 40.0
        player.stagger_timer = 0.0
        player.start_roll(1.0, 0.0)
        st_after_roll = player.stamina
        self.assertEqual(st_after_roll, 40.0 - DODGE_ROLL_STAMINA)
        dealt = player.take_damage(120)
        self.assertEqual(dealt, 0)
        self.assertTrue(player.dodged_last_hit)
        self.assertEqual(player.perfect_dodge_slowmo_timer, 1.5)
        self.assertTrue(player.next_attack_crit_buff)
        self.assertEqual(player.stamina, st_after_roll + 15.0)

        # Uji pacing Lv.1 mengalahkan monster Dungeon 1 dengan basic attack tanpa Fatigue
        p_lv1 = Player(x=220, y=580)
        _, s1_targets = create_map_entities("stage1_swamp.tmx")
        mob = s1_targets[0]
        mob.x, mob.y = 250.0, 580.0
        for _ in range(4):
            combat.attack_cd_timer = 0.0
            combat.perform_attack(p_lv1, (mob.x + 22, mob.y + 22), 0, 0, [mob])
            if not mob.is_alive():
                break
        self.assertFalse(mob.is_alive(), "Dungeon 1 basic mob should fall within 4 basic attacks at Lv.1")
        self.assertFalse(p_lv1.is_fatigued, "Player should not fall into fatigue defeating a single Dungeon 1 mob")

    def test_projectiles_blocked_by_pillars_and_boss_phase2_transformation(self):
        ml = MapLoader("stage1_swamp.tmx")
        player = Player(x=96, y=608)
        combat = CombatManager()

        # Pilar pada stage1_swamp ada di baris 15, kolom 7 -> px (224, 480)
        proj = Projectile(200, 496, 0.0, speed=300.0, damage=40)
        alive = True
        for _ in range(10):
            alive = proj.update(0.05, player, ml, combat)
            if not alive:
                break
        self.assertFalse(alive, "Projectile should be blocked by pillar cover")

        # Uji SporeTrap meletus saat didekati
        trap = SporeTrap(120, 632, damage=50)
        for _ in range(25):
            if not trap.update(0.05, player, combat):
                break
        self.assertFalse(trap.alive)
        self.assertLess(player.hp, player.max_hp)

        # Uji Transformasi Fase 2 Final Boss (Sang Penguasa Abu -> The Hollow Crown)
        boss = BossEntity("ash_lord", 608, 280)
        self.assertEqual(boss.phase, 1)
        boss.take_damage(boss.hp)
        self.assertTrue(boss.is_alive())
        self.assertEqual(boss.phase, 2)
        self.assertIn("Hollow Crown", boss.name)

    def test_hazards_mud_conveyor_and_weighted_drops(self):
        ml_swamp = MapLoader("stage1_swamp.tmx")
        p_mud = Player(x=6 * 32, y=12 * 32)
        p_mud.update(0.05, ml_swamp)
        self.assertIn("mud", p_mud.active_hazards)
        self.assertAlmostEqual(p_mud.speed, p_mud.base_speed * 0.70, places=2)

        ml_furnace = MapLoader("stage3_gehenna.tmx")
        p_conv = Player(x=8 * 32, y=10 * 32)
        x_before = p_conv.x
        p_conv.update(0.2, ml_furnace)
        self.assertGreater(p_conv.x, x_before, "Conveyor right should push player east")

        drop = roll_material_drop(tier_mult=1.5, is_boss=True, player_drop_mult=1.5)
        self.assertIn(drop, ("general_core", "broken_crown"))


class TestInventoryShopKarmaAndCartography(unittest.TestCase):
    def test_inventory_vektor_workshop_gael_karma_and_aell_map(self):
        player = Player()
        player.gold = 400
        inv = Inventory()
        shop = ShopManager()
        combat = CombatManager()
        quests = QuestManager()

        # Tambah material monster lalu jual via Vektor
        inv.add_item("bone_shard", 2)
        inv.add_item("karak_blood", 1)
        shop.open_vektor()
        _, _, _, _, _, sell_btn, skill_btns = shop._get_vektor_layout()
        shop.handle_click(sell_btn.center, player, inv, combat, quests)
        self.assertEqual(inv.get_count("bone_shard"), 0)
        self.assertGreater(player.skill_points, 0)
        self.assertTrue(next(q for q in quests.quests if q.id == "q3_supplies").is_completed)

        # Tempa Bilah Penebusan di Vektor -> +20 Karma & naik ke redemption_blade_1
        shop.handle_click(skill_btns[3].center, player, inv, combat, quests)
        self.assertEqual(player.weapon_id, "redemption_blade_1")
        self.assertEqual(player.karma, 20)

        # Beli Pedang Haus Darah di Gael -> -50 Karma (total -30 -> Bad Ending lock)
        shop.open_gael()
        _, _, _, _, _, rows = shop._get_merchant_layout()
        blood_btn = rows[-1][2]
        shop.handle_click(blood_btn.center, player, inv, combat, quests)
        self.assertEqual(player.weapon_id, "bloodthirst_blade")
        self.assertEqual(player.karma, -30)
        self.assertEqual(player.drop_multiplier, 1.5)

        # Uji Aell Cartography Map unlock bertahap
        cmap = CartographyMapUI()
        self.assertTrue(cmap.is_unlocked("stage1_swamp.tmx", player))
        self.assertFalse(cmap.is_unlocked("stage2_spore.tmx", player))
        player.beacons_cleared.add("stage1_swamp.tmx")
        self.assertTrue(cmap.is_unlocked("stage2_spore.tmx", player))


class TestSaveSystemAndScenes(unittest.TestCase):
    def test_save_load_round_trip_and_scenes_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test_save.json")
            p1 = Player(x=96, y=608)
            p1.level = 5
            p1.karma = 25
            p1.skill_points = 4
            p1.beacons_cleared = {"stage1_swamp.tmx"}
            p1.equip_weapon("redemption_blade_1")
            inv1 = Inventory()
            inv1.add_item("redemption_blade_1", 1)
            inv1.add_item("karak_blood", 2)
            q1 = QuestManager()
            q1.advance_progress("q1_awaken", 1, p1)

            self.assertTrue(SaveSystem.save_game(p1, inv1, q1, current_map="stage2_spore.tmx", filepath=save_path))
            p2 = Player()
            inv2 = Inventory()
            q2 = QuestManager()
            self.assertTrue(SaveSystem.load_game(p2, inv2, q2, filepath=save_path))
            self.assertEqual(p2.level, 5)
            self.assertEqual(p2.weapon_id, "redemption_blade_1")
            self.assertIn("stage1_swamp.tmx", p2.beacons_cleared)
            self.assertEqual(p2.saved_map, "stage2_spore.tmx")
            self.assertEqual(inv2.get_count("karak_blood"), 2)

        # Smoke test Title, Prolog, dan Ending QTE/Bad/Good
        screen = pygame.display.get_surface()
        ts = TitleScreenScene()
        ts.update(0.016)
        ts.draw(screen, (200, 350))

        ps = PrologScene()
        ps.update(0.016)
        ps.draw(screen)

        p_good = Player()
        p_good.karma = 30
        es_good = EndingScene(p_good)
        self.assertEqual(es_good.stage, "good_qte")
        for _ in range(10):
            es_good.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
        self.assertEqual(es_good.stage, "good_epilogue")
        es_good.draw(screen, (640, 580))

        p_bad = Player()
        p_bad.karma = -40
        es_bad = EndingScene(p_bad)
        self.assertEqual(es_bad.stage, "bad_epilogue")
        es_bad.draw(screen, (640, 580))

    def test_render_all_maps_and_ui_overlays(self):
        screen = pygame.display.get_surface()
        player = Player(x=LOBBY_SPAWN[0], y=LOBBY_SPAWN[1])
        inv = Inventory()
        combat = CombatManager()
        shop = ShopManager()
        quests = QuestManager()
        ds = DialogueSystem()
        cmap = CartographyMapUI()
        ui = UIManager()
        ui.show_minimap = True

        for tmx in STAGE_CONFIGS:
            ml = MapLoader(tmx)
            npcs, targets = create_map_entities(tmx)
            ml.draw(screen, 0, 0)
            for e in [*npcs, *targets]:
                e.update(0.016, player=player, map_loader=ml, combat_mgr=combat) if isinstance(e, TrainingTarget) else e.update(0.016)
                e.draw(screen, 0, 0)
            player.draw(screen, 0, 0)
            combat.draw(screen, 0, 0)
            ui.draw_hud(screen, player, combat, inv, quests, nearby_npc=npcs[0], current_map=tmx, targets=targets, map_loader=ml, npcs=npcs)

        inv.is_open = True
        inv.draw(screen, (640, 360), player)
        for item_id, item in ITEM_DATABASE.items():
            surf = item.icon_surf
            self.assertEqual(surf.get_size(), (36, 36))
            opaque = sum(
                1
                for x in range(surf.get_width())
                for y in range(surf.get_height())
                if surf.get_at((x, y)).a > 30
            )
            self.assertGreaterEqual(opaque, 300, f"Icon for {item_id} ({item.icon_file}) looks too sparse ({opaque} px)")
        shop.open_vektor()
        shop.draw(screen, (640, 360), player, inventory=inv)
        shop.open_gael()
        shop.draw(screen, (640, 360), player, inventory=inv)
        cmap.open()
        cmap.draw(screen, (640, 360), player)
        ds.start_dialogue("Elara", ["Tes render dialog."], choices=[("OK", ds.close)])
        ds.draw(screen, (640, 600))

    def test_responsive_display_resize_fullscreen_and_camera(self):
        self.assertEqual(compute_logical_size(1280, 720), (1280, 720))
        self.assertEqual(compute_logical_size(1920, 1080), (1280, 720))
        self.assertEqual(compute_logical_size(1920, 1200), (1152, 720))
        self.assertEqual(compute_logical_size(960, 720), (960, 720))
        uw_w, uw_h = compute_logical_size(2560, 1080)
        self.assertGreater(uw_w, 1280)
        self.assertEqual(uw_h, 620)

        self.assertEqual(window_to_logical((960, 540), (1920, 1080), (1280, 720)), (640, 360))
        cam_x, cam_y = compute_clamped_camera(0.0, 0.0, 1280, 1280, uw_w, uw_h)
        self.assertAlmostEqual(cam_x, -(uw_w - 1280) / 2.0)
        self.assertEqual(cam_y, 0.0)

        player = Player(x=LOBBY_SPAWN[0], y=LOBBY_SPAWN[1])
        inv = Inventory()
        combat = CombatManager()
        shop = ShopManager()
        quests = QuestManager()
        ds = DialogueSystem()
        cmap = CartographyMapUI()
        ui = UIManager()
        ui.show_minimap = True
        ml = MapLoader("stage1_swamp.tmx")
        npcs, targets = create_map_entities("stage1_swamp.tmx")

        try:
            # Uji perpindahan mode Resizable -> Fullscreen -> Normal
            s_fs = apply_window_mode(True)
            self.assertGreater(s_fs.get_width(), 0)
            s_norm = apply_window_mode(False, (DEFAULT_WIDTH, DEFAULT_HEIGHT))
            self.assertEqual(s_norm.get_size(), (DEFAULT_WIDTH, DEFAULT_HEIGHT))

            for vw, vh in ((960, 640), (1152, 720), (1470, 620)):
                set_screen_size(vw, vh)
                self.assertEqual(get_screen_size(), (vw, vh))
                surf = pygame.Surface((vw, vh))

                ts = TitleScreenScene()
                fs_btn = ts._get_fullscreen_button()
                self.assertTrue(surf.get_rect().contains(fs_btn))
                self.assertEqual(
                    ts.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=fs_btn.center)),
                    "toggle_fullscreen",
                )
                ts.draw(surf, fs_btn.center, is_fullscreen=False)

                ps = PrologScene()
                ps.draw(surf)

                es = EndingScene(player)
                es.draw(surf, (vw // 2, vh // 2))

                ui.draw_hud(surf, player, combat, inv, quests, nearby_npc=npcs[0], current_map="stage1_swamp.tmx", targets=targets, map_loader=ml, npcs=npcs)
                inv.is_open = True
                inv.draw(surf, (vw // 2, vh // 2), player)
                shop.open_vektor()
                shop.draw(surf, (vw // 2, vh // 2), player, inventory=inv)
                cmap.open()
                cmap.draw(surf, (vw // 2, vh // 2), player)
                ds.start_dialogue("Aell", ["Tes layar responsif."], choices=[("A", None), ("B", ds.close)])
                ds.draw(surf, (vw // 2, vh - 80))
        finally:
            set_screen_size(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT))

    def test_npc_spread_white_fire_skull_lasers_hotbar_and_progression(self):
        # 1. Verifikasi penyebaran NPC di Hub Oakhaven (tidak menumpuk di tengah) & role minimap
        hub_npcs, _ = create_map_entities("map1safeworld.tmx")
        xs = [n.x for n in hub_npcs]
        ys = [n.y for n in hub_npcs]
        self.assertGreaterEqual(max(xs) - min(xs), 700, "NPCs must spread horizontally across town")
        self.assertGreaterEqual(max(ys) - min(ys), 500, "NPCs must spread vertically across town")
        roles = {getattr(n, "map_role", "") for n in hub_npcs}
        for req_role in ("shop", "skill", "map", "quest", "bar", "campfire"):
            self.assertIn(req_role, roles)

        # 2. Verifikasi aset BGM sesuai suasana, skull GIF, white fire GIF, & potion icons
        for asset in (
            "assets/audio/bgm_village.wav",
            "assets/audio/bgm_dungeon.wav",
            "assets/audio/bgm_boss.wav",
            "assets/audio/bgm_throne.wav",
            "assets/audio/laser.wav",
            "character/boss_skull/idle.gif",
            "character/boss_skull/charge.gif",
            "assets/effects/white_fire.gif",
            "assets/items/potion_hp.png",
            "assets/items/potion_atk.png",
            "assets/items/potion_def.png",
            "assets/items/potion_crit.png",
        ):
            self.assertTrue(os.path.exists(asset), f"Missing generated asset: {asset}")

        # 3. Verifikasi tidak ada auto-regen pasif HP, dan Api Putih memulihkan HP saat di dekatnya
        ml = MapLoader("stage1_swamp.tmx")
        s1_npcs, _ = create_map_entities("stage1_swamp.tmx")
        white_flames = [n for n in s1_npcs if isinstance(n, WhiteFlame)]
        self.assertEqual(len(white_flames), 4, "Dungeon 1 must have 4 White Flames at corners")

        player = Player(x=500, y=500)
        player.hp = 45
        player.update(2.0, ml)
        self.assertEqual(player.hp, 45, "HP must NOT passively regenerate away from White Flame")

        wf = white_flames[0]
        player.x = wf.x - 6
        player.y = wf.y - 6
        combat = CombatManager()
        for _ in range(20):
            player.update(0.1, ml, combat_mgr=combat)
            wf.update(0.1, player=player, combat_mgr=combat)
        self.assertTrue(player.in_white_fire)
        self.assertGreater(player.hp, 45, "HP must regenerate when standing near White Flame")

        # 4. Verifikasi progresi Dungeon 1 -> Dungeon 4 makin sulit
        stages = ("stage1_swamp.tmx", "stage2_spore.tmx", "stage3_gehenna.tmx", "stage4_frost.tmx")
        for i in range(len(stages) - 1):
            c0, c1 = STAGE_CONFIGS[stages[i]], STAGE_CONFIGS[stages[i + 1]]
            self.assertLess(c0["hp_mult"], c1["hp_mult"])
            self.assertLess(c0["dmg_mult"], c1["dmg_mult"])

        # 5. Verifikasi serangan 6 Kepala Tengkorak Laser invincible di Final Boss Domain
        for form in ("top_bottom", "left_right"):
            cm = CombatManager()
            self.assertTrue(cm.trigger_skull_lasers(formation=form, damage=220, map_w=1280, map_h=1280))
            barrage = cm.skull_barrages[0]
            self.assertEqual(len(barrage.skulls), 6)
            p_laser = Player(x=barrage.skulls[0]["rect"].centerx - 24, y=barrage.skulls[0]["rect"].centery - 24)
            p_laser.hp = p_laser.max_hp
            cm.update(barrage.telegraph_duration + 0.1, player=p_laser)
            self.assertEqual(barrage.state, "firing")
            self.assertLess(p_laser.hp, p_laser.max_hp, f"Skull laser ({form}) must damage player in beam")

        # 6. Verifikasi Hotbar Bawah [1-4] menyimpan item drop/shop & Attack Boost 15s
        inv = Inventory()
        self.assertTrue(inv.add_item("defense_potion", 1))
        self.assertIn("defense_potion", inv.hotbar_ids)
        atk_idx = inv.hotbar_ids.index("attack_boost_potion")
        p_boost = Player()
        base_atk = p_boost.total_damage
        self.assertEqual(inv.use_hotbar_slot(atk_idx, p_boost, combat), "used")
        self.assertEqual(p_boost.total_damage, int(round(base_atk * ATTACK_BOOST_MULT)))
        self.assertAlmostEqual(p_boost.atk_boost_timer, 15.0, places=2)
        p_boost.update(15.2, ml)
        self.assertEqual(p_boost.total_damage, base_atk)


if __name__ == "__main__":
    unittest.main()
