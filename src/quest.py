"""
Sistem Quest & Dialog untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mengatur alur narasi, tugas pemain (quest progression), serta dialog interaktif dengan Elara, Brog, dan Penjaga.
"""
import pygame
from src.config import (
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT
)
from src.audio import audio_manager

class Quest:
    def __init__(self, qid, title, desc, target_count=1, exp_reward=50, gold_reward=25):
        self.id = qid
        self.title = title
        self.desc = desc
        self.target_count = target_count
        self.current_count = 0
        self.is_completed = False
        self.is_claimed = False
        self.exp_reward = exp_reward
        self.gold_reward = gold_reward

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
                "1. Bangkit dari Abu Oakhaven",
                "Bicaralah dengan Elara di area aula Guild untuk memahami situasi terkini.",
                target_count=1, exp_reward=40, gold_reward=20
            ),
            Quest(
                "q2_training",
                "2. Uji Kemampuan Tempur",
                "Latihlah tebasan pedang (LMB) & skill area (RMB) pada Target Latihan di sebelah timur (0/3).",
                target_count=3, exp_reward=75, gold_reward=40
            ),
            Quest(
                "q3_supplies",
                "3. Persiapan Ekspedisi Rawa",
                "Tukarkan abu di Brog atau beli barang perbekalan di Pedagang Misterius.",
                target_count=1, exp_reward=80, gold_reward=50
            ),
            Quest(
                "q4_gate",
                "4. Lapor ke Penjaga Gerbang Utara",
                "Bicaralah dengan Kapten Penjaga di Gerbang Utara untuk membuka Bab 1: Rawa Kematian.",
                target_count=1, exp_reward=120, gold_reward=80
            ),
        ]
        self.active_index = 0

    def get_current_quest(self):
        if self.active_index < len(self.quests):
            return self.quests[self.active_index]
        return None

    def advance_progress(self, quest_id, amount=1, player=None, combat_mgr=None):
        for idx, q in enumerate(self.quests):
            if q.id == quest_id and not q.is_completed:
                completed = q.add_progress(amount)
                if completed:
                    audio_manager.play_sound("levelup")
                    if player:
                        player.gain_exp(q.exp_reward)
                        player.gold += q.gold_reward
                        if combat_mgr:
                            combat_mgr.floating_texts.append(
                                combat_mgr.FloatingText(player.x + 24, player.y - 30, f"Quest Selesai: {q.title}!", COLOR_GOLD, font_size=18, is_crit=True)
                            )
                    if idx == self.active_index:
                        self.active_index += 1
                return completed
        return False


class DialogueSystem:
    def __init__(self):
        self.is_active = False
        self.npc_name = ""
        self.npc_portrait = None
        self.dialogue_pages = []
        self.current_page = 0
        self.choices = [] # list of (text, callback)
        self.typewriter_text = ""
        self.char_index = 0
        self.typewriter_speed = 45.0 # karakter per detik
        self.beep_timer = 0.0

    def start_dialogue(self, npc_name, pages, portrait=None, choices=None):
        self.is_active = True
        self.npc_name = npc_name
        self.npc_portrait = portrait
        self.dialogue_pages = pages
        self.current_page = 0
        self.choices = choices or []
        self.char_index = 0
        self.typewriter_text = ""
        audio_manager.play_sound("accept")

    def close(self):
        self.is_active = False
        audio_manager.play_sound("cancel")

    def update(self, dt):
        if not self.is_active or not self.dialogue_pages:
            return

        full_text = self.dialogue_pages[self.current_page]
        if self.char_index < len(full_text):
            self.char_index += self.typewriter_speed * dt
            cur_int = int(self.char_index)
            self.typewriter_text = full_text[:cur_int]

            self.beep_timer += dt
            if self.beep_timer >= 0.08:
                self.beep_timer = 0.0
                audio_manager.play_sound("dialogue_beep")
        else:
            self.typewriter_text = full_text

    def next_page_or_finish(self):
        if not self.is_active:
            return
        # Jika teks belum selesai mengetik, langsung tampilkan penuh
        full_text = self.dialogue_pages[self.current_page]
        if len(self.typewriter_text) < len(full_text):
            self.typewriter_text = full_text
            self.char_index = len(full_text)
            return

        # Pindah halaman atau selesai
        if self.current_page < len(self.dialogue_pages) - 1:
            self.current_page += 1
            self.char_index = 0
            self.typewriter_text = ""
            audio_manager.play_sound("accept")
        else:
            if not self.choices:
                self.close()

    def handle_click(self, mouse_pos):
        if not self.is_active:
            return False

        box_w = 980
        box_h = 190
        box_x = (1280 - box_w) // 2
        box_y = 720 - box_h - 25

        # Cek klik pada opsi pilihan (jika ada)
        if self.choices and self.char_index >= len(self.dialogue_pages[self.current_page]):
            start_cy = box_y + 115
            for idx, (choice_text, callback) in enumerate(self.choices):
                c_rect = pygame.Rect(box_x + 130 + idx * 260, start_cy, 245, 36)
                if c_rect.collidepoint(mouse_pos):
                    audio_manager.play_sound("accept")
                    if callback:
                        callback()
                    return True

        # Klik kotak dialog untuk maju halaman
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        if box_rect.collidepoint(mouse_pos):
            self.next_page_or_finish()
            return True

        return False

    def draw(self, surface, mouse_pos):
        if not self.is_active:
            return

        box_w = 980
        box_h = 190
        box_x = (1280 - box_w) // 2
        box_y = 720 - box_h - 25

        # Frame dialog RPG Dark Fantasy
        panel_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BG, (0, 0, box_w, box_h), border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER, (0, 0, box_w, box_h), 2, border_radius=12)
        pygame.draw.rect(panel_surf, COLOR_PANEL_BORDER_LIGHT, (4, 4, box_w - 8, box_h - 8), 1, border_radius=10)
        surface.blit(panel_surf, (box_x, box_y))

        # Portrait NPC di kiri
        portrait_box = pygame.Rect(box_x + 20, box_y + 20, 90, 90)
        pygame.draw.rect(surface, (18, 20, 28), portrait_box, border_radius=8)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER_LIGHT, portrait_box, 1, border_radius=8)

        if self.npc_portrait:
            surface.blit(self.npc_portrait, (box_x + 25, box_y + 25))
        else:
            p_font = pygame.font.SysFont("Segoe UI, Arial", 32, bold=True)
            p_text = p_font.render(self.npc_name[:1], True, COLOR_GOLD)
            surface.blit(p_text, (portrait_box.centerx - p_text.get_width() // 2, portrait_box.centery - p_text.get_height() // 2))

        # Badge Nama NPC
        name_font = pygame.font.SysFont("Segoe UI, Arial", 16, bold=True)
        name_surf = name_font.render(self.npc_name, True, COLOR_GOLD)
        surface.blit(name_surf, (box_x + 130, box_y + 20))

        # Teks Dialog Typewriter
        text_font = pygame.font.SysFont("Segoe UI, Arial", 14)
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

        # Pilihan aksi pemain (jika sudah selesai mengetik)
        if self.choices and self.char_index >= len(self.dialogue_pages[self.current_page]):
            start_cy = box_y + 125
            c_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
            for idx, (choice_text, _) in enumerate(self.choices):
                c_rect = pygame.Rect(box_x + 130 + idx * 260, start_cy, 245, 36)
                is_chover = c_rect.collidepoint(mouse_pos)
                bg_col = (180, 140, 40) if is_chover else (35, 40, 55)
                pygame.draw.rect(surface, bg_col, c_rect, border_radius=6)
                pygame.draw.rect(surface, COLOR_GOLD, c_rect, 1, border_radius=6)

                ctxt = c_font.render(choice_text, True, COLOR_WHITE if not is_chover else (15, 15, 20))
                surface.blit(ctxt, (c_rect.centerx - ctxt.get_width() // 2, c_rect.centery - ctxt.get_height() // 2))
        else:
            # Prompt Lanjutkan / Next
            hint_font = pygame.font.SysFont("Segoe UI, Arial", 11, italic=True)
            hint_surf = hint_font.render("[Klik Kiri / Spasi untuk melanjutkan ➔]", True, COLOR_TEXT_MUTED)
            surface.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 25, box_y + box_h - 26))
