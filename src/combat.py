"""
Combat System untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mengimplementasikan:
- Tebasan pedang ringan (LMB, -5 STA), Skill area berat Ash Cleave (RMB, -30 STA)
- Penolakan input Fatigue saat STA < 10
- Formula kalkulasi damage GDD: ((BaseATK + WeaponATK) / (EnemyDEF*0.5 + 10)) * Mod
- Sistem Proyektil Bullet Hell (terblokir pilar/dinding, dapat di-dodge)
- Jebakan Spora Peledak (Stage 2) & Weighted RNG Drop Table (4 tier rarity)
"""
import math
import os
import random
import pygame
from PIL import Image
from src.config import (
    COLOR_WHITE, COLOR_CRIT, COLOR_GOLD, COLOR_EXP, COLOR_ASH, get_font,
    BASIC_ATTACK_STAMINA, SKILL_ATTACK_STAMINA, PLAYER_DAMAGE_SCALING,
)
from src.audio import audio_manager


DROP_TABLE_TIERS = [
    ("epic", 0.03, ["general_core", "broken_crown"]),
    ("rare", 0.10, ["karak_blood", "pure_steel"]),
    ("uncommon", 0.24, ["spore_intact", "ice_core"]),
    ("common", 0.63, ["bone_shard", "rust_iron"]),
]


def roll_consumable_drop(is_boss=False, tier_mult=1.0, player_drop_mult=1.0):
    """Drop ramuan/boost fungsional dari monster agar langsung masuk ke Hotbar bawah."""
    if is_boss:
        return random.choice(["hp_potion", "attack_boost_potion", "defense_potion", "crit_elixir"])
    chance = min(0.55, 0.28 * max(1.0, tier_mult * 0.85) * player_drop_mult)
    if random.random() > chance:
        return None
    roll = random.random()
    if roll < 0.38:
        return "hp_potion"
    if roll < 0.62:
        return "attack_boost_potion"
    if roll < 0.80:
        return "stamina_tonic"
    if roll < 0.92:
        return "defense_potion"
    return "crit_elixir"


def roll_material_drop(tier_mult=1.0, is_boss=False, player_drop_mult=1.0):
    """Weighted RNG Drop sesuai GDD: P(Drop) = BaseRate * MonsterTierMultiplier."""
    if is_boss:
        return random.choice(["general_core", "broken_crown"])

    mult = tier_mult * player_drop_mult
    roll = random.random()
    acc = 0.0
    for _, base_rate, pool in DROP_TABLE_TIERS:
        prob = min(0.95, base_rate * mult)
        acc += prob
        if roll <= acc:
            return random.choice(pool)
    return random.choice(["bone_shard", "rust_iron"])


class FloatingText:
    def __init__(self, x, y, text, color=COLOR_WHITE, font_size=18, is_crit=False):
        self.x = float(x)
        self.y = float(y)
        self.text = text
        self.color = color
        self.alpha = 255.0
        self.lifetime = 0.85
        self.elapsed = 0.0
        self.vy = -45.0 if not is_crit else -65.0
        self.is_crit = is_crit
        self.font = get_font(font_size, bold=is_crit)

    def update(self, dt):
        self.elapsed += dt
        self.y += self.vy * dt
        self.vy += 25.0 * dt
        self.alpha = max(0.0, 255.0 * (1.0 - (self.elapsed / self.lifetime)))
        return self.elapsed < self.lifetime

    def draw(self, surface, camera_x, camera_y):
        if self.alpha <= 0:
            return
        rendered = self.font.render(self.text, True, self.color)
        rendered.set_alpha(int(self.alpha))
        outline = self.font.render(self.text, True, (0, 0, 0))
        outline.set_alpha(int(self.alpha * 0.7))
        draw_x = int(self.x - camera_x - rendered.get_width() // 2)
        draw_y = int(self.y - camera_y)

        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surface.blit(outline, (draw_x + ox, draw_y + oy))
        surface.blit(rendered, (draw_x, draw_y))


class SlashEffect:
    def __init__(self, x, y, angle_rad, radius=52, is_skill=False):
        self.x = x
        self.y = y
        self.angle_rad = angle_rad
        self.radius = radius
        self.is_skill = is_skill
        self.duration = 0.22 if not is_skill else 0.35
        self.timer = self.duration
        self.color = (255, 220, 100) if not is_skill else (240, 70, 40)

    def update(self, dt):
        self.timer -= dt
        return self.timer > 0

    def draw(self, surface, camera_x, camera_y):
        progress = 1.0 - (self.timer / self.duration)
        alpha = int(255 * (1.0 - progress))
        if alpha <= 0:
            return

        cx = int(self.x - camera_x)
        cy = int(self.y - camera_y)

        if not self.is_skill:
            arc_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
            local_center = (self.radius + 5, self.radius + 5)
            sweep = math.pi * 0.75
            start_angle = self.angle_rad - sweep / 2

            num_points = 14
            points = []
            cur_r = self.radius * (0.6 + 0.4 * progress)
            for i in range(num_points):
                t = i / (num_points - 1)
                ang = start_angle + sweep * t
                px = local_center[0] + cur_r * math.cos(ang)
                py = local_center[1] + cur_r * math.sin(ang)
                points.append((px, py))

            if len(points) >= 2:
                for idx in range(len(points) - 1):
                    pygame.draw.line(arc_surf, (*self.color, alpha), points[idx], points[idx + 1], 4)
                    pygame.draw.line(arc_surf, (255, 255, 255, alpha), points[idx], points[idx + 1], 2)

            surface.blit(arc_surf, (cx - local_center[0], cy - local_center[1]))
        else:
            wave_surf = pygame.Surface((self.radius * 2 + 20, self.radius * 2 + 20), pygame.SRCALPHA)
            local_center = (self.radius + 10, self.radius + 10)
            cur_r = int(self.radius * progress)
            if cur_r > 2:
                pygame.draw.circle(wave_surf, (*self.color, int(alpha * 0.4)), local_center, cur_r)
                pygame.draw.circle(wave_surf, (255, 255, 200, alpha), local_center, cur_r, 4)
            surface.blit(wave_surf, (cx - local_center[0], cy - local_center[1]))


class Projectile:
    """Proyektil musuh & bos (Elemen Bullet Hell: terblokir tembok/pilar cover)."""
    def __init__(self, x, y, angle_rad, speed=230.0, damage=30, radius=7, color=(220, 90, 255), lifetime=3.5):
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle_rad) * speed
        self.vy = math.sin(angle_rad) * speed
        self.damage = damage
        self.radius = radius
        self.color = color
        self.lifetime = lifetime
        self.alive = True

    def get_rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def update(self, dt, player, map_loader, combat_mgr):
        if not self.alive:
            return False
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return False

        self.x += self.vx * dt
        self.y += self.vy * dt

        rect = self.get_rect()
        if map_loader and map_loader.is_projectile_blocked(rect):
            self.alive = False
            return False

        if player and not player.is_dead and rect.colliderect(player.get_hitbox()):
            dealt = player.take_damage(self.damage)
            pc_x, pc_y = player.x + 24, player.y + 24
            if dealt > 0:
                combat_mgr.trigger_shake(0.12, 3.5)
                combat_mgr.floating_texts.append(
                    FloatingText(pc_x, player.y - 12, f"-{dealt}", COLOR_CRIT, font_size=17)
                )
            elif getattr(player, "dodged_last_hit", False):
                player.dodged_last_hit = False
                combat_mgr.floating_texts.append(
                    FloatingText(pc_x, player.y - 18, "PERFECT DODGE! +15 ST", (110, 220, 255), font_size=16, is_crit=True)
                )
            self.alive = False
            return False
        return True

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.x - camera_x)
        cy = int(self.y - camera_y)
        pygame.draw.circle(surface, self.color, (cx, cy), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), max(2, self.radius // 2))


class SporeTrap:
    """Jebakan spora peledak di Hutan Spora (Stage 2) yang meletus saat didekati."""
    def __init__(self, x, y, damage=25, radius=58):
        self.x = float(x)
        self.y = float(y)
        self.damage = damage
        self.radius = radius
        self.triggered = False
        self.fuse_timer = 1.05
        self.alive = True
        self.pulse = 0.0

    def update(self, dt, player, combat_mgr):
        if not self.alive:
            return False
        self.pulse += dt * 4.0
        if player and not player.is_dead:
            dist = math.hypot((player.x + 24) - self.x, (player.y + 24) - self.y)
            if not self.triggered and dist <= self.radius * 0.9:
                self.triggered = True

        if self.triggered:
            self.fuse_timer -= dt
            if self.fuse_timer <= 0:
                audio_manager.play_sound("explosion")
                combat_mgr.slash_effects.append(SlashEffect(self.x, self.y, 0, radius=self.radius, is_skill=True))
                if player and not player.is_dead:
                    dist = math.hypot((player.x + 24) - self.x, (player.y + 24) - self.y)
                    if dist <= self.radius:
                        dealt = player.take_damage(self.damage)
                        if dealt > 0:
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 12, f"-{dealt} SPORA", (190, 120, 255), font_size=17)
                            )
                        elif getattr(player, "dodged_last_hit", False):
                            player.dodged_last_hit = False
                            combat_mgr.floating_texts.append(
                                FloatingText(player.x + 24, player.y - 18, "PERFECT DODGE!", (110, 220, 255), font_size=15, is_crit=True)
                            )
                self.alive = False
                return False
        return True

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.x - camera_x)
        cy = int(self.y - camera_y)
        if self.triggered:
            warn = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(warn, (210, 80, 240, 55), (self.radius + 2, self.radius + 2), self.radius)
            pygame.draw.circle(warn, (240, 140, 255, 200), (self.radius + 2, self.radius + 2), self.radius, 2)
            surface.blit(warn, (cx - self.radius - 2, cy - self.radius - 2))
        r = 10 + int(math.sin(self.pulse) * 2)
        pygame.draw.circle(surface, (145, 65, 185), (cx, cy), r)
        pygame.draw.circle(surface, (210, 255, 140), (cx, cy), max(3, r // 2))


def _load_skull_frames(path):
    frames = []
    if os.path.exists(path):
        try:
            with Image.open(path) as im:
                for i in range(im.n_frames):
                    im.seek(i)
                    rgba = im.convert("RGBA")
                    from_bytes = getattr(pygame.image, "frombytes", pygame.image.fromstring)
                    surf = from_bytes(rgba.tobytes(), rgba.size, "RGBA")
                    frames.append(pygame.transform.scale(surf, (44, 44)))
        except Exception:
            frames = []
    if not frames:
        fallback = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (220, 210, 230), (22, 20), 14)
        pygame.draw.circle(fallback, (255, 60, 90), (16, 18), 4)
        pygame.draw.circle(fallback, (255, 60, 90), (28, 18), 4)
        frames = [fallback]
    return frames


class SkullLaserBarrage:
    """
    Serangan Khusus Final Boss Domain: 6 Kepala Tengkorak Laser tak bisa dihancurkan.
    Muncul dalam formasi 3 atas + 3 bawah atau 3 kiri + 3 kanan di tepi layar terlihat -> telegraph -> laser.
    """
    _FRAME_CACHE = {}

    def __init__(self, formation="top_bottom", damage=260, map_w=1280, map_h=1280, focus_x=640, focus_y=640):
        self.formation = formation if formation in ("top_bottom", "left_right") else "top_bottom"
        self.damage = int(damage)
        self.map_w = int(map_w)
        self.map_h = int(map_h)
        self.focus_x = float(focus_x)
        self.focus_y = float(focus_y)

        self.telegraph_duration = 1.35
        self.fire_duration = 1.20
        self.fade_duration = 0.35
        self.elapsed = 0.0
        self.alive = True
        self.state = "telegraph"  # telegraph | firing | fadeout
        self.hit_cd = 0.0
        self._fired_sfx = False

        if not SkullLaserBarrage._FRAME_CACHE:
            SkullLaserBarrage._FRAME_CACHE["idle"] = _load_skull_frames("character/boss_skull/idle.gif")
            SkullLaserBarrage._FRAME_CACHE["charge"] = _load_skull_frames("character/boss_skull/charge.gif")

        self.skulls = []  # list of dict: x, y, dx, dy, rect
        self._build_formation()

    def _build_formation(self):
        beam_half = 13
        # Posisikan 6 tengkorak pada rentang arena yang terlihat kamera pemain agar selalu tampak jelas
        half_vh = 265.0
        half_vw = 470.0
        top_y = max(92.0, min(self.map_h - 620.0, self.focus_y - half_vh))
        bot_y = min(float(self.map_h - 92), max(top_y + 440.0, self.focus_y + half_vh))
        left_x = max(92.0, min(self.map_w - 760.0, self.focus_x - half_vw))
        right_x = min(float(self.map_w - 92), max(left_x + 760.0, self.focus_x + half_vw))

        if self.formation == "top_bottom":
            # 3 tengkorak di sisi atas + 3 tengkorak di sisi bawah (jalur selang-seling)
            span_h = max(120, int(bot_y - top_y))
            cx0 = max(180.0, self.focus_x - 380.0)
            step_x = 180.0
            for idx in range(3):
                x = min(self.map_w - 140.0, cx0 + idx * (step_x * 2))
                rect = pygame.Rect(int(x - beam_half), int(top_y), beam_half * 2, span_h)
                self.skulls.append({"x": float(x), "y": float(top_y), "dx": 0, "dy": 1, "rect": rect})
            for idx in range(3):
                x = min(self.map_w - 100.0, cx0 + step_x + idx * (step_x * 2))
                rect = pygame.Rect(int(x - beam_half), int(top_y), beam_half * 2, span_h)
                self.skulls.append({"x": float(x), "y": float(bot_y), "dx": 0, "dy": -1, "rect": rect})
        else:
            # 3 tengkorak di sisi kiri + 3 tengkorak di sisi kanan (jalur selang-seling)
            span_w = max(120, int(right_x - left_x))
            cy0 = max(160.0, self.focus_y - 220.0)
            step_y = 95.0
            for idx in range(3):
                y = min(self.map_h - 140.0, cy0 + idx * (step_y * 2))
                rect = pygame.Rect(int(left_x), int(y - beam_half), span_w, beam_half * 2)
                self.skulls.append({"x": float(left_x), "y": float(y), "dx": 1, "dy": 0, "rect": rect})
            for idx in range(3):
                y = min(self.map_h - 100.0, cy0 + step_y + idx * (step_y * 2))
                rect = pygame.Rect(int(left_x), int(y - beam_half), span_w, beam_half * 2)
                self.skulls.append({"x": float(right_x), "y": float(y), "dx": -1, "dy": 0, "rect": rect})

    def update(self, dt, player=None, combat_mgr=None):
        if not self.alive:
            return False
        self.elapsed += dt
        if self.hit_cd > 0:
            self.hit_cd = max(0.0, self.hit_cd - dt)

        t_fire = self.telegraph_duration
        t_fade = t_fire + self.fire_duration
        t_end = t_fade + self.fade_duration

        if self.elapsed < t_fire:
            self.state = "telegraph"
        elif self.elapsed < t_fade:
            if not self._fired_sfx:
                self._fired_sfx = True
                audio_manager.play_sound("laser")
                if combat_mgr:
                    combat_mgr.trigger_shake(0.25, 5.0)
            self.state = "firing"
            if player is not None and not player.is_dead and self.hit_cd <= 0:
                phb = player.get_hitbox()
                if any(phb.colliderect(sk["rect"]) for sk in self.skulls):
                    dealt = player.take_damage(self.damage)
                    pc_x, pc_y = player.x + 24, player.y + 24
                    if dealt > 0:
                        self.hit_cd = 0.45
                        if combat_mgr:
                            combat_mgr.floating_texts.append(
                                FloatingText(pc_x, player.y - 14, f"-{dealt} LASER!", (255, 70, 120), font_size=18, is_crit=True)
                            )
                    elif getattr(player, "dodged_last_hit", False):
                        player.dodged_last_hit = False
                        self.hit_cd = 0.45
                        if combat_mgr:
                            combat_mgr.floating_texts.append(
                                FloatingText(pc_x, player.y - 20, "PERFECT DODGE LASER! +15 ST", (110, 220, 255), font_size=16, is_crit=True)
                            )
        elif self.elapsed < t_end:
            self.state = "fadeout"
        else:
            self.alive = False
            return False
        return True

    def draw(self, surface, camera_x, camera_y):
        frames = SkullLaserBarrage._FRAME_CACHE["charge" if self.state != "fadeout" else "idle"]
        frame_idx = int(self.elapsed * 9.0) % len(frames)
        sprite = frames[frame_idx]

        alpha = 255
        if self.state == "fadeout":
            p = (self.elapsed - (self.telegraph_duration + self.fire_duration)) / max(0.01, self.fade_duration)
            alpha = max(0, int(255 * (1.0 - p)))

        for sk in self.skulls:
            sx = int(sk["x"] - camera_x)
            sy = int(sk["y"] - camera_y)
            r = sk["rect"].move(-int(camera_x), -int(camera_y))

            if self.state == "telegraph":
                pulse = 110 + int(abs(math.sin(self.elapsed * 12.0)) * 120)
                line_surf = pygame.Surface((max(4, r.width), max(4, r.height)), pygame.SRCALPHA)
                pygame.draw.rect(line_surf, (255, 50, 90, int(pulse * 0.30)), (0, 0, r.width, r.height))
                if sk["dx"] == 0:
                    pygame.draw.line(line_surf, (255, 110, 140, pulse), (r.width // 2, 0), (r.width // 2, r.height), 2)
                else:
                    pygame.draw.line(line_surf, (255, 110, 140, pulse), (0, r.height // 2), (r.width, r.height // 2), 2)
                surface.blit(line_surf, r.topleft)
            elif self.state == "firing":
                beam_surf = pygame.Surface((max(4, r.width), max(4, r.height)), pygame.SRCALPHA)
                pygame.draw.rect(beam_surf, (190, 40, 235, 130), (0, 0, r.width, r.height), border_radius=6)
                if sk["dx"] == 0:
                    pygame.draw.rect(beam_surf, (255, 65, 95, 225), (4, 0, max(2, r.width - 8), r.height))
                    pygame.draw.rect(beam_surf, (255, 240, 245, 255), (max(0, r.width // 2 - 3), 0, 6, r.height))
                else:
                    pygame.draw.rect(beam_surf, (255, 65, 95, 225), (0, 4, r.width, max(2, r.height - 8)))
                    pygame.draw.rect(beam_surf, (255, 240, 245, 255), (0, max(0, r.height // 2 - 3), r.width, 6))
                surface.blit(beam_surf, r.topleft)

            if alpha < 255:
                s_copy = sprite.copy()
                s_copy.set_alpha(alpha)
                surface.blit(s_copy, (sx - 22, sy - 22))
            else:
                surface.blit(sprite, (sx - 22, sy - 22))


class CombatManager:
    def __init__(self):
        self.attack_cooldown = 0.22
        self.attack_cd_timer = 0.0

        self.skill_cooldown = 2.0
        self.skill_cd_timer = 0.0

        self.slash_effects = []
        self.floating_texts = []
        self.projectiles = []
        self.traps = []
        self.skull_barrages = []
        self.screen_shake_time = 0.0
        self.screen_shake_intensity = 0.0

    def clear_world_effects(self):
        self.slash_effects.clear()
        self.floating_texts.clear()
        self.projectiles.clear()
        self.traps.clear()
        self.skull_barrages.clear()

    def trigger_skull_lasers(self, formation="top_bottom", damage=260, map_w=1280, map_h=1280, focus_x=640, focus_y=640):
        """Memunculkan 6 kepala tengkorak invincible penembak laser di Final Boss Domain."""
        if any(b.alive for b in self.skull_barrages):
            return False
        self.skull_barrages.append(
            SkullLaserBarrage(formation=formation, damage=damage, map_w=map_w, map_h=map_h, focus_x=focus_x, focus_y=focus_y)
        )
        return True

    def spawn_projectile(self, x, y, angle_rad, speed=230.0, damage=30, radius=7, color=(220, 90, 255)):
        self.projectiles.append(Projectile(x, y, angle_rad, speed=speed, damage=damage, radius=radius, color=color))
        audio_manager.play_sound("projectile")

    def spawn_spore_trap(self, x, y, damage=35):
        self.traps.append(SporeTrap(x, y, damage=damage))

    def update(self, dt, player=None, map_loader=None):
        if self.attack_cd_timer > 0:
            self.attack_cd_timer = max(0.0, self.attack_cd_timer - dt)
        if self.skill_cd_timer > 0:
            self.skill_cd_timer = max(0.0, self.skill_cd_timer - dt)
        if self.screen_shake_time > 0:
            self.screen_shake_time = max(0.0, self.screen_shake_time - dt)

        self.slash_effects = [e for e in self.slash_effects if e.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]
        self.projectiles = [p for p in self.projectiles if p.update(dt, player, map_loader, self)]
        self.traps = [tr for tr in self.traps if tr.update(dt, player, self)]
        self.skull_barrages = [b for b in self.skull_barrages if b.update(dt, player=player, combat_mgr=self)]

    def get_shake_offset(self):
        if self.screen_shake_time > 0:
            ox = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            oy = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            return ox, oy
        return 0, 0

    def trigger_shake(self, duration=0.15, intensity=4.0):
        self.screen_shake_time = duration
        self.screen_shake_intensity = intensity

    def _check_stamina_for_attack(self, player, cost):
        if player.is_fatigued:
            player.stagger_timer = 0.15
            audio_manager.play_sound("cancel")
            self.floating_texts.append(
                FloatingText(player.x + 24, player.y - 12, "FATIGUE! (STA < 10)", (240, 90, 90), font_size=15)
            )
            return False
        if player.stamina < cost:
            audio_manager.play_sound("cancel")
            self.floating_texts.append(
                FloatingText(player.x + 24, player.y - 12, f"Butuh {int(cost)} STA!", (240, 140, 90), font_size=15)
            )
            return False
        return True

    def perform_attack(self, player, mouse_screen_pos, camera_x, camera_y, targets, inventory=None, tier_mult=1.0):
        """Serangan Normal (LMB, biaya ringan BASIC_ATTACK_STAMINA = 5 STA)."""
        if self.attack_cd_timer > 0 or player.is_dead or player.is_rolling or player.stagger_timer > 0:
            return False
        if not self._check_stamina_for_attack(player, BASIC_ATTACK_STAMINA):
            return False

        player.consume_stamina(BASIC_ATTACK_STAMINA)
        self.attack_cd_timer = self.attack_cooldown

        center_x = player.x + 24
        center_y = player.y + 24
        mouse_world_x = mouse_screen_pos[0] + camera_x
        mouse_world_y = mouse_screen_pos[1] + camera_y
        angle = math.atan2(mouse_world_y - center_y, mouse_world_x - center_x)

        self.slash_effects.append(SlashEffect(center_x, center_y, angle, radius=62, is_skill=False))
        audio_manager.play_sound(random.choice(["slash1", "slash2"]))

        attack_range = 78.0
        arc_width = math.pi * 0.85
        used_crit_buff = False

        for target in targets:
            if not target.is_alive():
                continue
            tc_x, tc_y = target.get_center()
            dist = math.hypot(tc_x - center_x, tc_y - center_y)
            if dist <= attack_range:
                target_ang = math.atan2(tc_y - center_y, tc_x - center_x)
                diff_ang = (target_ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(diff_ang) <= arc_width / 2:
                    if self._apply_damage_to_target(player, target, is_skill=False, inventory=inventory, tier_mult=tier_mult):
                        used_crit_buff = True

        if used_crit_buff:
            player.next_attack_crit_buff = False
        return True

    def perform_skill(self, player, mouse_screen_pos, camera_x, camera_y, targets, inventory=None, tier_mult=1.0):
        """Skill Berat Area 'Ash Cleave' (RMB, biaya SKILL_ATTACK_STAMINA = 30 STA)."""
        if self.skill_cd_timer > 0 or player.is_dead or player.is_rolling or player.stagger_timer > 0:
            return False
        if not self._check_stamina_for_attack(player, SKILL_ATTACK_STAMINA):
            return False

        player.consume_stamina(SKILL_ATTACK_STAMINA)
        self.skill_cd_timer = self.skill_cooldown

        center_x = player.x + 24
        center_y = player.y + 24

        self.slash_effects.append(SlashEffect(center_x, center_y, 0, radius=96, is_skill=True))
        self.trigger_shake(0.25, 6.0)
        audio_manager.play_sound("skill_slash")
        audio_manager.play_sound("skill_fx")

        skill_range = 102.0
        used_crit_buff = False
        for target in targets:
            if not target.is_alive():
                continue
            tc_x, tc_y = target.get_center()
            dist = math.hypot(tc_x - center_x, tc_y - center_y)
            if dist <= skill_range:
                if self._apply_damage_to_target(player, target, is_skill=True, inventory=inventory, tier_mult=tier_mult):
                    used_crit_buff = True

        if used_crit_buff:
            player.next_attack_crit_buff = False
        return True

    def _apply_damage_to_target(self, player, target, is_skill=False, inventory=None, tier_mult=1.0):
        """Menghitung damage keluar sesuai rumus GDD + drop material berbobot."""
        from src.inventory import ITEM_DATABASE

        enemy_def = getattr(target, "defense", 0)
        atk_sum = player.total_damage * (1.85 if is_skill else 1.0)

        used_perfect_crit = False
        crit_rate = getattr(player, "effective_crit_chance", player.crit_chance)
        if player.next_attack_crit_buff:
            is_crit = True
            mod = 1.5
            used_perfect_crit = True
        elif random.random() < crit_rate or is_skill:
            is_crit = True
            mod = 1.5
        else:
            is_crit = False
            mod = 1.0

        denom = (enemy_def * 0.5) + 10.0
        variance = random.uniform(0.94, 1.08)
        raw_damage = max(1, int(round((atk_sum / denom) * PLAYER_DAMAGE_SCALING * mod * variance)))

        dmg_dealt = target.take_damage(raw_damage)
        tc_x, tc_y = target.get_center()

        if hasattr(target, "apply_knockback"):
            pc_x, pc_y = player.x + 24, player.y + 24
            dx, dy = tc_x - pc_x, tc_y - pc_y
            dist = math.hypot(dx, dy)
            if dist > 0:
                force = 190.0 if is_skill else 130.0
                target.apply_knockback((dx / dist) * force, (dy / dist) * force)

        text = f"CRIT! {dmg_dealt}" if is_crit else str(dmg_dealt)
        color = COLOR_CRIT if is_crit else COLOR_WHITE
        self.floating_texts.append(FloatingText(tc_x, tc_y - 20, text, color, font_size=20 if is_crit else 17, is_crit=is_crit))

        if not target.is_alive():
            reward_exp, reward_ash, reward_gold = target.get_rewards()
            if reward_exp > 0:
                leveled = player.gain_exp(reward_exp)
                self.floating_texts.append(FloatingText(tc_x, tc_y - 40, f"+{reward_exp} EXP", COLOR_EXP, font_size=18, is_crit=True))
                if leveled:
                    self.floating_texts.append(FloatingText(player.x + 24, player.y - 50, "LEVEL UP!", COLOR_GOLD, font_size=24, is_crit=True))
            if reward_ash > 0:
                player.monster_ash += reward_ash
                self.floating_texts.append(FloatingText(tc_x, tc_y - 58, f"+{reward_ash} Ash", COLOR_ASH, font_size=15))
            if reward_gold > 0:
                player.gold += reward_gold
                self.floating_texts.append(FloatingText(tc_x, tc_y - 74, f"+{reward_gold} Gold", COLOR_GOLD, font_size=15))

            # Weighted RNG Drop Material + Peluang Drop Ramuan/Boost ke Hotbar (hanya untuk monster nyata)
            if inventory is not None and getattr(target, "is_monster", False):
                is_boss_target = getattr(target, "is_boss", False)
                drop_id = roll_material_drop(
                    tier_mult=tier_mult,
                    is_boss=is_boss_target,
                    player_drop_mult=player.drop_multiplier,
                )
                if drop_id and inventory.add_item(drop_id, 1):
                    d_item = ITEM_DATABASE[drop_id]
                    self.floating_texts.append(
                        FloatingText(tc_x, tc_y - 90, f"+1 {d_item.name}", d_item.get_rarity_color(), font_size=14, is_crit=True)
                    )
                cons_drop = roll_consumable_drop(
                    is_boss=is_boss_target,
                    tier_mult=tier_mult,
                    player_drop_mult=player.drop_multiplier,
                )
                if cons_drop and inventory.add_item(cons_drop, 1):
                    c_item = ITEM_DATABASE[cons_drop]
                    self.floating_texts.append(
                        FloatingText(tc_x, tc_y - 108, f"+1 {c_item.name} [Hotbar]", (130, 245, 195), font_size=13, is_crit=True)
                    )

        return used_perfect_crit

    def draw(self, surface, camera_x, camera_y):
        for tr in self.traps:
            tr.draw(surface, camera_x, camera_y)
        for effect in self.slash_effects:
            effect.draw(surface, camera_x, camera_y)
        for proj in self.projectiles:
            proj.draw(surface, camera_x, camera_y)
        for barrage in self.skull_barrages:
            barrage.draw(surface, camera_x, camera_y)
        for ft in self.floating_texts:
            ft.draw(surface, camera_x, camera_y)
