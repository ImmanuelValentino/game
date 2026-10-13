"""
Sistem Backpack & Inventory untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menangani penyimpanan item, grid slot, tooltip detail item, serta konsumsi ramuan HP/Stamina.
"""
import os
import pygame
from src.config import (
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_ASH, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)
from src.audio import audio_manager

class Item:
    def __init__(self, item_id, name, desc, category="material", rarity="common", icon_file=None, max_stack=99):
        self.id = item_id
        self.name = name
        self.desc = desc
        self.category = category # consumable, weapon, accessory, material
        self.rarity = rarity     # common, uncommon, rare, legendary
        self.icon_file = icon_file
        self.max_stack = max_stack
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
                    self._icon_surf = pygame.transform.scale(img, (36, 36))
                    return
                except Exception as e:
                    print(f"[Item] Error loading icon {path}: {e}")
        # Fallback icon jika gambar tidak ditemukan
        self._icon_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        col = (200, 180, 100) if self.category == "weapon" else (100, 200, 120)
        pygame.draw.circle(self._icon_surf, col, (18, 18), 15)

    def get_rarity_color(self):
        colors = {
            "common": (210, 210, 215),
            "uncommon": (100, 220, 120),
            "rare": (80, 170, 255),
            "legendary": (255, 195, 60),
        }
        return colors.get(self.rarity, (200, 200, 200))


# Database Item Game
ITEM_DATABASE = {
    "hp_potion": Item(
        "hp_potion", "Ramuan Pemulih (Health Potion)",
        "Memulihkan 50 HP secara instan. Dibuat dari lumut rawa Oakhaven.",
        category="consumable", rarity="uncommon", icon_file="Alchemy.png"
    ),
    "stamina_tonic": Item(
        "stamina_tonic", "Tonik Stamina (Stamina Tonic)",
        "Memulihkan 50 Stamina secara instan.",
        category="consumable", rarity="common", icon_file="AlchemyDisabled.png"
    ),
    "monster_ash": Item(
        "monster_ash", "Abu Monster (Monster Ash)",
        "Sisa abu jiwa dari monster Karak. Bawa ke Brog di Guild untuk ditukar dengan Emas.",
        category="material", rarity="common", icon_file="BookDarkness.png"
    ),
    "ancestral_blade": Item(
        "ancestral_blade", "Pedang Leluhur (Ancestral Blade)",
        "Pedang tua peninggalan klan Oakhaven. Tergores namun masih tajam membara.",
        category="weapon", rarity="rare", icon_file="AttackUpgrade.png"
    ),
    "whetstone": Item(
        "whetstone", "Batu Asah Hitam (Sharp Whetstone)",
        "Meningkatkan Attack Damage secara permanen (+5).",
        category="accessory", rarity="rare", icon_file="AttackUpgrade.png"
    ),
    "vitality_ring": Item(
        "vitality_ring", "Cincin Vitalitas (Vitality Ring)",
        "Cincin perak berlapis runa kuno (+25 Max HP).",
        category="accessory", rarity="rare", icon_file="Amulet.png"
    ),
    "swift_boots": Item(
        "swift_boots", "Sepatu Langkah Bayangan (Swift Boots)",
        "Sepatu kulit lentur yang meningkatkan kecepatan gerak (+15%).",
        category="accessory", rarity="uncommon", icon_file="Boot.png"
    ),
    "guardian_armor": Item(
        "guardian_armor", "Zirah Pelindung Ksatria",
        "Zirah baja tebal yang menyerap 3 damage dari setiap serangan musuh.",
        category="accessory", rarity="rare", icon_file="Armor.png"
    ),
    "karak_core": Item(
        "karak_core", "Inti Monster Karak",
        "Bahan langka untuk meracik ramuan tingkat tinggi.",
        category="material", rarity="uncommon", icon_file="BookDeath.png"
    ),
}


class Inventory:
    def __init__(self, capacity=16):
        self.capacity = capacity
        # List of dict: {"item": Item, "count": int} or None
        self.slots = [None] * capacity
        self.is_open = False
        
        # Inisialisasi item awal penyintas
        self.add_item("ancestral_blade", 1)
        self.add_item("hp_potion", 3)
        self.add_item("stamina_tonic", 2)
        self.add_item("monster_ash", 15)

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            audio_manager.play_sound("accept")
        else:
            audio_manager.play_sound("cancel")

    def add_item(self, item_id, count=1):
        if item_id not in ITEM_DATABASE:
            return False
        item_obj = ITEM_DATABASE[item_id]

        # 1. Coba stack pada slot yang sudah berisi item ini
        for slot in self.slots:
            if slot and slot["item"].id == item_id:
                space = item_obj.max_stack - slot["count"]
                if space > 0:
                    add_cnt = min(space, count)
                    slot["count"] += add_cnt
                    count -= add_cnt
                    if count <= 0:
                        return True

        # 2. Cari slot kosong
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
                return False # Tas penuh!

        return True

    def remove_item(self, item_id, count=1):
        for slot in self.slots:
            if slot and slot["item"].id == item_id:
                if slot["count"] >= count:
                    slot["count"] -= count
                    if slot["count"] <= 0:
                        slot["item"] = None
                        slot["count"] = 0
                    return True
                else:
                    count -= slot["count"]
                    slot["item"] = None
                    slot["count"] = 0
        return False

    def get_count(self, item_id):
        total = 0
        for slot in self.slots:
            if slot and slot["item"] and slot["item"].id == item_id:
                total += slot["count"]
        return total

    def use_slot(self, index, player, combat_mgr=None):
        if index < 0 or index >= self.capacity:
            return False
        slot = self.slots[index]
        if not slot or not slot["item"]:
            return False

        item = slot["item"]
        used = False

        if item.id == "hp_potion":
            if player.hp < player.max_hp:
                healed = player.heal(50)
                used = True
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 20, f"+{healed} HP", (100, 255, 120), is_crit=True)
                    )
        elif item.id == "stamina_tonic":
            if player.stamina < player.max_stamina:
                player.restore_stamina(50)
                audio_manager.play_sound("heal")
                used = True
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        combat_mgr.FloatingText(player.x + 24, player.y - 20, "+50 Stamina", (120, 220, 255))
                    )

        if used:
            slot["count"] -= 1
            if slot["count"] <= 0:
                self.slots[index] = None
            return True
        return False

    def handle_click(self, mouse_pos, player, combat_mgr=None):
        """Memproses klik pada slot backpack."""
        if not self.is_open:
            return False

        # Hitung koordinat slot grid
        panel_w = 480
        panel_h = 420
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        # Tombol Close [X]
        close_rect = pygame.Rect(panel_x + panel_w - 36, panel_y + 12, 24, 24)
        if close_rect.collidepoint(mouse_pos):
            self.toggle()
            return True

        # Posisi slot (4 kolom x 4 baris)
        cols = 4
        slot_size = 64
        spacing = 16
        start_x = panel_x + (panel_w - (cols * slot_size + (cols - 1) * spacing)) // 2
        start_y = panel_y + 70

        for i in range(self.capacity):
            col = i % cols
            row = i // cols
            sx = start_x + col * (slot_size + spacing)
            sy = start_y + row * (slot_size + spacing)
            s_rect = pygame.Rect(sx, sy, slot_size, slot_size)

            if s_rect.collidepoint(mouse_pos):
                self.use_slot(i, player, combat_mgr)
                return True

        return False

    def draw(self, surface, mouse_pos, player):
        if not self.is_open:
            return

        panel_w = 480
        panel_h = 430
        panel_x = (1280 - panel_w) // 2
        panel_y = (720 - panel_h) // 2

        # Dimmer overlay gelap di background
        dim_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 140))
        surface.blit(dim_surf, (0, 0))

        # Panel utama
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BG, (0, 0, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, panel_w, panel_h), 2, border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER_LIGHT, (4, 4, panel_w - 8, panel_h - 8), 1, border_radius=10)
        surface.blit(panel_surf, (panel_x, panel_y))

        # Judul Panel
        title_font = pygame.font.SysFont("Segoe UI, Arial", 19, bold=True)
        title_surf = title_font.render("TAS PENYINTAS (BACKPACK)", True, COLOR_GOLD)
        surface.blit(title_surf, (panel_x + 24, panel_y + 18))

        # Tombol [X]
        close_font = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        close_surf = close_font.render("X", True, (220, 80, 80))
        surface.blit(close_surf, (panel_x + panel_w - 30, panel_y + 16))

        # Grid slot (4x4)
        cols = 4
        slot_size = 64
        spacing = 16
        start_x = panel_x + (panel_w - (cols * slot_size + (cols - 1) * spacing)) // 2
        start_y = panel_y + 65

        hovered_slot = None

        for i in range(self.capacity):
            col = i % cols
            row = i // cols
            sx = start_x + col * (slot_size + spacing)
            sy = start_y + row * (slot_size + spacing)
            s_rect = pygame.Rect(sx, sy, slot_size, slot_size)

            is_hover = s_rect.collidepoint(mouse_pos)
            slot = self.slots[i]

            # Kotak slot
            bg_col = (38, 42, 58) if is_hover else (26, 28, 40)
            pygame.draw.rect(surface, bg_col, s_rect, border_radius=8)

            border_col = (200, 170, 100) if is_hover else (55, 60, 80)
            if slot and slot["item"]:
                border_col = slot["item"].get_rarity_color() if not is_hover else (255, 230, 140)
            pygame.draw.rect(surface, border_col, s_rect, 2, border_radius=8)

            # Gambar item jika ada
            if slot and slot["item"]:
                item = slot["item"]
                # Icon item di tengah slot
                ix = sx + (slot_size - 32) // 2
                iy = sy + (slot_size - 32) // 2
                if item.icon_surf:
                    surface.blit(item.icon_surf, (ix, iy))

                # Jumlah item (jika > 1)
                if slot["count"] > 1:
                    cnt_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
                    cnt_surf = cnt_font.render(str(slot["count"]), True, COLOR_WHITE)
                    surface.blit(cnt_surf, (sx + slot_size - cnt_surf.get_width() - 5, sy + slot_size - 18))

                if is_hover:
                    hovered_slot = slot

        # Footer info: Emas & Abu Monster
        footer_y = panel_y + panel_h - 42
        info_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        gold_text = info_font.render(f"Emas: {player.gold} Gold", True, COLOR_GOLD)
        ash_text = info_font.render(f"Abu: {player.monster_ash} Ash", True, COLOR_ASH)
        surface.blit(gold_text, (panel_x + 30, footer_y))
        surface.blit(ash_text, (panel_x + 190, footer_y))

        hint_font = pygame.font.SysFont("Segoe UI, Arial", 12)
        hint_surf = hint_font.render("[Klik Kiri: Gunakan / [B]: Tutup]", True, COLOR_TEXT_MUTED)
        surface.blit(hint_surf, (panel_x + panel_w - hint_surf.get_width() - 25, footer_y))

        # Render Tooltip jika ada slot yang di-hover
        if hovered_slot and hovered_slot["item"]:
            item = hovered_slot["item"]
            self._draw_tooltip(surface, item, mouse_pos)

    def _draw_tooltip(self, surface, item, mouse_pos):
        mx, my = mouse_pos
        tt_w = 260
        tt_h = 100
        tt_x = mx + 15
        tt_y = my + 15

        if tt_x + tt_w > 1260:
            tt_x = mx - tt_w - 15
        if tt_y + tt_h > 700:
            tt_y = my - tt_h - 15

        tt_surf = pygame.Surface((tt_w, tt_h), pygame.SRCALPHA)
        pygame.draw.rect(tt_surf, (16, 18, 26, 245), (0, 0, tt_w, tt_h), border_radius=8)
        pygame.draw.rect(tt_surf, item.get_rarity_color(), (0, 0, tt_w, tt_h), 2, border_radius=8)
        surface.blit(tt_surf, (tt_x, tt_y))

        # Nama Item
        name_font = pygame.font.SysFont("Segoe UI, Arial", 14, bold=True)
        name_surf = name_font.render(item.name, True, item.get_rarity_color())
        surface.blit(name_surf, (tt_x + 10, tt_y + 8))

        # Kategori
        cat_font = pygame.font.SysFont("Segoe UI, Arial", 11, italic=True)
        cat_surf = cat_font.render(f"Tipe: {item.category.capitalize()}", True, COLOR_TEXT_MUTED)
        surface.blit(cat_surf, (tt_x + 10, tt_y + 28))

        # Deskripsi (word wrap sederhana)
        desc_font = pygame.font.SysFont("Segoe UI, Arial", 11)
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
