"""
Sistem Toko & Penukaran Abu untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mencakup:
1. Toko Pedagang Misterius (Beli upgrade stat & item)
2. Meja Penukaran Brog (Tukar Monster Ash -> Gold)
"""
import pygame
from src.config import (
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_ASH, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)
from src.audio import audio_manager

class ShopManager:
    def __init__(self):
        self.is_merchant_open = False
        self.is_brog_open = False

        # Daftar Barang Toko Pedagang Misterius
        self.merchant_goods = [
            {
                "id": "hp_potion",
                "name": "Ramuan Pemulih HP",
                "desc": "Memulihkan 50 HP seketika.",
                "cost": 20,
                "type": "item",
                "count": 1,
            },
            {
                "id": "stamina_tonic",
                "name": "Tonik Stamina",
                "desc": "Memulihkan 50 Stamina seketika.",
                "cost": 15,
                "type": "item",
                "count": 1,
            },
            {
                "id": "whetstone_up",
                "name": "Asah Senjata (+5 ATK)",
                "desc": "Meningkatkan damage tebasan secara permanen.",
                "cost": 60,
                "type": "upgrade_atk",
                "val": 5,
            },
            {
                "id": "vitality_up",
                "name": "Cincin Vitalitas (+25 Max HP)",
                "desc": "Meningkatkan batas maksimal nyawa.",
                "cost": 80,
                "type": "upgrade_hp",
                "val": 25,
            },
            {
                "id": "boots_up",
                "name": "Sepatu Bayangan (+15% Speed)",
                "desc": "Meningkatkan kecepatan pergerakan karakter.",
                "cost": 75,
                "type": "upgrade_speed",
                "val": 26.0,
            },
            {
                "id": "armor_up",
                "name": "Tempa Zirah (+2 Armor)",
                "desc": "Mengurangi setiap damage yang diterima.",
                "cost": 90,
                "type": "upgrade_armor",
                "val": 2,
            },
        ]

    def open_merchant(self):
        self.is_merchant_open = True
        self.is_brog_open = False
        audio_manager.play_sound("accept")

    def open_brog(self):
        self.is_brog_open = True
        self.is_merchant_open = False
        audio_manager.play_sound("accept")

    def close_all(self):
        if self.is_merchant_open or self.is_brog_open:
            audio_manager.play_sound("cancel")
        self.is_merchant_open = False
        self.is_brog_open = False

    def is_active(self):
        return self.is_merchant_open or self.is_brog_open

    def handle_click(self, mouse_pos, player, inventory, combat_mgr=None):
        if self.is_merchant_open:
            return self._handle_merchant_click(mouse_pos, player, inventory, combat_mgr)
        elif self.is_brog_open:
            return self._handle_brog_click(mouse_pos, player, combat_mgr)
        return False

    def _handle_merchant_click(self, mouse_pos, player, inventory, combat_mgr):
        panel_w = 560
        panel_h = 510
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        # Tombol [X]
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 16, 24, 24)
        if close_rect.collidepoint(mouse_pos):
            self.close_all()
            return True

        # Klik tombol Beli tiap item
        start_y = panel_y + 80
        row_h = 62
        for idx, item in enumerate(self.merchant_goods):
            ry = start_y + idx * row_h
            buy_btn = pygame.Rect(panel_x + panel_w - 110, ry + 12, 85, 34)

            if buy_btn.collidepoint(mouse_pos):
                cost = item["cost"]
                if player.gold >= cost:
                    player.gold -= cost
                    audio_manager.play_sound("gold")
                    audio_manager.play_sound("powerup")

                    # Terapkan efek pembelian
                    if item["type"] == "item":
                        inventory.add_item(item["id"], item["count"])
                    elif item["type"] == "upgrade_atk":
                        player.bonus_damage += item["val"]
                    elif item["type"] == "upgrade_hp":
                        player.max_hp += item["val"]
                        player.hp += item["val"]
                    elif item["type"] == "upgrade_speed":
                        player.speed_bonus += item["val"]
                    elif item["type"] == "upgrade_armor":
                        player.armor += item["val"]

                    if combat_mgr:
                        combat_mgr.floating_texts.append(
                            combat_mgr.FloatingText(player.x + 24, player.y - 25, f"Beli {item['name']}!", COLOR_GOLD)
                        )
                else:
                    audio_manager.play_sound("cancel")
                    if combat_mgr:
                        combat_mgr.floating_texts.append(
                            combat_mgr.FloatingText(player.x + 24, player.y - 25, "Emas Tidak Cukup!", (240, 80, 80))
                        )
                return True

        return False

    def _handle_brog_click(self, mouse_pos, player, combat_mgr):
        panel_w = 460
        panel_h = 340
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        # Tombol [X]
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 16, 24, 24)
        if close_rect.collidepoint(mouse_pos):
            self.close_all()
            return True

        # Tombol 1: Tukar 10 Abu -> 25 Emas
        btn1 = pygame.Rect(panel_x + 40, panel_y + 140, 380, 48)
        if btn1.collidepoint(mouse_pos):
            if player.monster_ash >= 10:
                player.monster_ash -= 10
                player.gold += 25
                audio_manager.play_sound("coin")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 25, "+25 Gold!", COLOR_GOLD)
                    )
            else:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 25, "Abu Monster Kurang! (Butuh 10)", (240, 80, 80))
                    )
            return True

        # Tombol 2: Tukar Semua Abu (rate: 2.5 gold per ash)
        btn2 = pygame.Rect(panel_x + 40, panel_y + 205, 380, 48)
        if btn2.collidepoint(mouse_pos):
            if player.monster_ash > 0:
                gold_gained = int(player.monster_ash * 2.5)
                used_ash = player.monster_ash
                player.monster_ash = 0
                player.gold += gold_gained
                audio_manager.play_sound("coin")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 25, f"+{gold_gained} Gold! (Tukar {used_ash} Abu)", COLOR_GOLD)
                    )
            else:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 25, "Tidak ada Abu Monster!", (240, 80, 80))
                    )
            return True

        return False

    def draw(self, surface, mouse_pos, player):
        if self.is_merchant_open:
            self._draw_merchant_ui(surface, mouse_pos, player)
        elif self.is_brog_open:
            self._draw_brog_ui(surface, mouse_pos, player)

    def _draw_merchant_ui(self, surface, mouse_pos, player):
        panel_w = 560
        panel_h = 510
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        # Dim background
        dim = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        # Panel frame
        pygame.draw.rect(surface, COLOR_PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 1, border_radius=10)

        # Header
        t_font = pygame.font.SysFont("Segoe UI, Arial", 20, bold=True)
        title = t_font.render("TOKO PEDAGANG MISTERIUS", True, COLOR_GOLD)
        surface.blit(title, (panel_x + 24, panel_y + 18))

        sub_font = pygame.font.SysFont("Segoe UI, Arial", 12, italic=True)
        sub = sub_font.render("\"Kekuatan memiliki harga, penyintas... Apakah kau sanggup membayarnya?\"", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (panel_x + 24, panel_y + 46))

        # Close [X]
        c_font = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (panel_x + panel_w - 30, panel_y + 16))

        # Daftar Barang
        start_y = panel_y + 78
        row_h = 62
        name_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        desc_font = pygame.font.SysFont("Segoe UI, Arial", 11)
        btn_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)

        for idx, item in enumerate(self.merchant_goods):
            ry = start_y + idx * row_h
            r_rect = pygame.Rect(panel_x + 20, ry, panel_w - 40, 56)

            is_hover = r_rect.collidepoint(mouse_pos)
            bg_col = (32, 34, 48) if is_hover else (24, 26, 36)
            pygame.draw.rect(surface, bg_col, r_rect, border_radius=8)
            pygame.draw.rect(surface, (50, 55, 75), r_rect, 1, border_radius=8)

            # Nama & Deskripsi
            n_surf = name_font.render(item["name"], True, COLOR_WHITE)
            d_surf = desc_font.render(item["desc"], True, COLOR_TEXT_MUTED)
            surface.blit(n_surf, (panel_x + 32, ry + 8))
            surface.blit(d_surf, (panel_x + 32, ry + 30))

            # Tombol Beli
            buy_btn = pygame.Rect(panel_x + panel_w - 110, ry + 12, 85, 34)
            can_afford = player.gold >= item["cost"]
            b_hover = buy_btn.collidepoint(mouse_pos)

            btn_bg = (160, 120, 30) if can_afford else (60, 60, 70)
            if b_hover and can_afford:
                btn_bg = (200, 150, 40)
            pygame.draw.rect(surface, btn_bg, buy_btn, border_radius=6)
            pygame.draw.rect(surface, COLOR_GOLD if can_afford else (90, 90, 100), buy_btn, 1, border_radius=6)

            cost_text = btn_font.render(f"{item['cost']} G", True, COLOR_WHITE)
            surface.blit(cost_text, (buy_btn.centerx - cost_text.get_width() // 2, buy_btn.centery - cost_text.get_height() // 2))

        # Footer Emas Pemain
        foot_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        g_text = foot_font.render(f"Emas Tersedia: {player.gold} Gold", True, COLOR_GOLD)
        surface.blit(g_text, (panel_x + 30, panel_y + panel_h - 35))

    def _draw_brog_ui(self, surface, mouse_pos, player):
        panel_w = 460
        panel_h = 340
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        dim = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, COLOR_PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 1, border_radius=10)

        t_font = pygame.font.SysFont("Segoe UI, Arial", 19, bold=True)
        title = t_font.render("MEJA BAR BROG (PENUKARAN ABU)", True, COLOR_GOLD)
        surface.blit(title, (panel_x + 24, panel_y + 18))

        sub_font = pygame.font.SysFont("Segoe UI, Arial", 12, italic=True)
        sub = sub_font.render("\"Bawa abu monster Karak itu ke sini, akan ku bayar mahal dengan koin emas!\"", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (panel_x + 24, panel_y + 48))

        # Close [X]
        c_font = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (panel_x + panel_w - 30, panel_y + 16))

        # Info Status Pemain
        s_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        ash_info = s_font.render(f"Abu Monster: {player.monster_ash} Ash", True, COLOR_ASH)
        gold_info = s_font.render(f"Emas: {player.gold} Gold", True, COLOR_GOLD)
        surface.blit(ash_info, (panel_x + 40, panel_y + 90))
        surface.blit(gold_info, (panel_x + 260, panel_y + 90))

        # Tombol 1: Tukar 10 Abu -> 25 Emas
        btn1 = pygame.Rect(panel_x + 40, panel_y + 135, 380, 52)
        b1_hover = btn1.collidepoint(mouse_pos)
        can_10 = player.monster_ash >= 10
        b1_col = (40, 90, 50) if can_10 else (50, 50, 60)
        if b1_hover and can_10:
            b1_col = (50, 120, 65)
        pygame.draw.rect(surface, b1_col, btn1, border_radius=8)
        pygame.draw.rect(surface, (100, 180, 120) if can_10 else (80, 80, 90), btn1, 2, border_radius=8)

        btn_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        t1 = btn_font.render("Tukar 10 Abu Monster  ➔  25 Emas", True, COLOR_WHITE if can_10 else COLOR_TEXT_MUTED)
        surface.blit(t1, (btn1.centerx - t1.get_width() // 2, btn1.centery - t1.get_height() // 2))

        # Tombol 2: Tukar SEMUA Abu
        btn2 = pygame.Rect(panel_x + 40, panel_y + 205, 380, 52)
        b2_hover = btn2.collidepoint(mouse_pos)
        can_all = player.monster_ash > 0
        b2_col = (130, 85, 25) if can_all else (50, 50, 60)
        if b2_hover and can_all:
            b2_col = (170, 110, 35)
        pygame.draw.rect(surface, b2_col, btn2, border_radius=8)
        pygame.draw.rect(surface, COLOR_GOLD if can_all else (80, 80, 90), btn2, 2, border_radius=8)

        total_value = int(player.monster_ash * 2.5)
        t2 = btn_font.render(f"Tukar SEMUA Abu ({player.monster_ash} Ash)  ➔  +{total_value} Emas", True, COLOR_WHITE if can_all else COLOR_TEXT_MUTED)
        surface.blit(t2, (btn2.centerx - t2.get_width() // 2, btn2.centery - t2.get_height() // 2))

        hint_font = pygame.font.SysFont("Segoe UI, Arial", 11)
        h_text = hint_font.render("[Klik tombol untuk menukar abu / [ESC] atau [E] untuk tutup]", True, COLOR_TEXT_MUTED)
        surface.blit(h_text, (panel_x + panel_w // 2 - h_text.get_width() // 2, panel_y + panel_h - 32))
