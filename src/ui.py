"""
HUD & UI Manager untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menampilkan HP/Stamina/EXP, ATK/DEF/SKL/Weapon, Hazard & Slow-Mo badges,
Boss HP bar, minimap, prompt interaksi, help overlay, dan game over modal.
"""
import pygame
from src.config import (
    get_screen_size, STAGE_CONFIGS, get_font,
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
        self.show_minimap = True
        self.show_tutorial = True
        self.notification_text = ""
        self.notification_timer = 0.0

    def show_notification(self, text, duration=2.5):
        self.notification_text = text
        self.notification_timer = duration

    def update(self, dt):
        if self.notification_timer > 0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def get_respawn_button_rect(self):
        view_w, view_h = get_screen_size()
        gw, gh = 520, 260
        gx = (view_w - gw) // 2
        gy = (view_h - gh) // 2
        return pygame.Rect(gx + gw // 2 - 140, gy + 165, 280, 48)

    def get_tutorial_close_rect(self):
        _, view_h = get_screen_size()
        return pygame.Rect(20 + 258, view_h - 196, 22, 22)

    def _get_hotbar_geometry(self, view_size=None):
        view_w, view_h = view_size if view_size is not None else get_screen_size()
        slot_w, slot_h, spacing = 48, 48, 8
        item_slots = 4
        action_slots = 3
        divider_w = 12
        bar_w = (item_slots + action_slots) * slot_w + (item_slots + action_slots - 2) * spacing + divider_w + 22
        bar_h = 66
        bar_x = (view_w - bar_w) // 2
        bar_y = view_h - bar_h - 14
        return bar_x, bar_y, bar_w, bar_h, slot_w, slot_h, spacing, divider_w

    def get_hotbar_item_rects(self, view_size=None):
        bar_x, bar_y, _, _, slot_w, slot_h, spacing, _ = self._get_hotbar_geometry(view_size)
        return [
            (i, pygame.Rect(bar_x + 11 + i * (slot_w + spacing), bar_y + 9, slot_w, slot_h))
            for i in range(4)
        ]

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
        if self.show_tutorial:
            self._draw_tutorial_card(surface)
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
        """Menampilkan badge efek aktif (Buff Potion, Api Putih, Slow-Mo, Fatigue, Hazard)."""
        badges = []
        if getattr(player, "atk_boost_timer", 0.0) > 0:
            badges.append((f"ATK BOOST +50% ({player.atk_boost_timer:.0f}s)", (230, 100, 40)))
        if getattr(player, "def_boost_timer", 0.0) > 0:
            badges.append((f"DEF BOOST +18 ({player.def_boost_timer:.0f}s)", (65, 145, 230)))
        if getattr(player, "crit_boost_timer", 0.0) > 0:
            badges.append((f"CRIT FOCUS +35% ({player.crit_boost_timer:.0f}s)", (185, 85, 225)))
        if getattr(player, "in_white_fire", False):
            badges.append(("API PUTIH: MEMULIHKAN HP", (70, 170, 195)))
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
        view_w, _ = get_screen_size(surface)
        box_w, box_h = 300, 44
        box_x = view_w - box_w - 20
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
        h_surf = h_font.render("[F1]: Tutorial | [H]: Bantuan | [TAB]: Peta | [F11]: Layar", True, COLOR_WHITE)
        loc_name = STAGE_CONFIGS.get(current_map, {}).get("name", current_map)
        loc_surf = h_font.render(loc_name, True, COLOR_TEXT_ACCENT)
        info_w = max(h_surf.get_width(), loc_surf.get_width()) + 14
        info_box = pygame.Surface((info_w, 36), pygame.SRCALPHA)
        pygame.draw.rect(info_box, (14, 16, 24, 195), (0, 0, info_w, 36), border_radius=6)
        surface.blit(info_box, (box_x + box_w - info_w, box_y + box_h + 4))
        surface.blit(h_surf, (box_x + box_w - h_surf.get_width() - 6, box_y + box_h + 6))
        surface.blit(loc_surf, (box_x + box_w - loc_surf.get_width() - 6, box_y + box_h + 22))

    def _draw_quest_tracker(self, surface, quest_mgr):
        view_w, _ = get_screen_size(surface)
        current_q = quest_mgr.get_current_quest()
        q_text = f"{current_q.title} ({current_q.current_count}/{current_q.target_count})" if current_q else "Semua Quest Utama Selesai!"

        font = get_font(13, bold=True)
        rendered = font.render(q_text, True, COLOR_GOLD)

        box_w = min(view_w - 40, rendered.get_width() + 50)
        box_h = 32
        box_x = (view_w - box_w) // 2
        box_y = 20 if view_w >= 1060 else 142

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

        view_w, _ = get_screen_size(surface)
        bar_w, bar_h = min(500, view_w - 80), 16
        bx = (view_w - bar_w) // 2
        by = 62 if view_w >= 1060 else 182

        name_font = get_font(13, bold=True)
        n_surf = name_font.render(boss.name, True, (255, 115, 95))
        surface.blit(n_surf, (view_w // 2 - n_surf.get_width() // 2, by))

        ry = by + 20
        pygame.draw.rect(surface, (20, 12, 16), (bx - 2, ry - 2, bar_w + 4, bar_h + 4), border_radius=5)
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, ry, bar_w, bar_h), border_radius=4)
        pct = max(0.0, min(1.0, boss.hp / boss.max_hp))
        pygame.draw.rect(surface, (200, 40, 50), (bx, ry, int(bar_w * pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, COLOR_GOLD, (bx - 2, ry - 2, bar_w + 4, bar_h + 4), 1, border_radius=5)

    def _draw_hotbar(self, surface, player, combat_mgr, inventory):
        view_w, view_h = get_screen_size(surface)
        bar_x, bar_y, bar_w, bar_h, slot_w, slot_h, spacing, divider_w = self._get_hotbar_geometry((view_w, view_h))

        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 224), (0, 0, bar_w, bar_h), border_radius=10)
        pygame.draw.rect(surf, COLOR_PANEL_BORDER, (0, 0, bar_w, bar_h), 1, border_radius=10)
        surface.blit(surf, (bar_x, bar_y))

        k_font = get_font(10, bold=True)
        cnt_font = get_font(11, bold=True)

        # 1. Empat Kotak Slot Item Dinamis ([1]..[4]) dari Drop & Shop
        hotbar_entries = inventory.get_hotbar_entries() if hasattr(inventory, "get_hotbar_entries") else []
        for idx, key_lbl, item_obj, count in hotbar_entries:
            sx = bar_x + 11 + idx * (slot_w + spacing)
            sy = bar_y + 9
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)

            has_item = item_obj is not None and count > 0
            bg_col = (32, 36, 52) if has_item else (22, 24, 34)
            border_col = item_obj.get_rarity_color() if has_item else (55, 60, 78)
            pygame.draw.rect(surface, bg_col, s_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, s_rect, 1, border_radius=6)

            if item_obj and item_obj.icon_surf:
                icon = pygame.transform.scale(item_obj.icon_surf, (30, 30))
                if count <= 0:
                    icon = icon.copy()
                    icon.set_alpha(85)
                surface.blit(icon, (s_rect.centerx - 15, s_rect.centery - 14))

            if item_obj and count > 0:
                c_text = cnt_font.render(str(count), True, COLOR_WHITE)
                surface.blit(c_text, (s_rect.right - c_text.get_width() - 4, s_rect.bottom - 15))

            k_text = k_font.render(key_lbl, True, COLOR_GOLD)
            surface.blit(k_text, (s_rect.x + 4, s_rect.y + 3))

        # Pembatas antara slot item dan indikator skill tempur
        div_x = bar_x + 11 + 4 * (slot_w + spacing) - spacing // 2 + divider_w // 2
        pygame.draw.line(surface, (85, 80, 75), (div_x, bar_y + 12), (div_x, bar_y + bar_h - 12), 2)

        # 2. Indikator Serangan, Skill (30 STA), dan Dodge Roll
        action_start_x = div_x + divider_w // 2 + 4
        actions_data = [
            {"key": "LMB", "cd": combat_mgr.attack_cd_timer / combat_mgr.attack_cooldown, "icon_color": (240, 190, 50)},
            {"key": "RMB", "cd": combat_mgr.skill_cd_timer / combat_mgr.skill_cooldown, "icon_color": (230, 80, 40)},
            {"key": "Space", "cd": player.roll_cd_timer / player.roll_cooldown, "icon_color": (100, 170, 255)},
        ]
        for j, s in enumerate(actions_data):
            sx = action_start_x + j * (slot_w + spacing)
            sy = bar_y + 9
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)

            pygame.draw.rect(surface, (30, 32, 45), s_rect, border_radius=6)
            pygame.draw.rect(surface, (60, 65, 85), s_rect, 1, border_radius=6)
            pygame.draw.circle(surface, s["icon_color"], s_rect.center, 11)

            if s["cd"] > 0:
                cd_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
                cd_h = int(slot_w * min(1.0, s["cd"]))
                pygame.draw.rect(cd_surf, (0, 0, 0, 170), (0, slot_h - cd_h, slot_w, cd_h), border_radius=6)
                surface.blit(cd_surf, (sx, sy))

            k_text = k_font.render(s["key"], True, COLOR_GOLD)
            surface.blit(k_text, (sx + 4, sy + 3))

    def _draw_minimap_icon(self, surf, role, x, y):
        """Menggambar ikon penunjuk khusus yang intuitif pada minimap untuk tiap NPC/objek."""
        if role == "shop":  # Ikon Toko/Koin Emas
            pygame.draw.rect(surf, (245, 195, 45), (x - 4, y - 4, 8, 8), border_radius=2)
            pygame.draw.rect(surf, (40, 25, 10), (x - 4, y - 4, 8, 8), 1, border_radius=2)
            pygame.draw.line(surf, (255, 245, 180), (x, y - 2), (x, y + 2), 1)
        elif role == "skill":  # Ikon Bengkel Skill/Tempa (Berlian Biru-Cyan)
            pygame.draw.polygon(surf, (80, 200, 255), [(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)])
            pygame.draw.polygon(surf, (220, 248, 255), [(x, y - 5), (x + 5, y), (x, y + 5), (x - 5, y)], 1)
        elif role == "map":  # Ikon Peta / Kompas Aell
            pygame.draw.circle(surf, (95, 225, 165), (x, y), 4)
            pygame.draw.line(surf, (20, 50, 35), (x - 3, y), (x + 3, y), 1)
            pygame.draw.line(surf, (20, 50, 35), (x, y - 3), (x, y + 3), 1)
        elif role == "quest":  # Ikon Quest/Info Elara (!)
            pygame.draw.circle(surf, (255, 220, 65), (x, y), 5)
            pygame.draw.line(surf, (35, 20, 10), (x, y - 3), (x, y + 1), 2)
            surf.set_at((x, y + 3), (35, 20, 10))
        elif role == "bar":  # Ikon Kedai Brog
            pygame.draw.rect(surf, (225, 140, 50), (x - 3, y - 4, 6, 7), border_radius=1)
            pygame.draw.line(surf, (255, 235, 200), (x - 2, y - 4), (x + 2, y - 4), 1)
        elif role == "campfire":
            pygame.draw.polygon(surf, (255, 125, 35), [(x, y - 5), (x + 4, y + 4), (x - 4, y + 4)])
        elif role == "white_fire":  # Api Putih Regen HP di pojok dungeon
            pygame.draw.circle(surf, (195, 248, 255), (x, y), 5)
            pygame.draw.line(surf, (255, 255, 255), (x - 3, y), (x + 3, y), 1)
            pygame.draw.line(surf, (255, 255, 255), (x, y - 3), (x, y + 3), 1)
        elif role == "portal":
            pygame.draw.circle(surf, (175, 110, 255), (x, y), 5, 2)
            pygame.draw.circle(surf, (235, 210, 255), (x, y), 2)
        elif role in ("guard", "villager"):
            pygame.draw.circle(surf, (185, 195, 215), (x, y), 3)
        else:
            pygame.draw.circle(surf, COLOR_GOLD, (x, y), 3)

    def _draw_minimap(self, surface, player, map_loader, npcs, targets):
        view_w, _ = get_screen_size(surface)
        mm_size = 160
        mm_x = view_w - mm_size - 20
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

        roles_present = set()
        for npc in npcs:
            nx, ny = npc.get_center()
            role = getattr(npc, "map_role", "portal" if hasattr(npc, "target_map") else "npc")
            roles_present.add(role)
            self._draw_minimap_icon(mm_surf, role, int(nx * scale_x), int(ny * scale_y))

        has_boss = False
        has_enemy = False
        for t in targets:
            if t.is_alive():
                tx, ty = t.get_center()
                if getattr(t, "is_boss", False):
                    has_boss = True
                    bx, by = int(tx * scale_x), int(ty * scale_y)
                    pygame.draw.rect(mm_surf, (255, 55, 65), (bx - 4, by - 4, 8, 8))
                    pygame.draw.rect(mm_surf, COLOR_GOLD, (bx - 4, by - 4, 8, 8), 1)
                else:
                    has_enemy = True
                    pygame.draw.circle(mm_surf, (220, 95, 95), (int(tx * scale_x), int(ty * scale_y)), 2)

        px, py = int((player.x + 24) * scale_x), int((player.y + 24) * scale_y)
        pygame.draw.polygon(mm_surf, (95, 255, 130), [(px, py - 5), (px + 4, py + 4), (px - 4, py + 4)])
        pygame.draw.polygon(mm_surf, COLOR_WHITE, [(px, py - 5), (px + 4, py + 4), (px - 4, py + 4)], 1)

        pygame.draw.rect(mm_surf, COLOR_PANEL_BORDER_LIGHT, (0, 0, mm_size, mm_size), 2)
        surface.blit(mm_surf, (mm_x, mm_y))

        # Legenda Ikon Minimap Ringkas di bawah peta
        legend_items = []
        role_labels = [
            ("shop", "Toko Gael"),
            ("skill", "Skill Vektor"),
            ("map", "Peta Aell"),
            ("quest", "Quest/Info"),
            ("bar", "Kedai Brog"),
            ("white_fire", "Api Putih (+HP)"),
            ("portal", "Portal"),
        ]
        for r_key, r_txt in role_labels:
            if r_key in roles_present:
                legend_items.append((r_key, r_txt))
        if has_boss:
            legend_items.append(("boss", "Bos Domain"))
        elif has_enemy:
            legend_items.append(("enemy", "Musuh"))

        if legend_items:
            l_font = get_font(10)
            row_h = 15
            leg_h = len(legend_items) * row_h + 10
            leg_surf = pygame.Surface((mm_size, leg_h), pygame.SRCALPHA)
            pygame.draw.rect(leg_surf, (16, 18, 26, 200), (0, 0, mm_size, leg_h), border_radius=6)
            pygame.draw.rect(leg_surf, COLOR_PANEL_BORDER, (0, 0, mm_size, leg_h), 1, border_radius=6)
            for idx, (rk, rtxt) in enumerate(legend_items):
                ly = 11 + idx * row_h
                if rk == "boss":
                    pygame.draw.rect(leg_surf, (255, 55, 65), (9, ly - 4, 8, 8))
                    pygame.draw.rect(leg_surf, COLOR_GOLD, (9, ly - 4, 8, 8), 1)
                elif rk == "enemy":
                    pygame.draw.circle(leg_surf, (220, 95, 95), (13, ly), 3)
                else:
                    self._draw_minimap_icon(leg_surf, rk, 13, ly)
                leg_surf.blit(l_font.render(rtxt, True, COLOR_WHITE), (26, ly - 6))
            surface.blit(leg_surf, (mm_x, mm_y + mm_size + 6))

    def _draw_tutorial_card(self, surface):
        """Panduan tutorial & kontrol ringkas di sudut kiri bawah (toggle [F1])."""
        _, view_h = get_screen_size(surface)
        cw, ch = 285, 166
        cx, cy = 20, view_h - ch - 20

        card = pygame.Surface((cw, ch), pygame.SRCALPHA)
        pygame.draw.rect(card, (16, 18, 28, 215), (0, 0, cw, ch), border_radius=9)
        pygame.draw.rect(card, COLOR_PANEL_BORDER_LIGHT, (0, 0, cw, ch), 1, border_radius=9)
        surface.blit(card, (cx, cy))

        t_font = get_font(11, bold=True)
        surface.blit(t_font.render("TUTORIAL & KONTROL [F1]", True, COLOR_GOLD), (cx + 10, cy + 7))
        surface.blit(t_font.render("X", True, (225, 90, 90)), (cx + cw - 19, cy + 7))

        b_font = get_font(10)
        tips = [
            ("WASD + Shift", "Bergerak & Sprint | [E] Interaksi NPC"),
            ("LMB / RMB", "Tebasan (5 STA) & Ash Cleave (30 STA)"),
            ("Spasi", "Dodge Roll (15 STA) / Slow-Mo"),
            ("Tombol 1-4", "Pakai Item/Boost di Kotak Bawah"),
            ("TAB / F11", "Ikon Peta NPC & Layar Penuh"),
            ("Api Putih", "Dekati Api Putih di sudut Dungeon (+HP)"),
        ]
        for idx, (k, d) in enumerate(tips):
            ry = cy + 28 + idx * 22
            surface.blit(b_font.render(k, True, COLOR_TEXT_ACCENT), (cx + 10, ry))
            surface.blit(b_font.render(d, True, COLOR_WHITE), (cx + 88, ry))

    def _draw_interaction_prompt(self, surface, nearby_npc):
        if not nearby_npc:
            return
        if getattr(nearby_npc, "map_role", "") == "white_fire":
            prompt_str = "Api Putih: Berdiri di dalam aura untuk regenerasi HP"
        elif hasattr(nearby_npc, "target_map"):
            prompt_str = f"[E] {nearby_npc.name}"
        elif nearby_npc.name == "Api Unggun Oakhaven":
            prompt_str = "[E] Istirahat & Simpan Game"
        else:
            prompt_str = f"[E] Bicara dengan {nearby_npc.name}"

        view_w, view_h = get_screen_size(surface)
        font = get_font(14, bold=True)
        text = font.render(prompt_str, True, COLOR_GOLD)
        pw, ph = text.get_width() + 32, 36
        px = (view_w - pw) // 2
        py = view_h - 135

        psurf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(psurf, (18, 20, 28, 220), (0, 0, pw, ph), border_radius=8)
        pygame.draw.rect(psurf, COLOR_GOLD, (0, 0, pw, ph), 2, border_radius=8)
        surface.blit(psurf, (px, py))
        surface.blit(text, (px + 16, py + 8))

    def _draw_notification(self, surface):
        if self.notification_timer <= 0:
            return
        view_w, _ = get_screen_size(surface)
        font = get_font(16, bold=True)
        text = font.render(self.notification_text, True, COLOR_GOLD)
        nw, nh = text.get_width() + 40, 40
        nx = (view_w - nw) // 2
        ny = 98

        nsurf = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(nsurf, (20, 22, 32, 230), (0, 0, nw, nh), border_radius=8)
        pygame.draw.rect(nsurf, COLOR_GOLD, (0, 0, nw, nh), 1, border_radius=8)
        surface.blit(nsurf, (nx, ny))
        surface.blit(text, (nx + 20, ny + 9))

    def _draw_help_overlay(self, surface):
        view_w, view_h = get_screen_size(surface)
        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        hw, hh = min(640, view_w - 40), min(500, view_h - 40)
        hx = (view_w - hw) // 2
        hy = (view_h - hh) // 2

        pygame.draw.rect(surface, COLOR_PANEL_BG, (hx, hy, hw, hh), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (hx, hy, hw, hh), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (hx + 4, hy + 4, hw - 8, hh - 8), 1, border_radius=10)

        surface.blit(get_font(20, bold=True).render("PANDUAN KONTROL & MEKANIKA", True, COLOR_GOLD), (hx + 24, hy + 18))

        controls = [
            ("W / A / S / D", "Bergerak 8 arah (Top-Down)"),
            ("Shift Kiri (Tahan)", "Sprint (+40% Speed, 10 STA/s; 2x di lumpur)"),
            ("Mouse Kursor", "Membidik arah tebasan dan skill"),
            ("Klik Kiri (LMB)", "Serangan Pedang Ringan (5 STA, ditolak saat STA < 10)"),
            ("Klik Kanan (RMB)", "Skill Berat Ash Cleave (30 STA)"),
            ("Spasi", "Dodge Roll (15 STA) & Perfect Dodge Slow-Mo 1.5s"),
            ("Tombol [E]", "Interaksi NPC, Peta Aell, Vektor, Gael, Portal"),
            ("Tombol [B] / [I]", "Buka / Tutup Tas (Pakai potion / Equip senjata)"),
            ("Tombol [1] - [4]", "Pakai Item/Boost di Kotak Hotbar Bawah (atau klik)"),
            ("Tombol [TAB] / [F1]", "Ikon Minimap & Legenda / Tutorial Cepat"),
            ("F11 / Alt+Enter", "Layar Penuh <-> Normal (Tepi/Maximize bisa ditarik)"),
            ("Tombol [ESC] / [H]", "Tutup menu / Buka Bantuan ini"),
        ]

        c_font = get_font(13, bold=True)
        d_font = get_font(13)
        for idx, (ctrl, desc) in enumerate(controls):
            cy = hy + 56 + idx * 31
            surface.blit(c_font.render(ctrl, True, COLOR_GOLD), (hx + 28, cy))
            surface.blit(d_font.render(desc, True, COLOR_WHITE), (hx + 195, cy))

        close_txt = get_font(12, italic=True).render("[Tekan [H], [ESC], atau klik mana saja untuk kembali]", True, COLOR_TEXT_MUTED)
        surface.blit(close_txt, (hx + hw // 2 - close_txt.get_width() // 2, hy + hh - 28))

    def _draw_game_over(self, surface):
        view_w, view_h = get_screen_size(surface)
        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((25, 5, 5, 210))
        surface.blit(dim, (0, 0))

        gw, gh = 520, 260
        gx = (view_w - gw) // 2
        gy = (view_h - gh) // 2

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
