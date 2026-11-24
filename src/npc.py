"""
NPC, Portal, Enemy AI (Melee & Ranged), serta 5 Bos Bioma GDD + 2-Fase Final Boss.
"""
import os
import math
import random
import pygame
from src.config import (
    COLOR_WHITE, COLOR_GOLD, COLOR_HP, COLOR_HP_BG, COLOR_CRIT,
    COLOR_TEXT_ACCENT, get_font
)
from src.audio import audio_manager
from src.player import load_gif_frames
from src.combat import FloatingText, SlashEffect


def load_frames_from_gif_or_png(path, frame_w=None, frame_h=None, col_filter=None, max_frames=None):
    """Memuat frame animasi dari GIF (via Player helper) atau sprite sheet PNG."""
    if not os.path.exists(path):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, (150, 150, 150), (16, 16), 14)
        return [surf]

    if path.endswith(".gif"):
        frames = load_gif_frames(path, fallback_size=(32, 32))
        return frames[:max_frames] if max_frames else frames

    frames = []
    if path.endswith(".png"):
        try:
            full = pygame.image.load(path).convert_alpha()
            if frame_w and frame_h:
                cols = full.get_width() // frame_w
                rows = full.get_height() // frame_h
                for r in range(rows):
                    for c in range(cols):
                        if col_filter is not None and c != col_filter:
                            continue
                        sub = full.subsurface((c * frame_w, r * frame_h, frame_w, frame_h)).copy()
                        frames.append(sub)
                        if max_frames and len(frames) >= max_frames:
                            return frames
            else:
                frames.append(full)
        except Exception as e:
            print(f"[NPC] Error loading PNG {path}: {e}")
    return frames if frames else [pygame.Surface((32, 32), pygame.SRCALPHA)]


def _load_ninja_npc_assets(folder_name, fallback_size=(32, 32)):
    """Memuat sprite idle hadap selatan (kolom 0) dan portrait Faceset untuk aset Ninja Adventure."""
    frames = []
    idle_path = f"assets/characters/{folder_name}/SeparateAnim/Idle.png"
    sheet_path = f"assets/characters/{folder_name}/SpriteSheet.png"

    if os.path.exists(idle_path):
        raw = load_frames_from_gif_or_png(idle_path, 16, 16, col_filter=0, max_frames=1)
        frames = [pygame.transform.scale(f, fallback_size) for f in raw]
    elif os.path.exists(sheet_path):
        raw = load_frames_from_gif_or_png(sheet_path, 16, 16, col_filter=0, max_frames=1)
        frames = [pygame.transform.scale(f, fallback_size) for f in raw]

    portrait = None
    portrait_path = f"assets/characters/{folder_name}/Faceset.png"
    if os.path.exists(portrait_path):
        portrait = pygame.image.load(portrait_path).convert_alpha()
        portrait = pygame.transform.scale(portrait, (80, 80))

    return frames, portrait


class BaseNPC:
    def __init__(self, name, x, y, width=32, height=32, interact_radius=50, map_role="npc"):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.interact_radius = interact_radius
        self.map_role = map_role
        self.frames = []
        self.frame_index = 0.0
        self.anim_speed = 4.0
        self.portrait = None
        self.dialogue_tree = []

    def get_center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def is_player_near(self, player):
        cx, cy = self.get_center()
        px, py = player.x + 24, player.y + 24
        return math.hypot(cx - px, cy - py) <= self.interact_radius

    def update(self, dt):
        if len(self.frames) > 1:
            self.frame_index = (self.frame_index + self.anim_speed * dt) % len(self.frames)

    def draw(self, surface, camera_x, camera_y):
        shadow_surf = pygame.Surface((int(self.width * 0.8), 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_surf.get_width(), 8))
        surface.blit(shadow_surf, (int(self.x + self.width * 0.1 - camera_x), int(self.y + self.height - 4 - camera_y)))

        if self.frames:
            idx = int(self.frame_index) % len(self.frames)
            surface.blit(self.frames[idx], (int(self.x - camera_x), int(self.y - camera_y)))

        name_font = get_font(12, bold=True)
        name_surf = name_font.render(self.name, True, COLOR_GOLD)
        outline = name_font.render(self.name, True, (0, 0, 0))
        nx = int(self.x + self.width / 2 - camera_x - name_surf.get_width() / 2)
        ny = int(self.y - 16 - camera_y)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surface.blit(outline, (nx + ox, ny + oy))
        surface.blit(name_surf, (nx, ny))


class Campfire(BaseNPC):
    def __init__(self, x=544, y=256):
        super().__init__("Api Unggun Oakhaven", x, y, width=32, height=32, interact_radius=58, map_role="campfire")
        self.particles = []
        self._create_fire_frames()

    def _create_fire_frames(self):
        self.frames = []
        for f in range(6):
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (80, 75, 70), (4, 18, 24, 12))
            pygame.draw.ellipse(surf, (40, 35, 30), (6, 20, 20, 8))
            flame_colors = [(255, 60, 20), (255, 160, 30), (255, 230, 80)]
            h = 14 + (f % 3) * 3
            pygame.draw.polygon(surf, flame_colors[0], [(8, 22), (24, 22), (16, 22 - h)])
            pygame.draw.polygon(surf, flame_colors[1], [(10, 22), (22, 22), (16, 22 - int(h * 0.75))])
            pygame.draw.polygon(surf, flame_colors[2], [(12, 22), (20, 22), (16, 22 - int(h * 0.5))])
            self.frames.append(surf)

    def update(self, dt):
        super().update(dt)
        if random.random() < 0.4:
            self.particles.append({
                "x": self.x + random.uniform(10, 22),
                "y": self.y + 16,
                "vy": -random.uniform(20, 45),
                "alpha": 255.0,
                "color": random.choice([(255, 120, 20), (255, 200, 40), (255, 70, 10)])
            })
        for p in self.particles:
            p["y"] += p["vy"] * dt
            p["alpha"] -= 280 * dt
        self.particles = [p for p in self.particles if p["alpha"] > 0]

    def draw(self, surface, camera_x, camera_y):
        glow_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 140, 40, 35), (45, 45), 45)
        pygame.draw.circle(glow_surf, (255, 180, 60, 55), (45, 45), 26)
        surface.blit(glow_surf, (int(self.x + 16 - camera_x - 45), int(self.y + 16 - camera_y - 45)))
        super().draw(surface, camera_x, camera_y)
        for p in self.particles:
            psurf = pygame.Surface((3, 3), pygame.SRCALPHA)
            psurf.fill((*p["color"], int(p["alpha"])))
            surface.blit(psurf, (int(p["x"] - camera_x), int(p["y"] - camera_y)))


class WhiteFlame(BaseNPC):
    """Api Putih di sudut map dungeon: satu-satunya sumber regenerasi HP pasif via radius."""
    def __init__(self, x, y, heal_radius=74.0, heal_rate=12.0, max_energy=140.0):
        super().__init__("Api Putih", x, y, width=36, height=36, interact_radius=heal_radius, map_role="white_fire")
        self.heal_radius = float(heal_radius)
        self.heal_rate = float(heal_rate)
        self.max_energy = float(max_energy)
        self.energy = float(max_energy)
        self.recharge_delay = 16.0
        self.recharge_timer = 0.0
        self._heal_accum = 0.0
        self._sfx_timer = 0.0
        self._pulse = 0.0
        self._load_white_fire_frames()

    def _load_white_fire_frames(self):
        gif_path = "assets/effects/white_fire.gif"
        if os.path.exists(gif_path):
            raw = load_frames_from_gif_or_png(gif_path)
            self.frames = [pygame.transform.scale(f, (36, 36)) for f in raw]
            self.anim_speed = 7.0
        else:
            surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(surf, (220, 250, 255), (18, 18), 14)
            self.frames = [surf]

    def update(self, dt, player=None, combat_mgr=None):
        super().update(dt)
        self._pulse = (self._pulse + dt * 2.8) % (math.pi * 2)
        if self._sfx_timer > 0:
            self._sfx_timer = max(0.0, self._sfx_timer - dt)

        if self.recharge_timer > 0:
            self.recharge_timer = max(0.0, self.recharge_timer - dt)
            if self.recharge_timer == 0.0:
                self.energy = self.max_energy
        elif player is not None and not player.is_dead:
            cx, cy = self.get_center()
            px, py = player.x + 24, player.y + 24
            dist = math.hypot(cx - px, cy - py)
            if dist <= self.heal_radius and self.energy > 0:
                player.in_white_fire = True
                if player.hp < player.max_hp:
                    gain = min(self.energy, self.heal_rate * dt)
                    self.energy -= gain
                    self._heal_accum += gain
                    pts = int(self._heal_accum)
                    if pts >= 1:
                        self._heal_accum -= pts
                        healed = min(player.max_hp - player.hp, pts)
                        if healed > 0:
                            player.hp = min(player.max_hp, player.hp + healed)
                            player.hp_trail = float(player.hp)
                            if self._sfx_timer <= 0:
                                self._sfx_timer = 0.75
                                audio_manager.play_sound("heal")
                                if combat_mgr:
                                    combat_mgr.floating_texts.append(
                                        FloatingText(px, player.y - 14, f"+{healed} HP (Api Putih)", (200, 248, 255), font_size=15)
                                    )
                    if self.energy <= 0.5:
                        self.energy = 0.0
                        self.recharge_timer = self.recharge_delay
            elif self.energy < self.max_energy:
                self.energy = min(self.max_energy, self.energy + 6.0 * dt)

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.x + self.width / 2 - camera_x)
        cy = int(self.y + self.height / 2 - camera_y)
        r = int(self.heal_radius + math.sin(self._pulse) * 3)
        aura = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
        active = self.recharge_timer <= 0 and self.energy > 0
        fill_col = (195, 245, 255, 26) if active else (110, 125, 140, 18)
        ring_col = (225, 252, 255, 130) if active else (120, 130, 145, 80)
        pygame.draw.circle(aura, fill_col, (r + 3, r + 3), r)
        pygame.draw.circle(aura, ring_col, (r + 3, r + 3), r, 2)
        surface.blit(aura, (cx - r - 3, cy - r - 3))

        self.name = "Api Putih (Pulih HP)" if active else f"Api Putih ({int(self.recharge_timer)}s)"
        super().draw(surface, camera_x, camera_y)


class MapPortal(BaseNPC):
    """Portal / pintu transisi dua arah antar Hub, 5 Stage GDD, dan Dungeon Klasik."""
    def __init__(self, name, x, y, target_map, target_x, target_y, color=(100, 180, 255)):
        super().__init__(name, x, y, width=32, height=32, interact_radius=56, map_role="portal")
        self.target_map = target_map
        self.target_x = float(target_x)
        self.target_y = float(target_y)
        self.color = color
        self.pulse = 0.0

    def update(self, dt):
        self.pulse = (self.pulse + dt * 3.0) % (math.pi * 2)

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.x + self.width / 2 - camera_x)
        cy = int(self.y + self.height / 2 - camera_y)
        radius = 16 + int(math.sin(self.pulse) * 3)

        glow = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 55), (32, 32), radius + 8)
        pygame.draw.circle(glow, (*self.color, 130), (32, 32), radius, 3)
        pygame.draw.circle(glow, (255, 255, 255, 180), (32, 32), max(4, radius - 7), 2)
        surface.blit(glow, (cx - 32, cy - 32))

        name_font = get_font(12, bold=True)
        name_surf = name_font.render(self.name, True, COLOR_TEXT_ACCENT)
        outline = name_font.render(self.name, True, (0, 0, 0))
        nx = cx - name_surf.get_width() // 2
        ny = int(self.y - 16 - camera_y)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surface.blit(outline, (nx + ox, ny + oy))
        surface.blit(name_surf, (nx, ny))


class ElaraNPC(BaseNPC):
    def __init__(self, x=440, y=250):
        super().__init__("Elara (Arsiparis & Quest)", x, y, width=32, height=32, interact_radius=54, map_role="quest")
        self.frames, self.portrait = _load_ninja_npc_assets("Woman", (32, 32))


class BrogNPC(BaseNPC):
    def __init__(self, x=650, y=250):
        super().__init__("Brog (Barman Rusty Anchor)", x, y, width=32, height=32, interact_radius=58, map_role="bar")
        self.frames, self.portrait = _load_ninja_npc_assets("Villager", (32, 32))


class VektorNPC(BaseNPC):
    """Vektor (Guildmaster & Bengkel Skill) menggunakan sprite character/npc_guild."""
    def __init__(self, x=352, y=240):
        super().__init__("Vektor (Guildmaster & Skill)", x, y, width=52, height=52, interact_radius=60, map_role="skill")
        gif_path = "character/npc_guild/Idle_breathing-idle_south.gif"
        if os.path.exists(gif_path):
            raw_frames = load_frames_from_gif_or_png(gif_path)
            self.frames = [pygame.transform.scale(f, (52, 52)) for f in raw_frames]
        portrait_path = "assets/characters/Monk/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


class AellNPC(BaseNPC):
    """Aell (Map Reader / Kartografi Dinamis) menggunakan sprite character/npc_mapReader."""
    def __init__(self, x=352, y=320):
        super().__init__("Aell (Map Reader)", x, y, width=48, height=48, interact_radius=56, map_role="map")
        gif_path = "character/npc_mapReader/Idle_custom-walking_south.gif"
        if os.path.exists(gif_path):
            raw = load_frames_from_gif_or_png(gif_path, max_frames=2)
            self.frames = [pygame.transform.scale(f, (48, 48)) for f in raw]
            self.anim_speed = 2.0


class GaelNPC(BaseNPC):
    """Gael (Former Adventurer & Pedagang Senjata) menggunakan sprite character/npc_formerAdvanture."""
    def __init__(self, x=584, y=364):
        super().__init__("Gael (Pedagang Senjata & Shop)", x, y, width=48, height=48, interact_radius=58, map_role="shop")
        gif_path = "character/npc_formerAdvanture/Idle_breathing-idle_south.gif"
        if os.path.exists(gif_path):
            raw = load_frames_from_gif_or_png(gif_path)
            self.frames = [pygame.transform.scale(f, (48, 48)) for f in raw]
        portrait_path = "assets/characters/SorcererBlack/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


# Alias untuk menjaga kompatibilitas impor lama
MerchantNPC = GaelNPC
MapReaderNPC = AellNPC


class GatekeeperNPC(BaseNPC):
    def __init__(self, x=864, y=120):
        super().__init__("Kapten Penjaga Gerbang", x, y, width=32, height=32, interact_radius=56, map_role="guard")
        self.frames, self.portrait = _load_ninja_npc_assets("Knight", (32, 32))


class VillagerChildNPC(BaseNPC):
    """Penyintas muda Oakhaven menggunakan sprite character/npc_boy atau npc_girl."""
    def __init__(self, name, x, y, variant="boy"):
        super().__init__(name, x, y, width=44, height=44, interact_radius=52, map_role="villager")
        path = "character/npc_boy/Idle_breathing-idle_south.gif" if variant == "boy" else "character/npc_girl/south.png"
        if os.path.exists(path):
            raw = load_frames_from_gif_or_png(path)
            self.frames = [pygame.transform.scale(f, (44, 44)) for f in raw]


class TrainingTarget:
    """Target boneka latihan / monster latihan di Lobby."""
    def __init__(self, name, x, y, max_hp=45, defense=2, is_monster=False, can_respawn=True):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.width = 36
        self.height = 36
        self.max_hp = max_hp
        self.hp = max_hp
        self.defense = defense
        self.is_monster = is_monster
        self.can_respawn = can_respawn
        self.is_boss = False
        self.respawn_timer = 0.0
        self.respawn_delay = 3.5
        self.hurt_flash = 0.0
        self.frames = []
        self.frame_index = 0.0
        self.anim_speed = 6.0

        self.surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if not is_monster:
            pygame.draw.rect(self.surf, (140, 100, 50), (14, 18, 8, 18))
            pygame.draw.ellipse(self.surf, (210, 180, 100), (6, 6, 24, 20))
            pygame.draw.circle(self.surf, (230, 200, 120), (18, 8), 7)
            pygame.draw.line(self.surf, (100, 70, 30), (2, 14), (34, 14), 4)
        else:
            slime_path = "assets/characters/slime.png"
            if os.path.exists(slime_path):
                raw = load_frames_from_gif_or_png(slime_path, 32, 32, max_frames=4)
                self.frames = [pygame.transform.scale(f, (self.width, self.height)) for f in raw]
                self.surf = self.frames[0]

    def is_alive(self):
        return self.hp > 0

    def get_center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def take_damage(self, amount):
        if not self.is_alive():
            return 0
        actual = min(self.hp, amount)
        self.hp -= actual
        self.hurt_flash = 0.18
        audio_manager.play_sound("impact")
        if self.hp <= 0 and self.can_respawn:
            self.respawn_timer = self.respawn_delay
        return actual

    def get_rewards(self):
        if self.is_monster:
            return 35, random.randint(4, 8), random.randint(6, 14)
        return 18, random.randint(1, 3), random.randint(3, 7)

    def update(self, dt, player=None, map_loader=None, combat_mgr=None):
        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self.frames and len(self.frames) > 1:
            self.frame_index = (self.frame_index + self.anim_speed * dt) % len(self.frames)
            self.surf = self.frames[int(self.frame_index)]
        if not self.is_alive() and self.can_respawn:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.hp = self.max_hp
                audio_manager.play_sound("powerup")

    def draw(self, surface, camera_x, camera_y):
        if not self.is_alive():
            return
        dx = int(self.x - camera_x)
        dy = int(self.y - camera_y)

        shadow_surf = pygame.Surface((self.width, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), (0, 0, self.width, 8))
        surface.blit(shadow_surf, (dx, dy + self.height - 4))

        if self.hurt_flash > 0:
            tinted = self.surf.copy()
            tinted.fill((255, 80, 80, 200), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, (dx, dy))
        else:
            surface.blit(self.surf, (dx, dy))

        bar_w = max(34, self.width)
        bar_h = 5
        bx = int(self.x + self.width / 2 - camera_x - bar_w / 2)
        by = int(self.y - 12 - camera_y)

        pygame.draw.rect(surface, (20, 20, 25), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pct = max(0.0, min(1.0, self.hp / self.max_hp))
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, COLOR_HP, (bx, by, int(bar_w * pct), bar_h))

        font = get_font(11, bold=True)
        t_surf = font.render(self.name, True, COLOR_WHITE)
        surface.blit(t_surf, (int(self.x + self.width / 2 - camera_x - t_surf.get_width() / 2), by - 14))


class Enemy(TrainingTarget):
    """Monster aktif (Melee/Ranged) dengan multiplier kesulitan GDD."""
    def __init__(
        self, name, x, y, max_hp=36, defense=4, attack_damage=120, speed=82.0,
        aggro_range=250.0, attack_range=44.0, sprite_kind="monster1",
        exp_reward=55, ash_range=(6, 12), gold_range=(10, 22), is_boss=False,
        is_ranged=False, proj_color=(220, 90, 255)
    ):
        size = 60 if is_boss else (44 if sprite_kind in ("monster1", "monster_ranged") else 36)
        super().__init__(name, x, y, max_hp=max_hp, defense=defense, is_monster=True, can_respawn=False)
        self.width = size
        self.height = size
        self.attack_damage = attack_damage
        self.speed = speed
        self.aggro_range = aggro_range
        self.attack_range = attack_range
        self.sprite_kind = sprite_kind
        self.exp_reward = exp_reward
        self.ash_range = ash_range
        self.gold_range = gold_range
        self.is_boss = is_boss
        self.map_role = "boss" if is_boss else "enemy"
        self.is_ranged = is_ranged
        self.proj_color = proj_color

        self.direction = "south"
        self.state = "idle"
        self.windup_duration = 0.55 if not is_boss else 0.65
        self.windup_timer = 0.0
        self.attack_cooldown = 1.55 if not is_boss else 1.45
        self.attack_cd_timer = 0.0
        self.knockback_vx = 0.0
        self.knockback_vy = 0.0

        self.dir_animations = {}
        self.attack_animations = {}
        self._load_enemy_sprites(sprite_kind)

    def _load_enemy_sprites(self, sprite_kind):
        self.dir_animations = {}
        self.attack_animations = {}
        dirs = ("east", "north", "south", "west")

        gif_map = {
            "monster1": ("character/monster1/Idle_scary-walk_{d} (1).gif", None),
            "monster_ranged": ("character/monster_ranged/walk_{d}.gif", None),
            "boss_demonKing": ("character/boss_demonKing/Idle_scary-walk_{d}.gif", "character/boss_demonKing/Idle_cross-punch_{d}.gif"),
            "boss_gargantua": ("character/boss_gargantua/walk_{d}.gif", "character/boss_gargantua/attack_{d}.gif"),
            "boss_vespa": ("character/boss_vespa/walk_{d}.gif", "character/boss_vespa/attack_{d}.gif"),
            "boss_ignis": ("character/boss_ignis/walk_{d}.gif", "character/boss_ignis/attack_{d}.gif"),
            "boss_valerius": ("character/boss_valerius/walk_{d}.gif", "character/boss_valerius/attack_{d}.gif"),
            "boss_hollow_crown": ("character/boss_hollow_crown/float_{d}.gif", "character/boss_hollow_crown/float_{d}.gif"),
        }

        if sprite_kind in gif_map:
            walk_tpl, atk_tpl = gif_map[sprite_kind]
            for d in dirs:
                wp = walk_tpl.format(d=d)
                if os.path.exists(wp):
                    self.dir_animations[d] = [
                        pygame.transform.scale(f, (self.width, self.height))
                        for f in load_gif_frames(wp, (self.width, self.height))
                    ]
                if atk_tpl:
                    ap = atk_tpl.format(d=d)
                    if os.path.exists(ap):
                        self.attack_animations[d] = [
                            pygame.transform.scale(f, (self.width, self.height))
                            for f in load_gif_frames(ap, (self.width, self.height))
                        ]
        elif sprite_kind == "slime":
            slime_path = "assets/characters/slime.png"
            if os.path.exists(slime_path):
                raw = load_frames_from_gif_or_png(slime_path, 32, 32, max_frames=4)
                self.frames = [pygame.transform.scale(f, (self.width, self.height)) for f in raw]

        if self.dir_animations:
            self.frames = self.dir_animations.get("south", next(iter(self.dir_animations.values())))
        if self.frames:
            self.surf = self.frames[0]

    def get_hitbox(self):
        hw = max(16, int(self.width * 0.45))
        hh = max(12, int(self.height * 0.30))
        return pygame.Rect(
            int(self.x + (self.width - hw) / 2),
            int(self.y + self.height - hh - 2),
            hw, hh
        )

    def apply_knockback(self, vx, vy):
        mult = 0.40 if self.is_boss else 1.0
        self.knockback_vx = vx * mult
        self.knockback_vy = vy * mult

    def _move_with_collision(self, step_x, step_y, map_loader):
        if map_loader is None:
            self.x += step_x
            self.y += step_y
            return
        if step_x != 0:
            self.x += step_x
            if map_loader.is_blocked(self.get_hitbox()):
                self.x -= step_x
        if step_y != 0:
            self.y += step_y
            if map_loader.is_blocked(self.get_hitbox()):
                self.y -= step_y

    def get_rewards(self):
        return self.exp_reward, random.randint(*self.ash_range), random.randint(*self.gold_range)

    def _update_direction(self, dx, dy):
        if abs(dx) >= abs(dy):
            self.direction = "east" if dx >= 0 else "west"
        else:
            self.direction = "south" if dy >= 0 else "north"

    def _execute_attack(self, player, combat_mgr):
        if player is None or player.is_dead:
            return
        ec_x, ec_y = self.get_center()
        pc_x, pc_y = player.x + 24, player.y + 24
        dx, dy = pc_x - ec_x, pc_y - ec_y
        dist = math.hypot(dx, dy)

        if self.is_ranged and combat_mgr:
            ang = math.atan2(dy, dx)
            combat_mgr.spawn_projectile(ec_x, ec_y, ang, speed=175.0, damage=self.attack_damage, radius=7, color=self.proj_color)
            return

        if dist <= self.attack_range + 18:
            dealt = player.take_damage(self.attack_damage)
            if dealt > 0:
                if dist > 0:
                    kb = 175.0 if self.is_boss else 120.0
                    player.apply_knockback((dx / dist) * kb, (dy / dist) * kb)
                if combat_mgr:
                    combat_mgr.trigger_shake(0.14, 4.5 if self.is_boss else 3.0)
                    combat_mgr.floating_texts.append(
                        FloatingText(pc_x, player.y - 12, f"-{dealt}", COLOR_CRIT, font_size=18, is_crit=self.is_boss)
                    )
            elif getattr(player, "dodged_last_hit", False):
                player.dodged_last_hit = False
                if combat_mgr:
                    combat_mgr.floating_texts.append(
                        FloatingText(pc_x, player.y - 18, "PERFECT DODGE! +15 ST", (110, 220, 255), font_size=16, is_crit=True)
                    )

    def update(self, dt, player=None, map_loader=None, combat_mgr=None):
        if not self.is_alive():
            return

        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)
        if self.attack_cd_timer > 0:
            self.attack_cd_timer = max(0.0, self.attack_cd_timer - dt)

        if abs(self.knockback_vx) > 2.0 or abs(self.knockback_vy) > 2.0:
            self._move_with_collision(self.knockback_vx * dt, self.knockback_vy * dt, map_loader)
            decay = max(0.0, 1.0 - 9.0 * dt)
            self.knockback_vx *= decay
            self.knockback_vy *= decay
        else:
            self.knockback_vx = 0.0
            self.knockback_vy = 0.0

        if player and not player.is_dead:
            ec_x, ec_y = self.get_center()
            pc_x, pc_y = player.x + 24, player.y + 24
            dx, dy = pc_x - ec_x, pc_y - ec_y
            dist = math.hypot(dx, dy)

            if self.state == "windup":
                self._update_direction(dx, dy)
                self.windup_timer -= dt
                if self.windup_timer <= 0:
                    self._execute_attack(player, combat_mgr)
                    self.attack_cd_timer = self.attack_cooldown
                    self.state = "cooldown"
            elif self.is_ranged and dist <= self.aggro_range and self.attack_cd_timer <= 0:
                self._update_direction(dx, dy)
                self.state = "windup"
                self.windup_timer = self.windup_duration
            elif not self.is_ranged and dist <= self.attack_range and self.attack_cd_timer <= 0:
                self._update_direction(dx, dy)
                self.state = "windup"
                self.windup_timer = self.windup_duration
            elif dist <= self.aggro_range:
                self.state = "chase"
                if self.is_ranged:
                    # Jaga jarak taktis di belakang cover/pojok
                    if dist < 110 and dist > 0:
                        self._move_with_collision(-(dx / dist) * self.speed * 0.6 * dt, -(dy / dist) * self.speed * 0.6 * dt, map_loader)
                    elif dist > 200 and dist > 0:
                        self._move_with_collision((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt, map_loader)
                    self._update_direction(dx, dy)
                elif dist > self.attack_range * 0.75 and dist > 0:
                    self._update_direction(dx, dy)
                    self._move_with_collision((dx / dist) * self.speed * dt, (dy / dist) * self.speed * dt, map_loader)
            else:
                self.state = "idle"
        else:
            self.state = "idle"

        active_frames = self.frames
        if self.state == "windup" and self.attack_animations:
            active_frames = self.attack_animations.get(self.direction, active_frames)
        elif self.dir_animations:
            active_frames = self.dir_animations.get(self.direction, active_frames)

        if active_frames:
            if self.state in ("chase", "windup") or len(active_frames) > 1:
                spd = 11.0 if self.state == "windup" else self.anim_speed
                self.frame_index = (self.frame_index + spd * dt) % len(active_frames)
            self.surf = active_frames[int(self.frame_index) % len(active_frames)]

    def draw(self, surface, camera_x, camera_y):
        if not self.is_alive():
            return
        if self.state == "windup" and not self.is_ranged:
            cx = int(self.x + self.width / 2 - camera_x)
            cy = int(self.y + self.height / 2 - camera_y)
            r = int(self.attack_range)
            warn = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(warn, (255, 50, 40, 45), (r + 2, r + 2), r)
            pygame.draw.circle(warn, (255, 90, 60, 170), (r + 2, r + 2), r, 2)
            surface.blit(warn, (cx - r - 2, cy - r - 2))
        super().draw(surface, camera_x, camera_y)


class BossEntity(Enemy):
    """4 Jenderal Dungeon 1-4 & Final Boss 2 Fase Domain Ruang Takhta."""
    BOSS_SPECS = {
        "gargantua": ("Jenderal Gargantua (Dungeon 1)", "boss_gargantua", 95, 6, 95, 78.0, (110, 170, 75), 180),
        "vespa": ("Ratu Spora Vespa (Dungeon 2)", "boss_vespa", 230, 14, 155, 90.0, (185, 95, 245), 320),
        "ignis": ("Ignis Executioner (Dungeon 3)", "boss_ignis", 420, 24, 240, 102.0, (255, 125, 40), 500),
        "valerius": ("Jenderal Valerius (Dungeon 4)", "boss_valerius", 680, 36, 330, 114.0, (150, 230, 255), 740),
        "ash_lord": ("Sang Penguasa Abu (Fase 1)", "boss_demonKing", 560, 32, 300, 106.0, (255, 70, 55), 1100),
        "demon_king": ("Raja Iblis: Penguasa Abu", "boss_demonKing", 240, 15, 175, 88.0, (255, 70, 55), 400),
    }

    def __init__(self, boss_id, x, y):
        name, sprite_kind, hp, defense, atk, spd, pcol, exp_rew = self.BOSS_SPECS.get(
            boss_id, self.BOSS_SPECS["demon_king"]
        )
        super().__init__(
            name=name, x=x, y=y, max_hp=hp, defense=defense, attack_damage=atk,
            speed=spd, aggro_range=400.0, attack_range=58.0, sprite_kind=sprite_kind,
            exp_reward=exp_rew, ash_range=(20, 35), gold_range=(45, 80), is_boss=True,
            proj_color=pcol,
        )
        self.boss_id = boss_id
        self.phase = 1
        self.special_timer = 2.8
        self.skull_barrage_timer = 4.2
        self.skull_formation_idx = 0
        self.spiral_angle = 0.0

    def take_damage(self, amount):
        if not self.is_alive():
            return 0
        actual = min(self.hp, amount)
        self.hp -= actual
        self.hurt_flash = 0.18
        audio_manager.play_sound("impact")

        # Transformasi Fase 2 Final Boss (Sang Penguasa Abu -> Mahkota Kutukan)
        if self.hp <= 0 and self.boss_id == "ash_lord" and self.phase == 1:
            self.phase = 2
            self.name = "Mahkota Kutukan: The Hollow Crown (Fase 2)"
            self.max_hp = 720
            self.hp = 720
            self.attack_damage = 350
            self.speed = 118.0
            self.skull_barrage_timer = 2.0
            self._load_enemy_sprites("boss_hollow_crown")
            audio_manager.play_sound("explosion")
        return actual

    def update(self, dt, player=None, map_loader=None, combat_mgr=None):
        super().update(dt, player=player, map_loader=map_loader, combat_mgr=combat_mgr)
        if not self.is_alive() or player is None or player.is_dead or combat_mgr is None:
            return

        ec_x, ec_y = self.get_center()
        pc_x, pc_y = player.x + 24, player.y + 24
        dist = math.hypot(pc_x - ec_x, pc_y - ec_y)
        if dist > self.aggro_range:
            return

        base_ang = math.atan2(pc_y - ec_y, pc_x - ec_x)
        if self.boss_id == "ash_lord":
            # Serangan Khusus Final Boss Domain: 6 Kepala Tengkorak Laser (tak bisa dihancurkan)
            self.skull_barrage_timer -= dt
            if self.skull_barrage_timer <= 0 and hasattr(combat_mgr, "trigger_skull_lasers"):
                if self.phase == 2 or self.hp <= self.max_hp * 0.82:
                    formation = "top_bottom" if (self.skull_formation_idx % 2 == 0) else "left_right"
                    self.skull_formation_idx += 1
                    map_w = map_loader.map_width_px if map_loader else 1280
                    map_h = map_loader.map_height_px if map_loader else 1280
                    combat_mgr.trigger_skull_lasers(
                        formation=formation,
                        damage=int(self.attack_damage * (0.9 if self.phase == 1 else 1.05)),
                        map_w=map_w,
                        map_h=map_h,
                        focus_x=pc_x,
                        focus_y=pc_y,
                    )
                    self.skull_barrage_timer = 9.5 if self.phase == 1 else 6.8

        self.special_timer -= dt
        if self.special_timer > 0:
            return

        if self.boss_id == "gargantua":
            self.special_timer = 4.2
            # Hentakan tanah + lumpur radial 4 arah
            combat_mgr.slash_effects.append(SlashEffect(ec_x, ec_y, 0, radius=80, is_skill=True))
            for k in range(4):
                combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + k * (math.pi / 2), speed=150.0, damage=self.attack_damage, radius=8, color=self.proj_color)
        elif self.boss_id == "vespa":
            self.special_timer = 3.8
            combat_mgr.spawn_spore_trap(pc_x + random.uniform(-45, 45), pc_y + random.uniform(-45, 45), damage=self.attack_damage)
            for off in (-0.32, 0.0, 0.32):
                combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + off, speed=170.0, damage=self.attack_damage, radius=7, color=self.proj_color)
        elif self.boss_id == "ignis":
            self.special_timer = 3.4
            for off in (-0.35, 0.0, 0.35):
                combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + off, speed=195.0, damage=self.attack_damage, radius=8, color=self.proj_color)
        elif self.boss_id == "valerius":
            self.special_timer = 3.0
            for off in (-0.25, 0.0, 0.25):
                combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + off, speed=230.0, damage=self.attack_damage, radius=7, color=self.proj_color)
        elif self.boss_id == "ash_lord":
            if self.phase == 1:
                self.special_timer = 3.2
                for k in range(5):
                    combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + k * (2 * math.pi / 5), speed=195.0, damage=self.attack_damage, radius=8, color=(255, 85, 65))
            else:
                # Fase 2 Mahkota Kutukan: Spiral Bullet Hell gabungan 4 elemen
                self.special_timer = 1.7
                self.spiral_angle += 0.55
                elem_colors = [(110, 175, 75), (185, 95, 245), (255, 125, 40), (150, 230, 255)]
                for k in range(6):
                    ang = self.spiral_angle + k * (math.pi / 3)
                    combat_mgr.spawn_projectile(ec_x, ec_y, ang, speed=200.0, damage=self.attack_damage, radius=8, color=elem_colors[k % 4])
        else:
            self.special_timer = 3.6
            for off in (-0.3, 0.0, 0.3):
                combat_mgr.spawn_projectile(ec_x, ec_y, base_ang + off, speed=180.0, damage=self.attack_damage, radius=7, color=self.proj_color)


# Alias untuk menjaga kompatibilitas impor lama
BossEnemy = BossEntity
