"""
NPC & Interactive Objects System untuk Lobby 'Ashes of Oakhaven: The Hollow Crown'.
Mencakup:
1. Campfire (Api Unggun) - Istirahat & Save Progress
2. Elara - Quest & Lore Master
3. Brog - Guild Receptionist & Tukar Abu Monster -> Emas
4. Pedagang Misterius - Toko Upgrade & Potion
5. Kapten Penjaga - Penjaga Gerbang Bab 1 Rawa Kematian
6. Training Dummy & Monster Target - Latihan serangan, leveling & kumpulkan ash.
"""
import os
import math
import random
import pygame
from PIL import Image
from src.config import COLOR_WHITE, COLOR_GOLD, COLOR_HP, COLOR_HP_BG, COLOR_TEXT
from src.audio import audio_manager

def load_frames_from_gif_or_png(path, frame_w=None, frame_h=None):
    frames = []
    if not os.path.exists(path):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(surf, (150, 150, 150), (16, 16), 14)
        return [surf]

    if path.endswith(".gif"):
        try:
            with Image.open(path) as im:
                for i in range(im.n_frames):
                    im.seek(i)
                    rgba = im.convert("RGBA")
                    surf = pygame.image.fromstring(rgba.tobytes(), rgba.size, "RGBA")
                    frames.append(surf)
        except Exception as e:
            print(f"[NPC] Error loading GIF {path}: {e}")
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            frames = [surf]
    elif path.endswith(".png"):
        try:
            full = pygame.image.load(path).convert_alpha()
            if frame_w and frame_h:
                cols = full.get_width() // frame_w
                rows = full.get_height() // frame_h
                for r in range(rows):
                    for c in range(cols):
                        sub = full.subsurface((c * frame_w, r * frame_h, frame_w, frame_h))
                        frames.append(sub)
            else:
                frames.append(full)
        except Exception as e:
            print(f"[NPC] Error loading PNG {path}: {e}")
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            frames = [surf]
    return frames if frames else [pygame.Surface((32, 32), pygame.SRCALPHA)]


class BaseNPC:
    def __init__(self, name, x, y, width=32, height=32, interact_radius=50):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.interact_radius = interact_radius
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
        # Render bayangan kecil
        shadow_surf = pygame.Surface((int(self.width * 0.8), 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, shadow_surf.get_width(), 8))
        surface.blit(shadow_surf, (int(self.x + self.width * 0.1 - camera_x), int(self.y + self.height - 4 - camera_y)))

        # Render frame sprite
        if self.frames:
            idx = int(self.frame_index) % len(self.frames)
            frame = self.frames[idx]
            surface.blit(frame, (int(self.x - camera_x), int(self.y - camera_y)))

        # Render nama NPC di atas kepala
        name_font = pygame.font.SysFont("Segoe UI, Arial", 13, bold=True)
        name_surf = name_font.render(self.name, True, COLOR_GOLD)
        outline = name_font.render(self.name, True, (0, 0, 0))
        nx = int(self.x + self.width / 2 - camera_x - name_surf.get_width() / 2)
        ny = int(self.y - 18 - camera_y)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            surface.blit(outline, (nx + ox, ny + oy))
        surface.blit(name_surf, (nx, ny))


class Campfire(BaseNPC):
    def __init__(self, x=544, y=288):
        super().__init__("Api Unggun Oakhaven", x, y, width=32, height=32, interact_radius=58)
        self.particles = []
        # Buat visual campfire dari lingkaran batu dan api
        self._create_fire_frames()

    def _create_fire_frames(self):
        self.frames = []
        for f in range(6):
            surf = pygame.Surface((32, 32), pygame.SRCALPHA)
            # Batu melingkar
            pygame.draw.ellipse(surf, (80, 75, 70), (4, 18, 24, 12))
            pygame.draw.ellipse(surf, (40, 35, 30), (6, 20, 20, 8))
            # Api berkedip
            flame_colors = [(255, 60, 20), (255, 160, 30), (255, 230, 80)]
            h = 14 + (f % 3) * 3
            pygame.draw.polygon(surf, flame_colors[0], [(8, 22), (24, 22), (16, 22 - h)])
            pygame.draw.polygon(surf, flame_colors[1], [(10, 22), (22, 22), (16, 22 - int(h * 0.75))])
            pygame.draw.polygon(surf, flame_colors[2], [(12, 22), (20, 22), (16, 22 - int(h * 0.5))])
            self.frames.append(surf)

    def update(self, dt):
        super().update(dt)
        # Partikel percikan api
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
        # Efek cahaya api (halo glow)
        glow_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 140, 40, 35), (45, 45), 45)
        pygame.draw.circle(glow_surf, (255, 180, 60, 55), (45, 45), 26)
        surface.blit(glow_surf, (int(self.x + 16 - camera_x - 45), int(self.y + 16 - camera_y - 45)))

        super().draw(surface, camera_x, camera_y)

        # Draw particles
        for p in self.particles:
            psurf = pygame.Surface((3, 3), pygame.SRCALPHA)
            psurf.fill((*p["color"], int(p["alpha"])))
            surface.blit(psurf, (int(p["x"] - camera_x), int(p["y"] - camera_y)))


class ElaraNPC(BaseNPC):
    def __init__(self, x=440, y=250):
        super().__init__("Elara (Pemandu Quest)", x, y, width=32, height=32, interact_radius=54)
        # Load sprite Woman
        sprite_path = "assets/characters/Woman/SpriteSheet.png"
        if os.path.exists(sprite_path):
            self.frames = load_frames_from_gif_or_png(sprite_path, 16, 16)
            # Skala 2x agar sesuai ukuran dunia
            self.frames = [pygame.transform.scale(f, (32, 32)) for f in self.frames[:4]]
        # Load portrait
        portrait_path = "assets/characters/Woman/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


class BrogNPC(BaseNPC):
    def __init__(self, x=650, y=250):
        super().__init__("Brog (Penukar Abu)", x, y, width=48, height=48, interact_radius=60)
        # Gunakan animated sprite npc_guild yang disediakan pengguna!
        gif_path = "character/npc_guild/Idle_breathing-idle_south.gif"
        if os.path.exists(gif_path):
            raw_frames = load_frames_from_gif_or_png(gif_path)
            # Skala sedikit agar proporsional
            self.frames = [pygame.transform.scale(f, (52, 52)) for f in raw_frames]
            self.width = 52
            self.height = 52
        
        portrait_path = "assets/characters/Villager/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


class MerchantNPC(BaseNPC):
    def __init__(self, x=480, y=440):
        super().__init__("Pedagang Misterius", x, y, width=32, height=32, interact_radius=54)
        sprite_path = "assets/characters/SorcererBlack/SpriteSheet.png"
        if os.path.exists(sprite_path):
            self.frames = load_frames_from_gif_or_png(sprite_path, 16, 16)
            self.frames = [pygame.transform.scale(f, (32, 32)) for f in self.frames[:4]]
        
        portrait_path = "assets/characters/SorcererBlack/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


class GatekeeperNPC(BaseNPC):
    def __init__(self, x=864, y=120):
        super().__init__("Kapten Penjaga Gerbang", x, y, width=32, height=32, interact_radius=55)
        sprite_path = "assets/characters/Knight/SpriteSheet.png"
        if os.path.exists(sprite_path):
            self.frames = load_frames_from_gif_or_png(sprite_path, 16, 16)
            self.frames = [pygame.transform.scale(f, (32, 32)) for f in self.frames[:4]]
        
        portrait_path = "assets/characters/Knight/Faceset.png"
        if os.path.exists(portrait_path):
            self.portrait = pygame.image.load(portrait_path).convert_alpha()
            self.portrait = pygame.transform.scale(self.portrait, (80, 80))


class TrainingTarget:
    """Target boneka latihan / monster percobaan untuk menguji serangan, damage, dan drop reward."""
    def __init__(self, name, x, y, max_hp=120, is_monster=False):
        self.name = name
        self.x = float(x)
        self.y = float(y)
        self.width = 36
        self.height = 36
        self.max_hp = max_hp
        self.hp = max_hp
        self.is_monster = is_monster
        self.respawn_timer = 0.0
        self.respawn_delay = 3.5 # detik
        self.hurt_flash = 0.0

        # Sprite / Visual
        self.surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if not is_monster:
            # Boneka jerami latihan
            pygame.draw.rect(self.surf, (140, 100, 50), (14, 18, 8, 18)) # tiang
            pygame.draw.ellipse(self.surf, (210, 180, 100), (6, 6, 24, 20)) # badan jerami
            pygame.draw.circle(self.surf, (230, 200, 120), (18, 8), 7) # kepala
            pygame.draw.line(self.surf, (100, 70, 30), (2, 14), (34, 14), 4) # tangan kayu
        else:
            # Monster pengintai rawa (Slime / Karak)
            slime_path = "assets/characters/slime.png"
            if os.path.exists(slime_path):
                img = pygame.image.load(slime_path).convert_alpha()
                self.surf = pygame.transform.scale(img.subsurface((0, 0, 16, 16)), (self.width, self.height))
            else:
                pygame.draw.ellipse(self.surf, (80, 180, 90), (4, 8, 28, 24))
                pygame.draw.circle(self.surf, (255, 255, 255), (13, 16), 4)
                pygame.draw.circle(self.surf, (255, 255, 255), (23, 16), 4)
                pygame.draw.circle(self.surf, (10, 10, 10), (13, 16), 2)
                pygame.draw.circle(self.surf, (10, 10, 10), (23, 16), 2)

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

        if self.hp <= 0:
            self.respawn_timer = self.respawn_delay
        return actual

    def get_rewards(self):
        if self.is_monster:
            return 35, random.randint(3, 7), random.randint(5, 12) # exp, ash, gold
        else:
            return 20, random.randint(1, 3), random.randint(2, 6) # exp, ash, gold

    def update(self, dt):
        if self.hurt_flash > 0:
            self.hurt_flash = max(0.0, self.hurt_flash - dt)

        if not self.is_alive():
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.hp = self.max_hp
                audio_manager.play_sound("powerup")

    def draw(self, surface, camera_x, camera_y):
        if not self.is_alive():
            return

        dx = int(self.x - camera_x)
        dy = int(self.y - camera_y)

        # Shadow
        shadow_surf = pygame.Surface((self.width, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 90), (0, 0, self.width, 8))
        surface.blit(shadow_surf, (dx, dy + self.height - 4))

        # Main surface
        if self.hurt_flash > 0:
            tinted = self.surf.copy()
            tinted.fill((255, 80, 80, 200), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tinted, (dx, dy))
        else:
            surface.blit(self.surf, (dx, dy))

        # Health bar di atas kepala
        bar_w = 34
        bar_h = 5
        bx = int(self.x + self.width / 2 - camera_x - bar_w / 2)
        by = int(self.y - 12 - camera_y)

        pygame.draw.rect(surface, (20, 20, 25), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pct = max(0.0, min(1.0, self.hp / self.max_hp))
        pygame.draw.rect(surface, COLOR_HP_BG, (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, COLOR_HP, (bx, by, int(bar_w * pct), bar_h))

        # Nama target
        font = pygame.font.SysFont("Segoe UI, Arial", 11, bold=True)
        t_surf = font.render(self.name, True, COLOR_WHITE)
        surface.blit(t_surf, (int(self.x + self.width / 2 - camera_x - t_surf.get_width() / 2), by - 14))
