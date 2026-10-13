"""
Combat System untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menangani serangan pedang (LMB), skill area (RMB), hit detection, efek visual slash, dan floating damage text.
"""
import math
import random
import pygame
from src.config import COLOR_WHITE, COLOR_CRIT, COLOR_GOLD, COLOR_EXP, COLOR_ASH
from src.audio import audio_manager

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
        self.font = pygame.font.SysFont("Segoe UI, Arial", font_size, bold=is_crit)

    def update(self, dt):
        self.elapsed += dt
        self.y += self.vy * dt
        # Kurangi kecepatan vertikal perlahan
        self.vy += 25.0 * dt
        self.alpha = max(0.0, 255.0 * (1.0 - (self.elapsed / self.lifetime)))
        return self.elapsed < self.lifetime

    def draw(self, surface, camera_x, camera_y):
        if self.alpha <= 0:
            return
        rendered = self.font.render(self.text, True, self.color)
        rendered.set_alpha(int(self.alpha))
        # Tambahkan outline hitam tipis untuk keterbacaan
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
            # Tebasan melengkung (Arc Slash)
            arc_surf = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
            local_center = (self.radius + 5, self.radius + 5)
            
            sweep = math.pi * 0.75
            start_angle = self.angle_rad - sweep / 2
            end_angle = self.angle_rad + sweep / 2

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
                    col = (*self.color, alpha)
                    pygame.draw.line(arc_surf, col, points[idx], points[idx+1], 4)
                    # Garis cahaya putih di tengah
                    pygame.draw.line(arc_surf, (255, 255, 255, alpha), points[idx], points[idx+1], 2)

            surface.blit(arc_surf, (cx - local_center[0], cy - local_center[1]))
        else:
            # Skill lingkaran ledakan area (AOE Shockwave)
            wave_surf = pygame.Surface((self.radius * 2 + 20, self.radius * 2 + 20), pygame.SRCALPHA)
            local_center = (self.radius + 10, self.radius + 10)
            cur_r = int(self.radius * progress)
            if cur_r > 2:
                pygame.draw.circle(wave_surf, (*self.color, int(alpha * 0.4)), local_center, cur_r)
                pygame.draw.circle(wave_surf, (255, 255, 200, alpha), local_center, cur_r, 4)
            surface.blit(wave_surf, (cx - local_center[0], cy - local_center[1]))


class CombatManager:
    def __init__(self):
        self.attack_cooldown = 0.32
        self.attack_cd_timer = 0.0

        self.skill_cooldown = 2.4
        self.skill_cd_timer = 0.0

        self.slash_effects = []
        self.floating_texts = []
        self.screen_shake_time = 0.0
        self.screen_shake_intensity = 0.0

    def update(self, dt):
        if self.attack_cd_timer > 0:
            self.attack_cd_timer = max(0.0, self.attack_cd_timer - dt)
        if self.skill_cd_timer > 0:
            self.skill_cd_timer = max(0.0, self.skill_cd_timer - dt)

        if self.screen_shake_time > 0:
            self.screen_shake_time = max(0.0, self.screen_shake_time - dt)

        # Update efek visual
        self.slash_effects = [e for e in self.slash_effects if e.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]

    def get_shake_offset(self):
        if self.screen_shake_time > 0:
            ox = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            oy = random.uniform(-self.screen_shake_intensity, self.screen_shake_intensity)
            return ox, oy
        return 0, 0

    def trigger_shake(self, duration=0.15, intensity=4.0):
        self.screen_shake_time = duration
        self.screen_shake_intensity = intensity

    def perform_attack(self, player, mouse_screen_pos, camera_x, camera_y, targets):
        """Mengeksekusi serangan normal (Klik Kiri) ke arah kursor mouse."""
        if self.attack_cd_timer > 0 or player.is_dead or player.is_rolling:
            return False
        if player.stamina < 10.0:
            self.floating_texts.append(FloatingText(player.x + 24, player.y - 10, "Stamina Habis!", (220, 100, 100)))
            return False

        # Kurangi stamina & pasang cooldown
        player.stamina -= 10.0
        self.attack_cd_timer = self.attack_cooldown

        # Hitung sudut ke mouse
        center_x = player.x + 24
        center_y = player.y + 24
        mouse_world_x = mouse_screen_pos[0] + camera_x
        mouse_world_y = mouse_screen_pos[1] + camera_y
        angle = math.atan2(mouse_world_y - center_y, mouse_world_x - center_x)

        # Efek visual tebasan
        self.slash_effects.append(SlashEffect(center_x, center_y, angle, radius=54, is_skill=False))
        audio_manager.play_sound(random.choice(["slash1", "slash2"]))

        # Hit detection pada target
        hits = 0
        attack_range = 65.0
        arc_width = math.pi * 0.75

        for target in targets:
            if not target.is_alive():
                continue
            tc_x, tc_y = target.get_center()
            dist = math.hypot(tc_x - center_x, tc_y - center_y)
            if dist <= attack_range:
                target_ang = math.atan2(tc_y - center_y, tc_x - center_x)
                # Beda sudut
                diff_ang = (target_ang - angle + math.pi) % (2 * math.pi) - math.pi
                if abs(diff_ang) <= arc_width / 2:
                    # Kena!
                    self._apply_damage_to_target(player, target, is_skill=False)
                    hits += 1

        return True

    def perform_skill(self, player, mouse_screen_pos, camera_x, camera_y, targets):
        """Mengeksekusi skill khusus area / Dark Ash Burst (Klik Kanan)."""
        if self.skill_cd_timer > 0 or player.is_dead or player.is_rolling:
            return False
        if player.stamina < 25.0:
            self.floating_texts.append(FloatingText(player.x + 24, player.y - 10, "Stamina Kurang!", (220, 100, 100)))
            return False

        # Kurangi stamina & pasang cooldown
        player.stamina -= 25.0
        self.skill_cd_timer = self.skill_cooldown

        center_x = player.x + 24
        center_y = player.y + 24

        # Visual shockwave & camera shake
        self.slash_effects.append(SlashEffect(center_x, center_y, 0, radius=90, is_skill=True))
        self.trigger_shake(0.25, 6.0)
        audio_manager.play_sound("skill_slash")
        audio_manager.play_sound("skill_fx")

        # Hit detection 360 derajat
        skill_range = 95.0
        for target in targets:
            if not target.is_alive():
                continue
            tc_x, tc_y = target.get_center()
            dist = math.hypot(tc_x - center_x, tc_y - center_y)
            if dist <= skill_range:
                self._apply_damage_to_target(player, target, is_skill=True)

        return True

    def _apply_damage_to_target(self, player, target, is_skill=False):
        # Hitung damage dengan variasi acak +/- 10%
        base = player.total_damage * (2.2 if is_skill else 1.0)
        variance = random.uniform(0.9, 1.1)
        raw_damage = int(base * variance)

        # Cek Critical Hit
        is_crit = random.random() < player.crit_chance or is_skill
        if is_crit:
            raw_damage = int(raw_damage * 1.5)

        dmg_dealt = target.take_damage(raw_damage)
        tc_x, tc_y = target.get_center()

        # Tampilkan floating damage
        if is_crit:
            text = f"CRIT! {dmg_dealt}"
            color = COLOR_CRIT
        else:
            text = str(dmg_dealt)
            color = COLOR_WHITE

        self.floating_texts.append(FloatingText(tc_x, tc_y - 20, text, color, font_size=20 if is_crit else 17, is_crit=is_crit))

        # Jika target kalah, berikan reward exp dan ash!
        if not target.is_alive():
            reward_exp, reward_ash, reward_gold = target.get_rewards()
            if reward_exp > 0:
                leveled = player.gain_exp(reward_exp)
                self.floating_texts.append(FloatingText(tc_x, tc_y - 40, f"+{reward_exp} EXP", COLOR_EXP, font_size=18, is_crit=True))
                if leveled:
                    self.floating_texts.append(FloatingText(player.x + 24, player.y - 50, "★ LEVEL UP! ★", COLOR_GOLD, font_size=24, is_crit=True))
            if reward_ash > 0:
                player.monster_ash += reward_ash
                self.floating_texts.append(FloatingText(tc_x, tc_y - 60, f"+{reward_ash} Ash", COLOR_ASH, font_size=16))
            if reward_gold > 0:
                player.gold += reward_gold
                self.floating_texts.append(FloatingText(tc_x, tc_y - 75, f"+{reward_gold} Gold", COLOR_GOLD, font_size=16))

    def draw(self, surface, camera_x, camera_y):
        for effect in self.slash_effects:
            effect.draw(surface, camera_x, camera_y)
        for ft in self.floating_texts:
            ft.draw(surface, camera_x, camera_y)
