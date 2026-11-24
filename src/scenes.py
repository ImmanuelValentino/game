"""
Scene Flow Manager (Main Menu, Prolog Interaktif, & Klimaks/Ending GDD)
untuk 'Ashes of Oakhaven: The Hollow Crown'.
"""
import math
import os
import random
import pygame
from src.config import (
    get_screen_size, get_font,
    COLOR_PANEL_BG, COLOR_PANEL_BORDER, COLOR_PANEL_BORDER_LIGHT,
    COLOR_WHITE, COLOR_GOLD, COLOR_TEXT_MUTED, COLOR_TEXT_ACCENT, COLOR_CRIT
)
from src.audio import audio_manager
from src.player import load_gif_frames
from src.save_system import SaveSystem


def _load_actor_anim(path, size=(72, 72)):
    raw = load_gif_frames(path, fallback_size=size)
    return [pygame.transform.scale(f, size) for f in raw]


class AshParticleOverlay:
    """Efek hujan abu & bara api yang jatuh perlahan di latar menu & prolog."""
    def __init__(self, count=48):
        view_w, view_h = get_screen_size()
        self.particles = [
            {
                "x": random.uniform(0, view_w),
                "y": random.uniform(0, view_h),
                "vx": random.uniform(-22, -6),
                "vy": random.uniform(22, 55),
                "size": random.randint(2, 4),
                "ember": random.random() < 0.25,
            }
            for _ in range(count)
        ]

    def update(self, dt, view_size=None):
        view_w, view_h = view_size if view_size is not None else get_screen_size()
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] > view_h:
                p["y"] = -5
                p["x"] = random.uniform(0, view_w + 80)
            if p["x"] < -10:
                p["x"] = view_w + 5

    def draw(self, surface):
        for p in self.particles:
            col = (255, 110, 45) if p["ember"] else (170, 170, 185)
            pygame.draw.circle(surface, col, (int(p["x"]), int(p["y"])), p["size"])


class TitleScreenScene:
    def __init__(self):
        self.bg_raw = None
        self._bg_cache_size = None
        self._bg_scaled = None
        if os.path.exists("assets/ui/title_bg.png"):
            try:
                self.bg_raw = pygame.image.load("assets/ui/title_bg.png").convert()
            except Exception:
                self.bg_raw = None
        self.ash = AshParticleOverlay(55)
        self.show_controls = False

    def _get_scaled_bg(self, view_w, view_h):
        if not self.bg_raw:
            return None
        if self._bg_scaled is None or self._bg_cache_size != (view_w, view_h):
            rw, rh = self.bg_raw.get_size()
            scale = max(view_w / max(1, rw), view_h / max(1, rh))
            sw, sh = max(1, int(round(rw * scale))), max(1, int(round(rh * scale)))
            scaled = pygame.transform.scale(self.bg_raw, (sw, sh))
            crop_x = max(0, (sw - view_w) // 2)
            crop_y = max(0, (sh - view_h) // 2)
            self._bg_scaled = scaled.subsurface(pygame.Rect(crop_x, crop_y, view_w, view_h)).copy()
            self._bg_cache_size = (view_w, view_h)
        return self._bg_scaled

    def _get_buttons(self):
        view_w, view_h = get_screen_size()
        bw, bh = 300, 48
        bx = max(44, int(view_w * 0.066))
        start_y = max(265, min(view_h - 270, int(view_h * 0.46)))
        has_save = SaveSystem.has_save()
        return [
            ("new_game", "Permainan Baru", pygame.Rect(bx, start_y, bw, bh), True),
            ("continue", "Lanjutkan (Load Save)", pygame.Rect(bx, start_y + 62, bw, bh), has_save),
            ("controls", "Panduan Kontrol", pygame.Rect(bx, start_y + 124, bw, bh), True),
            ("exit", "Keluar Game", pygame.Rect(bx, start_y + 186, bw, bh), True),
        ]

    def _get_fullscreen_button(self):
        view_w, _ = get_screen_size()
        return pygame.Rect(view_w - 236, 24, 212, 38)

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
            if self._get_fullscreen_button().collidepoint((mx, my)):
                audio_manager.play_sound("accept")
                return "toggle_fullscreen"
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

    def draw(self, surface, mouse_pos, is_fullscreen=False):
        view_w, view_h = get_screen_size(surface)
        bg = self._get_scaled_bg(view_w, view_h)
        if bg:
            surface.blit(bg, (0, 0))
            shade = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
            shade.fill((10, 8, 16, 110))
            surface.blit(shade, (0, 0))
        else:
            surface.fill((18, 14, 24))

        self.ash.draw(surface)

        t_font = get_font(44, bold=True)
        s_font = get_font(20, italic=True)
        c_font = get_font(13)

        buttons = self._get_buttons()
        bx = buttons[0][2].x
        title_y = max(56, buttons[0][2].y - 205)

        title_shadow = t_font.render("ASHES OF OAKHAVEN", True, (0, 0, 0))
        title_surf = t_font.render("ASHES OF OAKHAVEN", True, COLOR_GOLD)
        surface.blit(title_shadow, (bx + 2, title_y + 2))
        surface.blit(title_surf, (bx, title_y))

        sub_surf = s_font.render("The Hollow Crown  —  2D Action RPG", True, COLOR_WHITE)
        surface.blit(sub_surf, (bx + 3, title_y + 60))

        surface.blit(c_font.render("Aplikasi Perancangan Program Game — Kelompok 1", True, COLOR_TEXT_MUTED), (bx + 3, title_y + 96))

        b_font = get_font(16, bold=True)
        for _, label, rect, enabled in buttons:
            hover = rect.collidepoint(mouse_pos) and enabled
            bg_col = (165, 115, 35, 235) if hover else ((28, 30, 44, 220) if enabled else (24, 24, 30, 175))
            border = COLOR_GOLD if enabled else (65, 65, 75)
            box = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(box, bg_col, (0, 0, rect.width, rect.height), border_radius=8)
            pygame.draw.rect(box, border, (0, 0, rect.width, rect.height), 2, border_radius=8)
            surface.blit(box, rect.topleft)

            txt_col = (15, 15, 20) if hover else (COLOR_WHITE if enabled else (110, 110, 120))
            txt = b_font.render(label, True, txt_col)
            surface.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))

        fs_rect = self._get_fullscreen_button()
        fs_hover = fs_rect.collidepoint(mouse_pos)
        fs_label = "Ukuran Normal [F11]" if is_fullscreen else "Layar Penuh [F11]"
        fs_box = pygame.Surface((fs_rect.width, fs_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(fs_box, (165, 115, 35, 230) if fs_hover else (24, 28, 42, 215), (0, 0, fs_rect.width, fs_rect.height), border_radius=8)
        pygame.draw.rect(fs_box, COLOR_GOLD, (0, 0, fs_rect.width, fs_rect.height), 2, border_radius=8)
        surface.blit(fs_box, fs_rect.topleft)
        fs_txt = get_font(13, bold=True).render(fs_label, True, (15, 15, 20) if fs_hover else COLOR_WHITE)
        surface.blit(fs_txt, (fs_rect.centerx - fs_txt.get_width() // 2, fs_rect.centery - fs_txt.get_height() // 2))

        if self.show_controls:
            dim = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 195))
            surface.blit(dim, (0, 0))
            pw, ph = min(600, view_w - 40), min(430, view_h - 40)
            px, py = (view_w - pw) // 2, (view_h - ph) // 2
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
                ("F11 / Alt+Enter", "Toggle Layar Penuh / Normal (Atau tarik tepi jendela)"),
            ]
            f1, f2 = get_font(14, bold=True), get_font(14)
            for idx, (k, desc) in enumerate(lines):
                surface.blit(f1.render(k, True, COLOR_GOLD), (px + 28, py + 72 + idx * 38))
                surface.blit(f2.render(desc, True, COLOR_WHITE), (px + 205, py + 72 + idx * 38))
            hint_ctrl = get_font(12, italic=True).render("[Klik atau tekan tombol apa saja untuk kembali]", True, COLOR_TEXT_MUTED)
            surface.blit(hint_ctrl, (px + pw // 2 - hint_ctrl.get_width() // 2, py + ph - 32))


class PrologScene:
    """Cutscene pembuka Prolog Hujan Abu beranimasi + penyelamatan Aell menuju Hub Rusty Anchor."""
    SLIDES = [
        (
            "BABAK I: HUJAN ABU DI OAKHAVEN",
            "Ethan — Penyintas Terakhir",
            "Langit berwarna merah berkarat tertutup asap pekat. Hujan abu menyelimuti puing-puing desa Oakhaven.",
            "Ethan merangkak keluar dari reruntuhan kedai kayu. Di bawah kakinya tergeletak syal adiknya yang setengah hangus—ia mengikat syal itu erat di pergelangan tangannya.",
        ),
        (
            "BABAK II: BISIKAN ROH LELUHUR",
            "Roh Penjaga Oakhaven",
            "\"Bangkitlah... Abu keluargamu menuntut jawaban. Angkat bilah leluhur ini atau biarkan namamu terkubur bersama bara.\"",
            "Dari balik kabut, barisan monster berzirah leleh—para Karak—bergerak serentak menjaga empat Suar Kematian yang mengurung wilayah ini.",
        ),
        (
            "BABAK III: DINDING KEPUTUSASAAN",
            "Rawa Kematian & Jenderal Gargantua",
            "Berbekal pedang usang, Ethan nekat menerobos Rawa Kematian demi membalas kehancuran kampung halamannya.",
            "Namun tebasan Jenderal Gargantua menghantamnya hingga nyaris tak sadarkan diri! Tepat pada detik terakhir, ledakan asap hijau Aell membutakan monster itu dan menarik Ethan menjauh.",
        ),
        (
            "BABAK IV: SUAKA ORANG-ORANG BUANGAN",
            "Hub Rusty Anchor — Harapan Baru",
            "Ethan terbangun di hadapan hangatnya Api Unggun Hub Rusty Anchor, tempat berkumpulnya para penyintas yang menolak tunduk pada kutukan.",
            "Bicaralah dengan Vektor (Skill & Tempa), Aell (Peta), Gael (Toko Ramuan & Senjata), Elara, dan Brog untuk bersiap menaklukkan Dungeon 1 hingga Ruang Takhta!",
        ),
    ]

    def __init__(self):
        self.index = 0
        self.ash = AshParticleOverlay(55)
        self.elapsed = 0.0
        self.slide_time = 0.0
        self.char_idx = 0.0
        self.actors = {
            "ethan_e": _load_actor_anim("character/main_Char/Idle_walk_east.gif", (76, 76)),
            "ethan_s": _load_actor_anim("character/main_Char/Idle_walk_south.gif", (76, 76)),
            "aell": _load_actor_anim("character/npc_mapReader/Idle_custom-walking_east.gif", (72, 72)),
            "vektor": _load_actor_anim("character/npc_guild/Idle_breathing-idle_south.gif", (76, 76)),
            "gael": _load_actor_anim("character/npc_formerAdvanture/Idle_breathing-idle_south.gif", (72, 72)),
            "karak": _load_actor_anim("character/monster1/Idle_scary-walk_west (1).gif", (68, 68)),
            "gargantua": _load_actor_anim("character/boss_gargantua/attack_west.gif", (96, 96)),
        }

    def update(self, dt):
        self.ash.update(dt)
        self.elapsed += dt
        self.slide_time += dt
        _, _, b1, b2 = self.SLIDES[self.index]
        total_len = len(b1) + len(b2)
        if self.char_idx < total_len:
            self.char_idx = min(float(total_len), self.char_idx + 68.0 * dt)

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
        _, _, b1, b2 = self.SLIDES[self.index]
        total_len = len(b1) + len(b2)
        if int(self.char_idx) < total_len:
            self.char_idx = float(total_len)
            audio_manager.play_sound("dialogue_beep")
            return None
        audio_manager.play_sound("accept")
        self.index += 1
        self.slide_time = 0.0
        self.char_idx = 0.0
        if self.index >= len(self.SLIDES):
            return "done"
        return None

    def _draw_story_diorama(self, surface, px, dy, pw, dh):
        stage = pygame.Surface((pw, dh), pygame.SRCALPHA)
        sky_colors = [
            (38, 16, 18),
            (22, 20, 38),
            (24, 34, 24),
            (34, 26, 20),
        ]
        stage.fill((*sky_colors[self.index % 4], 235))
        pygame.draw.rect(stage, (18, 16, 24, 255), (0, dh - 36, pw, 36))
        pygame.draw.line(stage, (95, 78, 55, 180), (0, dh - 36), (pw, dh - 36), 2)

        def blit_actor(key, x, y, speed=7.0):
            frames = self.actors[key]
            f = frames[int(self.elapsed * speed) % len(frames)]
            stage.blit(f, (int(x), int(y)))

        if self.index == 0:
            # Ethan & syal merah menyala di tengah abu
            glow_r = 26 + int(math.sin(self.elapsed * 4) * 5)
            pygame.draw.circle(stage, (180, 45, 35, 95), (pw // 2 + 52, dh - 28), glow_r)
            pygame.draw.line(stage, (220, 60, 50), (pw // 2 + 40, dh - 28), (pw // 2 + 70, dh - 34), 4)
            slide_in = min(0.0, (self.slide_time - 0.5) * 80)
            blit_actor("ethan_e", pw // 2 - 55 + slide_in, dh - 92, 5.0)
        elif self.index == 1:
            # Cahaya pedang leluhur + siluet pasukan Karak
            pulse = 34 + int(math.sin(self.elapsed * 5) * 8)
            pygame.draw.circle(stage, (110, 210, 255, 70), (150, dh - 58), pulse)
            blit_actor("ethan_e", 112, dh - 92, 6.0)
            for k in range(3):
                kx = pw - 160 - k * 85 + math.sin(self.elapsed * 2 + k) * 8
                blit_actor("karak", kx, dh - 84, 5.5)
        elif self.index == 2:
            # Benturan Ethan vs Gargantua + Aell melempar bom asap hijau
            dash = min(1.0, self.slide_time / 0.8)
            blit_actor("ethan_e", 130 + dash * 95, dh - 92, 8.0)
            blit_actor("gargantua", pw - 220 - dash * 55, dh - 108, 7.0)
            if self.slide_time > 0.7:
                smoke_r = 18 + int((math.sin(self.elapsed * 6) + 1) * 14)
                pygame.draw.circle(stage, (95, 225, 130, 120), (pw // 2 + 40, dh - 56), smoke_r)
                blit_actor("aell", 60 + min(75, (self.slide_time - 0.7) * 90), dh - 88, 7.0)
        else:
            # Berkumpul di Api Unggun Hub Rusty Anchor
            cx = pw // 2
            f_r = 30 + int(math.sin(self.elapsed * 6) * 5)
            pygame.draw.circle(stage, (255, 145, 45, 75), (cx, dh - 36), f_r)
            pygame.draw.polygon(stage, (255, 195, 65), [(cx - 10, dh - 26), (cx + 10, dh - 26), (cx, dh - 56 - int(math.sin(self.elapsed * 9) * 5))])
            blit_actor("vektor", cx - 170, dh - 94, 4.0)
            blit_actor("ethan_s", cx - 75, dh - 90, 4.0)
            blit_actor("aell", cx + 35, dh - 88, 3.5)
            blit_actor("gael", cx + 115, dh - 90, 4.0)

        pygame.draw.rect(stage, COLOR_PANEL_BORDER_LIGHT, (0, 0, pw, dh), 2, border_radius=12)
        surface.blit(stage, (px, dy))

    def draw(self, surface):
        view_w, view_h = get_screen_size(surface)
        surface.fill((14, 11, 18))
        self.ash.draw(surface)

        heading, speaker, body1, body2 = self.SLIDES[self.index]
        pw = min(920, view_w - 60)
        dh = min(148, max(110, int(view_h * 0.22)))
        ph = min(310, view_h - dh - 70)
        total_h = dh + 14 + ph
        px = (view_w - pw) // 2
        top_y = max(20, (view_h - total_h) // 2)

        self._draw_story_diorama(surface, px, top_y, pw, dh)

        py = top_y + dh + 14
        fade = min(255, int(255 * min(1.0, self.slide_time / 0.25 + 0.35)))
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, COLOR_PANEL_BG, (0, 0, pw, ph), border_radius=14)
        pygame.draw.rect(panel, COLOR_GOLD, (0, 0, pw, ph), 2, border_radius=14)
        panel.set_alpha(fade)
        surface.blit(panel, (px, py))

        surface.blit(get_font(21, bold=True).render(heading, True, COLOR_GOLD), (px + 32, py + 24))
        surface.blit(get_font(13, italic=True).render(speaker, True, COLOR_TEXT_ACCENT), (px + 32, py + 52))

        shown = int(self.char_idx)
        vis_b1 = body1[:min(len(body1), shown)]
        vis_b2 = body2[:max(0, shown - len(body1))]
        self._draw_wrapped(surface, vis_b1, px + 32, py + 84, pw - 64, get_font(15), COLOR_WHITE)
        self._draw_wrapped(surface, vis_b2, px + 32, py + 166, pw - 64, get_font(14), (210, 210, 225))

        bob = int(math.sin(self.elapsed * 5.0) * 3)
        hint = f"Bab {self.index + 1}/{len(self.SLIDES)}  |  [Klik / Spasi: Lanjut ->]  |  [ESC: Masuk ke Hub]"
        h_surf = get_font(12, italic=True).render(hint, True, COLOR_TEXT_MUTED)
        surface.blit(h_surf, (px + pw - h_surf.get_width() - 28, py + ph - 32 + bob // 2))

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
        self.elapsed = 0.0
        self.shake_timer = 0.0
        self.ash = AshParticleOverlay(45)
        self.crown_frames = _load_actor_anim("character/boss_hollow_crown/float_south.gif", (88, 88))
        self.ethan_frames = _load_actor_anim("character/main_Char/Idle_walk_north.gif", (72, 72))
        self.ally_frames = [
            _load_actor_anim("character/npc_guild/Idle_breathing-idle_south.gif", (64, 64)),
            _load_actor_anim("character/npc_mapReader/Idle_custom-walking_south.gif", (60, 60)),
            _load_actor_anim("character/npc_formerAdvanture/Idle_breathing-idle_south.gif", (64, 64)),
        ]

        if self.karma <= -30 or (self.is_cursed_weapon and self.karma < 20):
            self.stage = "bad_epilogue"
            audio_manager.stop_music()
            audio_manager.play_sound("ending_bad")
        elif self.karma >= 20:
            self.stage = "good_qte"
        else:
            self.stage = "choice"

    def _get_panel_layout(self, surface=None):
        view_w, view_h = get_screen_size(surface)
        pw, ph = min(900, view_w - 60), 480
        px = (view_w - pw) // 2
        py = max(24, (view_h - 540) // 2)
        return view_w, view_h, px, py, pw, ph

    def _get_choice_rects(self):
        view_w, _, _, py, _, _ = self._get_panel_layout()
        return (
            pygame.Rect(view_w // 2 - 330, py + 310, 300, 56),
            pygame.Rect(view_w // 2 + 30, py + 310, 300, 56),
        )

    def _get_end_buttons(self):
        view_w, _, _, py, _, ph = self._get_panel_layout()
        by = py + ph + 16
        return (
            pygame.Rect(view_w // 2 - 260, by, 240, 48),
            pygame.Rect(view_w // 2 + 20, by, 240, 48),
        )

    def update(self, dt):
        self.ash.update(dt)
        self.elapsed += dt
        if self.shake_timer > 0:
            self.shake_timer = max(0.0, self.shake_timer - dt)
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
                self.shake_timer = 0.14
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

        view_w, view_h, px, py, pw, ph = self._get_panel_layout(surface)
        ox = int(random.uniform(-4, 4)) if self.shake_timer > 0 else 0
        oy = int(random.uniform(-4, 4)) if self.shake_timer > 0 else 0
        px += ox
        py += oy

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(panel, (18, 20, 30, 230), (0, 0, pw, ph), border_radius=14)
        border_col = (240, 210, 120) if self.stage == "good_epilogue" else ((220, 60, 60) if self.stage == "bad_epilogue" else COLOR_GOLD)
        pygame.draw.rect(panel, border_col, (0, 0, pw, ph), 2, border_radius=14)
        surface.blit(panel, (px, py))

        # Animasi karakter & mahkota di bagian atas panel Ending
        crown_f = self.crown_frames[int(self.elapsed * 6) % len(self.crown_frames)]
        ethan_f = self.ethan_frames[int(self.elapsed * 5) % len(self.ethan_frames)]
        if self.stage in ("choice", "good_qte"):
            bob = int(math.sin(self.elapsed * 4.0) * 5)
            surface.blit(crown_f, (px + pw - 138, py + 24 + bob))
        elif self.stage == "good_epilogue":
            pygame.draw.circle(surface, (255, 225, 130, 80), (px + pw - 95, py + 68), 42)
            surface.blit(ethan_f, (px + pw - 130, py + 32))
        elif self.stage == "bad_epilogue":
            pygame.draw.circle(surface, (220, 30, 45, 90), (px + pw - 95, py + 68), 42)
            surface.blit(crown_f, (px + pw - 138, py + 24))

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

            # Tampilkan siluet para penyintas & Ethan menumpu kekuatan seiring QTE naik
            ally_alpha = min(255, int(110 + self.qte_progress * 1.4))
            for idx, af_list in enumerate(self.ally_frames):
                af = af_list[int(self.elapsed * 4) % len(af_list)].copy()
                af.set_alpha(ally_alpha)
                surface.blit(af, (px + pw // 2 - 140 + idx * 100, py + 315))
            surface.blit(ethan_f, (px + pw // 2 - 36, py + 322))

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
            flash = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self.flash_alpha)))
            surface.blit(flash, (0, 0))
