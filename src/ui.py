"""
HUD & UI Manager untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menampilkan HP/Stamina/EXP, ATK/DEF/SKL/Weapon, Hazard & Slow-Mo badges,
Boss HP bar, minimap, prompt interaksi, help overlay, dan game over modal.
"""
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, STAGE_CONFIGS, get_font,
    COLOR_HP, COLOR_HP_BG, COLOR_HP_TRAIL,
    COLOR_STAMINA, COLOR_STAMINA_BG,
    COLOR_EXP, COLOR_EXP_BG,
    COLOR_GOLD, COLOR_ASH, COLOR_CRIT,
    COLOR_WHITE, COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)


class UIManager:
    def __init__(self):
        self.show_help = False
        self.show_minimap = False
        self.notification_text = ""
        self.notification_timer = 0.0

    def show_notification(self, text, duration=2.5):
        self.notification_text = text
        self.notification_timer = duration

    def update(self, dt):
        if self.notification_timer > 0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def get_respawn_button_rect(self):
        gw, gh = 520, 260
        gx = (SCREEN_WIDTH - gw) // 2
        gy = (SCREEN_HEIGHT - gh) // 2
        return pygame.Rect(gx + gw // 2 - 140, gy + 165, 280, 48)

    def draw_hud(
        self, surface, player, combat_mgr, inventory, quest_mgr,
        nearby_npc=None, current_map="map1safeworld.tmx", targets=None,
        map_loader=None, npcs=None
    ):
        self._draw_status_bars(surface, player)
        self._draw_status_badges(surface, player)
        self._draw_currency(surface, player, current_map)
        self._draw_quest_tracker(surface, quest_mgr)
        self._draw_boss_bar(surface, targets or [])
        self._draw_hotbar(surface, player, combat_mgr, inventory)
        self._draw_interaction_prompt(surface, nearby_npc)
        self._draw_notification(surface)

        if self.show_minimap and map_loader is not None:
            self._draw_minimap(surface, player, map_loader, npcs or [], targets or [])

        if self.show_help:
            self._draw_help_overlay(surface)

        if player.is_dead:
            self._draw_game_over(surface)

    def _draw_status_bars(self, surface, player):
        start_x, start_y = 20, 20
        panel_w, panel_h = 305, 114
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (18, 20, 28, 215), (0, 0, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=10)
        surface.blit(panel_surf, (start_x, start_y))

        badge_cx, badge_cy = start_x + 36, start_y + 36
        pygame.draw.circle(surface, (28, 30, 42), (badge_cx, badge_cy), 24)
        pygame.draw.circle(surface, COLOR_GOLD, (badge_cx, badge_cy), 24, 2)
        lvl_font = get_font(14, bold=True)
        lvl_text = lvl_font.render(f"Lv.{player.level}", True, COLOR_GOLD)
        surface.blit(lvl_text, (badge_cx - lvl_text.get_width() // 2, badge_cy - lvl_text.get_height() // 2))

        bx, bar_w = start_x + 72, 212
        font_num = get_font(10, bold=True)

        # 1. Health Bar
        by_hp, bar_h = start_y + 12, 16
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, by_hp, bar_w, bar_h), border_radius=4)
        trail_pct = max(0.0, min(1.0, player.hp_trail / player.max_hp))
        pygame.draw.rect(surface, COLOR_HP_TRAIL, (bx, by_hp, int(bar_w * trail_pct), bar_h), border_radius=4)
        hp_pct = max(0.0, min(1.0, player.hp / player.max_hp))
        pygame.draw.rect(surface, COLOR_HP, (bx, by_hp, int(bar_w * hp_pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, (80, 25, 30), (bx, by_hp, bar_w, bar_h), 1, border_radius=4)
        hp_txt = font_num.render(f"HP {player.hp}/{player.max_hp}", True, COLOR_WHITE)
        surface.blit(hp_txt, (bx + (bar_w - hp_txt.get_width()) // 2, by_hp + 1))

        # 2. Stamina Bar (berubah warna saat Fatigue < 10)
        by_st, st_h = start_y + 34, 13
        pygame.draw.rect(surface, COLOR_STAMINA_BG, (bx, by_st, bar_w, st_h), border_radius=3)
        st_pct = max(0.0, min(1.0, player.stamina / player.max_stamina))
        st_col = (210, 95, 50) if player.is_fatigued else COLOR_STAMINA
        pygame.draw.rect(surface, st_col, (bx, by_st, int(bar_w * st_pct), st_h), border_radius=3)
        pygame.draw.rect(surface, (20, 60, 30), (bx, by_st, bar_w, st_h), 1, border_radius=3)
        st_label = f"ST {int(player.stamina)}/{player.max_stamina}" + (" [FATIGUE]" if player.is_fatigued else "")
        st_txt = font_num.render(st_label, True, COLOR_WHITE)
        surface.blit(st_txt, (bx + (bar_w - st_txt.get_width()) // 2, by_st - 1))

        # 3. EXP Bar
        by_exp, exp_h = start_y + 52, 7
        pygame.draw.rect(surface, COLOR_EXP_BG, (bx, by_exp, bar_w, exp_h), border_radius=2)
        exp_pct = max(0.0, min(1.0, player.exp / player.exp_to_next)) if player.exp_to_next > 0 else 0
        pygame.draw.rect(surface, COLOR_EXP, (bx, by_exp, int(bar_w * exp_pct), exp_h), border_radius=2)
        surface.blit(font_num.render(f"EXP {player.exp}/{player.exp_to_next}", True, (220, 200, 140)), (bx, by_exp + 9))

        # 4. Baris Ringkas Stat GDD (ATK / DEF / SKL & Senjata)
        stat_font = get_font(11, bold=True)
        stat_str = f"ATK:{player.total_damage}  DEF:{player.armor}  SKL:{player.skill_level}"
        surface.blit(stat_font.render(stat_str, True, COLOR_TEXT_ACCENT), (start_x + 14, start_y + 76))
        w_str = f"Senjata: {player.weapon_info['name']}"
        surface.blit(font_num.render(w_str, True, COLOR_GOLD), (start_x + 14, start_y + 94))

    def _draw_status_badges(self, surface, player):
        """Menampilkan badge efek aktif (Perfect Dodge Slow-Mo, Fatigue, Hazard Bioma)."""
        badges = []
        if player.perfect_dodge_slowmo_timer > 0:
            badges.append(("SLOW-MO + 150% CRIT!", (70, 175, 240)))
        if player.is_fatigued:
            badges.append(("FATIGUE (+20% DMG Masuk)", (215, 75, 65)))
        if "mud" in player.active_hazards or "sinkhole" in player.active_hazards:
            badges.append(("LUMPUR (-30% SPD, 2x Sprint)", (145, 105, 65)))
        if player.has_hazard_debuff:
            badges.append(("KABUT RACUN (DoT +15% DMG)", (125, 195, 95)))
        if "lava" in player.active_hazards:
            badges.append(("TERBAKAR LAHAR!", (240, 95, 35)))
        if "ice" in player.active_hazards:
            badges.append(("ES LICIN (Inersia)", (125, 200, 245)))
        if "conv_right" in player.active_hazards or "conv_left" in player.active_hazards:
            badges.append(("CONVEYOR BELT", (220, 155, 55)))

        b_font = get_font(11, bold=True)
        y = 140
        for text, col in badges:
            txt_s = b_font.render(text, True, COLOR_WHITE)
            bw = txt_s.get_width() + 18
            pill = pygame.Surface((bw, 22), pygame.SRCALPHA)
            pygame.draw.rect(pill, (*col, 195), (0, 0, bw, 22), border_radius=5)
            surface.blit(pill, (20, y))
            surface.blit(txt_s, (29, y + 3))
            y += 26

    def _draw_currency(self, surface, player, current_map):
        box_w, box_h = 300, 44
        box_x = SCREEN_WIDTH - box_w - 20
        box_y = 20

        surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 215), (0, 0, box_w, box_h), border_radius=8)
        pygame.draw.rect(surf, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), 1, border_radius=8)
        surface.blit(surf, (box_x, box_y))

        c_font = get_font(13, bold=True)
        pygame.draw.circle(surface, COLOR_GOLD, (box_x + 18, box_y + 22), 6)
        surface.blit(c_font.render(f"{player.gold} G", True, COLOR_GOLD), (box_x + 30, box_y + 13))

        pygame.draw.circle(surface, COLOR_ASH, (box_x + 112, box_y + 22), 6)
        surface.blit(c_font.render(f"{player.monster_ash} Ash", True, COLOR_ASH), (box_x + 124, box_y + 13))

        pygame.draw.circle(surface, COLOR_TEXT_ACCENT, (box_x + 208, box_y + 22), 6)
        surface.blit(c_font.render(f"{player.skill_points} SKL", True, COLOR_TEXT_ACCENT), (box_x + 220, box_y + 13))

        h_font = get_font(11)
        h_surf = h_font.render("[H]: Bantuan | [TAB]: Peta | [M]: Mute", True, COLOR_TEXT_MUTED)
        surface.blit(h_surf, (box_x + box_w - h_surf.get_width() - 2, box_y + box_h + 6))

        loc_name = STAGE_CONFIGS.get(current_map, {}).get("name", current_map)
        loc_surf = h_font.render(loc_name, True, COLOR_TEXT_ACCENT)
        surface.blit(loc_surf, (box_x + box_w - loc_surf.get_width() - 2, box_y + box_h + 22))

    def _draw_quest_tracker(self, surface, quest_mgr):
        current_q = quest_mgr.get_current_quest()
        q_text = f"{current_q.title} ({current_q.current_count}/{current_q.target_count})" if current_q else "Semua Quest Utama Selesai!"

        font = get_font(13, bold=True)
        rendered = font.render(q_text, True, COLOR_GOLD)

        box_w = rendered.get_width() + 50
        box_h = 32
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = 20

        surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 205), (0, 0, box_w, box_h), border_radius=6)
        pygame.draw.rect(surf, (140, 115, 60), (0, 0, box_w, box_h), 1, border_radius=6)
        surface.blit(surf, (box_x, box_y))

        dx, dy = box_x + 18, box_y + box_h // 2
        pygame.draw.polygon(surface, COLOR_GOLD, [(dx, dy - 6), (dx + 6, dy), (dx, dy + 6), (dx - 6, dy)])
        surface.blit(rendered, (box_x + 32, box_y + 7))

    def _draw_boss_bar(self, surface, targets):
        boss = next((t for t in targets if getattr(t, "is_boss", False) and t.is_alive()), None)
        if not boss:
            return

        bar_w, bar_h = 500, 16
        bx = (SCREEN_WIDTH - bar_w) // 2
        by = 62

        name_font = get_font(13, bold=True)
        n_surf = name_font.render(boss.name, True, (255, 115, 95))
        surface.blit(n_surf, (SCREEN_WIDTH // 2 - n_surf.get_width() // 2, by))

        ry = by + 20
        pygame.draw.rect(surface, (20, 12, 16), (bx - 2, ry - 2, bar_w + 4, bar_h + 4), border_radius=5)
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, ry, bar_w, bar_h), border_radius=4)
        pct = max(0.0, min(1.0, boss.hp / boss.max_hp))
        pygame.draw.rect(surface, (200, 40, 50), (bx, ry, int(bar_w * pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, (bx - 2, ry - 2, bar_w + 4, bar_h + 4), 1, border_radius=5)

    def _draw_hotbar(self, surface, player, combat_mgr, inventory):
        slot_w, slot_h, spacing, total_slots = 48, 48, 10, 5
        bar_w = total_slots * slot_w + (total_slots - 1) * spacing + 20
        bar_h = 66
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = SCREEN_HEIGHT - bar_h - 15

        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 220), (0, 0, bar_w, bar_h), border_radius=10)
        pygame.draw.rect(surf, COLOR_PANEL_BORDER, (0, 0, bar_w, bar_h), 1, border_radius=10)
        surface.blit(surf, (bar_x, bar_y))

        k_font = get_font(11, bold=True)
        cnt_font = get_font(11, bold=True)

        slots_data = [
            {"key": "1", "count": inventory.get_count("hp_potion"), "cd": 0.0, "icon_color": (220, 50, 60)},
            {"key": "2", "count": inventory.get_count("stamina_tonic"), "cd": 0.0, "icon_color": (40, 170, 70)},
            {"key": "LMB", "count": None, "cd": combat_mgr.attack_cd_timer / combat_mgr.attack_cooldown, "icon_color": (240, 190, 50)},
            {"key": "RMB", "count": None, "cd": combat_mgr.skill_cd_timer / combat_mgr.skill_cooldown, "icon_color": (230, 80, 40)},
            {"key": "Space", "count": None, "cd": player.roll_cd_timer / player.roll_cooldown, "icon_color": (100, 170, 255)},
        ]

        for i, s in enumerate(slots_data):
            sx = bar_x + 10 + i * (slot_w + spacing)
            sy = bar_y + 9
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)

            pygame.draw.rect(surface, (30, 32, 45), s_rect, border_radius=6)
            pygame.draw.rect(surface, (60, 65, 85), s_rect, 1, border_radius=6)
            pygame.draw.circle(surface, s["icon_color"], s_rect.center, 12)

            if s["cd"] > 0:
                cd_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
                cd_h = int(slot_w * min(1.0, s["cd"]))
                pygame.draw.rect(cd_surf, (0, 0, 0, 170), (0, slot_h - cd_h, slot_w, cd_h), border_radius=6)
                surface.blit(cd_surf, (sx, sy))

            if s["count"] is not None:
                c_text = cnt_font.render(str(s["count"]), True, COLOR_WHITE)
                surface.blit(c_text, (sx + slot_w - c_text.get_width() - 4, sy + slot_w - 15))

            k_text = k_font.render(s["key"], True, COLOR_GOLD)
            surface.blit(k_text, (sx + 4, sy + 3))

    def _draw_minimap(self, surface, player, map_loader, npcs, targets):
        mm_size = 160
        mm_x = SCREEN_WIDTH - mm_size - 20
        mm_y = 112

        mm_surf = pygame.Surface((mm_size, mm_size), pygame.SRCALPHA)
        mm_surf.fill((16, 18, 26, 215))

        scale_x = mm_size / max(1, map_loader.map_width_px)
        scale_y = mm_size / max(1, map_loader.map_height_px)

        for obs in map_loader.colliders:
            pygame.draw.rect(
                mm_surf, (75, 80, 95, 220),
                (int(obs.x * scale_x), int(obs.y * scale_y), max(2, int(obs.width * scale_x)), max(2, int(obs.height * scale_y)))
            )

        for npc in npcs:
            nx, ny = npc.get_center()
            col = COLOR_TEXT_ACCENT if hasattr(npc, "target_map") else COLOR_GOLD
            pygame.draw.circle(mm_surf, col, (int(nx * scale_x), int(ny * scale_y)), 3)

        for t in targets:
            if t.is_alive():
                tx, ty = t.get_center()
                col = (255, 60, 60) if getattr(t, "is_boss", False) else (220, 100, 100)
                pygame.draw.circle(mm_surf, col, (int(tx * scale_x), int(ty * scale_y)), 4 if getattr(t, "is_boss", False) else 2)

        px, py = (player.x + 24) * scale_x, (player.y + 24) * scale_y
        pygame.draw.circle(mm_surf, (100, 255, 130), (int(px), int(py)), 4)

        pygame.draw.rect(mm_surf, COLOR_PANEL_BORDER_LIGHT, (0, 0, mm_size, mm_size), 2)
        surface.blit(mm_surf, (mm_x, mm_y))

    def _draw_interaction_prompt(self, surface, nearby_npc):
        if not nearby_npc:
            return
        if hasattr(nearby_npc, "target_map"):
            prompt_str = f"[E] {nearby_npc.name}"
        elif nearby_npc.name == "Api Unggun Oakhaven":
            prompt_str = "[E] Istirahat & Simpan Game"
        else:
            prompt_str = f"[E] Bicara dengan {nearby_npc.name}"

        font = get_font(14, bold=True)
        text = font.render(prompt_str, True, COLOR_GOLD)
        pw, ph = text.get_width() + 32, 36
        px = (SCREEN_WIDTH - pw) // 2
        py = SCREEN_HEIGHT - 135

        psurf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(psurf, (18, 20, 28, 220), (0, 0, pw, ph), border_radius=8)
        pygame.draw.rect(psurf, COLOR_GOLD, (0, 0, pw, ph), 2, border_radius=8)
        surface.blit(psurf, (px, py))
        surface.blit(text, (px + 16, py + 8))

    def _draw_notification(self, surface):
        if self.notification_timer <= 0:
            return
        font = get_font(16, bold=True)
        text = font.render(self.notification_text, True, COLOR_GOLD)
        nw, nh = text.get_width() + 40, 40
        nx = (SCREEN_WIDTH - nw) // 2
        ny = 98

        nsurf = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(nsurf, (20, 22, 32, 230), (0, 0, nw, nh), border_radius=8)
        pygame.draw.rect(nsurf, COLOR_GOLD, (0, 0, nw, nh), 1, border_radius=8)
        surface.blit(nsurf, (nx, ny))
        surface.blit(text, (nx + 20, ny + 9))

    def _draw_help_overlay(self, surface):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        hw, hh = 590, 470
        hx = (SCREEN_WIDTH - hw) // 2
        hy = (SCREEN_HEIGHT - hh) // 2

        pygame.draw.rect(surface, COLOR_PANEL_BG, (hx, hy, hw, hh), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (hx, hy, hw, hh), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (hx + 4, hy + 4, hw - 8, hh - 8), 1, border_radius=10)

        surface.blit(get_font(20, bold=True).render("PANDUAN KONTROL & MEKANIKA GDD", True, COLOR_GOLD), (hx + 24, hy + 18))

        controls = [
            ("W / A / S / D", "Bergerak 8 arah (Top-Down)"),
            ("Shift Kiri (Tahan)", "Sprint (+40% Speed, 10 STA/s; 2x di lumpur)"),
            ("Mouse Kursor", "Membidik arah tebasan dan skill"),
            ("Klik Kiri (LMB)", "Serangan Pedang Ringan (5 STA, ditolak saat STA < 10)"),
            ("Klik Kanan (RMB)", "Skill Berat Ash Cleave (30 STA)"),
            ("Spasi", "Dodge Roll (15 STA) & Perfect Dodge Slow-Mo 1.5s"),
            ("Tombol [E]", "Interaksi NPC, Peta Aell, Vektor, Gael, Portal"),
            ("Tombol [B] / [I]", "Buka / Tutup Tas (Pakai potion / Equip senjata)"),
            ("Tombol [1] & [2]", "Gunakan Ramuan HP & Tonik Stamina Cepat"),
            ("Tombol [TAB] / [M]", "Minimap / Mute Audio"),
            ("Tombol [ESC] / [H]", "Tutup menu / Buka Bantuan ini"),
        ]

        c_font = get_font(13, bold=True)
        d_font = get_font(13)
        for idx, (ctrl, desc) in enumerate(controls):
            cy = hy + 60 + idx * 32
            surface.blit(c_font.render(ctrl, True, COLOR_GOLD), (hx + 28, cy))
            surface.blit(d_font.render(desc, True, COLOR_WHITE), (hx + 195, cy))

        close_txt = get_font(12, italic=True).render("[Tekan [H], [ESC], atau klik mana saja untuk kembali]", True, COLOR_TEXT_MUTED)
        surface.blit(close_txt, (hx + hw // 2 - close_txt.get_width() // 2, hy + hh - 30))

    def _draw_game_over(self, surface):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((25, 5, 5, 210))
        surface.blit(dim, (0, 0))

        gw, gh = 520, 260
        gx = (SCREEN_WIDTH - gw) // 2
        gy = (SCREEN_HEIGHT - gh) // 2

        pygame.draw.rect(surface, (28, 15, 18), (gx, gy, gw, gh), border_radius=12)
        pygame.draw.rect(surface, (180, 50, 50), (gx, gy, gw, gh), 2, border_radius=12)

        title = get_font(26, bold=True).render("KAU TELAH GUGUR...", True, (255, 80, 80))
        surface.blit(title, (gx + gw // 2 - title.get_width() // 2, gy + 30))

        sub_font = get_font(13)
        sub1 = sub_font.render("Nafas abu memadamkan kesadaranmu. Kau kembali ke Hub Rusty Anchor.", True, COLOR_WHITE)
        sub2 = sub_font.render("Konsekuensi GDD: kehilangan 30% Abu Monster & 50% material belum terjual.", True, (220, 180, 180))
        surface.blit(sub1, (gx + gw // 2 - sub1.get_width() // 2, gy + 85))
        surface.blit(sub2, (gx + gw // 2 - sub2.get_width() // 2, gy + 110))

        btn_rect = self.get_respawn_button_rect()
        pygame.draw.rect(surface, (160, 40, 40), btn_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 120, 120), btn_rect, 2, border_radius=8)

        btn_txt = get_font(15, bold=True).render("Bangkit di Api Unggun [R]", True, COLOR_WHITE)
        surface.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width() // 2, btn_rect.centery - btn_txt.get_height() // 2))
