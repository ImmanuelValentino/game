"""
Config file untuk game 'Ashes of Oakhaven: The Hollow Crown'.
Mendefinisikan resolusi, palet warna, tabel progresi GDD, konfigurasi 5 Stage/Bioma,
senjata, dan helper cache font.
"""
import pygame

# Resolusi Layar & Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Ashes of Oakhaven: The Hollow Crown"

# Map & Dimensi Default
TILE_SIZE = 32
MAP_WIDTH_TILES = 40
MAP_HEIGHT_TILES = 40
MAP_WIDTH_PX = MAP_WIDTH_TILES * TILE_SIZE
MAP_HEIGHT_PX = MAP_HEIGHT_TILES * TILE_SIZE

# Palet Warna Dark Fantasy
COLOR_BG = (15, 14, 23)
COLOR_WHITE = (245, 245, 247)
COLOR_BLACK = (10, 10, 12)
COLOR_DARK_SLATE = (24, 26, 36)
COLOR_PANEL_BG = (22, 24, 34, 235)
COLOR_PANEL_BORDER = (90, 78, 65)
COLOR_PANEL_BORDER_LIGHT = (180, 155, 110)

# Warna Bar Status
COLOR_HP = (220, 53, 69)
COLOR_HP_BG = (60, 20, 25)
COLOR_HP_TRAIL = (255, 140, 150)
COLOR_STAMINA = (40, 167, 69)
COLOR_STAMINA_BG = (15, 50, 25)
COLOR_EXP = (255, 193, 7)
COLOR_EXP_BG = (60, 50, 20)

# Warna Teks & Aksen
COLOR_GOLD = (245, 197, 66)
COLOR_ASH = (180, 180, 195)
COLOR_CRIT = (255, 80, 40)
COLOR_TEXT = (235, 235, 240)
COLOR_TEXT_MUTED = (160, 160, 175)
COLOR_TEXT_ACCENT = (110, 180, 255)

# Font Defaults & Cache
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
_FONT_CACHE = {}


def get_font(size, bold=False, italic=False):
    """Mengembalikan instance font yang di-cache agar tidak membuat SysFont tiap frame."""
    key = (size, bold, italic)
    font = _FONT_CACHE.get(key)
    if font is None:
        if not pygame.font.get_init():
            pygame.font.init()
        font = pygame.font.SysFont("Segoe UI, Arial", size, bold=bold, italic=italic)
        _FONT_CACHE[key] = font
    return font


# Keybindings
KEY_INTERACT = pygame.K_e
KEY_INVENTORY = pygame.K_b
KEY_INVENTORY_ALT = pygame.K_i
KEY_POTION_HP = pygame.K_1
KEY_POTION_STAMINA = pygame.K_2
KEY_HELP = pygame.K_h
KEY_MUTE = pygame.K_m
KEY_MINIMAP = pygame.K_TAB


# Parameter Keseimbangan Combat (Basic attack ringan, skill berat tetap 30 STA)
BASIC_ATTACK_STAMINA = 5.0
SKILL_ATTACK_STAMINA = 30.0
DODGE_ROLL_STAMINA = 15.0
STAMINA_REGEN_RATE = 24.0
STAMINA_REGEN_DELAY = 0.6
PLAYER_DAMAGE_SCALING = 1.65
HP_POTION_HEAL = 80
STAMINA_TONIC_RESTORE = 60


# Konfigurasi Bioma / Stage (Multiplier HP / DMG / SPD + Hazard + Spawn)
STAGE_CONFIGS = {
    "map1safeworld.tmx": {
        "stage_num": 0,
        "name": "Hub Oakhaven: Rusty Anchor",
        "rec_level": "Safe Zone",
        "hazard": "Aman (Api Unggun)",
        "hp_mult": 1.0, "dmg_mult": 1.0, "spd_mult": 1.0,
        "tier_mult": 1.0,
        "spawn": (584, 232),
        "bgm": "bgm_lobby",
    },
    "stage1_swamp.tmx": {
        "stage_num": 1,
        "name": "Stage 1: Rawa Kematian (Selatan)",
        "rec_level": "Lv. 1 - 10",
        "hazard": "Lumpur Pekat (-30% SPD) & Jebakan Hisap",
        "hp_mult": 1.0, "dmg_mult": 0.90, "spd_mult": 0.95,
        "tier_mult": 1.0,
        "spawn": (96, 608),
        "bgm": "bgm_dungeon",
    },
    "stage2_spore.tmx": {
        "stage_num": 2,
        "name": "Stage 2: Hutan Spora Membara (Timur)",
        "rec_level": "Lv. 11 - 25",
        "hazard": "Spora Peledak (AoE) & Kabut Racun (DoT)",
        "hp_mult": 1.2, "dmg_mult": 1.15, "spd_mult": 1.05,
        "tier_mult": 1.35,
        "spawn": (96, 608),
        "bgm": "bgm_dungeon",
    },
    "stage3_gehenna.tmx": {
        "stage_num": 3,
        "name": "Stage 3: Tungku Gehenna (Barat)",
        "rec_level": "Lv. 26 - 40",
        "hazard": "Conveyor Belt & Parit Lahar Panas",
        "hp_mult": 1.5, "dmg_mult": 1.4, "spd_mult": 1.2,
        "tier_mult": 1.75,
        "spawn": (96, 608),
        "bgm": "bgm_boss",
    },
    "stage4_frost.tmx": {
        "stage_num": 4,
        "name": "Stage 4: Benteng Salju Hitam (Utara)",
        "rec_level": "Lv. 41 - 55",
        "hazard": "Lantai Es Licin (Momentum Inersia)",
        "hp_mult": 1.85, "dmg_mult": 1.75, "spd_mult": 1.35,
        "tier_mult": 2.2,
        "spawn": (608, 1120),
        "bgm": "bgm_boss",
    },
    "stage5_throne.tmx": {
        "stage_num": 5,
        "name": "Stage 5: Ruang Takhta Obsidian (Pusat)",
        "rec_level": "Lv. 56 - 70",
        "hazard": "Tanpa Cover Statis - Duel Murni 2 Fase",
        "hp_mult": 2.2, "dmg_mult": 2.1, "spd_mult": 1.5,
        "tier_mult": 3.0,
        "spawn": (608, 1100),
        "bgm": "bgm_throne",
    },
    "dungeon1.tmx": {
        "stage_num": 1,
        "name": "Ruang Bawah Tanah 1 (Klasik)",
        "rec_level": "Lv. 3+",
        "hazard": "Lorong Labirin",
        "hp_mult": 1.0, "dmg_mult": 0.85, "spd_mult": 0.95,
        "tier_mult": 1.2,
        "spawn": (128, 288),
        "bgm": "bgm_dungeon",
    },
    "dungeon2.tmx": {
        "stage_num": 2,
        "name": "Ruang Bawah Tanah 2 (Klasik)",
        "rec_level": "Lv. 8+",
        "hazard": "Aula Penjaga Terkutuk",
        "hp_mult": 1.25, "dmg_mult": 1.15, "spd_mult": 1.05,
        "tier_mult": 1.5,
        "spawn": (1120, 288),
        "bgm": "bgm_boss",
    },
}

# Database Senjata GDD (mempengaruhi WeaponATK, Drop Multiplier, dan Karma)
WEAPON_DATABASE = {
    "ancestral_blade": {
        "name": "Pedang Leluhur",
        "weapon_atk": 65,
        "drop_mult": 1.0,
        "karma": 0,
        "desc": "Pedang tua klan Oakhaven.",
    },
    "redemption_blade_1": {
        "name": "Bilah Penebusan +1",
        "weapon_atk": 115,
        "drop_mult": 1.1,
        "karma": 10,
        "desc": "Pedang hitam yang ditempa ulang oleh Vektor.",
    },
    "redemption_blade_2": {
        "name": "Bilah Penebusan +2",
        "weapon_atk": 185,
        "drop_mult": 1.25,
        "karma": 15,
        "desc": "Bilah tempaan bercahaya perak penumpas Karak.",
    },
    "redemption_blade_3": {
        "name": "Bilah Penebusan Suci",
        "weapon_atk": 280,
        "drop_mult": 1.4,
        "karma": 20,
        "desc": "Wujud puncak Bilah Penebusan pemutus kutukan.",
    },
    "bloodthirst_blade": {
        "name": "Pedang Haus Darah",
        "weapon_atk": 320,
        "drop_mult": 1.5,
        "karma": -50,
        "desc": "Senjata terlarang Gael: ATK dahsyat & +50% Drop, mengunci jalan gelap.",
    },
}


def compute_level_stats(level):
    """Menghitung status dasar player per level mengikuti titik acuan tabel GDD."""
    # Titik acuan GDD: Lv 1(100/50/15/10), Lv 15(350/80/45/35), Lv 35(800/120/110/85), Lv 55(1500/200/240/180)
    anchors = [
        (1, 100, 50, 15, 10, 120),
        (15, 350, 80, 45, 35, 650),
        (35, 800, 120, 110, 85, 2200),
        (55, 1500, 200, 240, 180, 5500),
        (70, 2100, 240, 320, 240, 9500),
    ]
    lvl = max(1, min(70, int(level)))
    for i in range(len(anchors) - 1):
        l0, hp0, st0, atk0, def0, exp0 = anchors[i]
        l1, hp1, st1, atk1, def1, exp1 = anchors[i + 1]
        if l0 <= lvl <= l1:
            t = (lvl - l0) / max(1, (l1 - l0))
            return {
                "max_hp": int(round(hp0 + (hp1 - hp0) * t)),
                "max_stamina": int(round(st0 + (st1 - st0) * t)),
                "base_atk": int(round(atk0 + (atk1 - atk0) * t)),
                "base_def": int(round(def0 + (def1 - def0) * t)),
                "exp_to_next": int(round(exp0 + (exp1 - exp0) * t)),
            }
    _, hp, st, atk, df, expn = anchors[-1]
    return {"max_hp": hp, "max_stamina": st, "base_atk": atk, "base_def": df, "exp_to_next": expn}
