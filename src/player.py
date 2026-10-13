"""
Player class untuk 'Ashes of Oakhaven: The Hollow Crown'.
Menangani pergerakan 8 arah, animasi GIF, dodge roll dengan i-frame, sistem stamina, exp & level up.
"""
import os
import math
import pygame
from PIL import Image
from src.config import TILE_SIZE
from src.audio import audio_manager

def load_gif_frames(path):
    frames = []
    if not os.path.exists(path):
        # Fallback surface jika file tidak ada
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(surf, (100, 150, 255), (24, 24), 20)
        return [surf]
    try:
        with Image.open(path) as im:
            for i in range(im.n_frames):
                im.seek(i)
                rgba = im.convert('RGBA')
                data = rgba.tobytes()
                surf = pygame.image.fromstring(data, rgba.size, 'RGBA')
                frames.append(surf)
    except Exception as e:
        print(f"[Player] Gagal memuat GIF {path}: {e}")
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(surf, (100, 150, 255), (24, 24), 20)
        frames = [surf]
    return frames

class Player:
    def __init__(self, x=544, y=210):
        self.x = float(x)
        self.y = float(y)
        self.width = 48
        self.height = 48

        # Hitbox kaki untuk collision yang presisi & smooth (tidak mudah nyangkut)
        self.hitbox_w = 14
        self.hitbox_h = 10
        self.hitbox_offset_x = 17
        self.hitbox_offset_y = 36

        # Arah dan Animasi
        self.direction = "south"
        self.animations = {
            "east": load_gif_frames("character/main_Char/Idle_walk_east.gif"),
            "north": load_gif_frames("character/main_Char/Idle_walk_north.gif"),
            "south": load_gif_frames("character/main_Char/Idle_walk_south.gif"),
            "west": load_gif_frames("character/main_Char/Idle_walk_west.gif"),
        }
        self.frame_index = 0.0
        self.anim_speed = 10.0 # FPS animasi

        # Statistik Dasar (Sesuai GDD)
        self.level = 1
        self.exp = 0
        self.exp_to_next = 100
        
        self.max_hp = 100
        self.hp = 100
        self.hp_trail = 100.0 # Untuk animasi smooth health drop

        self.max_stamina = 100
        self.stamina = 100.0
        self.stamina_regen = 24.0 # per detik

        self.gold = 50
        self.monster_ash = 15

        # Kekuatan tempur
        self.base_damage = 22
        self.bonus_damage = 0
        self.armor = 0
        self.crit_chance = 0.15 # 15% crit
        self.base_speed = 175.0
        self.speed_bonus = 0.0

        # Dodge Roll / Dash Mechanics
        self.is_rolling = False
        self.roll_duration = 0.26 # detik
        self.roll_timer = 0.0
        self.roll_cooldown = 0.65
        self.roll_cd_timer = 0.0
        self.roll_speed = 360.0
        self.roll_dir_x = 0.0
        self.roll_dir_y = 0.0
        self.is_invincible = False
        self.invincible_timer = 0.0

        # Afterimage effect untuk dodge roll
        self.ghost_trails = []

        # Damage flash effect (warna merah sesaat ketika terkena damage)
        self.hurt_flash_timer = 0.0

        # Status
        self.is_moving = False
        self.is_dead = False

    @property
    def total_damage(self):
        return self.base_damage + self.bonus_damage

    @property
    def speed(self):
        return self.base_speed + self.speed_bonus

    def get_hitbox(self):
        return pygame.Rect(
            int(self.x + self.hitbox_offset_x),
            int(self.y + self.hitbox_offset_y),
            self.hitbox_w,
            self.hitbox_h
        )

    def handle_input(self, keys, dt):
        if self.is_dead or self.is_rolling:
            return

        dx = 0.0
        dy = 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0

        # Normalisasi vektor pergerakan diagonal
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.is_moving = (dx != 0 or dy != 0)

        # Update arah hadap karakter
        if dx > 0:
            self.direction = "east"
        elif dx < 0:
            self.direction = "west"
        elif dy < 0:
            self.direction = "north"
        elif dy > 0:
            self.direction = "south"

        # Trigger Dodge Roll (Spacebar atau Shift)
        if (keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]) and self.roll_cd_timer <= 0:
            if self.stamina >= 15:
                self.start_roll(dx, dy)
                return

        return dx, dy

    def start_roll(self, move_dx, move_dy):
        self.is_rolling = True
        self.roll_timer = self.roll_duration
        self.roll_cd_timer = self.roll_cooldown
        self.is_invincible = True
        self.invincible_timer = self.roll_duration + 0.05
        self.stamina = max(0.0, self.stamina - 15.0)

        audio_manager.play_sound("roll")

        # Jika sedang bergerak, dash ke arah gerakan. Jika diam, dash ke arah hadap.
        if move_dx != 0 or move_dy != 0:
            self.roll_dir_x = move_dx
            self.roll_dir_y = move_dy
        else:
            dirs = {
                "east": (1.0, 0.0),
                "west": (-1.0, 0.0),
                "north": (0.0, -1.0),
                "south": (0.0, 1.0)
            }
            self.roll_dir_x, self.roll_dir_y = dirs.get(self.direction, (0.0, 1.0))

    def update(self, dt, map_loader, move_dir=None):
        if self.is_dead:
            return

        # Cooldown timer
        if self.roll_cd_timer > 0:
            self.roll_cd_timer = max(0.0, self.roll_cd_timer - dt)

        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)
            if self.invincible_timer == 0:
                self.is_invincible = False

        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer = max(0.0, self.hurt_flash_timer - dt)

        # Regenerasi Stamina
        if not self.is_rolling:
            self.stamina = min(float(self.max_stamina), self.stamina + self.stamina_regen * dt)

        # Smooth HP Trail decay
        if self.hp_trail > self.hp:
            self.hp_trail = max(float(self.hp), self.hp_trail - 35.0 * dt)
        else:
            self.hp_trail = float(self.hp)

        # Update pergerakan
        if self.is_rolling:
            # Pergerakan cepat roll
            step_x = self.roll_dir_x * self.roll_speed * dt
            step_y = self.roll_dir_y * self.roll_speed * dt
            self._move_with_collision(step_x, step_y, map_loader)

            # Tambahkan ghost trail
            self.ghost_trails.append({
                "x": self.x,
                "y": self.y,
                "surf": self.get_current_frame().copy(),
                "alpha": 180
            })

            self.roll_timer -= dt
            if self.roll_timer <= 0:
                self.is_rolling = False
        elif move_dir:
            dx, dy = move_dir
            step_x = dx * self.speed * dt
            step_y = dy * self.speed * dt
            self._move_with_collision(step_x, step_y, map_loader)

        # Update frame animasi
        if self.is_moving or self.is_rolling:
            self.frame_index += self.anim_speed * dt
        else:
            # Diam pada frame 0
            self.frame_index = 0.0

        # Update ghost trail fading
        for ghost in self.ghost_trails:
            ghost["alpha"] -= 600 * dt
        self.ghost_trails = [g for g in self.ghost_trails if g["alpha"] > 0]

    def _move_with_collision(self, step_x, step_y, map_loader):
        """Uji sumbu X dan Y secara terpisah agar pemain bisa meluncur di sepanjang dinding."""
        # Auto-unstuck: Jika pemain terjebak di dalam collider (misal dari save file lama), cari posisi terdekat yang bebas
        curr_box = self.get_hitbox()
        if map_loader.is_blocked(curr_box):
            for radius in range(2, 60, 4):
                found = False
                for ox, oy in [(0, -radius), (0, radius), (-radius, 0), (radius, 0),
                               (-radius, -radius), (radius, -radius), (-radius, radius), (radius, radius)]:
                    test_rect = curr_box.move(ox, oy)
                    if not map_loader.is_blocked(test_rect):
                        self.x += ox
                        self.y += oy
                        found = True
                        break
                if found:
                    break

        # Uji gerak sumbu X
        if step_x != 0:
            self.x += step_x
            test_box = self.get_hitbox()
            if map_loader.is_blocked(test_box):
                self.x -= step_x

        # Uji gerak sumbu Y
        if step_y != 0:
            self.y += step_y
            test_box = self.get_hitbox()
            if map_loader.is_blocked(test_box):
                self.y -= step_y

    def get_current_frame(self):
        frames = self.animations.get(self.direction, self.animations["south"])
        idx = int(self.frame_index) % len(frames)
        return frames[idx]

    def gain_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.4)
            # Bonus stat per level up
            self.max_hp += 15
            self.hp = self.max_hp
            self.hp_trail = float(self.max_hp)
            self.max_stamina += 10
            self.stamina = float(self.max_stamina)
            self.base_damage += 4
            leveled_up = True
            audio_manager.play_sound("levelup")
        return leveled_up

    def heal(self, amount):
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        self.hp_trail = float(self.hp)
        audio_manager.play_sound("heal")
        return self.hp - old_hp

    def restore_stamina(self, amount):
        self.stamina = min(float(self.max_stamina), self.stamina + amount)

    def take_damage(self, amount):
        if self.is_invincible or self.is_dead:
            return 0
        
        effective_damage = max(1, amount - self.armor)
        self.hp = max(0, self.hp - effective_damage)
        self.hurt_flash_timer = 0.2
        audio_manager.play_sound("hit1")

        if self.hp <= 0:
            self.is_dead = True
            audio_manager.play_sound("gameover")

        return effective_damage

    def respawn(self, spawn_x=544, y=288):
        """Respawn di dekat Api Unggun Lobby & kurangi 30% Monster Ash sesuai GDD."""
        self.x = float(spawn_x)
        self.y = float(y)
        self.hp = self.max_hp
        self.hp_trail = float(self.max_hp)
        self.stamina = float(self.max_stamina)
        self.is_dead = False
        self.is_rolling = False
        self.roll_timer = 0.0
        # Potong 30% Monster Ash sesuai aturan GDD
        lost_ash = int(self.monster_ash * 0.3)
        self.monster_ash = max(0, self.monster_ash - lost_ash)
        return lost_ash

    def draw(self, surface, camera_x, camera_y):
        # Render ghost trails saat roll
        for ghost in self.ghost_trails:
            g_surf = ghost["surf"].copy()
            g_surf.set_alpha(int(ghost["alpha"]))
            surface.blit(g_surf, (ghost["x"] - camera_x, ghost["y"] - camera_y))

        # Render bayangan di bawah karakter
        shadow_rect = pygame.Rect(
            int(self.x + 10 - camera_x),
            int(self.y + 38 - camera_y),
            28, 10
        )
        shadow_surf = pygame.Surface((28, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 110), (0, 0, 28, 10))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # Render karakter
        frame = self.get_current_frame()
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)

        if self.hurt_flash_timer > 0:
            # Buat flash merah saat terluka
            tinted = frame.copy()
            tinted.fill((255, 60, 60, 180), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, (draw_x, draw_y))
        else:
            surface.blit(frame, (draw_x, draw_y))
