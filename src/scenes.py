"""
Scene Flow Manager (Main Menu, Prolog Interaktif, & Klimaks/Ending GDD)
untuk 'Ashes of Oakhaven: The Hollow Crown'.
"""
import os
import random
import pygame
from src.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, get_font,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT, COLOR_CRIT
)
from src.audio import audio_manager
from src.save_system import SaveSystem


class AshParticleOverlay:
    """Efek hujan abu & bara api yang jatuh perlahan di latar menu & prolog."""
    def __init__(self, count=48):
        self.particles = [
            {
                "x": random.uniform(0, SCREEN_WIDTH),
                "y": random.uniform(0, SCREEN_HEIGHT),
                "vx": random.uniform(-22, -6),
                "vy": random.uniform(22, 55),
                "size": random.randint(2, 4),
                "ember": random.random() < 0.25,
            }
            for _ in range(count)
        ]

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] > SCREEN_HEIGHT:
                p["y"] = -5
                p["x"] = random.uniform(0, SCREEN_WIDTH + 80)
            if p["x"] < -10:
                p["x"] = SCREEN_WIDTH + 5

    def draw(self, surface):
        for p in self.particles:
            col = (255, 110, 45) if p["ember"] else (170, 170, 185)
            pygame.draw.circle(surface, col, (int(p["x"]), int(p["y"])), p["size"])


class TitleScreenScene:
    def __init__(self):
        self.bg_surf = None
        if os.path.exists("assets/ui/title_bg.png"):
            try:
                img = pygame.image.load("assets/ui/title_bg.png").convert()
                self.bg_surf = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception:
                self.bg_surf = None
        self.ash = AshParticleOverlay(55)
        self.show_controls = False

    def _get_buttons(self):
        bw, bh = 300, 48
        bx = 85
        start_y = 335
        has_save = SaveSystem.has_save()
        return [
            ("new_game", "Permainan Baru", pygame.Rect(bx, start_y, bw, bh), True),
            ("continue", "Lanjutkan (Load Save)", pygame.Rect(bx, start_y + 62, bw, bh), has_save),
            ("controls", "Panduan Kontrol", pygame.Rect(bx, start_y + 124, bw, bh), True),
            ("exit", "Keluar Game", pygame.Rect(bx, start_y + 186, bw, bh), True),
        ]

    def update(self, dt):
        self.ash.update(dt)

    def handle_event(self, event):
        if self.show_controls:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.show_controls = False
                audio_manager.play_sound("cancel")
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for action, _, rect, enabled in self._get_buttons():
                if rect.collidepoint((mx, my)) and enabled:
                    audio_manager.play_sound("accept")
                    if action == "controls":
                        self.show_controls = True
                        return None
                    return action
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                audio_manager.play_sound("accept")
                return "continue" if SaveSystem.has_save() else "new_game"
            if event.key == pygame.K_ESCAPE:
                return "exit"
        return None

    def draw(self, surface, mouse_pos):
        if self.bg_surf:
            surface.blit(self.bg_surf, (0, 0))
            shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            shade.fill((10, 8, 16, 110))
            surface.blit(shade, (0, 0))
        else:
            surface.fill((18, 14, 24))

        self.ash.draw(surface)

        t_font = get_font(44, bold=True)
        s_font = get_font(20, italic=True)
        c_font = get_font(13)

        title_shadow = t_font.render("ASHES OF OAKHAVEN", True, (0, 0, 0))
        title_surf = t_font.render("ASHES OF OAKHAVEN", True, COLOR_GOLD)
        surface.blit(title_shadow, (87, 132))
        surface.blit(title_surf, (85, 130))

        sub_surf = s_font.render("The Hollow Crown  —  2D Action RPG", True, COLOR_WHITE)
        surface.blit(sub_surf, (88, 190))

        surface.blit(c_font.render("Aplikasi Perancangan Program Game — Kelompok 1", True, COLOR_TEXT_MUTED), (88, 226))

        b_font = get_font(16, bold=True)
        for _, label, rect, enabled in self._get_buttons():
            hover = rect.collidepoint(mouse_pos) and enabled
            bg = (165, 115, 35, 235) if hover else ((28, 30, 44, 220) if enabled else (24, 24, 30, 175))
            border = COLOR_GOLD if enabled else (65, 65, 75)
            box = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(box, bg, (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(box, border, (0, 0, rect.width, rect.height), 2, border_radius=8)
            surface.blit(box, rect.topleft)

            txt_col = (15, 15, 20) if hover else (COLOR_WHITE if enabled else (110, 110, 120))
            txt = b_font.render(label, True, txt_col)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        if self.show_controls:
            dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 195))
            surface.blit(dim, (0, 0))
            pw, ph = 560, 390
            px, py = (SCREEN_WIDTH - pw) // 2, (SCREEN_HEIGHT - ph) // 2
            pygame.draw.rect(surface, (22, 24, 34), (px, py, pw, ph), border_radius=12)
            pygame.draw.rect(surface, COLOR_GOLD, (px, py, pw, ph), 2, border_radius=12)
            surface.blit(get_font(20, bold=True).render("PANDUAN KONTROL OAKHAVEN", True, COLOR_GOLD), (px + 28, py + 22))
            lines = [
                ("WASD / Panah", "Bergerak 8 arah (Top-Down)"),
                ("Shift Kiri (Tahan)", "Sprint (+40% Speed, konsumsi STA)"),
                ("Spasi", "Dodge Roll (15 STA, i-frame & Perfect Dodge Slow-Mo)"),
                ("Klik Kiri (LMB)", "Tebasan Pedang Ringan (5 STA)"),
                ("Klik Kanan (RMB)", "Skill Berat Ash Cleave (30 STA)"),
                ("E / B / 1 / 2 / TAB", "Interaksi / Tas / Potion / Minimap"),
            ]
            f1, f2 = get_font(14, bold=True), get_font(14)
            for idx, (k, desc) in enumerate(lines):
                surface.blit(f1.render(k, True, COLOR_GOLD), (px + 28, py + 76 + idx * 40))
                surface.blit(f2.render(desc, True, COLOR_WHITE), (px + 205, py + 76 + idx * 40))
            surface.blit(get_font(12, italic=True).render("[Klik atau tekan tombol apa saja untuk kembali]", True, COLOR_TEXT_MUTED), (px + 135, py + ph - 36))


class PrologScene:
    """Cutscene pembuka Prolog Hujan Abu + penyelamatan Aell menuju Hub Rusty Anchor."""
    SLIDES = [
        (
            "PROLOG: HUJAN ABU DI OAKHAVEN",
            "Langit berwarna merah berkarat tertutup asap tebal. Hujan abu turun menutupi puing-puing desa Oakhaven.",
            "Ethan merangkak keluar dari reruntuhan kedai kayu. Di bawah kakinya tergeletak syal adiknya yang setengah hangus. Ia mengikat syal itu erat di pergelangan tangannya.",
        ),
        (
            "BISIKAN ROH LELUHUR",
            "\"Bangkitlah... Abu dari saudaramu menuntut balas. Angkat pedangmu atau biarkan jiwamu membusuk bersama reruntuhan ini.\"",
            "Dari kejauhan, barisan monster berzirah leleh — para Karak — melangkah menuju empat Suar Kematian yang menyegel seluruh negeri.",
        ),
        (
            "BAB 2: DINDING KEPUTUSASAAN",
            "Dengan pedang pinjaman, Ethan mencoba menerobos perbatasan Rawa Kematian dan menghadapi Jenderal Gargantua.",
            "Namun serangan raksasa itu mematahkan pedangnya hingga HP Ethan tersisa 1%! Tepat sebelum eksekusi, panah asap hijau Aell meledak dan menarik Ethan melarikan diri.",
        ),
        (
            "SUAKA ORANG-ORANG BUANGAN (RUSTY ANCHOR)",
            "Ethan terbangun di Hub Oakhaven di dekat Api Unggun hangat.",
            "Temui Vektor (Guildmaster), Aell (Map Reader), Gael (Pedagang Senjata), Elara, dan Brog untuk melatih skill, menempa Bilah Penebusan, dan menumpas 4 Suar Kematian!",
        ),
    ]

    def __init__(self):
        self.index = 0
        self.ash = AshParticleOverlay(45)

    def update(self, dt):
        self.ash.update(dt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "done"
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                return self._next()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._next()
        return None

    def _next(self):
        audio_manager.play_sound("accept")
        self.index += 1
        if self.index >= len(self.SLIDES):
            return "done"
        return None

    def draw(self, surface):
        surface.fill((14, 11, 18))
        self.ash.draw(surface)

        heading, body1, body2 = self.SLIDES[self.index]
        pw, ph = 920, 340
        px, py = (SCREEN_WIDTH - pw) // 2, (SCREEN_HEIGHT - ph) // 2

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, pw, ph), border_radius=14)
        pygame.draw.rect(panel, COLOR_GOLD, (0, 0, pw, ph), 2, border_radius=14)
        surface.blit(panel, (px, py))

        surface.blit(get_font(22, bold=True).render(heading, True, COLOR_GOLD), (px + 36, py + 32))
        self._draw_wrapped(surface, body1, px + 36, py + 90, pw - 72, get_font(16), COLOR_WHITE)
        self._draw_wrapped(surface, body2, px + 36, py + 180, pw - 72, get_font(15), (210, 210, 225))

        hint = f"Slide {self.index + 1}/{len(self.SLIDES)}  |  [Klik / Spasi: Lanjut]  |  [ESC: Lewati Prolog]"
        h_surf = get_font(12, italic=True).render(hint, True, COLOR_TEXT_MUTED)
        surface.blit(h_surf, (px + pw - h_surf.get_width() - 32, py + ph - 36))

    def _draw_wrapped(self, surface, text, x, y, max_w, font, color):
        words = text.split(" ")
        lines, cur = [], []
        for w in words:
            if font.size(" ".join(cur + [w]))[0] < max_w:
                cur.append(w)
            else:
                lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        for idx, line in enumerate(lines[:4]):
            surface.blit(font.render(line, True, color), (x, y + idx * 24))


class EndingScene:
    """
    Menangani Klimaks Ruang Takhta Obsidian:
    - Pilihan Terakhir bila Karma netral (-29..19)
    - QTE Good Ending (tekan Spasi berkali-kali untuk membelah Mahkota Kutukan)
    - Cutscene Epilog Good Ending / Bad Ending + Credits
    """
    def __init__(self, player):
        self.player = player
        self.karma = getattr(player, "karma", 0)
        self.is_cursed_weapon = getattr(player, "weapon_id", "") == "bloodthirst_blade"
        self.qte_progress = 20.0
        self.flash_alpha = 0.0
        self.ash = AshParticleOverlay(35)

        if self.karma <= -30 or (self.is_cursed_weapon and self.karma < 20):
            self.stage = "bad_epilogue"
            audio_manager.stop_music()
            audio_manager.play_sound("ending_bad")
        elif self.karma >= 20:
            self.stage = "good_qte"
        else:
            self.stage = "choice"

    def _get_choice_rects(self):
        return (
            pygame.Rect(SCREEN_WIDTH // 2 - 330, 420, 300, 56),
            pygame.Rect(SCREEN_WIDTH // 2 + 30, 420, 300, 56),
        )

    def _get_end_buttons(self):
        return (
            pygame.Rect(SCREEN_WIDTH // 2 - 260, 560, 240, 48),
            pygame.Rect(SCREEN_WIDTH // 2 + 20, 560, 240, 48),
        )

    def update(self, dt):
        self.ash.update(dt)
        if self.stage == "good_qte":
            # Tarikan mahkota perlahan menurun jika pemain tidak menekan Spasi
            self.qte_progress = max(0.0, self.qte_progress - 9.0 * dt)
        if self.flash_alpha > 0:
            self.flash_alpha = max(0.0, self.flash_alpha - 180.0 * dt)

    def handle_event(self, event):
        if self.stage == "choice":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn_good, btn_bad = self._get_choice_rects()
                if btn_good.collidepoint(event.pos):
                    audio_manager.play_sound("accept")
                    self.stage = "good_qte"
                elif btn_bad.collidepoint(event.pos):
                    audio_manager.stop_music()
                    audio_manager.play_sound("ending_bad")
                    self.stage = "bad_epilogue"
            return None

        if self.stage == "good_qte":
            triggered = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or (
                event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            )
            if triggered:
                self.qte_progress = min(100.0, self.qte_progress + 14.0)
                audio_manager.play_sound("slash1")
                if self.qte_progress >= 100.0:
                    self.flash_alpha = 255.0
                    self.stage = "good_epilogue"
                    audio_manager.stop_music()
                    audio_manager.play_sound("ending_good")
            return None

        if self.stage in ("good_epilogue", "bad_epilogue"):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn_hub, btn_menu = self._get_end_buttons()
                if btn_hub.collidepoint(event.pos):
                    audio_manager.play_sound("accept")
                    return "hub"
                if btn_menu.collidepoint(event.pos):
                    audio_manager.play_sound("accept")
                    return "menu"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "hub"
        return None

    def draw(self, surface, mouse_pos):
        if self.stage == "good_epilogue":
            surface.fill((36, 48, 72))
        elif self.stage == "bad_epilogue":
            surface.fill((18, 8, 12))
        else:
            surface.fill((15, 12, 22))
        self.ash.draw(surface)

        pw, ph = 900, 480
        px, py = (SCREEN_WIDTH - pw) // 2, 110
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (18, 20, 30, 230), (0, 0, pw, ph), border_radius=14)
        border_col = (240, 210, 120) if self.stage == "good_epilogue" else ((220, 60, 60) if self.stage == "bad_epilogue" else COLOR_GOLD)
        pygame.draw.rect(panel, border_col, (0, 0, pw, ph), 2, border_radius=14)
        surface.blit(panel, (px, py))

        t_font = get_font(26, bold=True)
        b_font = get_font(15)

        if self.stage == "choice":
            surface.blit(t_font.render("KLIMAKS: MAHKOTA KUTUKAN DI RUANG TAKHTA", True, COLOR_GOLD), (px + 40, py + 36))
            msg = "\"Wadah yang rapuh telah pecah... Kebencianmu menyala terang, Anak Oakhaven. Naiklah ke takhta, atau lawan dirimu sendiri.\""
            surface.blit(b_font.render(msg[:88], True, COLOR_WHITE), (px + 40, py + 110))
            surface.blit(b_font.render(msg[88:], True, COLOR_WHITE), (px + 40, py + 138))
            surface.blit(get_font(14, italic=True).render(f"Karma Saat Ini: {self.karma}", True, COLOR_TEXT_ACCENT), (px + 40, py + 190))

            btn_good, btn_bad = self._get_choice_rects()
            for rect, lbl, col in [
                (btn_good, "Cabut Kutukan (Bilah Penebusan)", (45, 115, 145)),
                (btn_bad, "Raih Mahkota (Raja Iblis Baru)", (145, 40, 45)),
            ]:
                pygame.draw.rect(surface, col, rect, border_radius=8)
                pygame.draw.rect(surface, COLOR_GOLD, rect, 2, border_radius=8)
                ts = get_font(14, bold=True).render(lbl, True, COLOR_WHITE)
                surface.blit(ts, (rect.centerx - ts.get_width() // 2, rect.centery - ts.get_height() // 2))

        elif self.stage == "good_qte":
            surface.blit(t_font.render("LAWAN TARIKAN MAHKOTA KUTUKAN!", True, COLOR_TEXT_ACCENT), (px + 40, py + 40))
            surface.blit(b_font.render("Siluet Vektor, Aell, dan Gael berdiri menopang punggung Ethan!", True, COLOR_WHITE), (px + 40, py + 100))
            surface.blit(b_font.render("TEKAN [SPASI] ATAU [KLIK KIRI] BERKALI-KALI UNTUK MEMBELAH MAHKOTA!", True, COLOR_GOLD), (px + 40, py + 145))

            bar_rect = pygame.Rect(px + 90, py + 240, pw - 180, 38)
            pygame.draw.rect(surface, (35, 35, 50), bar_rect, border_radius=8)
            fill_w = int((bar_rect.width - 4) * (self.qte_progress / 100.0))
            pygame.draw.rect(surface, (110, 220, 255), (bar_rect.x + 2, bar_rect.y + 2, fill_w, bar_rect.height - 4), border_radius=6)
            pygame.draw.rect(surface, COLOR_GOLD, bar_rect, 2, border_radius=8)
            pct_txt = get_font(15, bold=True).render(f"{int(self.qte_progress)}%", True, COLOR_WHITE)
            surface.blit(pct_txt, (bar_rect.centerx - pct_txt.get_width() // 2, bar_rect.centery - pct_txt.get_height() // 2))

        elif self.stage == "good_epilogue":
            surface.blit(t_font.render("GOOD ENDING: BILAH PENEBUSAN (MENCABUT KUTUKAN)", True, COLOR_GOLD), (px + 40, py + 36))
            lines = [
                "Mahkota: \"KAU... KAU AKAN KOSONG TANPAKU! APA YANG TERSISA JIKA DENDAM INI MATI?!\"",
                "Ethan: \"...Sesuatu yang layak untuk dilindungi.\"",
                "",
                "Dengan ayunan vertikal Bilah Penebusan, Mahkota Abu terbelah dua. Cahaya matahari pagi menyinari",
                "ruang takhta untuk pertama kalinya. Syal adiknya kini bersih dari abu. Ethan melangkah pulang",
                "menuju Oakhaven Hub di mana Vektor, Aell, Gael, Elara, dan para penyintas menunggunya.",
                "",
                "\"Kutukan itu hancur bersama siklus kebencian. Kini saatnya untuk pulang.\"",
            ]
            for idx, ln in enumerate(lines):
                surface.blit(b_font.render(ln, True, COLOR_WHITE if idx != 7 else COLOR_GOLD), (px + 40, py + 100 + idx * 30))

        elif self.stage == "bad_epilogue":
            surface.blit(t_font.render("BAD ENDING: TAKHTA RAJA IBLIS BARU", True, COLOR_CRIT), (px + 40, py + 36))
            lines = [
                "Langkah Ethan membeku di luar kendali. Pedangnya jatuh berdenting di lantai cermin obsidian.",
                "Saat Mahkota Kutukan mendarat di kepalanya, syal adiknya terbakar menjadi abu dan tertiup angin.",
                "Mata Ethan menyala merah terang saat ia duduk di atas singgasana batu.",
                "",
                "Ethan / The Crown: \"Oakhaven telah menjadi abu... Biarkan seluruh dunia merasakan dingin yang sama.\"",
                "",
                "\"Dendam telah terbayar lunas. Sang Penguasa Abu telah mati... Hidup Raja yang baru.\"",
            ]
            for idx, ln in enumerate(lines):
                surface.blit(b_font.render(ln, True, COLOR_WHITE if idx != 6 else COLOR_CRIT), (px + 40, py + 105 + idx * 32))

        if self.stage in ("good_epilogue", "bad_epilogue"):
            surface.blit(get_font(12, italic=True).render("Credits: Kelompok 1 — Aplikasi Perancangan Program Game", True, COLOR_TEXT_MUTED), (px + 40, py + ph - 45))
            btn_hub, btn_menu = self._get_end_buttons()
            for rect, lbl in [(btn_hub, "Kembali ke Hub Oakhaven"), (btn_menu, "Menu Utama")]:
                hover = rect.collidepoint(mouse_pos)
                pygame.draw.rect(surface, (165, 115, 35) if hover else (35, 40, 58), rect, border_radius=8)
                pygame.draw.rect(surface, COLOR_GOLD, rect, 2, border_radius=8)
                ts = get_font(14, bold=True).render(lbl, True, COLOR_WHITE)
                surface.blit(ts, (rect.centerx - ts.get_width() // 2, rect.centery - ts.get_height() // 2))

        if self.flash_alpha > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self.flash_alpha)))
            surface.blit(flash, (0, 0))
