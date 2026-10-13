"""
Config file untuk game 'Ashes of Oakhaven: The Hollow Crown'
Mendefinisikan konstanta, resolusi, kontrol, dan palet warna UI.
"""
import pygame

# Resolusi Layar & Display
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "Ashes of Oakhaven: The Hollow Crown - Guild Lobby (Safe Zone)"

# Map & Dimensi
TILE_SIZE = 32
MAP_WIDTH_TILES = 40
MAP_HEIGHT_TILES = 40
MAP_WIDTH_PX = MAP_WIDTH_TILES * TILE_SIZE   # 1280 px
MAP_HEIGHT_PX = MAP_HEIGHT_TILES * TILE_SIZE # 1280 px

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

# Font Defaults
FONT_FAMILY = "Segoe UI, Arial, sans-serif"

# Keybindings
KEY_INTERACT = pygame.K_e
KEY_INVENTORY = pygame.K_b
KEY_INVENTORY_ALT = pygame.K_i
KEY_POTION_HP = pygame.K_1
KEY_POTION_STAMINA = pygame.K_2
KEY_HELP = pygame.K_h
KEY_MUTE = pygame.K_m
KEY_MINIMAP = pygame.K_TAB
