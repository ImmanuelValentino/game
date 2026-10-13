"""
HUD & UI Manager untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mencakup status bar (HP/Stamina/EXP), currency tracker, hotbar quickslots, prompt interaksi, help overlay, dan game over modal.
"""
import math
import pygame
from src.config import (
    COLOR_HP, COLOR_HP_BG, COLOR_HP_TRAIL,
    COLOR_STAMINA, COLOR_STAMINA_BG,
    COLOR_EXP, COLOR_EXP_BG,
    COLOR_GOLD, COLOR_ASH,
    COLOR_WHITE, COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)

class UIManager:
    def __init__(self):
        self.show_help = False
        self.notification_text = ""
        self.notification_timer = 0.0

    def show_notification(self, text, duration=2.5):
        self.notification_text = text
        self.notification_timer = duration

    def update(self, dt):
        if self.notification_timer > 0:
            self.notification_timer = max(0.0, self.notification_timer - dt)

    def draw_hud(self, surface, player, combat_mgr, inventory, quest_mgr, nearby_npc=None):
        self._draw_status_bars(surface, player)
        self._draw_currency(surface, player)
        self._draw_quest_tracker(surface, quest_mgr)
        self._draw_hotbar(surface, player, combat_mgr, inventory)
        self._draw_interaction_prompt(surface, nearby_npc)
        self._draw_notification(surface)

        if self.show_help:
            self._draw_help_overlay(surface)

        if player.is_dead:
            self._draw_game_over(surface, player)

    def _draw_status_bars(self, surface, player):
        """Merender Level badge, Health Bar, Stamina Bar, dan EXP Bar di kiri atas."""
        start_x = 20
        start_y = 20

        # Background panel status
        panel_w = 290
        panel_h = 92
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (18, 20, 28, 210), (0, 0, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=10)
        surface.blit(panel_surf, (start_x, start_y))

        # Badge Level Ornate
        badge_cx = start_x + 36
        badge_cy = start_y + 36
        pygame.draw.circle(surface, (28, 30, 42), (badge_cx, badge_cy), 24)
        pygame.draw.circle(surface, COLOR_GOLD, (badge_cx, badge_cy), 24, 2)
        lvl_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        lvl_text = lvl_font.render(f"Lv.{player.level}", True, COLOR_GOLD)
        surface.blit(lvl_text, (badge_cx - lvl_text.get_width() // 2, badge_cy - lvl_text.get_height() // 2))

        # Posisi bar
        bx = start_x + 72
        bar_w = 196

        # 1. Health Bar
        by_hp = start_y + 14
        bar_h = 16
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, by_hp, bar_w, bar_h), border_radius=4)
        # Trail bar (animasi darah turun)
        trail_pct = max(0.0, min(1.0, player.hp_trail / player.max_hp))
        pygame.draw.rect(surface, COLOR_HP_TRAIL, (bx, by_hp, int(bar_w * trail_pct), bar_h), border_radius=4)
        # Actual HP
        hp_pct = max(0.0, min(1.0, player.hp / player.max_hp))
        pygame.draw.rect(surface, COLOR_HP, (bx, by_hp, int(bar_w * hp_pct), bar_h), border_radius=4)
        pygame.draw.rect(surface, (80, 25, 30), (bx, by_hp, bar_w, bar_h), 1, border_radius=4)

        font_num = pygame.font.SysFont("Segoe UI, Arial", 10, bold=True)
        hp_str = f"HP {player.hp}/{player.max_hp}"
        hp_txt = font_num.render(hp_str, True, COLOR_WHITE)
        surface.blit(hp_txt, (bx + (bar_w - hp_txt.get_width()) // 2, by_hp + 1))

        # 2. Stamina Bar
        by_st = start_y + 36
        st_h = 12
        pygame.draw.rect(surface, COLOR_STAMINA_BG, (bx, by_st, bar_w, st_h), border_radius=3)
        st_pct = max(0.0, min(1.0, player.stamina / player.max_stamina))
        pygame.draw.rect(surface, COLOR_STAMINA, (bx, by_st, int(bar_w * st_pct), st_h), border_radius=3)
        pygame.draw.rect(surface, (20, 60, 30), (bx, by_st, bar_w, st_h), 1, border_radius=3)

        st_str = f"ST {int(player.stamina)}/{player.max_stamina}"
        st_txt = font_num.render(st_str, True, COLOR_WHITE)
        surface.blit(st_txt, (bx + (bar_w - st_txt.get_width()) // 2, by_st - 1))

        # 3. EXP Bar
        by_exp = start_y + 54
        exp_h = 7
        pygame.draw.rect(surface, COLOR_EXP_BG, (bx, by_exp, bar_w, exp_h), border_radius=2)
        exp_pct = max(0.0, min(1.0, player.exp / player.exp_to_next)) if player.exp_to_next > 0 else 0
        pygame.draw.rect(surface, COLOR_EXP, (bx, by_exp, int(bar_w * exp_pct), exp_h), border_radius=2)
        pygame.draw.rect(surface, (70, 55, 15), (bx, by_exp, bar_w, exp_h), 1, border_radius=2)

        exp_label = font_num.render(f"EXP {player.exp}/{player.exp_to_next}", True, (220, 200, 140))
        surface.blit(exp_label, (bx, by_exp + 10))

    def _draw_currency(self, surface, player):
        """Merender counter Emas dan Abu Monster di kanan atas."""
        box_w = 250
        box_h = 44
        box_x = 1280 - box_w - 20
        box_y = 20

        surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 210), (0, 0, box_w, box_h), border_radius=8)
        pygame.draw.rect(surf, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), 1, border_radius=8)
        surface.blit(surf, (box_x, box_y))

        c_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        # Gold
        gold_icon_pos = (box_x + 18, box_y + 22)
        pygame.draw.circle(surface, COLOR_GOLD, gold_icon_pos, 7)
        pygame.draw.circle(surface, (180, 130, 20), gold_icon_pos, 7, 1)
        g_txt = c_font.render(f"{player.gold} Gold", True, COLOR_GOLD)
        surface.blit(g_txt, (box_x + 32, box_y + 12))

        # Ash
        ash_icon_pos = (box_x + 135, box_y + 22)
        pygame.draw.circle(surface, COLOR_ASH, ash_icon_pos, 7)
        pygame.draw.circle(surface, (100, 100, 115), ash_icon_pos, 7, 1)
        a_txt = c_font.render(f"{player.monster_ash} Ash", True, COLOR_ASH)
        surface.blit(a_txt, (box_x + 149, box_y + 12))

        # Tombol Bantuan [H]
        h_font = pygame.font.SysFont("Segoe UI, Arial", 11)
        h_surf = h_font.render("[H]: Kontrol / [M]: Mute", True, COLOR_TEXT_MUTED)
        surface.blit(h_surf, (box_x + box_w - h_surf.get_width() - 8, box_y + box_h + 6))

    def _draw_quest_tracker(self, surface, quest_mgr):
        """Menampilkan target quest aktif di atas tengah."""
        current_q = quest_mgr.get_current_quest()
        if not current_q:
            return

        q_text = f"🎯 {current_q.title} ({current_q.current_count}/{current_q.target_count})"
        font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
        rendered = font.render(q_text, True, COLOR_GOLD)

        box_w = rendered.get_width() + 28
        box_h = 32
        box_x = (1280 - box_w) // 2
        box_y = 20

        surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 200), (0, 0, box_w, box_h), border_radius=6)
        pygame.draw.rect(surf, (140, 115, 60), (0, 0, box_w, box_h), 1, border_radius=6)
        surface.blit(surf, (box_x, box_y))
        surface.blit(rendered, (box_x + 14, box_y + 6))

    def _draw_hotbar(self, surface, player, combat_mgr, inventory):
        """Merender hotbar skill dan quickslots di bawah tengah layar."""
        slot_w = 48
        slot_h = 48
        spacing = 10
        total_slots = 5
        bar_w = total_slots * slot_w + (total_slots - 1) * spacing + 20
        bar_h = 66
        bar_x = (1280 - bar_w) // 2
        bar_y = 720 - bar_h - 15

        surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 20, 28, 220), (0, 0, bar_w, bar_h), border_radius=10)
        pygame.draw.rect(surf, COLOR_PANEL_BORDER, (0, 0, bar_w, bar_h), 1, border_radius=10)
        surface.blit(surf, (bar_x, bar_y))

        k_font = pygame.font.SysFont("Segoe UI, Arial", 11, bold=True)
        cnt_font = pygame.font.SysFont("Segoe UI, Arial", 11, bold=True)

        slots_data = [
            {"key": "1", "name": "HP Potion", "count": inventory.get_count("hp_potion"), "cd": 0.0, "icon_color": (220, 50, 60)},
            {"key": "2", "name": "Stamina", "count": inventory.get_count("stamina_tonic"), "cd": 0.0, "icon_color": (40, 170, 70)},
            {"key": "LMB", "name": "Slash", "count": None, "cd": combat_mgr.attack_cd_timer / combat_mgr.attack_cooldown, "icon_color": (240, 190, 50)},
            {"key": "RMB", "name": "Ash Skill", "count": None, "cd": combat_mgr.skill_cd_timer / combat_mgr.skill_cooldown, "icon_color": (230, 80, 40)},
            {"key": "Space", "name": "Roll", "count": None, "cd": player.roll_cd_timer / player.roll_cooldown, "icon_color": (100, 170, 255)},
        ]

        for i, s in enumerate(slots_data):
            sx = bar_x + 10 + i * (slot_w + spacing)
            sy = bar_y + 9
            s_rect = pygame.Rect(sx, sy, slot_w, slot_h)

            pygame.draw.rect(surface, (30, 32, 45), s_rect, border_radius=6)
            pygame.draw.rect(surface, (60, 65, 85), s_rect, 1, border_radius=6)

            # Icon visual kecil di tengah
            pygame.draw.circle(surface, s["icon_color"], s_rect.center, 12)

            # Cooldown overlay jika ada
            if s["cd"] > 0:
                cd_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
                cd_h = int(slot_w * min(1.0, s["cd"]))
                pygame.draw.rect(cd_surf, (0, 0, 0, 170), (0, slot_h - cd_h, slot_w, cd_h), border_radius=6)
                surface.blit(cd_surf, (sx, sy))

            # Jumlah jika item
            if s["count"] is not None:
                c_text = cnt_font.render(str(s["count"]), True, COLOR_WHITE)
                surface.blit(c_text, (sx + slot_w - c_text.get_width() - 4, sy + slot_w - 15))

            # Label Hotkey
            k_text = k_font.render(s["key"], True, COLOR_GOLD)
            surface.blit(k_text, (sx + 4, sy + 3))

    def _draw_interaction_prompt(self, surface, nearby_npc):
        if not nearby_npc:
            return

        prompt_str = f"[E] Bicara dengan {nearby_npc.name}"
        if nearby_npc.name == "Api Unggun Oakhaven":
            prompt_str = "[E] Istirahat & Simpan Game"

        font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        text = font.render(prompt_str, True, COLOR_GOLD)

        pw = text.get_width() + 32
        ph = 36
        px = (1280 - pw) // 2
        py = 720 - 135

        psurf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(psurf, (18, 20, 28, 220), (0, 0, pw, ph), border_radius=8)
        pygame.draw.rect(psurf, COLOR_GOLD, (0, 0, pw, ph), 2, border_radius=8)
        surface.blit(psurf, (px, py))
        surface.blit(text, (px + 16, py + 8))

    def _draw_notification(self, surface):
        if self.notification_timer <= 0:
            return
        font = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        text = font.render(self.notification_text, True, COLOR_GOLD)
        nw = text.get_width() + 40
        nh = 40
        nx = (1280 - nw) // 2
        ny = 80

        nsurf = pygame.Surface((nw, nh), pygame.SRCALPHA)
        pygame.draw.rect(nsurf, (20, 22, 32, 230), (0, 0, nw, nh), border_radius=8)
        pygame.draw.rect(nsurf, COLOR_GOLD, (0, 0, nw, nh), 1, border_radius=8)
        surface.blit(nsurf, (nx, ny))
        surface.blit(text, (nx + 20, ny + 9))

    def _draw_help_overlay(self, surface):
        dim = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        hw = 540
        hh = 420
        hx = (1280 - hw) // 2
        hy = (720 - hh) // 2

        pygame.draw.rect(surface, COLOR_PANEL_BG, (hx, hy, hw, hh), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (hx, hy, hw, hh), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (hx + 4, hy + 4, hw - 8, hh - 8), 1, border_radius=10)

        t_font = pygame.font.SysFont("Segoe UI, Arial", 20, bold=True)
        title = t_font.render("PANDUAN KONTROL & SISTEM GAME", True, COLOR_GOLD)
        surface.blit(title, (hx + 24, hy + 20))

        controls = [
            ("W / A / S / D", "Bergerak 8 arah (Top-Down)"),
            ("Mouse Kursor", "Membidik arah tebasan dan skill"),
            ("Klik Kiri (LMB)", "Serangan Tebasan Pedang (Konsumsi 10 Stamina)"),
            ("Klik Kanan (RMB)", "Skill Area 'Ash Cleave' (Konsumsi 25 Stamina)"),
            ("Spasi / Shift Kiri", "Dodge Roll / Dash cepat dengan i-frame"),
            ("Tombol [E]", "Interaksi NPC, Api Unggun & Toko"),
            ("Tombol [B] / [I]", "Buka / Tutup Tas Penyintas (Backpack)"),
            ("Tombol [1] & [2]", "Gunakan Ramuan HP & Tonik Stamina Cepat"),
            ("Tombol [M]", "Mute / Unmute Musik & Suara"),
            ("Tombol [H]", "Buka / Tutup Panduan Bantuan ini"),
        ]

        c_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
        d_font = pygame.font.SysFont("Segoe UI, Arial", 13)

        start_y = hy + 65
        for idx, (ctrl, desc) in enumerate(controls):
            cy = start_y + idx * 30
            c_surf = c_font.render(ctrl, True, COLOR_GOLD)
            d_surf = d_font.render(desc, True, COLOR_WHITE)
            surface.blit(c_surf, (hx + 30, cy))
            surface.blit(d_surf, (hx + 175, cy))

        close_font = pygame.font.SysFont("Segoe UI, Arial", 12, italic=True)
        close_txt = close_font.render("[Tekan [H] atau [ESC] untuk kembali ke permainan]", True, COLOR_TEXT_MUTED)
        surface.blit(close_txt, (hx + hw // 2 - close_txt.get_width() // 2, hy + hh - 30))

    def _draw_game_over(self, surface, player):
        dim = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim.fill((25, 5, 5, 210))
        surface.blit(dim, (0, 0))

        gw = 520
        gh = 260
        gx = (1280 - gw) // 2
        gy = (720 - gh) // 2

        pygame.draw.rect(surface, (28, 15, 18), (gx, gy, gw, gh), border_radius=12)
        pygame.draw.rect(surface, (180, 50, 50), (gx, gy, gw, gh), 2, border_radius=12)

        t_font = pygame.font.SysFont("Segoe UI, Arial", 26, bold=True)
        title = t_font.render("KAU TELAH GUGUR...", True, (255, 80, 80))
        surface.blit(title, (gx + gw // 2 - title.get_width() // 2, gy + 30))

        sub_font = pygame.font.SysFont("Segoe UI, Arial", 13)
        sub1 = sub_font.render("Nafas abu memadamkan kesadaranmu di reruntuhan Oakhaven.", True, COLOR_WHITE)
        sub2 = sub_font.render("Sesuai aturan GDD, kau kehilangan 30% Abu Monster saat respawn.", True, (220, 180, 180))
        surface.blit(sub1, (gx + gw // 2 - sub1.get_width() // 2, gy + 85))
        surface.blit(sub2, (gx + gw // 2 - sub2.get_width() // 2, gy + 110))

        # Tombol Bangkit Kembali
        btn_rect = pygame.Rect(gx + gw // 2 - 140, gy + 165, 280, 48)
        pygame.draw.rect(surface, (160, 40, 40), btn_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 120, 120), btn_rect, 2, border_radius=8)

        b_font = pygame.font.SysFont("Segoe UI, Arial", 15, bold=True)
        btn_txt = b_font.render("Bangkit di Api Unggun [R]", True, COLOR_WHITE)
        surface.blit(btn_txt, (btn_rect.centerx - btn_txt.get_width() // 2, btn_rect.centery - btn_txt.get_height() // 2))
