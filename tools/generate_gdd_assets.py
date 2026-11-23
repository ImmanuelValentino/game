"""
Generator Aset Visual, Peta Tiled (.tmx/.tsx), dan Audio untuk menyatukan game
'Ashes of Oakhaven: The Hollow Crown' secara penuh sesuai GDD Kelompok 1.
"""
import math
import os
import random
import struct
import wave
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

random.seed(42)

# =============================================================================
# 1. GENERATOR TILESET BIOMA (32x32 pixel art, 8 kolom x 4 baris = 32 tile)
# =============================================================================
# Indeks Tile (local_id 0..31 -> firstgid=1 -> GID 1..32):
# Baris 0 (Rawa Kematian):
#   0: Rumput Rawa Gelap, 1: Lumpur Pekat (Hazard), 2: Air Rawa Beracun,
#   3: Dinding Batu Rawa, 4: Pohon Mati/Pilar Rawa, 5: Jebakan Hisap (Sinkhole),
#   6: Jalan Papan Rawa, 7: Pintu/Gerbang Rawa
# Baris 1 (Hutan Spora Membara):
#   8: Tanah Lumut Spora, 9: Tanah Berakar, 10: Kabut Racun Floor (Hazard),
#   11: Dinding Akar Spora, 12: Jamur Raksasa/Pilar, 13: Spora Peledak Pad,
#   14: Jalan Spora Ungu, 15: Gerbang Spora
# Baris 2 (Tungku Gehenna):
#   16: Lantai Besi Gelap, 17: Lahar Panas (Hazard), 18: Conveyor Kanan,
#   19: Conveyor Kiri, 20: Dinding Baja Tungku, 21: Pilar Besi Panas,
#   22: Ubin Kisi Api, 23: Gerbang Baja
# Baris 3 (Salju Hitam & Ruang Takhta Obsidian):
#   24: Salju Abu Gelap, 25: Lantai Es Licin (Hazard), 26: Dinding Es Hitam,
#   27: Pilar Es Kristal, 28: Lantai Cermin Obsidian, 29: Retakan Obsidian,
#   30: Dinding Obsidian Takhta, 31: Karpet/Singgasana Mahkota

TILE_NAMES = {
    "swamp_ground": 1, "swamp_mud": 2, "swamp_acid": 3, "swamp_wall": 4,
    "swamp_pillar": 5, "swamp_sink": 6, "swamp_path": 7, "swamp_door": 8,
    "spore_ground": 9, "spore_root": 10, "spore_poison": 11, "spore_wall": 12,
    "spore_pillar": 13, "spore_trap": 14, "spore_path": 15, "spore_door": 16,
    "furnace_floor": 17, "furnace_lava": 18, "conv_right": 19, "conv_left": 20,
    "furnace_wall": 21, "furnace_pillar": 22, "furnace_grate": 23, "furnace_door": 24,
    "frost_snow": 25, "frost_ice": 26, "frost_wall": 27, "frost_pillar": 28,
    "obsidian_floor": 29, "obsidian_crack": 30, "obsidian_wall": 31, "obsidian_throne": 32,
}


def _noise_fill(draw, ox, oy, base_rgb, delta=12, density=0.35):
    draw.rectangle([ox, oy, ox + 31, oy + 31], fill=base_rgb)
    for py in range(32):
        for px in range(32):
            if random.random() < density:
                d = random.randint(-delta, delta)
                col = tuple(max(0, min(255, c + d)) for c in base_rgb[:3]) + ((base_rgb[3],) if len(base_rgb) == 4 else (255,))
                draw.point((ox + px, oy + py), fill=col)


def _draw_brick_wall(draw, ox, oy, main_col, mortar_col, hi_col):
    draw.rectangle([ox, oy, ox + 31, oy + 31], fill=mortar_col)
    for row_i, y0 in enumerate((1, 11, 21)):
        offset = 0 if row_i % 2 == 0 else 8
        for x0 in range(-offset, 32, 16):
            x1 = max(0, x0 + 1)
            x2 = min(30, x0 + 14)
            if x2 > x1:
                draw.rectangle([ox + x1, oy + y0, ox + x2, oy + y0 + 8], fill=main_col)
                draw.line([ox + x1, oy + y0, ox + x2, oy + y0], fill=hi_col)


def _draw_pillar(draw, ox, oy, base_col, top_col, shadow_col):
    draw.rectangle([ox, oy, ox + 31, oy + 31], fill=(0, 0, 0, 0))
    draw.ellipse([ox + 4, oy + 20, ox + 28, oy + 30], fill=shadow_col)
    draw.rectangle([ox + 6, oy + 6, ox + 25, oy + 26], fill=base_col, outline=(20, 20, 25, 255))
    draw.ellipse([ox + 5, oy + 2, ox + 26, oy + 12], fill=top_col, outline=(20, 20, 25, 255))


def _draw_door(draw, ox, oy, frame_col, glow_col):
    draw.rectangle([ox, oy, ox + 31, oy + 31], fill=frame_col)
    draw.rectangle([ox + 4, oy + 3, ox + 27, oy + 30], fill=(22, 18, 28, 255), outline=glow_col)
    draw.ellipse([ox + 8, oy + 7, ox + 23, oy + 25], fill=glow_col)


def generate_biome_tileset():
    os.makedirs("assets/tilesets", exist_ok=True)
    img = Image.new("RGBA", (8 * 32, 4 * 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # --- Baris 0: Rawa Kematian ---
    # 0: swamp_ground
    _noise_fill(d, 0, 0, (44, 58, 42, 255), 10, 0.4)
    # 1: swamp_mud (lumpur pekat)
    _noise_fill(d, 32, 0, (66, 48, 34, 255), 8, 0.5)
    d.ellipse([38, 6, 56, 22], fill=(50, 36, 24, 255))
    d.ellipse([42, 10, 48, 16], fill=(86, 66, 44, 255))
    # 2: swamp_acid
    _noise_fill(d, 64, 0, (52, 88, 48, 255), 12, 0.45)
    d.ellipse([70, 8, 80, 18], fill=(110, 175, 70, 255))
    # 3: swamp_wall
    _draw_brick_wall(d, 96, 0, (58, 66, 54, 255), (28, 34, 28, 255), (84, 96, 76, 255))
    # 4: swamp_pillar (batang pohon mati)
    _draw_pillar(d, 128, 0, (74, 54, 38, 255), (96, 72, 52, 255), (20, 24, 18, 170))
    # 5: swamp_sink (jebakan hisap)
    _noise_fill(d, 160, 0, (54, 42, 30, 255), 8, 0.4)
    d.ellipse([164, 4, 188, 28], outline=(30, 20, 14, 255), width=2)
    d.ellipse([169, 9, 183, 23], fill=(24, 18, 14, 255))
    # 6: swamp_path
    _noise_fill(d, 192, 0, (92, 76, 54, 255), 10, 0.35)
    for y in (7, 15, 23):
        d.line([192, y, 223, y], fill=(54, 40, 26, 255))
    # 7: swamp_door
    _draw_door(d, 224, 0, (58, 66, 54, 255), (95, 190, 110, 200))

    # --- Baris 1: Hutan Spora Membara ---
    # 8: spore_ground
    _noise_fill(d, 0, 32, (40, 34, 62, 255), 10, 0.4)
    # 9: spore_root
    _noise_fill(d, 32, 32, (52, 42, 74, 255), 10, 0.35)
    d.line([34, 38, 60, 56], fill=(82, 58, 95, 255), width=2)
    # 10: spore_poison (kabut racun hijau-ungu)
    _noise_fill(d, 64, 32, (56, 74, 64, 255), 14, 0.5)
    d.ellipse([70, 38, 88, 56], fill=(115, 205, 110, 170))
    # 11: spore_wall
    _draw_brick_wall(d, 96, 32, (64, 44, 82, 255), (28, 18, 42, 255), (105, 72, 130, 255))
    # 12: spore_pillar (jamur raksasa)
    _draw_pillar(d, 128, 32, (98, 78, 120, 255), (175, 75, 190, 255), (20, 14, 30, 170))
    # 13: spore_trap
    _noise_fill(d, 160, 32, (48, 38, 68, 255), 8, 0.3)
    d.ellipse([166, 38, 186, 58], fill=(180, 90, 210, 255), outline=(230, 170, 255, 255))
    # 14: spore_path
    _noise_fill(d, 192, 32, (74, 60, 96, 255), 9, 0.35)
    # 15: spore_door
    _draw_door(d, 224, 32, (64, 44, 82, 255), (195, 95, 225, 200))

    # --- Baris 2: Tungku Gehenna ---
    # 16: furnace_floor
    _noise_fill(d, 0, 64, (54, 44, 44, 255), 8, 0.3)
    d.rectangle([0, 64, 31, 95], outline=(34, 28, 28, 255))
    # 17: furnace_lava
    _noise_fill(d, 32, 64, (220, 72, 18, 255), 25, 0.55)
    d.ellipse([38, 70, 56, 86], fill=(255, 195, 45, 255))
    # 18: conv_right
    _noise_fill(d, 64, 64, (72, 74, 84, 255), 6, 0.2)
    for x in (68, 78, 88):
        d.polygon([(x, 70), (x + 6, 80), (x, 90)], fill=(235, 150, 50, 255))
    # 19: conv_left
    _noise_fill(d, 96, 64, (72, 74, 84, 255), 6, 0.2)
    for x in (104, 114, 124):
        d.polygon([(x, 70), (x - 6, 80), (x, 90)], fill=(235, 150, 50, 255))
    # 20: furnace_wall
    _draw_brick_wall(d, 128, 64, (86, 48, 42, 255), (36, 20, 18, 255), (145, 76, 56, 255))
    # 21: furnace_pillar
    _draw_pillar(d, 160, 64, (92, 62, 54, 255), (150, 86, 56, 255), (30, 15, 10, 180))
    # 22: furnace_grate
    _noise_fill(d, 192, 64, (120, 48, 24, 255), 14, 0.4)
    for gx in range(195, 224, 6):
        d.line([gx, 64, gx, 95], fill=(44, 38, 38, 255), width=2)
    # 23: furnace_door
    _draw_door(d, 224, 64, (86, 48, 42, 255), (255, 145, 45, 210))

    # --- Baris 3: Benteng Salju Hitam & Ruang Takhta Obsidian ---
    # 24: frost_snow
    _noise_fill(d, 0, 96, (150, 166, 185, 255), 12, 0.35)
    # 25: frost_ice (es licin)
    _noise_fill(d, 32, 96, (110, 188, 228, 255), 10, 0.25)
    d.line([36, 102, 52, 118], fill=(220, 245, 255, 230), width=2)
    d.line([44, 100, 58, 114], fill=(200, 240, 255, 190), width=1)
    # 26: frost_wall
    _draw_brick_wall(d, 64, 96, (76, 98, 124, 255), (32, 44, 62, 255), (135, 175, 215, 255))
    # 27: frost_pillar
    _draw_pillar(d, 96, 96, (95, 145, 190, 255), (185, 230, 255, 255), (25, 35, 50, 170))
    # 28: obsidian_floor (cermin hitam)
    _noise_fill(d, 128, 96, (22, 20, 32, 255), 5, 0.2)
    d.line([130, 98, 156, 124], fill=(48, 44, 72, 200), width=1)
    d.rectangle([128, 96, 159, 127], outline=(40, 36, 58, 255))
    # 29: obsidian_crack
    _noise_fill(d, 160, 96, (26, 20, 34, 255), 6, 0.2)
    d.line([164, 100, 176, 114, 186, 122], fill=(175, 45, 55, 255), width=2)
    # 30: obsidian_wall
    _draw_brick_wall(d, 192, 96, (38, 30, 52, 255), (14, 10, 22, 255), (90, 52, 84, 255))
    # 31: obsidian_throne (karpet merah-emas)
    _noise_fill(d, 224, 96, (125, 24, 34, 255), 8, 0.25)
    d.rectangle([226, 98, 253, 125], outline=(230, 185, 70, 255), width=2)

    img.save("assets/tilesets/biome_tiles.png")

    tsx = """<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2" name="biome_tiles" tilewidth="32" tileheight="32" tilecount="32" columns="8">
 <image source="biome_tiles.png" width="256" height="128"/>
</tileset>
"""
    with open("assets/tilesets/biome_tiles.tsx", "w", encoding="utf-8") as f:
        f.write(tsx)
    print("Generated biome_tiles.png & biome_tiles.tsx")


# =============================================================================
# 2. GENERATOR 5 PETA STAGE GDD (.tmx 40x40 tile = 1280x1280 px)
# =============================================================================
def _build_tmx(filename, layers_dict):
    w, h = 40, 40
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<map version="1.10" tiledversion="1.12.2" orientation="orthogonal" renderorder="right-down" width="{w}" height="{h}" tilewidth="32" tileheight="32" infinite="0" nextlayerid="{len(layers_dict)+1}" nextobjectid="1">',
        ' <tileset firstgid="1" source="assets/tilesets/biome_tiles.tsx"/>',
    ]
    for lid, (lname, grid) in enumerate(layers_dict.items(), start=1):
        lines.append(f' <layer id="{lid}" name="{lname}" width="{w}" height="{h}">')
        lines.append('  <data encoding="csv">')
        for r in range(h):
            row_str = ",".join(str(grid[r][c]) for c in range(w))
            if r < h - 1:
                row_str += ","
            lines.append(row_str)
        lines.append('</data>')
        lines.append(' </layer>')
    lines.append('</map>')
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated {filename}")


def _empty_grid(val=0):
    return [[val for _ in range(40)] for _ in range(40)]


def _add_border_walls(wall_grid, wall_gid):
    for i in range(40):
        wall_grid[0][i] = wall_gid
        wall_grid[1][i] = wall_gid
        wall_grid[38][i] = wall_gid
        wall_grid[39][i] = wall_gid
        wall_grid[i][0] = wall_gid
        wall_grid[i][1] = wall_gid
        wall_grid[i][38] = wall_gid
        wall_grid[i][39] = wall_gid


def _add_rect(grid, r0, c0, r1, c1, val):
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            grid[r][c] = val


def generate_5_stage_maps():
    T = TILE_NAMES

    # --- STAGE 1: RAWA KEMATIAN ---
    base = _empty_grid(T["swamp_ground"])
    _add_rect(base, 17, 2, 22, 37, T["swamp_path"])
    _add_rect(base, 4, 18, 35, 21, T["swamp_path"])
    hazard = _empty_grid(0)
    # Genangan lumpur pekat & jebakan hisap
    _add_rect(hazard, 12, 6, 15, 11, T["swamp_mud"])
    _add_rect(hazard, 24, 8, 28, 13, T["swamp_mud"])
    _add_rect(hazard, 12, 27, 15, 32, T["swamp_mud"])
    _add_rect(hazard, 24, 26, 28, 31, T["swamp_mud"])
    hazard[19][14] = T["swamp_sink"]
    hazard[19][25] = T["swamp_sink"]
    hazard[14][19] = T["swamp_acid"]
    wall = _empty_grid(0)
    _add_border_walls(wall, T["swamp_wall"])
    # Sekat ruangan dengan pintu besar di tengah
    _add_rect(wall, 2, 13, 15, 13, T["swamp_wall"])
    _add_rect(wall, 24, 13, 37, 13, T["swamp_wall"])
    _add_rect(wall, 2, 26, 15, 26, T["swamp_wall"])
    _add_rect(wall, 24, 26, 37, 26, T["swamp_wall"])
    # Pilar/pohon mati untuk cover bullet-hell
    pillars = _empty_grid(0)
    for r, c in [(15, 7), (24, 7), (14, 16), (25, 16), (14, 23), (25, 23), (12, 31), (27, 31)]:
        pillars[r][c] = T["swamp_pillar"]
    door = _empty_grid(0)
    door[19][1] = T["swamp_door"]
    door[20][1] = T["swamp_door"]
    door[19][38] = T["swamp_door"]
    door[20][38] = T["swamp_door"]
    _build_tmx("stage1_swamp.tmx", {
        "Tile Layer 1": base, "hazard_mud": hazard, "dinding": wall, "pillars": pillars, "pintu": door
    })

    # --- STAGE 2: HUTAN SPORA MEMBARA ---
    base = _empty_grid(T["spore_ground"])
    _add_rect(base, 6, 4, 33, 35, T["spore_root"])
    _add_rect(base, 18, 2, 21, 37, T["spore_path"])
    hazard = _empty_grid(0)
    _add_rect(hazard, 8, 9, 13, 13, T["spore_poison"])
    _add_rect(hazard, 26, 10, 31, 14, T["spore_poison"])
    _add_rect(hazard, 9, 24, 14, 29, T["spore_poison"])
    _add_rect(hazard, 25, 24, 30, 29, T["spore_poison"])
    wall = _empty_grid(0)
    _add_border_walls(wall, T["spore_wall"])
    _add_rect(wall, 8, 16, 16, 17, T["spore_wall"])
    _add_rect(wall, 23, 16, 31, 17, T["spore_wall"])
    pillars = _empty_grid(0)
    for r, c in [(12, 7), (27, 7), (14, 21), (25, 21), (13, 33), (26, 33)]:
        pillars[r][c] = T["spore_pillar"]
    door = _empty_grid(0)
    door[19][1] = T["spore_door"]
    door[20][1] = T["spore_door"]
    _build_tmx("stage2_spore.tmx", {
        "Tile Layer 1": base, "hazard_poison": hazard, "dinding": wall, "pillars": pillars, "pintu": door
    })

    # --- STAGE 3: TUNGKU GEHENNA ---
    base = _empty_grid(T["furnace_floor"])
    _add_rect(base, 14, 10, 25, 29, T["furnace_grate"])
    hazard_conv_r = _empty_grid(0)
    hazard_conv_l = _empty_grid(0)
    hazard_lava = _empty_grid(0)
    # Conveyor belt mendorong ke parit lahar
    _add_rect(hazard_conv_r, 10, 7, 12, 16, T["conv_right"])
    _add_rect(hazard_conv_l, 27, 7, 29, 16, T["conv_left"])
    _add_rect(hazard_conv_r, 10, 23, 12, 32, T["conv_right"])
    _add_rect(hazard_conv_l, 27, 23, 29, 32, T["conv_left"])
    # Parit lahar (pinggir arena & jebakan tengah-sisi)
    _add_rect(hazard_lava, 5, 18, 9, 21, T["furnace_lava"])
    _add_rect(hazard_lava, 30, 18, 34, 21, T["furnace_lava"])
    _add_rect(hazard_lava, 10, 17, 12, 18, T["furnace_lava"])
    _add_rect(hazard_lava, 27, 21, 29, 22, T["furnace_lava"])
    wall = _empty_grid(0)
    _add_border_walls(wall, T["furnace_wall"])
    pillars = _empty_grid(0)
    for r, c in [(15, 8), (24, 8), (16, 15), (23, 15), (16, 24), (23, 24), (14, 33), (25, 33)]:
        pillars[r][c] = T["furnace_pillar"]
    door = _empty_grid(0)
    door[19][1] = T["furnace_door"]
    door[20][1] = T["furnace_door"]
    _build_tmx("stage3_gehenna.tmx", {
        "Tile Layer 1": base,
        "hazard_conveyor_right": hazard_conv_r,
        "hazard_conveyor_left": hazard_conv_l,
        "hazard_lava": hazard_lava,
        "dinding": wall,
        "pillars": pillars,
        "pintu": door,
    })

    # --- STAGE 4: BENTENG SALJU HITAM ---
    base = _empty_grid(T["frost_snow"])
    hazard_ice = _empty_grid(0)
    # Lantai es licin luas di aula benteng
    _add_rect(hazard_ice, 8, 6, 31, 33, T["frost_ice"])
    wall = _empty_grid(0)
    _add_border_walls(wall, T["frost_wall"])
    _add_rect(wall, 6, 13, 14, 13, T["frost_wall"])
    _add_rect(wall, 25, 13, 33, 13, T["frost_wall"])
    pillars = _empty_grid(0)
    for r, c in [(12, 9), (27, 9), (12, 20), (27, 20), (14, 28), (25, 28)]:
        pillars[r][c] = T["frost_pillar"]
    door = _empty_grid(0)
    door[38][19] = T["frost_snow"]
    door[38][20] = T["frost_snow"]
    _build_tmx("stage4_frost.tmx", {
        "Tile Layer 1": base, "hazard_ice": hazard_ice, "dinding": wall, "pillars": pillars, "pintu": door
    })

    # --- STAGE 5: RUANG TAKHTA OBSIDIAN ---
    base = _empty_grid(T["obsidian_floor"])
    # Retakan obsidian & karpet takhta di tengah-atas, TANPA pilar pelindung (sesuai GDD)
    decor = _empty_grid(0)
    for r, c in [(10, 10), (10, 29), (28, 10), (28, 29), (16, 16), (16, 23), (23, 16), (23, 23)]:
        decor[r][c] = T["obsidian_crack"]
    _add_rect(decor, 4, 18, 14, 21, T["obsidian_throne"])
    wall = _empty_grid(0)
    _add_border_walls(wall, T["obsidian_wall"])
    door = _empty_grid(0)
    door[38][19] = T["obsidian_floor"]
    door[38][20] = T["obsidian_floor"]
    _build_tmx("stage5_throne.tmx", {
        "Tile Layer 1": base, "decor": decor, "dinding": wall, "pintu": door
    })


# =============================================================================
# 3. GENERATOR SPRITE KARAKTER, MONSTER RANGED, & 5 BOS GDD (ANIMATED GIF)
#    Menggunakan teknik palette-transform & pixel-overlay berbasis sprite asli
#    repo (boss_demonKing, monster1, npc_formerAdvanture, npc_mapReader)
#    sehingga gaya pixel art & animasi 4 arah 100% serasi.
# =============================================================================
def _remap_pixel(r, g, b, a, theme):
    if a < 20:
        return (0, 0, 0, 0)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    # Pertahankan outline hitam agar sprite tetap tajam
    if r < 32 and g < 32 and b < 32:
        return (r, g, b, a)

    if theme == "gargantua":
        # Lumut rawa hijau-gelap + batu kecokelatan
        if lum > 0.72:
            return (min(255, int(195 * lum)), min(255, int(225 * lum)), int(110 * lum), a)
        return (int(55 + 95 * lum), int(85 + 115 * lum), int(42 + 48 * lum), a)
    if theme == "vespa":
        # Spora ungu membusuk + aksen racun hijau neon
        if lum > 0.78:
            return (int(120 * lum), 255, int(135 * lum), a)
        return (int(85 + 135 * lum), int(32 + 55 * lum), int(105 + 145 * lum), a)
    if theme == "ignis":
        # Baja hangus + bara api membara oranye-kuning
        if lum > 0.68:
            return (255, int(120 + 130 * lum), int(25 + 65 * lum), a)
        return (int(70 + 165 * lum), int(22 + 55 * lum), int(18 + 24 * lum), a)
    if theme == "valerius":
        # Zirah salju hitam perak & biru es bersinar
        if lum > 0.72:
            return (int(175 + 80 * lum), int(225 + 30 * lum), 255, a)
        return (int(48 + 115 * lum), int(88 + 140 * lum), int(135 + 120 * lum), a)
    if theme == "ranged":
        # Jubah kultis ungu gelap + orb sihir magenta
        if lum > 0.74:
            return (235, int(115 * lum), 255, a)
        return (int(62 + 95 * lum), int(35 + 48 * lum), int(95 + 135 * lum), a)
    return (r, g, b, a)


def _transform_gif(src_path, dst_path, theme, target_size=(64, 64), overlay_fn=None):
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    out_frames = []
    durations = []
    with Image.open(src_path) as im:
        for i in range(im.n_frames):
            im.seek(i)
            dur = im.info.get("duration", 120)
            durations.append(dur)
            rgba = im.convert("RGBA")
            w, h = rgba.size
            px = rgba.load()
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    px[x, y] = _remap_pixel(r, g, b, a, theme)
            if rgba.size != target_size:
                rgba = rgba.resize(target_size, Image.Resampling.NEAREST)
            if overlay_fn:
                overlay_fn(rgba, i)
            out_frames.append(rgba)

    out_frames[0].save(
        dst_path,
        save_all=True,
        append_images=out_frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )


def _overlay_orb(img, frame_idx):
    d = ImageDraw.Draw(img)
    r = 3 + (frame_idx % 2)
    cx, cy = img.width - 10, img.height // 2 - 4 + (frame_idx % 2)
    d.ellipse([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], fill=(190, 70, 255, 95))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(245, 165, 255, 255), outline=(60, 20, 90, 255))


def _overlay_fire_aura(img, frame_idx):
    d = ImageDraw.Draw(img)
    for k in range(3):
        ang = frame_idx * 0.9 + k * 2.1
        px = int(img.width // 2 + math.cos(ang) * 20)
        py = int(img.height // 2 + math.sin(ang) * 18)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 190, 40, 220))


def _overlay_ice_aura(img, frame_idx):
    d = ImageDraw.Draw(img)
    for k in range(3):
        ang = -frame_idx * 0.8 + k * 2.1
        px = int(img.width // 2 + math.cos(ang) * 20)
        py = int(img.height // 2 + math.sin(ang) * 18)
        d.polygon([(px, py - 3), (px + 3, py), (px, py + 3), (px - 3, py)], fill=(190, 245, 255, 230))


def _draw_crown_frame(size, frame_idx):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    hover = int(math.sin(frame_idx * math.pi / 3) * 3)
    glow_r = 22 + (frame_idx % 3) * 2
    d.ellipse([cx - glow_r, cy - glow_r + hover, cx + glow_r, cy + glow_r + hover], fill=(150, 18, 30, 75))
    d.ellipse([cx - 16, cy - 16 + hover, cx + 16, cy + 16 + hover], fill=(220, 40, 50, 95))
    pts = [
        (cx - 19, cy + 10 + hover), (cx - 22, cy - 12 + hover),
        (cx - 11, cy - 2 + hover), (cx, cy - 22 + hover),
        (cx + 11, cy - 2 + hover), (cx + 22, cy - 12 + hover),
        (cx + 19, cy + 10 + hover),
    ]
    d.polygon(pts, fill=(46, 20, 32, 255), outline=(14, 8, 16, 255))
    d.polygon([(cx - 15, cy + 7 + hover), (cx - 17, cy - 7 + hover), (cx, cy - 15 + hover), (cx + 17, cy - 7 + hover), (cx + 15, cy + 7 + hover)], fill=(78, 28, 42, 255))
    d.ellipse([cx - 6, cy - 4 + hover, cx + 6, cy + 7 + hover], fill=(255, 65, 55, 255), outline=(255, 195, 120, 255))
    return img


def generate_characters_and_bosses():
    dirs = ("east", "north", "south", "west")

    # Monster Ranged (basis sprite mapReader berjubah -> ungu gelap + orb sihir)
    for dname in dirs:
        _transform_gif(
            f"character/npc_mapReader/Idle_custom-walking_{dname}.gif",
            f"character/monster_ranged/walk_{dname}.gif",
            "ranged", target_size=(48, 48), overlay_fn=_overlay_orb,
        )

    # Boss 1: Gargantua (basis monster1 -> raksasa rawa lumut & batu)
    for dname in dirs:
        src = f"character/monster1/Idle_scary-walk_{dname} (1).gif"
        _transform_gif(src, f"character/boss_gargantua/walk_{dname}.gif", "gargantua", target_size=(64, 64))
        _transform_gif(src, f"character/boss_gargantua/attack_{dname}.gif", "gargantua", target_size=(68, 68))

    # Boss 2: Vespa / Mycelia (basis boss_demonKing -> spora ungu + hijau bioluminesensi)
    for dname in dirs:
        _transform_gif(f"character/boss_demonKing/Idle_scary-walk_{dname}.gif", f"character/boss_vespa/walk_{dname}.gif", "vespa", target_size=(64, 64), overlay_fn=_overlay_orb)
        _transform_gif(f"character/boss_demonKing/Idle_cross-punch_{dname}.gif", f"character/boss_vespa/attack_{dname}.gif", "vespa", target_size=(64, 64), overlay_fn=_overlay_orb)

    # Boss 3: Ignis Executioner (basis boss_demonKing -> bara api + partikel api)
    for dname in dirs:
        _transform_gif(f"character/boss_demonKing/Idle_scary-walk_{dname}.gif", f"character/boss_ignis/walk_{dname}.gif", "ignis", target_size=(64, 64), overlay_fn=_overlay_fire_aura)
        _transform_gif(f"character/boss_demonKing/Idle_cross-punch_{dname}.gif", f"character/boss_ignis/attack_{dname}.gif", "ignis", target_size=(64, 64), overlay_fn=_overlay_fire_aura)

    # Boss 4: Valerius / Valkyrie Frostbite (basis npc_formerAdvanture bersenjata -> ksatria es biru-perak)
    for dname in dirs:
        _transform_gif(f"character/npc_formerAdvanture/Idle_walk_{dname}.gif", f"character/boss_valerius/walk_{dname}.gif", "valerius", target_size=(64, 64), overlay_fn=_overlay_ice_aura)
        _transform_gif(f"character/npc_formerAdvanture/Idle_custom-slashing_with_sword_{dname}.gif", f"character/boss_valerius/attack_{dname}.gif", "valerius", target_size=(64, 64), overlay_fn=_overlay_ice_aura)

    # Boss 5 Fase 2: The Hollow Crown (mahkota duri abu merah melayang)
    os.makedirs("character/boss_hollow_crown", exist_ok=True)
    for dname in dirs:
        frames = [_draw_crown_frame(64, i) for i in range(6)]
        frames[0].save(
            f"character/boss_hollow_crown/float_{dname}.gif",
            save_all=True, append_images=frames[1:], duration=130, loop=0, disposal=2,
        )

    print("Generated all PixelLab-matched GDD monster & boss animated GIFs.")


# =============================================================================
# 4. GENERATOR AUDIO PROCEDURAL (.wav) UNTUK DUNGEON, BOSS, DETAK JANTUNG, SFX
# =============================================================================
def _write_wav(path, samples, sample_rate=22050):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(bytes(frames))


def _gen_tone_seq(notes, dur_each=0.35, amp=0.22, wave_type="sine", sr=22050):
    out = []
    for freq in notes:
        n = int(sr * dur_each)
        for i in range(n):
            t = i / sr
            env = min(1.0, i / (sr * 0.03)) * max(0.0, 1.0 - (i / n) ** 1.6)
            if freq <= 0:
                val = 0.0
            elif wave_type == "tri":
                val = 2.0 * abs(2.0 * ((t * freq) % 1.0) - 1.0) - 1.0
            else:
                val = math.sin(2.0 * math.pi * freq * t)
            out.append(val * amp * env)
    return out


def generate_audio_assets():
    sr = 22050
    # 1. Projectile fire SFX
    proj = []
    for i in range(int(sr * 0.16)):
        t = i / sr
        freq = 560 - 340 * (t / 0.16)
        env = 1.0 - (t / 0.16)
        proj.append(math.sin(2 * math.pi * freq * t) * 0.3 * env)
    _write_wav("assets/audio/projectile.wav", proj, sr)

    # 2. Explosion / Spore burst SFX
    expl = []
    for i in range(int(sr * 0.35)):
        t = i / sr
        env = (1.0 - t / 0.35) ** 2
        rumble = math.sin(2 * math.pi * (85 - 40 * t) * t)
        noise = random.uniform(-0.6, 0.6)
        expl.append((rumble * 0.5 + noise * 0.5) * 0.4 * env)
    _write_wav("assets/audio/explosion.wav", expl, sr)

    # 3. Perfect Dodge / Parry chime
    parry = _gen_tone_seq([660, 990], dur_each=0.09, amp=0.3, wave_type="sine", sr=sr)
    _write_wav("assets/audio/parry.wav", parry, sr)

    # 4. BGM Dungeon (dark minor ambient loop ~8s)
    dungeon_notes = [110, 130.8, 146.8, 123.5, 110, 164.8, 146.8, 130.8] * 2
    _write_wav("assets/audio/bgm_dungeon.wav", _gen_tone_seq(dungeon_notes, 0.48, 0.20, "tri", sr), sr)

    # 5. BGM Boss (tense rhythmic bass loop)
    boss_notes = [98, 98, 116.5, 110, 98, 130.8, 146.8, 116.5] * 2
    _write_wav("assets/audio/bgm_boss.wav", _gen_tone_seq(boss_notes, 0.32, 0.25, "tri", sr), sr)

    # 6. Heartbeat BGM untuk Ruang Takhta Obsidian (GDD Bab 6: "hanya suara detak jantung berirama")
    hb = []
    beat_len = int(sr * 1.1)
    for i in range(beat_len):
        t = i / sr
        pulse1 = math.exp(-((t - 0.12) / 0.035) ** 2) * math.sin(2 * math.pi * 55 * t)
        pulse2 = math.exp(-((t - 0.30) / 0.04) ** 2) * math.sin(2 * math.pi * 48 * t) * 0.75
        hb.append((pulse1 + pulse2) * 0.55)
    _write_wav("assets/audio/bgm_throne.wav", hb, sr)

    # 7. Good Ending & Bad Ending stingers
    _write_wav("assets/audio/ending_good.wav", _gen_tone_seq([261.6, 329.6, 392.0, 523.2, 659.2], 0.45, 0.28, "sine", sr), sr)
    _write_wav("assets/audio/ending_bad.wav", _gen_tone_seq([146.8, 138.6, 116.5, 98.0, 73.4], 0.50, 0.28, "tri", sr), sr)
    print("Generated all procedural GDD audio files.")


if __name__ == "__main__":
    generate_biome_tileset()
    generate_5_stage_maps()
    generate_characters_and_bosses()
    generate_audio_assets()
