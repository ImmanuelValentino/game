"""
Player class (Ethan) untuk 'Ashes of Oakhaven: The Hollow Crown'.
Mengimplementasikan seluruh mekanik GDD:
- Tabel progresi level (HP, STA, Base ATK, Base DEF)
- Konsumsi stamina (15/30/25/sprint) + jeda pemulihan 1.2 detik + Fatigue (<10 STA)
- Dodge Roll (25 STA, i-frames) & Perfect Dodge (Slow-Mo 1.5s, +15 STA, 150% Crit)
- Hazard lingkungan (Lumpur -30%, Es licin momentum, Conveyor belt, Racun DoT, Lahar)
- Formula Damage GDD & Shadow Visual Karma
"""
import os
import random
import pygame
from PIL import Image
from src.config import (
    WEAPON_DATABASE, compute_level_stats,
    DODGE_ROLL_STAMINA, STAMINA_REGEN_RATE, STAMINA_REGEN_DELAY,
)
from src.audio import audio_manager


def load_gif_frames(path, fallback_size=(48, 48)):
    frames = []
    fw, fh = fallback_size
    if not os.path.exists(path):
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        pygame.draw.circle(surf, (100, 150, 255), (fw // 2, fh // 2), min(fw, fh) // 2 - 4)
        return [surf]
    try:
        with Image.open(path) as im:
            for i in range(im.n_frames):
                im.seek(i)
                rgba = im.convert("RGBA")
                data = rgba.tobytes()
                from_bytes = getattr(pygame.image, "frombytes", pygame.image.fromstring)
                surf = from_bytes(data, rgba.size, "RGBA")
                frames.append(surf)
    except Exception as e:
        print(f"[Player] Gagal memuat GIF {path}: {e}")
        surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
        pygame.draw.circle(surf, (100, 150, 255), (fw // 2, fh // 2), min(fw, fh) // 2 - 4)
        frames = [surf]
    return frames


class Player:
    def __init__(self, x=584, y=232):
        self.x = float(x)
        self.y = float(y)
        self.width = 48
        self.height = 48

        # Hitbox kaki untuk collision presisi
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
        self.anim_speed = 10.0

        # Statistik Dasar Sesuai Tabel GDD
        self.level = 1
        self.exp = 0
        stats = compute_level_stats(1)
        self.exp_to_next = stats["exp_to_next"]

        self.max_hp = stats["max_hp"]
        self.hp = stats["max_hp"]
        self.hp_trail = float(self.max_hp)

        self.max_stamina = stats["max_stamina"]
        self.stamina = float(self.max_stamina)
        self.stamina_regen = STAMINA_REGEN_RATE  # Pulih lebih responsif (24 STA/detik)
        self.stamina_regen_delay = 0.0  # Jeda pemulihan singkat (0.6 detik)

        self.gold = 80
        self.monster_ash = 15

        # Kekuatan tempur & skill Vektor
        self.base_damage = stats["base_atk"]
        self.bonus_damage = 0
        self._armor = stats["base_def"]
        self.bonus_def = 0
        self.crit_chance = 0.22
        self.base_speed = 185.0
        self.speed_bonus = 0.0

        self.weapon_id = "ancestral_blade"
        self.karma = 0
        self.skill_points = 0
        self.skill_levels = {"power": 0, "stamina": 0, "defense": 0, "blade": 0}
        self.beacons_cleared = set()
        self.saved_map = "map1safeworld.tmx"

        # Dodge Roll / Sprint / Perfect Dodge / Fatigue
        self.is_rolling = False
        self.roll_duration = 0.26
        self.roll_timer = 0.0
        self.roll_cooldown = 0.50
        self.roll_cd_timer = 0.0
        self.roll_speed = 365.0
        self.roll_dir_x = 0.0
        self.roll_dir_y = 0.0
        self.is_invincible = False
        self.invincible_timer = 0.0
        self.perfect_dodge_ready = False
        self.dodged_last_hit = False
        self.perfect_dodge_slowmo_timer = 0.0
        self.next_attack_crit_buff = False
        self.stagger_timer = 0.0
        self.is_sprinting = False

        # Fisika Inersia (Es Licin) & Hazard Lingkungan
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.active_hazards = set()
        self.has_hazard_debuff = False
        self.hazard_dot_timer = 0.0
        self.lava_dot_timer = 0.0

        # Efek Visual & Knockback
        self.ghost_trails = []
        self.hurt_flash_timer = 0.0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0

        self.is_moving = False
        self.is_dead = False

    @property
    def armor(self):
        return self._armor + self.bonus_def + self.skill_levels["defense"] * 5

    @armor.setter
    def armor(self, value):
        self._armor = int(value)

    @property
    def weapon_info(self):
        return WEAPON_DATABASE.get(self.weapon_id, WEAPON_DATABASE["ancestral_blade"])

    @property
    def weapon_atk(self):
        return self.weapon_info["weapon_atk"]

    @property
    def drop_multiplier(self):
        return self.weapon_info["drop_mult"]

    @property
    def total_damage(self):
        return self.base_damage + self.weapon_atk + self.bonus_damage + self.skill_levels["power"] * 12

    @property
    def skill_level(self):
        return 1 + sum(self.skill_levels.values())

    @property
    def is_fatigued(self):
        return self.stamina < 10.0

    @property
    def speed(self):
        spd = self.base_speed + self.speed_bonus
        if self.is_sprinting:
            spd *= 1.40
        if "sinkhole" in self.active_hazards:
            spd *= 0.45
        elif "mud" in self.active_hazards:
            spd *= 0.70  # GDD: Lumpur pekat -30% movement speed
        return spd

    def equip_weapon(self, weapon_id):
        if weapon_id in WEAPON_DATABASE:
            self.weapon_id = weapon_id
            return True
        return False

    def consume_stamina(self, amount):
        self.stamina = max(0.0, self.stamina - amount)
        self.stamina_regen_delay = STAMINA_REGEN_DELAY

    def get_hitbox(self):
        return pygame.Rect(
            int(self.x + self.hitbox_offset_x),
            int(self.y + self.hitbox_offset_y),
            self.hitbox_w,
            self.hitbox_h
        )

    def handle_input(self, keys, dt):
        if self.is_dead or self.is_rolling or self.stagger_timer > 0:
            self.is_sprinting = False
            return None

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

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.is_moving = (dx != 0 or dy != 0)

        if dx > 0:
            self.direction = "east"
        elif dx < 0:
            self.direction = "west"
        elif dy < 0:
            self.direction = "north"
        elif dy > 0:
            self.direction = "south"

        # Sprint (LShift ditahan saat bergerak -> -10 STA/s, atau -20 STA/s di lumpur)
        wants_sprint = keys[pygame.K_LSHIFT] and self.is_moving and self.stamina > 2.0
        self.is_sprinting = bool(wants_sprint)

        # Dodge Roll (Spacebar -> -15 STA agar masih cukup stamina untuk bertarung)
        if keys[pygame.K_SPACE] and self.roll_cd_timer <= 0:
            if self.stamina >= DODGE_ROLL_STAMINA:
                self.start_roll(dx, dy)
                return None

        return dx, dy

    def start_roll(self, move_dx, move_dy):
        self.is_rolling = True
        self.is_sprinting = False
        self.roll_timer = self.roll_duration
        self.roll_cd_timer = self.roll_cooldown
        self.is_invincible = True
        self.invincible_timer = self.roll_duration + 0.08
        self.perfect_dodge_ready = True
        self.consume_stamina(DODGE_ROLL_STAMINA)

        audio_manager.play_sound("roll")

        if move_dx != 0 or move_dy != 0:
            self.roll_dir_x = move_dx
            self.roll_dir_y = move_dy
        else:
            dirs = {
                "east": (1.0, 0.0),
                "west": (-1.0, 0.0),
                "north": (0.0, -1.0),
                "south": (0.0, 1.0),
            }
            self.roll_dir_x, self.roll_dir_y = dirs.get(self.direction, (0.0, 1.0))

    def update(self, dt, map_loader, move_dir=None, combat_mgr=None):
        if self.is_dead:
            return

        # Cooldowns & timers
        if self.roll_cd_timer > 0:
            self.roll_cd_timer = max(0.0, self.roll_cd_timer - dt)
        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)
            if self.invincible_timer == 0:
                self.is_invincible = False
        if self.hurt_flash_timer > 0:
            self.hurt_flash_timer = max(0.0, self.hurt_flash_timer - dt)
        if self.stagger_timer > 0:
            self.stagger_timer = max(0.0, self.stagger_timer - dt)
        if self.perfect_dodge_slowmo_timer > 0:
            self.perfect_dodge_slowmo_timer = max(0.0, self.perfect_dodge_slowmo_timer - dt)

        # Deteksi Hazard Lingkungan di kaki Ethan
        hazards, conv_vx = map_loader.get_hazards_at(self.get_hitbox())
        self.active_hazards = hazards
        self.has_hazard_debuff = ("poison" in hazards or "acid" in hazards)

        # Sprint stamina drain (2x di lumpur sesuai GDD)
        if self.is_sprinting and not self.is_rolling:
            drain_rate = 20.0 if "mud" in hazards else 10.0
            self.consume_stamina(drain_rate * dt)
            if self.stamina <= 0:
                self.is_sprinting = False

        # Jeda & Regenerasi Stamina (1.2s delay setelah aksi, regen 15/s)
        if self.stamina_regen_delay > 0:
            used_dt = min(dt, self.stamina_regen_delay)
            self.stamina_regen_delay = max(0.0, self.stamina_regen_delay - used_dt)
            regen_dt = dt - used_dt
        else:
            regen_dt = dt

        if regen_dt > 0 and not self.is_rolling and not self.is_sprinting:
            regen = self.stamina_regen + self.skill_levels["stamina"] * 2.5
            self.stamina = min(float(self.max_stamina), self.stamina + regen * regen_dt)

        # Smooth HP Trail decay
        if self.hp_trail > self.hp:
            self.hp_trail = max(float(self.hp), self.hp_trail - 35.0 * dt)
        else:
            self.hp_trail = float(self.hp)

        # Pergerakan Roll / Normal / Lantai Es Licin
        if self.is_rolling:
            step_x = self.roll_dir_x * self.roll_speed * dt
            step_y = self.roll_dir_y * self.roll_speed * dt
            self._move_with_collision(step_x, step_y, map_loader)
            self.ghost_trails.append({
                "x": self.x, "y": self.y,
                "surf": self.get_current_frame().copy(), "alpha": 180
            })
            self.roll_timer -= dt
            if self.roll_timer <= 0:
                self.is_rolling = False
        elif "ice" in hazards:
            # Momentum inersia di lantai es Benteng Salju Hitam
            target_vx = (move_dir[0] * self.speed) if move_dir else 0.0
            target_vy = (move_dir[1] * self.speed) if move_dir else 0.0
            accel = 3.2 * dt
            self.vel_x += (target_vx - self.vel_x) * min(1.0, accel)
            self.vel_y += (target_vy - self.vel_y) * min(1.0, accel)
            if abs(self.vel_x) > 1.0 or abs(self.vel_y) > 1.0:
                self._move_with_collision(self.vel_x * dt, self.vel_y * dt, map_loader)
        elif move_dir:
            dx, dy = move_dir
            self.vel_x = dx * self.speed
            self.vel_y = dy * self.speed
            self._move_with_collision(self.vel_x * dt, self.vel_y * dt, map_loader)
        else:
            self.vel_x = 0.0
            self.vel_y = 0.0

        # Dorongan Conveyor Belt (Stage 3: Tungku Gehenna)
        if conv_vx != 0.0:
            self._move_with_collision(conv_vx * dt, 0.0, map_loader)

        # Knockback fisik
        if abs(self.knockback_vx) > 1.0 or abs(self.knockback_vy) > 1.0:
            self._move_with_collision(self.knockback_vx * dt, self.knockback_vy * dt, map_loader)
            decay = max(0.0, 1.0 - 10.0 * dt)
            self.knockback_vx *= decay
            self.knockback_vy *= decay
        else:
            self.knockback_vx = 0.0
            self.knockback_vy = 0.0

        # Damage Over Time Hazard (Racun & Lahar)
        if self.has_hazard_debuff:
            self.hazard_dot_timer += dt
            if self.hazard_dot_timer >= 1.5:
                self.hazard_dot_timer = 0.0
                self._apply_hazard_damage(3, "RACUN", (140, 230, 120), combat_mgr)
        else:
            self.hazard_dot_timer = 0.0

        if "lava" in hazards and not self.is_invincible:
            self.lava_dot_timer += dt
            if self.lava_dot_timer >= 0.75:
                self.lava_dot_timer = 0.0
                self._apply_hazard_damage(10, "LAHAR!", (255, 110, 40), combat_mgr)
        else:
            self.lava_dot_timer = 0.0

        # Animasi
        if self.is_moving or self.is_rolling:
            self.frame_index += (self.anim_speed * (1.3 if self.is_sprinting else 1.0)) * dt
        else:
            self.frame_index = 0.0

        for ghost in self.ghost_trails:
            ghost["alpha"] -= 600 * dt
        self.ghost_trails = [g for g in self.ghost_trails if g["alpha"] > 0]

    def _apply_hazard_damage(self, raw_dmg, label, color, combat_mgr=None):
        if self.is_dead:
            return
        self.hp = max(0, self.hp - raw_dmg)
        self.hurt_flash_timer = 0.14
        if combat_mgr:
            from src.combat import FloatingText
            combat_mgr.floating_texts.append(
                FloatingText(self.x + 24, self.y - 12, f"-{raw_dmg} {label}", color, font_size=15)
            )
        if self.hp <= 0:
            self.is_dead = True
            audio_manager.play_sound("gameover")

    def _move_with_collision(self, step_x, step_y, map_loader):
        """Uji sumbu X dan Y secara terpisah agar pemain meluncur halus di dinding."""
        curr_box = self.get_hitbox()
        if map_loader.is_blocked(curr_box):
            for radius in range(2, 60, 4):
                found = False
                for ox, oy in [(0, -radius), (0, radius), (-radius, 0), (radius, 0),
                               (-radius, -radius), (radius, -radius), (-radius, radius), (radius, radius)]:
                    if not map_loader.is_blocked(curr_box.move(ox, oy)):
                        self.x += ox
                        self.y += oy
                        found = True
                        break
                if found:
                    break

        if step_x != 0:
            self.x += step_x
            if map_loader.is_blocked(self.get_hitbox()):
                self.x -= step_x
                self.vel_x = 0.0

        if step_y != 0:
            self.y += step_y
            if map_loader.is_blocked(self.get_hitbox()):
                self.y -= step_y
                self.vel_y = 0.0

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
            prev_stats = compute_level_stats(self.level - 1)
            new_stats = compute_level_stats(self.level)
            self.exp_to_next = new_stats["exp_to_next"]

            # Pertahankan tambahan upgrade permanen dari toko/skill
            self.max_hp += max(10, new_stats["max_hp"] - prev_stats["max_hp"])
            self.max_stamina += max(2, new_stats["max_stamina"] - prev_stats["max_stamina"])
            self.base_damage += max(2, new_stats["base_atk"] - prev_stats["base_atk"])
            self._armor += max(1, new_stats["base_def"] - prev_stats["base_def"])

            self.hp = self.max_hp
            self.hp_trail = float(self.max_hp)
            self.stamina = float(self.max_stamina)
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

    def apply_knockback(self, vx, vy):
        if not self.is_invincible and not self.is_dead:
            self.knockback_vx = vx
            self.knockback_vy = vy

    def take_damage(self, enemy_atk):
        """Menghitung damage masuk dengan formula GDD + Perfect Dodge + Fatigue/Hazard penalty."""
        if self.is_dead:
            return 0
        if self.is_invincible:
            if self.perfect_dodge_ready:
                self.perfect_dodge_ready = False
                self.dodged_last_hit = True
                self.restore_stamina(15.0)
                self.perfect_dodge_slowmo_timer = 1.5  # GDD: Slow-Mo 1.5 detik
                self.next_attack_crit_buff = True      # GDD: Serangan berikutnya Crit 150%
                audio_manager.play_sound("parry")
            return 0

        self.dodged_last_hit = False
        fatigue_pen = 1.2 if self.is_fatigued else 1.0
        hazard_pen = 1.15 if self.has_hazard_debuff else 1.0
        denom = (self.armor * 0.5) + 10.0
        effective_damage = max(1, int(round((enemy_atk / denom) * hazard_pen * fatigue_pen)))

        self.hp = max(0, self.hp - effective_damage)
        self.hurt_flash_timer = 0.2
        audio_manager.play_sound(random.choice(["hit1", "hit2"]))

        if self.hp <= 0:
            self.is_dead = True
            audio_manager.play_sound("gameover")

        return effective_damage

    def respawn(self, spawn_x=584, y=232, inventory=None):
        """Respawn di Api Unggun Hub: -30% Abu Monster & -50% material belum terjual sesuai GDD."""
        self.x = float(spawn_x)
        self.y = float(y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.hp = self.max_hp
        self.hp_trail = float(self.max_hp)
        self.stamina = float(self.max_stamina)
        self.stamina_regen_delay = 0.0
        self.is_dead = False
        self.is_rolling = False
        self.roll_timer = 0.0
        self.is_invincible = False
        self.invincible_timer = 0.0
        self.hurt_flash_timer = 0.0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0
        self.perfect_dodge_slowmo_timer = 0.0
        self.next_attack_crit_buff = False

        lost_ash = int(self.monster_ash * 0.3)
        self.monster_ash = max(0, self.monster_ash - lost_ash)
        if inventory is not None and hasattr(inventory, "apply_death_material_penalty"):
            inventory.apply_death_material_penalty(0.5)
        return lost_ash

    def draw(self, surface, camera_x, camera_y):
        for ghost in self.ghost_trails:
            g_surf = ghost["surf"].copy()
            g_surf.set_alpha(int(ghost["alpha"]))
            surface.blit(g_surf, (ghost["x"] - camera_x, ghost["y"] - camera_y))

        # Bayangan karakter (berubah merah gelap beraura bila Karma negatif/senjata kutukan)
        cursed = self.karma <= -30 or self.weapon_id == "bloodthirst_blade"
        shadow_col = (150, 15, 25, 145) if cursed else (0, 0, 0, 110)
        shadow_surf = pygame.Surface((32, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, shadow_col, (0, 0, 32, 12))
        surface.blit(shadow_surf, (int(self.x + 8 - camera_x), int(self.y + 37 - camera_y)))

        frame = self.get_current_frame()
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)

        if self.hurt_flash_timer > 0:
            tinted = frame.copy()
            tinted.fill((255, 60, 60, 180), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, (draw_x, draw_y))
        else:
            surface.blit(frame, (draw_x, draw_y))

        # Indikator cincin emas jika Perfect Dodge Crit Buff aktif
        if self.next_attack_crit_buff:
            cx, cy = int(self.x + 24 - camera_x), int(self.y + 24 - camera_y)
            pygame.draw.circle(surface, (110, 220, 255), (cx, cy), 24, 1)
