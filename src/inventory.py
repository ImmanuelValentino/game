"""
Sistem Backpack & Inventory untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mendukung item konsumsi, senjata (equip), aksesori, dan material 4 rarity sesuai GDD.
"""
import os
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WEAPON_DATABASE, get_font,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_ASH, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT,
    HP_POTION_HEAL, STAMINA_TONIC_RESTORE,
)
from src.audio import audio_manager
from src.combat import FloatingText


class Item:
    def __init__(
        self, item_id, name, desc, category="material", rarity="common",
        icon_file=None, max_stack=99, sell_gold=0, sell_skl=0
    ):
        self.id = item_id
        self.name = name
        self.desc = desc
        self.category = category  # consumable, weapon, accessory, material
        self.rarity = rarity      # common, uncommon, rare, epic, legendary
        self.icon_file = icon_file
        self.max_stack = max_stack
        self.sell_gold = sell_gold
        self.sell_skl = sell_skl
        self._icon_surf = None

    @property
    def icon_surf(self):
        if self._icon_surf is None:
            self._load_icon()
        return self._icon_surf

    def _load_icon(self):
        if self.icon_file:
            path = os.path.join("assets/items", self.icon_file)
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path)
                    if pygame.display.get_surface():
                        img = img.convert_alpha()
                    w, h = img.get_size()
                    # Weapon/tool sheets in assets/items (e.g. Katana.png, Hammer.png, Axe.png) are 256x256 4x4 grids.
                    if w >= 128 and h >= 128:
                        cell = img.subsurface(pygame.Rect(0, 0, w // 4, h // 4))
                        bbox = cell.get_bounding_rect()
                        if bbox.width > 0 and bbox.height > 0:
                            sprite = cell.subsurface(bbox)
                            scale = min(32.0 / bbox.width, 32.0 / bbox.height)
                            nw = max(1, int(round(bbox.width * scale)))
                            nh = max(1, int(round(bbox.height * scale)))
                            scaled = pygame.transform.scale(sprite, (nw, nh))
                            surf = pygame.Surface((36, 36), pygame.SRCALPHA)
                            surf.blit(scaled, ((36 - nw) // 2, (36 - nh) // 2))
                            self._icon_surf = surf
                            return
                    self._icon_surf = pygame.transform.scale(img, (36, 36))
                    return
                except Exception as e:
                    print(f"[Item] Error loading icon {path}: {e}")
        self._icon_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        col = (200, 180, 100) if self.category == "weapon" else (100, 200, 120)
        pygame.draw.circle(self._icon_surf, col, (18, 18), 15)

    def get_rarity_color(self):
        colors = {
            "common": (210, 210, 215),
            "uncommon": (100, 220, 120),
            "rare": (80, 170, 255),
            "epic": (205, 110, 255),
            "legendary": (255, 195, 60),
        }
        return colors.get(self.rarity, (200, 200, 200))


# Database Item Game Lengkap (Sesuai GDD)
ITEM_DATABASE = {
    "hp_potion": Item(
        "hp_potion", "Ramuan Pemulih (Health Potion)",
        "Memulihkan 80 HP secara instan. Dibuat dari lumut rawa Oakhaven.",
        category="consumable", rarity="uncommon", icon_file="Alchemy.png"
    ),
    "stamina_tonic": Item(
        "stamina_tonic", "Tonik Stamina (Stamina Tonic)",
        "Memulihkan 60 Stamina secara instan.",
        category="consumable", rarity="common", icon_file="BackgroundFlask.png"
    ),
    # Senjata (dapat di-equip langsung dari backpack)
    "ancestral_blade": Item(
        "ancestral_blade", "Pedang Leluhur",
        "Pedang tua peninggalan klan Oakhaven (ATK +65). Klik untuk memakai.",
        category="weapon", rarity="rare", icon_file="Katana.png", max_stack=1
    ),
    "redemption_blade_1": Item(
        "redemption_blade_1", "Bilah Penebusan +1",
        "Pedang hitam tempaan Vektor (ATK +115). Klik untuk memakai.",
        category="weapon", rarity="rare", icon_file="MagicWeapon.png", max_stack=1
    ),
    "redemption_blade_2": Item(
        "redemption_blade_2", "Bilah Penebusan +2",
        "Pedang bercahaya perak penumpas Karak (ATK +185). Klik untuk memakai.",
        category="weapon", rarity="epic", icon_file="MagicWeapon.png", max_stack=1
    ),
    "redemption_blade_3": Item(
        "redemption_blade_3", "Bilah Penebusan Suci",
        "Wujud puncak Bilah Penebusan pemutus kutukan (ATK +280). Klik untuk memakai.",
        category="weapon", rarity="legendary", icon_file="MagicWeapon.png", max_stack=1
    ),
    "bloodthirst_blade": Item(
        "bloodthirst_blade", "Pedang Haus Darah",
        "Artefak terlarang Gael (ATK +320, Drop x1.5). Memakainya mengunci jalan gelap.",
        category="weapon", rarity="legendary", icon_file="Axe.png", max_stack=1
    ),
    # Material Drop 4 Tier Rarity (Sesuai Tabel GDD: Common 70%, Uncommon 20%, Rare 8%, Epic 2%)
    "bone_shard": Item(
        "bone_shard", "Pecahan Tulang",
        "Material Common (8G, +1 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="common", icon_file="BookRock.png", sell_gold=8, sell_skl=1
    ),
    "rust_iron": Item(
        "rust_iron", "Baja Karat",
        "Material Common (10G, +1 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="common", icon_file="Hammer.png", sell_gold=10, sell_skl=1
    ),
    "spore_intact": Item(
        "spore_intact", "Spora Utuh",
        "Material Uncommon (18G, +2 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="uncommon", icon_file="OrbPlant.png", sell_gold=18, sell_skl=2
    ),
    "ice_core": Item(
        "ice_core", "Inti Es",
        "Material Uncommon (22G, +2 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="uncommon", icon_file="BookIce.png", sell_gold=22, sell_skl=2
    ),
    "karak_blood": Item(
        "karak_blood", "Darah Karak",
        "Material Rare (40G, +4 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="rare", icon_file="BookFire.png", sell_gold=40, sell_skl=4
    ),
    "pure_steel": Item(
        "pure_steel", "Baja Murni",
        "Material Rare (45G, +4 SKL). Serahkan ke Vektor di Hub.",
        category="material", rarity="rare", icon_file="AttackUpgrade.png", sell_gold=45, sell_skl=4
    ),
    "general_core": Item(
        "general_core", "Inti Jenderal",
        "Material Epic Bos (90G, +8 SKL). Bukti tumbangnya Jenderal bioma.",
        category="material", rarity="epic", icon_file="OrbFire.png", sell_gold=90, sell_skl=8
    ),
    "broken_crown": Item(
        "broken_crown", "Mahkota Pecah",
        "Relik Epic/Boss langka (160G, +12 SKL). Serahkan ke Vektor.",
        category="material", rarity="legendary", icon_file="OrbDarkness.png", sell_gold=160, sell_skl=12
    ),
    "monster_ash": Item(
        "monster_ash", "Abu Monster",
        "Sisa abu jiwa monster Karak.",
        category="material", rarity="common", icon_file="BookDarkness.png", sell_gold=3, sell_skl=0
    ),
    "karak_core": Item(
        "karak_core", "Inti Monster Karak",
        "Bahan langka untuk meracik ramuan tingkat tinggi.",
        category="material", rarity="uncommon", icon_file="BookDeath.png", sell_gold=20, sell_skl=2
    ),
}


class Inventory:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.slots = [None] * capacity
        self.is_open = False

        # Inisialisasi item awal penyintas
        self.add_item("ancestral_blade", 1)
        self.add_item("hp_potion", 5)
        self.add_item("stamina_tonic", 3)

    def reset_to_empty(self):
        self.slots = [None] * self.capacity

    def toggle(self):
        self.is_open = not self.is_open
        audio_manager.play_sound("accept" if self.is_open else "cancel")

    def can_add_item(self, item_id, count=1):
        if item_id not in ITEM_DATABASE or count <= 0:
            return False
        item_obj = ITEM_DATABASE[item_id]
        remaining = count
        for slot in self.slots:
            if slot and slot["item"] and slot["item"].id == item_id:
                remaining -= max(0, item_obj.max_stack - slot["count"])
            elif slot is None:
                remaining -= item_obj.max_stack
            if remaining <= 0:
                return True
        return False

    def add_item(self, item_id, count=1):
        if item_id not in ITEM_DATABASE or count <= 0:
            return False
        if not self.can_add_item(item_id, count):
            return False
        item_obj = ITEM_DATABASE[item_id]

        for slot in self.slots:
            if slot and slot["item"] and slot["item"].id == item_id:
                space = item_obj.max_stack - slot["count"]
                if space > 0:
                    add_cnt = min(space, count)
                    slot["count"] += add_cnt
                    count -= add_cnt
                    if count <= 0:
                        return True

        while count > 0:
            found_empty = False
            for i in range(self.capacity):
                if self.slots[i] is None:
                    add_cnt = min(item_obj.max_stack, count)
                    self.slots[i] = {"item": item_obj, "count": add_cnt}
                    count -= add_cnt
                    found_empty = True
                    break
            if not found_empty:
                return False
        return True

    def remove_item(self, item_id, count=1):
        if count <= 0 or self.get_count(item_id) < count:
            return False
        remaining = count
        for i, slot in enumerate(self.slots):
            if slot and slot["item"] and slot["item"].id == item_id:
                take = min(slot["count"], remaining)
                slot["count"] -= take
                remaining -= take
                if slot["count"] <= 0:
                    self.slots[i] = None
                if remaining <= 0:
                    return True
        return remaining <= 0

    def get_count(self, item_id):
        total = 0
        for slot in self.slots:
            if slot and slot["item"] and slot["item"].id == item_id:
                total += slot["count"]
        return total

    def get_material_summary(self):
        """Mengembalikan (total_items, total_gold, total_skl) dari seluruh material di tas."""
        total_cnt = 0
        total_gold = 0
        total_skl = 0
        for slot in self.slots:
            if slot and slot["item"] and slot["item"].category == "material":
                cnt = slot["count"]
                total_cnt += cnt
                total_gold += slot["item"].sell_gold * cnt
                total_skl += slot["item"].sell_skl * cnt
        return total_cnt, total_gold, total_skl

    def sell_all_materials(self, player):
        """Menukarkan seluruh material monster ke Gold dan Skill Points (SKL) via Vektor."""
        total_cnt, total_gold, total_skl = self.get_material_summary()
        if total_cnt <= 0:
            return 0, 0, 0
        for i, slot in enumerate(self.slots):
            if slot and slot["item"] and slot["item"].category == "material":
                self.slots[i] = None
        player.gold += total_gold
        player.skill_points += total_skl
        return total_cnt, total_gold, total_skl

    def apply_death_material_penalty(self, loss_ratio=0.5):
        """Mengurangi material yang belum dijual sebesar 50% ketika gugur (sesuai GDD)."""
        removed_total = 0
        for i, slot in enumerate(self.slots):
            if slot and slot["item"] and slot["item"].category == "material":
                lost = max(1, int(slot["count"] * loss_ratio))
                slot["count"] -= lost
                removed_total += lost
                if slot["count"] <= 0:
                    self.slots[i] = None
        return removed_total

    def use_slot(self, index, player, combat_mgr=None):
        if index < 0 or index >= self.capacity:
            return False
        slot = self.slots[index]
        if not slot or not slot["item"]:
            return False

        item = slot["item"]
        used = False

        if item.category == "weapon" and item.id in WEAPON_DATABASE:
            if player.equip_weapon(item.id):
                audio_manager.play_sound("accept")
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 20, f"Pakai: {item.name}", COLOR_GOLD, is_crit=True)
                    )
                return True

        if item.id == "hp_potion":
            if player.hp < player.max_hp:
                healed = player.heal(HP_POTION_HEAL)
                used = True
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 20, f"+{healed} HP", (100, 255, 120), is_crit=True)
                    )
        elif item.id == "stamina_tonic":
            if player.stamina < player.max_stamina:
                player.restore_stamina(STAMINA_TONIC_RESTORE)
                audio_manager.play_sound("heal")
                used = True
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(player.x + 24, player.y - 20, f"+{STAMINA_TONIC_RESTORE} Stamina", (120, 220, 255))
                    )

        if used:
            slot["count"] -= 1
            if slot["count"] <= 0:
                self.slots[index] = None
            return True
        return False

    def use_item_by_id(self, item_id, player, combat_mgr=None):
        """Pakai 1 unit consumable pertama yang cocok berdasarkan item_id. Mengembalikan status: 'used', 'full', atau 'missing'."""
        for i, slot in enumerate(self.slots):
            if slot and slot["item"] and slot["item"].id == item_id:
                return "used" if self.use_slot(i, player, combat_mgr) else "full"
        return "missing"

    def _get_layout(self):
        panel_w = 480
        panel_h = 430
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 12, 24, 24)

        cols = 4
        slot_size = 64
        spacing = 16
        start_x = panel_x + (panel_w - (cols * slot_size + (cols - 1) * spacing)) // 2
        start_y = panel_y + 65
        slot_rects = [
            pygame.Rect(
                start_x + (i % cols) * (slot_size + spacing),
                start_y + (i // cols) * (slot_size + spacing),
                slot_size,
                slot_size,
            )
            for i in range(self.capacity)
        ]
        return panel_x, panel_y, panel_w, panel_h, close_rect, slot_rects

    def handle_click(self, mouse_pos, player, combat_mgr=None):
        if not self.is_open:
            return False

        _, _, _, _, close_rect, slot_rects = self._get_layout()
        if close_rect.collidepoint(mouse_pos):
            self.toggle()
            return True

        for i, s_rect in enumerate(slot_rects):
            if s_rect.collidepoint(mouse_pos):
                self.use_slot(i, player, combat_mgr)
                return True

        return False

    def draw(self, surface, mouse_pos, player):
        if not self.is_open:
            return

        panel_x, panel_y, panel_w, panel_h, close_rect, slot_rects = self._get_layout()

        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140))
        surface.blit(dim_surf, (0, 0))

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BG, (0, 0, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER_LIGHT, (4, 4, panel_w - 8, panel_h - 8), 1, border_radius=10)
        surface.blit(panel_surf, (panel_x, panel_y))

        title_font = get_font(19, bold=True)
        title_surf = title_font.render("TAS PENYINTAS (BACKPACK)", True, COLOR_GOLD)
        surface.blit(title_surf, (panel_x + 24, panel_y + 18))

        close_font = get_font(16, bold=True)
        close_surf = close_font.render("X", True, (220, 80, 80))
        surface.blit(close_surf, (close_rect.centerx - close_surf.get_width() // 2, close_rect.centery - close_surf.get_height() // 2))

        hovered_slot = None
        cnt_font = get_font(13, bold=True)
        eq_font = get_font(10, bold=True)

        for i, s_rect in enumerate(slot_rects):
            is_hover = s_rect.collidepoint(mouse_pos)
            slot = self.slots[i]

            bg_col = (38, 42, 58) if is_hover else (26, 28, 40)
            pygame.draw.rect(surface, bg_col, s_rect, border_radius=8)

            border_col = (200, 170, 100) if is_hover else (55, 60, 80)
            if slot and slot["item"]:
                border_col = slot["item"].get_rarity_color() if not is_hover else (255, 230, 140)
            pygame.draw.rect(surface, border_col, s_rect, 2, border_radius=8)

            if slot and slot["item"]:
                item = slot["item"]
                if item.icon_surf:
                    ix = s_rect.x + (s_rect.width - item.icon_surf.get_width()) // 2
                    iy = s_rect.y + (s_rect.height - item.icon_surf.get_height()) // 2
                    surface.blit(item.icon_surf, (ix, iy))

                if item.id == player.weapon_id:
                    eq_txt = eq_font.render("EQ", True, COLOR_GOLD)
                    surface.blit(eq_txt, (s_rect.x + 4, s_rect.y + 3))

                if slot["count"] > 1:
                    cnt_surf = cnt_font.render(str(slot["count"]), True, COLOR_WHITE)
                    surface.blit(cnt_surf, (s_rect.right - cnt_surf.get_width() - 5, s_rect.bottom - 18))

                if is_hover:
                    hovered_slot = slot

        footer_y = panel_y + panel_h - 42
        info_font = get_font(13, bold=True)
        gold_text = info_font.render(f"Gold: {player.gold}", True, COLOR_GOLD)
        ash_text = info_font.render(f"Ash: {player.monster_ash}", True, COLOR_ASH)
        skl_text = info_font.render(f"SKL: {player.skill_points}", True, COLOR_TEXT_ACCENT)
        surface.blit(gold_text, (panel_x + 24, footer_y))
        surface.blit(ash_text, (panel_x + 125, footer_y))
        surface.blit(skl_text, (panel_x + 215, footer_y))

        hint_font = get_font(11)
        hint_surf = hint_font.render("[Klik: Pakai/Equip | [B]: Tutup]", True, COLOR_TEXT_MUTED)
        surface.blit(hint_surf, (panel_x + panel_w - hint_surf.get_width() - 20, footer_y + 2))

        if hovered_slot and hovered_slot["item"]:
            self._draw_tooltip(surface, hovered_slot["item"], mouse_pos)

    def _draw_tooltip(self, surface, item, mouse_pos):
        mx, my = mouse_pos
        tt_w = 270
        tt_h = 104
        tt_x = mx + 15
        tt_y = my + 15

        if tt_x + tt_w > SCREEN_WIDTH - 20:
            tt_x = mx - tt_w - 15
        if tt_y + tt_h > SCREEN_HEIGHT - 20:
            tt_y = my - tt_h - 15

        tt_surf = pygame.Surface((tt_w, tt_h), pygame.SRCALPHA)
        pygame.draw.rect(tt_surf, (16, 18, 26, 245), (0, 0, tt_w, tt_h), border_radius=8)
        pygame.draw.rect(tt_surf, item.get_rarity_color(), (0, 0, tt_w, tt_h), 2, border_radius=8)
        surface.blit(tt_surf, (tt_x, tt_y))

        name_font = get_font(14, bold=True)
        name_surf = name_font.render(item.name, True, item.get_rarity_color())
        surface.blit(name_surf, (tt_x + 10, tt_y + 8))

        cat_font = get_font(11, italic=True)
        cat_surf = cat_font.render(f"{item.category.capitalize()} ({item.rarity.capitalize()})", True, COLOR_TEXT_MUTED)
        surface.blit(cat_surf, (tt_x + 10, tt_y + 28))

        desc_font = get_font(11)
        words = item.desc.split(" ")
        lines = []
        cur_line = []
        for w in words:
            test = " ".join(cur_line + [w])
            if desc_font.size(test)[0] < tt_w - 20:
                cur_line.append(w)
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        for idx, line in enumerate(lines[:3]):
            l_surf = desc_font.render(line, True, COLOR_WHITE)
            surface.blit(l_surf, (tt_x + 10, tt_y + 46 + idx * 15))
