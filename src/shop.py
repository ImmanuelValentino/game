"""
Sistem Toko Senjata Gael, Bengkel Skill Vektor, dan Penukaran Abu Brog.
Mengimplementasikan sistem ekonomi & Karma GDD:
1. Gael (Former Adventurer & Pedagang Senjata): Ramuan, Armor, Senjata, & Pedang Haus Darah (-50 Karma)
2. Vektor (Guildmaster & Bengkel Skill): Jual material monster -> Gold & SKL, latih skill, tempa Bilah Penebusan (+Karma)
3. Brog (Barman Rusty Anchor): Tukar Abu Monster -> Gold
"""
import pygame
from src.config import (
    get_screen_size, get_font,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_ASH, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)
from src.audio import audio_manager
from src.combat import FloatingText


class ShopManager:
    def __init__(self):
        self.is_merchant_open = False
        self.is_brog_open = False
        self.is_vektor_open = False

        # Daftar Barang Toko Gael (Pedagang Senjata, Ramuan, & Boost)
        self.merchant_goods = [
            {
                "id": "hp_potion",
                "name": "Ramuan Pemulih HP",
                "desc": "Pulihkan 80 HP instan (Hotbar).",
                "cost": 20,
                "type": "item",
                "count": 1,
            },
            {
                "id": "stamina_tonic",
                "name": "Tonik Stamina",
                "desc": "Pulihkan 60 STA instan (Hotbar).",
                "cost": 15,
                "type": "item",
                "count": 1,
            },
            {
                "id": "attack_boost_potion",
                "name": "Ramuan Amarah (ATK+)",
                "desc": "+50% Attack Power selama 15 detik.",
                "cost": 35,
                "type": "item",
                "count": 1,
            },
            {
                "id": "defense_potion",
                "name": "Ramuan Zirah (DEF+)",
                "desc": "+18 DEF selama 20 detik.",
                "cost": 30,
                "type": "item",
                "count": 1,
            },
            {
                "id": "crit_elixir",
                "name": "Eliksir Fokus (Crit+)",
                "desc": "+35% Crit Chance selama 20 detik.",
                "cost": 40,
                "type": "item",
                "count": 1,
            },
            {
                "id": "armor_up",
                "name": "Pelindung Zirah (+4 DEF)",
                "desc": "Kurangi damage musuh permanen.",
                "cost": 70,
                "type": "upgrade_armor",
                "val": 4,
            },
            {
                "id": "boots_up",
                "name": "Sepatu Bayangan (+26 SPD)",
                "desc": "Kecepatan gerak & dodge lincah.",
                "cost": 65,
                "type": "upgrade_speed",
                "val": 26.0,
            },
            {
                "id": "redemption_blade_1",
                "name": "Bilah Penebusan +1",
                "desc": "ATK +115, +10 Karma Good Ending.",
                "cost": 120,
                "type": "weapon",
                "karma": 10,
            },
            {
                "id": "bloodthirst_blade",
                "name": "Pedang Haus Darah",
                "desc": "ATK +320, Drop x1.5, -50 Karma.",
                "cost": 220,
                "type": "weapon",
                "karma": -50,
            },
        ]

    def open_merchant(self):
        self.is_merchant_open = True
        self.is_brog_open = False
        self.is_vektor_open = False
        audio_manager.play_sound("accept")

    open_gael = open_merchant

    def open_brog(self):
        self.is_brog_open = True
        self.is_merchant_open = False
        self.is_vektor_open = False
        audio_manager.play_sound("accept")

    def open_vektor(self):
        self.is_vektor_open = True
        self.is_merchant_open = False
        self.is_brog_open = False
        audio_manager.play_sound("accept")

    def close_all(self):
        if self.is_active():
            audio_manager.play_sound("cancel")
        self.is_merchant_open = False
        self.is_brog_open = False
        self.is_vektor_open = False

    def is_active(self):
        return self.is_merchant_open or self.is_brog_open or self.is_vektor_open

    def handle_click(self, mouse_pos, player, inventory, combat_mgr=None, quest_mgr=None):
        if self.is_merchant_open:
            return self._handle_merchant_click(mouse_pos, player, inventory, combat_mgr, quest_mgr)
        if self.is_brog_open:
            return self._handle_brog_click(mouse_pos, player, combat_mgr, quest_mgr)
        if self.is_vektor_open:
            return self._handle_vektor_click(mouse_pos, player, inventory, combat_mgr, quest_mgr)
        return False

    def _get_merchant_layout(self):
        view_w, view_h = get_screen_size()
        cols = 2
        num_rows = (len(self.merchant_goods) + cols - 1) // cols
        panel_w = min(780, view_w - 40)
        panel_h = min(500, 128 + num_rows * 66)
        panel_x = (view_w - panel_w) // 2
        panel_y = (view_h - panel_h) // 2
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 16, 24, 24)
        start_y = panel_y + 78
        gap_x = 12
        card_w = (panel_w - 40 - gap_x) // cols
        row_h = 64
        rows = []
        for idx, item in enumerate(self.merchant_goods):
            col_i = idx % cols
            row_i = idx // cols
            rx = panel_x + 20 + col_i * (card_w + gap_x)
            ry = start_y + row_i * row_h
            row_rect = pygame.Rect(rx, ry, card_w, 56)
            buy_btn = pygame.Rect(rx + card_w - 78, ry + 11, 68, 34)
            rows.append((item, row_rect, buy_btn))
        return panel_x, panel_y, panel_w, panel_h, close_rect, rows

    def _get_brog_layout(self):
        view_w, view_h = get_screen_size()
        panel_w = min(460, view_w - 40)
        panel_h = min(340, view_h - 40)
        panel_x = (view_w - panel_w) // 2
        panel_y = (view_h - panel_h) // 2
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 16, 24, 24)
        btn1 = pygame.Rect(panel_x + 40, panel_y + 135, panel_w - 80, 52)
        btn2 = pygame.Rect(panel_x + 40, panel_y + 205, panel_w - 80, 52)
        return panel_x, panel_y, panel_w, panel_h, close_rect, btn1, btn2

    def _get_vektor_layout(self):
        view_w, view_h = get_screen_size()
        panel_w = min(590, view_w - 40)
        panel_h = min(490, view_h - 40)
        panel_x = (view_w - panel_w) // 2
        panel_y = (view_h - panel_h) // 2
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 16, 24, 24)
        sell_btn = pygame.Rect(panel_x + 24, panel_y + 108, panel_w - 48, 48)
        skill_btns = [
            pygame.Rect(panel_x + 24, panel_y + 178 + idx * 62, panel_w - 48, 52)
            for idx in range(4)
        ]
        return panel_x, panel_y, panel_w, panel_h, close_rect, sell_btn, skill_btns

    def _handle_merchant_click(self, mouse_pos, player, inventory, combat_mgr, quest_mgr=None):
        _, _, _, _, close_rect, rows = self._get_merchant_layout()

        if close_rect.collidepoint(mouse_pos):
            self.close_all()
            return True

        for item, _, buy_btn in rows:
            if not buy_btn.collidepoint(mouse_pos):
                continue

            cost = item["cost"]
            if player.gold < cost:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Emas Tidak Cukup!", (240, 80, 80))
                    )
                return True

            if item["type"] in ("item", "weapon") and not inventory.can_add_item(item["id"], item.get("count", 1)):
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Tas Penuh!", (240, 140, 60))
                    )
                return True

            if item["type"] == "weapon" and inventory.get_count(item["id"]) > 0:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Senjata Sudah Dimiliki!", (240, 180, 60))
                    )
                return True

            if item["type"] == "upgrade_speed" and player.speed_bonus >= 130.0:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Kecepatan Maksimal!", (240, 180, 60))
                    )
                return True

            if item["type"] == "upgrade_armor" and player.bonus_def >= 60:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Zirah Maksimal!", (240, 180, 60))
                    )
                return True

            player.gold -= cost
            audio_manager.play_sound("gold")
            audio_manager.play_sound("powerup")

            if item["type"] == "item":
                inventory.add_item(item["id"], item["count"])
            elif item["type"] == "weapon":
                inventory.add_item(item["id"], 1)
                player.equip_weapon(item["id"])
                player.karma += item.get("karma", 0)
            elif item["type"] == "upgrade_speed":
                player.speed_bonus += item["val"]
            elif item["type"] == "upgrade_armor":
                player.bonus_def += item["val"]

            if combat_mgr:
                combat_mgr.floating_texts.append(
                    FloatingText(player.x + 24, player.y - 25, f"Beli {item['name']}!", COLOR_GOLD)
                )
            if quest_mgr:
                quest_mgr.advance_progress("q3_supplies", 1, player, combat_mgr)
            return True

        return False

    def _handle_brog_click(self, mouse_pos, player, combat_mgr, quest_mgr=None):
        _, _, _, _, close_rect, btn1, btn2 = self._get_brog_layout()

        if close_rect.collidepoint(mouse_pos):
            self.close_all()
            return True

        if btn1.collidepoint(mouse_pos):
            if player.monster_ash >= 10:
                player.monster_ash -= 10
                player.gold += 25
                audio_manager.play_sound("coin")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "+25 Gold!", COLOR_GOLD)
                    )
                if quest_mgr:
                    quest_mgr.advance_progress("q3_supplies", 1, player, combat_mgr)
            else:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Abu Monster Kurang! (Butuh 10)", (240, 80, 80))
                    )
            return True

        if btn2.collidepoint(mouse_pos):
            if player.monster_ash > 0:
                gold_gained = max(1, int(player.monster_ash * 2.5))
                used_ash = player.monster_ash
                player.monster_ash = 0
                player.gold += gold_gained
                audio_manager.play_sound("coin")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, f"+{gold_gained} Gold! ({used_ash} Ash)", COLOR_GOLD)
                    )
                if quest_mgr:
                    quest_mgr.advance_progress("q3_supplies", 1, player, combat_mgr)
            else:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Tidak ada Abu Monster!", (240, 80, 80))
                    )
            return True

        return False

    def _handle_vektor_click(self, mouse_pos, player, inventory, combat_mgr, quest_mgr=None):
        _, _, _, _, close_rect, sell_btn, skill_btns = self._get_vektor_layout()

        if close_rect.collidepoint(mouse_pos):
            self.close_all()
            return True

        if sell_btn.collidepoint(mouse_pos):
            cnt, gold_gained, skl_gained = inventory.sell_all_materials(player)
            if cnt > 0:
                audio_manager.play_sound("coin")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, f"+{gold_gained}G & +{skl_gained} SKL!", COLOR_GOLD, is_crit=True)
                    )
                if quest_mgr:
                    quest_mgr.advance_progress("q3_supplies", 1, player, combat_mgr)
            else:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, "Tidak ada material di tas!", (240, 140, 90))
                    )
            return True

        # Skill training & tempa Bilah Penebusan (+Karma)
        actions = [
            ("power", 1, 0, "Kekuatan Tebasan +12 ATK"),
            ("stamina", 1, 0, "Ketahanan +15 Max STA & +2.5 Regen"),
            ("defense", 1, 0, "Baja Pertahanan +25 Max HP & +5 DEF"),
            ("blade", 2, 40, "Tempa Bilah Penebusan (+Karma)"),
        ]
        for idx, btn in enumerate(skill_btns):
            if not btn.collidepoint(mouse_pos):
                continue
            key, skl_cost, gold_cost, msg = actions[idx]
            if player.skill_points < skl_cost or player.gold < gold_cost:
                audio_manager.play_sound("cancel")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 25, f"Butuh {skl_cost} SKL & {gold_cost}G!", (240, 80, 80))
                    )
                return True

            if key == "blade":
                next_map = {
                    "ancestral_blade": "redemption_blade_1",
                    "redemption_blade_1": "redemption_blade_2",
                    "redemption_blade_2": "redemption_blade_3",
                }
                next_wid = next_map.get(player.weapon_id)
                if not next_wid:
                    # Jika sedang memakai bloodthirst_blade atau sudah maksimal, bisa tempa redemption_blade_1 atau max
                    if player.weapon_id == "redemption_blade_3":
                        audio_manager.play_sound("cancel")
                        if combat_mgr:
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 25, "Bilah Penebusan Sudah Suci!", COLOR_GOLD)
                            )
                        return True
                    next_wid = "redemption_blade_1"
                player.skill_points -= skl_cost
                player.gold -= gold_cost
                player.skill_levels["blade"] += 1
                player.karma += 20  # GDD: Upgrade Bilah Penebusan di jalur normal memberi +20 Karma
                if inventory.get_count(next_wid) == 0:
                    inventory.add_item(next_wid, 1)
                player.equip_weapon(next_wid)
                audio_manager.play_sound("levelup")
            else:
                player.skill_points -= skl_cost
                player.gold -= gold_cost
                player.skill_levels[key] += 1
                if key == "stamina":
                    player.max_stamina += 15
                    player.stamina = float(player.max_stamina)
                elif key == "defense":
                    player.max_hp += 25
                    player.hp += 25
                    player.hp_trail = float(player.hp)
                audio_manager.play_sound("powerup")

            if combat_mgr:
                combat_mgr.floating_texts.append(
                    FloatingText(player.x + 24, player.y - 25, msg, COLOR_TEXT_ACCENT, is_crit=True)
                )
            if quest_mgr:
                quest_mgr.advance_progress("q3_supplies", 1, player, combat_mgr)
            return True

        return False

    def draw(self, surface, mouse_pos, player, inventory=None):
        if self.is_merchant_open:
            self._draw_merchant_ui(surface, mouse_pos, player)
        elif self.is_brog_open:
            self._draw_brog_ui(surface, mouse_pos, player)
        elif self.is_vektor_open:
            self._draw_vektor_ui(surface, mouse_pos, player, inventory)

    def _draw_merchant_ui(self, surface, mouse_pos, player):
        view_w, view_h = get_screen_size(surface)
        panel_x, panel_y, panel_w, panel_h, close_rect, rows = self._get_merchant_layout()

        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, COLOR_PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 1, border_radius=10)

        t_font = get_font(20, bold=True)
        title = t_font.render("GAEL - PEDAGANG SENJATA & ARTEFAK", True, COLOR_GOLD)
        surface.blit(title, (panel_x + 24, panel_y + 18))

        sub_font = get_font(12, italic=True)
        sub = sub_font.render("\"Senjata yang tepat adalah pembeda hidup dan mati... asal kau sanggup membayarnya.\"", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (panel_x + 24, panel_y + 46))

        c_font = get_font(16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (close_rect.centerx - c_surf.get_width() // 2, close_rect.centery - c_surf.get_height() // 2))

        name_font = get_font(12, bold=True)
        desc_font = get_font(10)
        btn_font = get_font(12, bold=True)

        for item, r_rect, buy_btn in rows:
            is_hover = r_rect.collidepoint(mouse_pos)
            is_cursed = item.get("karma", 0) < 0
            bg_col = (44, 24, 30) if is_cursed else ((32, 34, 48) if is_hover else (24, 26, 36))
            pygame.draw.rect(surface, bg_col, r_rect, border_radius=8)
            pygame.draw.rect(surface, (160, 50, 60) if is_cursed else (50, 55, 75), r_rect, 1, border_radius=8)

            n_surf = name_font.render(item["name"], True, (255, 110, 110) if is_cursed else COLOR_WHITE)
            d_surf = desc_font.render(item["desc"], True, COLOR_TEXT_MUTED)
            surface.blit(n_surf, (r_rect.x + 10, r_rect.y + 8))
            surface.blit(d_surf, (r_rect.x + 10, r_rect.y + 28))

            can_afford = player.gold >= item["cost"]
            b_hover = buy_btn.collidepoint(mouse_pos)
            btn_bg = (160, 120, 30) if can_afford else (60, 60, 70)
            if b_hover and can_afford:
                btn_bg = (200, 150, 40)
            pygame.draw.rect(surface, btn_bg, buy_btn, border_radius=6)
            pygame.draw.rect(surface, COLOR_GOLD if can_afford else (90, 90, 100), buy_btn, 1, border_radius=6)

            cost_text = btn_font.render(f"{item['cost']} G", True, COLOR_WHITE)
            surface.blit(cost_text, (buy_btn.centerx - cost_text.get_width() // 2, buy_btn.centery - cost_text.get_height() // 2))

        foot_font = get_font(14, bold=True)
        g_text = foot_font.render(f"Emas: {player.gold} Gold | Senjata: {player.weapon_info['name']}", True, COLOR_GOLD)
        surface.blit(g_text, (panel_x + 24, panel_y + panel_h - 34))

        hint_font = get_font(11)
        h_text = hint_font.render("[ESC] / [E] Tutup", True, COLOR_TEXT_MUTED)
        surface.blit(h_text, (panel_x + panel_w - h_text.get_width() - 24, panel_y + panel_h - 32))

    def _draw_brog_ui(self, surface, mouse_pos, player):
        view_w, view_h = get_screen_size(surface)
        panel_x, panel_y, panel_w, panel_h, close_rect, btn1, btn2 = self._get_brog_layout()

        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, COLOR_PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 1, border_radius=10)

        t_font = get_font(19, bold=True)
        title = t_font.render("MEJA BAR BROG (PENUKARAN ABU)", True, COLOR_GOLD)
        surface.blit(title, (panel_x + 24, panel_y + 18))

        sub_font = get_font(12, italic=True)
        sub = sub_font.render("\"Bawa abu monster Karak itu ke sini, akan ku bayar dengan koin emas!\"", True, COLOR_TEXT_MUTED)
        surface.blit(sub, (panel_x + 24, panel_y + 48))

        c_font = get_font(16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (close_rect.centerx - c_surf.get_width() // 2, close_rect.centery - c_surf.get_height() // 2))

        s_font = get_font(14, bold=True)
        ash_info = s_font.render(f"Abu Monster: {player.monster_ash} Ash", True, COLOR_ASH)
        gold_info = s_font.render(f"Emas: {player.gold} Gold", True, COLOR_GOLD)
        surface.blit(ash_info, (panel_x + 40, panel_y + 90))
        surface.blit(gold_info, (panel_x + 260, panel_y + 90))

        b1_hover = btn1.collidepoint(mouse_pos)
        can_10 = player.monster_ash >= 10
        b1_col = (50, 120, 65) if (b1_hover and can_10) else ((40, 90, 50) if can_10 else (50, 50, 60))
        pygame.draw.rect(surface, b1_col, btn1, border_radius=8)
        pygame.draw.rect(surface, (100, 180, 120) if can_10 else (80, 80, 90), btn1, 2, border_radius=8)

        btn_font = get_font(14, bold=True)
        t1 = btn_font.render("Tukar 10 Abu Monster  ->  25 Emas", True, COLOR_WHITE if can_10 else COLOR_TEXT_MUTED)
        surface.blit(t1, (btn1.centerx - t1.get_width() // 2, btn1.centery - t1.get_height() // 2))

        b2_hover = btn2.collidepoint(mouse_pos)
        can_all = player.monster_ash > 0
        b2_col = (170, 110, 35) if (b2_hover and can_all) else ((130, 85, 25) if can_all else (50, 50, 60))
        pygame.draw.rect(surface, b2_col, btn2, border_radius=8)
        pygame.draw.rect(surface, COLOR_GOLD if can_all else (80, 80, 90), btn2, 2, border_radius=8)

        total_value = max(1, int(player.monster_ash * 2.5)) if can_all else 0
        t2 = btn_font.render(f"Tukar SEMUA Abu ({player.monster_ash} Ash)  ->  +{total_value} Emas", True, COLOR_WHITE if can_all else COLOR_TEXT_MUTED)
        surface.blit(t2, (btn2.centerx - t2.get_width() // 2, btn2.centery - t2.get_height() // 2))

        hint_font = get_font(11)
        h_text = hint_font.render("[Klik tombol untuk menukar abu / [ESC] atau [E] untuk tutup]", True, COLOR_TEXT_MUTED)
        surface.blit(h_text, (panel_x + panel_w // 2 - h_text.get_width() // 2, panel_y + panel_h - 32))

    def _draw_vektor_ui(self, surface, mouse_pos, player, inventory=None):
        view_w, view_h = get_screen_size(surface)
        panel_x, panel_y, panel_w, panel_h, close_rect, sell_btn, skill_btns = self._get_vektor_layout()

        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 155))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, COLOR_PANEL_BG, (panel_x, panel_y, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (panel_x + 4, panel_y + 4, panel_w - 8, panel_h - 8), 1, border_radius=10)

        t_font = get_font(19, bold=True)
        surface.blit(t_font.render("VEKTOR - BENGKEL SKILL & TEMPA PENEBUSAN", True, COLOR_GOLD), (panel_x + 24, panel_y + 18))

        sub_font = get_font(12, italic=True)
        surface.blit(sub_font.render("\"Serahkan sisa monster buruanmu. Kita ubah menjadi teknik tempur & tempaan suci.\"", True, COLOR_TEXT_MUTED), (panel_x + 24, panel_y + 46))

        c_font = get_font(16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (close_rect.centerx - c_surf.get_width() // 2, close_rect.centery - c_surf.get_height() // 2))

        s_font = get_font(13, bold=True)
        surface.blit(s_font.render(f"Poin Skill (SKL): {player.skill_points}  |  Emas: {player.gold} G  |  Level SKL: {player.skill_level}", True, COLOR_TEXT_ACCENT), (panel_x + 24, panel_y + 76))

        mat_cnt, mat_gold, mat_skl = inventory.get_material_summary() if inventory else (0, 0, 0)
        can_sell = mat_cnt > 0
        s_hover = sell_btn.collidepoint(mouse_pos)
        s_col = (50, 120, 75) if (s_hover and can_sell) else ((35, 85, 55) if can_sell else (45, 48, 58))
        pygame.draw.rect(surface, s_col, sell_btn, border_radius=8)
        pygame.draw.rect(surface, (110, 210, 140) if can_sell else (70, 75, 90), sell_btn, 2, border_radius=8)

        b_font = get_font(13, bold=True)
        sell_txt = (
            f"Serahkan Semua Material ({mat_cnt} item) -> +{mat_gold} Gold & +{mat_skl} SKL"
            if can_sell else "Belum Ada Material Monster di Tas (Kalahkan Monster di Stage!)"
        )
        st_surf = b_font.render(sell_txt, True, COLOR_WHITE if can_sell else COLOR_TEXT_MUTED)
        surface.blit(st_surf, (sell_btn.centerx - st_surf.get_width() // 2, sell_btn.centery - st_surf.get_height() // 2))

        rows_info = [
            ("power", 1, 0, f"Latih Kekuatan Tebasan (Lv.{player.skill_levels['power']})", "Meningkatkan +12 ATK permanen (Biaya: 1 SKL)"),
            ("stamina", 1, 0, f"Latih Ketahanan Napas (Lv.{player.skill_levels['stamina']})", "Meningkatkan +15 Max STA & +2.5/s Regen (Biaya: 1 SKL)"),
            ("defense", 1, 0, f"Latih Pertahanan Baja (Lv.{player.skill_levels['defense']})", "Meningkatkan +25 Max HP & +5 DEF (Biaya: 1 SKL)"),
            ("blade", 2, 40, f"Tempa Bilah Penebusan (Tier {player.skill_levels['blade']}/3)", "Upgrade senjata suci & +20 Karma Good Ending (Biaya: 2 SKL + 40G)"),
        ]
        d_font = get_font(11)
        for idx, btn in enumerate(skill_btns):
            key, skl_cost, gold_cost, title_str, desc_str = rows_info[idx]
            can_buy = player.skill_points >= skl_cost and player.gold >= gold_cost
            hover = btn.collidepoint(mouse_pos)
            bg = (45, 52, 74) if (hover and can_buy) else ((30, 34, 48) if can_buy else (24, 26, 36))
            pygame.draw.rect(surface, bg, btn, border_radius=8)
            pygame.draw.rect(surface, COLOR_GOLD if can_buy else (65, 70, 85), btn, 1, border_radius=8)

            surface.blit(b_font.render(title_str, True, COLOR_GOLD if key == "blade" else COLOR_WHITE), (btn.x + 14, btn.y + 7))
            surface.blit(d_font.render(desc_str, True, COLOR_TEXT_MUTED), (btn.x + 14, btn.y + 28))

            tag = f"{skl_cost} SKL" + (f" + {gold_cost}G" if gold_cost > 0 else "")
            tag_surf = b_font.render(tag, True, (110, 220, 255) if can_buy else (120, 120, 130))
            surface.blit(tag_surf, (btn.right - tag_surf.get_width() - 14, btn.centery - tag_surf.get_height() // 2))

        hint_font = get_font(11)
        surface.blit(hint_font.render("[ESC] / [E] untuk menutup Bengkel Vektor", True, COLOR_TEXT_MUTED), (panel_x + 24, panel_y + panel_h - 28))
