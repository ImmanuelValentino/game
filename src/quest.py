"""
Sistem Quest, Dialog Typewriter, dan Peta Kartografi Dinamis Aell (World Map)
untuk 'Ashes of Oakhaven: The Hollow Crown'.
"""
import math
import pygame
from src.config import (
    get_screen_size, STAGE_CONFIGS, get_font,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)
from src.audio import audio_manager
from src.combat import FloatingText


class Quest:
    def __init__(self, qid, title, desc, target_count=1, exp_reward=50, gold_reward=25, karma_reward=0):
        self.id = qid
        self.title = title
        self.desc = desc
        self.target_count = target_count
        self.current_count = 0
        self.is_completed = False
        self.is_claimed = False
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward
        self.karma_reward = karma_reward

    def add_progress(self, amount=1):
        if self.is_completed:
            return False
        self.current_count = min(self.target_count, self.current_count + amount)
        if self.current_count >= self.target_count:
            self.is_completed = True
            return True
        return False


class QuestManager:
    def __init__(self):
        self.quests = [
            Quest(
                "q1_awaken",
                "1. Suaka Oakhaven (Rusty Anchor)",
                "Bicaralah dengan Elara atau Vektor di aula Hub untuk memahami Suar Kematian.",
                target_count=1, exp_reward=40, gold_reward=25, karma_reward=5
            ),
            Quest(
                "q2_training",
                "2. Uji Kemampuan Tempur",
                "Latih tebasan (LMB), Ash Cleave (RMB), & Dodge (Spasi) di Training Yard.",
                target_count=3, exp_reward=75, gold_reward=40
            ),
            Quest(
                "q3_supplies",
                "3. Persiapan Bengkel & Perlengkapan",
                "Tukar Abu di Brog, serahkan material ke Vektor, atau belanja di Gael.",
                target_count=1, exp_reward=80, gold_reward=50
            ),
            Quest(
                "q4_stage1",
                "4. Bab 1: Rawa Kematian (Gargantua)",
                "Masuki Stage 1 lewat Aell/Gerbang Utara & kalahkan Jenderal Gargantua.",
                target_count=1, exp_reward=140, gold_reward=90, karma_reward=5
            ),
            Quest(
                "q5_stage2",
                "5. Bab 2: Hutan Spora (Vespa)",
                "Masuki Stage 2 dan tumbangkan Ratu Spora Vespa (Mycelia).",
                target_count=1, exp_reward=220, gold_reward=140, karma_reward=5
            ),
            Quest(
                "q6_stage3",
                "6. Bab 3: Tungku Gehenna (Ignis)",
                "Lintasi conveyor & lahar Stage 3 untuk mengalahkan Ignis Executioner.",
                target_count=1, exp_reward=320, gold_reward=200, karma_reward=5
            ),
            Quest(
                "q7_stage4",
                "7. Bab 4: Salju Hitam (Valerius)",
                "Taklukkan arena es licin Stage 4 melawan Jenderal Valerius.",
                target_count=1, exp_reward=460, gold_reward=280, karma_reward=5
            ),
            Quest(
                "q8_stage5",
                "8. Bab 5: Ruang Takhta Obsidian",
                "Hadapi Sang Penguasa Abu & Mahkota Kutukan dalam pertarungan 2 fase.",
                target_count=1, exp_reward=800, gold_reward=500
            ),
        ]
        self.active_index = 0

    def sync_active_index(self):
        for idx, q in enumerate(self.quests):
            if not q.is_completed:
                self.active_index = idx
                return
        self.active_index = len(self.quests)

    def get_current_quest(self):
        if 0 <= self.active_index < len(self.quests):
            return self.quests[self.active_index]
        return None

    def advance_progress(self, quest_id, amount=1, player=None, combat_mgr=None):
        for q in self.quests:
            if q.id == quest_id and not q.is_completed:
                completed = q.add_progress(amount)
                if completed:
                    audio_manager.play_sound("levelup")
                    if player:
                        player.gain_exp(q.exp_reward)
                        player.gold += q.gold_reward
                        player.karma += q.karma_reward
                        if combat_mgr:
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 30, f"Quest Selesai: {q.title}!", COLOR_GOLD, font_size=18, is_crit=True)
                            )
                    self.sync_active_index()
                return completed
        return False


class DialogueSystem:
    def __init__(self):
        self.is_active = False
        self.npc_name = ""
        self.npc_portrait = None
        self.dialogue_pages = []
        self.current_page = 0
        self.choices = []  # list of (text, callback)
        self.typewriter_text = ""
        self.char_index = 0
        self.typewriter_speed = 48.0
        self.beep_timer = 0.0
        self.anim_time = 0.0
        self.open_progress = 0.0

    def start_dialogue(self, npc_name, pages, portrait=None, choices=None):
        self.is_active = True
        self.npc_name = npc_name
        self.npc_portrait = portrait
        self.dialogue_pages = pages
        self.current_page = 0
        self.choices = choices or []
        self.char_index = 0
        self.typewriter_text = ""
        self.anim_time = 0.0
        self.open_progress = 0.0
        audio_manager.play_sound("accept")

    def close(self):
        self.is_active = False
        audio_manager.play_sound("cancel")

    def update(self, dt):
        if not self.is_active or not self.dialogue_pages:
            return
        self.anim_time += dt
        if self.open_progress < 1.0:
            self.open_progress = min(1.0, self.open_progress + dt * 6.0)
        full_text = self.dialogue_pages[self.current_page]
        if self.char_index < len(full_text):
            self.char_index += self.typewriter_speed * dt
            self.typewriter_text = full_text[:int(self.char_index)]
            self.beep_timer += dt
            if self.beep_timer >= 0.08:
                self.beep_timer = 0.0
                audio_manager.play_sound("dialogue_beep")
        else:
            self.typewriter_text = full_text

    def next_page_or_finish(self):
        if not self.is_active:
            return
        full_text = self.dialogue_pages[self.current_page]
        if len(self.typewriter_text) < len(full_text):
            self.typewriter_text = full_text
            self.char_index = len(full_text)
            return

        if self.current_page < len(self.dialogue_pages) - 1:
            self.current_page += 1
            self.char_index = 0
            self.typewriter_text = ""
            audio_manager.play_sound("accept")
        elif not self.choices:
            self.close()

    def _get_layout(self):
        view_w, view_h = get_screen_size()
        box_w = min(980, view_w - 40)
        box_h = 190
        box_x = (view_w - box_w) // 2
        box_y = view_h - box_h - 25
        start_cy = box_y + 125
        n_choices = len(self.choices)
        avail_w = box_w - 150
        choice_w = min(245, max(160, (avail_w - max(0, n_choices - 1) * 14) // max(1, n_choices)))
        choice_rects = [
            pygame.Rect(box_x + 130 + idx * (choice_w + 14), start_cy, choice_w, 36)
            for idx in range(n_choices)
        ]
        return box_x, box_y, box_w, box_h, choice_rects

    def handle_key(self, key):
        if not self.is_active:
            return False
        if key in (pygame.K_SPACE, pygame.K_RETURN):
            self.next_page_or_finish()
            return True
        return False

    def handle_click(self, mouse_pos):
        if not self.is_active:
            return False

        box_x, box_y, box_w, box_h, choice_rects = self._get_layout()

        if self.choices and self.char_index >= len(self.dialogue_pages[self.current_page]):
            for idx, c_rect in enumerate(choice_rects):
                if c_rect.collidepoint(mouse_pos):
                    _, callback = self.choices[idx]
                    audio_manager.play_sound("accept")
                    if callback:
                        callback()
                    return True

        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        if box_rect.collidepoint(mouse_pos):
            self.next_page_or_finish()
            return True

        return False

    def draw(self, surface, mouse_pos):
        if not self.is_active:
            return

        box_x, box_y, box_w, box_h, choice_rects = self._get_layout()
        slide_offset = int((1.0 - self.open_progress) * 28) if hasattr(self, "open_progress") else 0
        box_y += slide_offset

        panel_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BG, (0, 0, box_w, box_h), border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), 2, border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER_LIGHT, (4, 4, box_w - 8, box_h - 8), 1, border_radius=10)
        surface.blit(panel_surf, (box_x, box_y))

        portrait_bob = int(math.sin(self.anim_time * 3.8) * 2.5) if hasattr(self, "anim_time") else 0
        portrait_box = pygame.Rect(box_x + 20, box_y + 20 + portrait_bob, 90, 90)
        pygame.draw.rect(surface, (18, 20, 28), portrait_box, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, portrait_box, 1, border_radius=8)

        if self.npc_portrait:
            surface.blit(self.npc_portrait, (box_x + 25, box_y + 25 + portrait_bob))
        else:
            p_font = get_font(32, bold=True)
            p_text = p_font.render(self.npc_name[:1], True, COLOR_GOLD)
            surface.blit(p_text, (portrait_box.centerx - p_text.get_width() // 2, portrait_box.centery - p_text.get_height() // 2))

        name_font = get_font(16, bold=True)
        name_surf = name_font.render(self.npc_name, True, COLOR_GOLD)
        surface.blit(name_surf, (box_x + 130, box_y + 20))

        text_font = get_font(14)
        words = self.typewriter_text.split(" ")
        lines = []
        cur_line = []
        max_w = box_w - 160
        for w in words:
            test = " ".join(cur_line + [w])
            if text_font.size(test)[0] < max_w:
                cur_line.append(w)
            else:
                lines.append(" ".join(cur_line))
                cur_line = [w]
        if cur_line:
            lines.append(" ".join(cur_line))

        for idx, line in enumerate(lines[:3]):
            l_surf = text_font.render(line, True, COLOR_WHITE)
            surface.blit(l_surf, (box_x + 130, box_y + 50 + idx * 22))

        if self.choices and self.char_index >= len(self.dialogue_pages[self.current_page]):
            c_font = get_font(13, bold=True)
            for idx, c_rect in enumerate(choice_rects):
                choice_text, _ = self.choices[idx]
                is_chover = c_rect.collidepoint(mouse_pos)
                bg_col = (180, 140, 40) if is_chover else (35, 40, 55)
                pygame.draw.rect(surface, bg_col, c_rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_GOLD, c_rect, 1, border_radius=6)

                ctxt = c_font.render(choice_text, True, COLOR_WHITE if not is_chover else (15, 15, 20))
                surface.blit(ctxt, (c_rect.centerx - ctxt.get_width() // 2, c_rect.centery - ctxt.get_height() // 2))
        else:
            hint_font = get_font(11, italic=True)
            hint_surf = hint_font.render("[Klik Kiri / Spasi untuk melanjutkan ->]", True, COLOR_TEXT_MUTED)
            surface.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 25, box_y + box_h - 26))


class CartographyMapUI:
    """Layar Peta Dunia Dinamis Aell (Map Reader) untuk Fast Travel ke 5 Bioma GDD + Dungeon."""
    def __init__(self):
        self.is_open = False
        self.nodes = [
            # (tmx, title, subtitle, rel_x, rel_y, color, req_beacon)
            ("stage4_frost.tmx", "4. Dungeon 4: Salju Hitam", "Bos: Valerius (Lv.41-55)", 0.50, 0.22, (130, 205, 250), "stage3_gehenna.tmx"),
            ("stage3_gehenna.tmx", "3. Dungeon 3: Tungku Gehenna", "Bos: Ignis (Lv.26-40)", 0.21, 0.50, (240, 120, 45), "stage2_spore.tmx"),
            ("stage5_throne.tmx", "5. Final Boss Domain", "Mahkota Kutukan (Laser!)", 0.50, 0.50, (220, 60, 75), "stage4_frost.tmx"),
            ("stage2_spore.tmx", "2. Dungeon 2: Hutan Spora", "Bos: Vespa (Lv.11-25)", 0.79, 0.50, (185, 95, 235), "stage1_swamp.tmx"),
            ("stage1_swamp.tmx", "1. Dungeon 1: Rawa Kematian", "Bos: Gargantua (Lv.1-10)", 0.50, 0.77, (110, 195, 115), None),
            ("dungeon1.tmx", "Labirin Dungeon 1", "Ekspedisi Klasik", 0.19, 0.80, (140, 160, 195), None),
            ("dungeon2.tmx", "Labirin Dungeon 2", "Aula Raja Iblis", 0.81, 0.80, (180, 140, 210), None),
        ]

    def open(self):
        self.is_open = True
        audio_manager.play_sound("accept")

    def close(self):
        if self.is_open:
            self.is_open = False
            audio_manager.play_sound("cancel")

    def is_unlocked(self, tmx_path, player):
        for ntmx, _, _, _, _, _, req in self.nodes:
            if ntmx == tmx_path:
                if req is None:
                    return True
                return req in getattr(player, "beacons_cleared", set())
        return False

    def _get_layout(self):
        view_w, view_h = get_screen_size()
        pw, ph = min(820, view_w - 40), min(520, view_h - 40)
        px = (view_w - pw) // 2
        py = (view_h - ph) // 2
        close_rect = pygame.Rect(px + pw - 36, py + 16, 24, 24)
        node_rects = []
        bw = min(215, max(175, int(pw * 0.26)))
        bh = min(68, max(56, int(ph * 0.13)))
        for tmx, title, sub, rx, ry, col, req in self.nodes:
            bx = int(px + rx * pw - bw // 2)
            by = int(py + 60 + ry * (ph - 105) - bh // 2)
            node_rects.append((tmx, title, sub, col, req, pygame.Rect(bx, by, bw, bh)))
        return px, py, pw, ph, close_rect, node_rects

    def handle_click(self, mouse_pos, player, switch_map_fn, ui_mgr):
        if not self.is_open:
            return False
        _, _, _, _, close_rect, node_rects = self._get_layout()
        if close_rect.collidepoint(mouse_pos):
            self.close()
            return True

        for tmx, title, _, _, _, rect in node_rects:
            if rect.collidepoint(mouse_pos):
                if not self.is_unlocked(tmx, player):
                    audio_manager.play_sound("cancel")
                    ui_mgr.show_notification(f"Kalahkan bos stage sebelumnya untuk membuka {title}!", duration=2.5)
                    return True
                cfg = STAGE_CONFIGS.get(tmx, {})
                sx, sy = cfg.get("spawn", (200, 200))
                self.is_open = False
                audio_manager.play_sound("accept")
                switch_map_fn(tmx, sx, sy)
                return True
        return False

    def draw(self, surface, mouse_pos, player):
        if not self.is_open:
            return
        view_w, view_h = get_screen_size(surface)
        px, py, pw, ph, close_rect, node_rects = self._get_layout()

        dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, COLOR_PANEL_BG, (px, py, pw, ph), border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, (px, py, pw, ph), 2, border_radius=12)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, (px + 4, py + 4, pw - 8, ph - 8), 1, border_radius=10)

        t_font = get_font(20, bold=True)
        surface.blit(t_font.render("PETA KARTOGRAFI DINAMIS AELL (EKSPEDISI 5 BIOMA)", True, COLOR_GOLD), (px + 24, py + 16))
        sub_font = get_font(12, italic=True)
        beacons = len([b for b in getattr(player, "beacons_cleared", set()) if b.startswith("stage")])
        surface.blit(sub_font.render(f"Cakupan Peta: Lv.{player.level} | Suar Kematian Padam: {beacons}/5 — Klik bioma terbuka untuk berangkat!", True, COLOR_TEXT_MUTED), (px + 24, py + 44))

        c_font = get_font(16, bold=True)
        c_surf = c_font.render("X", True, (220, 80, 80))
        surface.blit(c_surf, (close_rect.centerx - c_surf.get_width() // 2, close_rect.centery - c_surf.get_height() // 2))

        # Garis penghubung antar bioma ke pusat Takhta
        center_pos = (px + int(0.50 * pw), py + 60 + int(0.50 * (ph - 105)))
        for _, _, _, _, _, rect in node_rects[:5]:
            pygame.draw.line(surface, (75, 70, 90), rect.center, center_pos, 2)

        n_font = get_font(13, bold=True)
        s_font = get_font(11)
        for tmx, title, sub, col, _, rect in node_rects:
            unlocked = self.is_unlocked(tmx, player)
            cleared = tmx in getattr(player, "beacons_cleared", set())
            hover = rect.collidepoint(mouse_pos)

            bg = (42, 48, 68) if (hover and unlocked) else ((28, 32, 44) if unlocked else (20, 20, 28))
            border = COLOR_GOLD if cleared else (col if unlocked else (65, 65, 75))
            pygame.draw.rect(surface, bg, rect, border_radius=8)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)

            status_tag = "[SELESAI]" if cleared else ("[TERBUKA]" if unlocked else "[TERSEGEL]")
            surface.blit(n_font.render(title, True, COLOR_WHITE if unlocked else COLOR_TEXT_MUTED), (rect.x + 10, rect.y + 8))
            surface.blit(s_font.render(sub, True, COLOR_TEXT_MUTED), (rect.x + 10, rect.y + 29))
            surface.blit(s_font.render(status_tag, True, COLOR_GOLD if cleared else (col if unlocked else (160, 80, 80))), (rect.x + 10, rect.y + 46))

        hint_font = get_font(11)
        surface.blit(hint_font.render("[ESC] / [E] Tutup Peta", True, COLOR_TEXT_MUTED), (px + 24, py + ph - 26))
