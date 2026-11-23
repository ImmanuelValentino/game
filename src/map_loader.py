"""
Map Loader untuk memuat dan merender map1safeworld.tmx secara efisien di Pygame.
Mendukung flip tile Tiled (horizontal, vertikal, diagonal) dan collider otomatis.
"""
import os
import re
import xml.etree.ElementTree as ET
import pygame
from src.config import TILE_SIZE, MAP_WIDTH_TILES, MAP_HEIGHT_TILES

FLIPPED_HORIZONTALLY_FLAG = 0x80000000
FLIPPED_VERTICALLY_FLAG   = 0x40000000
FLIPPED_DIAGONALLY_FLAG   = 0x20000000
FLAGS_MASK                = 0x1FFFFFFF

WALL_LAYER_NAMES = (
    "tebing", "castle", "rumah",
    "dinding", "dinding bawah", "atas dinidng",
    "wall", "atas tembok", "pillars",
)
PROP_LAYER_NAMES = ("meja", "patung", "chest", "pot tinggi air", "kursi", "rak")
DOOR_LAYER_NAMES = ("door", "pintu")
HAZARD_LAYER_MAP = {
    "hazard_mud": "mud",
    "hazard_poison": "poison",
    "hazard_conveyor_right": "conv_right",
    "hazard_conveyor_left": "conv_left",
    "hazard_lava": "lava",
    "hazard_ice": "ice",
}


class MapLoader:
    def __init__(self, tmx_path="map1safeworld.tmx"):
        self.tmx_path = tmx_path
        self.tile_width = TILE_SIZE
        self.tile_height = TILE_SIZE
        self.map_width_tiles = MAP_WIDTH_TILES
        self.map_height_tiles = MAP_HEIGHT_TILES
        self.map_width_px = self.map_width_tiles * self.tile_width
        self.map_height_px = self.map_height_tiles * self.tile_height

        self.tilesets = []
        self.tile_cache = {} # gid -> pygame.Surface
        self.layers = {}     # layer_name -> list of raw gids
        self.colliders = []  # list of pygame.Rect
        self.collider_grid = {} # (col, row) -> list of pygame.Rect
        self.hazard_grid = {}   # (col, row) -> str hazard type

        self.ground_surface = None

        self._load_tmx()
        self._pre_render_surfaces()
        self._build_colliders()
        self._build_hazards()

    def _resolve_file(self, primary_path, fallback_dir="assets/tilesets"):
        if os.path.exists(primary_path):
            return primary_path
        base = os.path.basename(primary_path)
        for cand_dir in (fallback_dir, "map"):
            local_path = os.path.join(cand_dir, base)
            if os.path.exists(local_path):
                return local_path
        return primary_path

    def _load_tmx(self):
        tree = ET.parse(self.tmx_path)
        root = tree.getroot()

        self.map_width_tiles = int(root.attrib.get("width", 40))
        self.map_height_tiles = int(root.attrib.get("height", 40))
        self.tile_width = int(root.attrib.get("tilewidth", 32))
        self.tile_height = int(root.attrib.get("tileheight", 32))
        self.map_width_px = self.map_width_tiles * self.tile_width
        self.map_height_px = self.map_height_tiles * self.tile_height

        # Parse Tilesets
        for ts_elem in root.findall("tileset"):
            firstgid = int(ts_elem.attrib["firstgid"])
            source = ts_elem.attrib["source"]
            tsx_path = self._resolve_file(source)

            if not os.path.exists(tsx_path):
                print(f"[MapLoader] WARNING: TSX file not found: {source}")
                continue

            tsx_tree = ET.parse(tsx_path)
            tsx_root = tsx_tree.getroot()
            ts_name = tsx_root.attrib.get("name", os.path.splitext(os.path.basename(tsx_path))[0])
            ts_tw = int(tsx_root.attrib.get("tilewidth", self.tile_width))
            ts_th = int(tsx_root.attrib.get("tileheight", self.tile_height))

            img_elem = tsx_root.find("image")
            if img_elem is not None:
                img_rel = img_elem.attrib["source"]
                tsx_dir = os.path.dirname(tsx_path)
                img_path = self._resolve_file(os.path.normpath(os.path.join(tsx_dir, img_rel)))

                if os.path.exists(img_path):
                    surf = pygame.image.load(img_path).convert_alpha()
                    self.tilesets.append({
                        "name": ts_name,
                        "firstgid": firstgid,
                        "tilewidth": ts_tw,
                        "tileheight": ts_th,
                        "surface": surf,
                        "cols": surf.get_width() // ts_tw,
                        "rows": surf.get_height() // ts_th
                    })
                else:
                    print(f"[MapLoader] Image not found: {img_path}")
                    placeholder_cols = 10
                    placeholder_rows = 10
                    surf = pygame.Surface((ts_tw * placeholder_cols, ts_th * placeholder_rows), pygame.SRCALPHA)
                    surf.fill((255, 0, 255, 255))
                    self.tilesets.append({
                        "name": ts_name,
                        "firstgid": firstgid,
                        "tilewidth": ts_tw,
                        "tileheight": ts_th,
                        "surface": surf,
                        "cols": placeholder_cols,
                        "rows": placeholder_rows
                    })

        # Urutkan tileset menurun berdasarkan firstgid agar pencarian mudah
        self.tilesets.sort(key=lambda x: x["firstgid"], reverse=True)

        # Parse Data Layers
        for layer_elem in root.findall("layer"):
            name = layer_elem.attrib.get("name")
            data_elem = layer_elem.find("data")
            if data_elem is not None and data_elem.text:
                raw_gids = [int(v) for v in re.split(r'[\s,]+', data_elem.text.strip()) if v]
                self.layers[name] = raw_gids

        print(f"[MapLoader] TMX loaded ({self.tmx_path}): {len(self.tilesets)} tilesets, {len(self.layers)} layers.")

    def get_tile_surface(self, raw_gid):
        if raw_gid == 0:
            return None
        if raw_gid in self.tile_cache:
            return self.tile_cache[raw_gid]

        flip_h = bool(raw_gid & FLIPPED_HORIZONTALLY_FLAG)
        flip_v = bool(raw_gid & FLIPPED_VERTICALLY_FLAG)
        flip_d = bool(raw_gid & FLIPPED_DIAGONALLY_FLAG)

        gid = raw_gid & FLAGS_MASK

        ts_match = None
        for ts in self.tilesets:
            if gid >= ts["firstgid"]:
                ts_match = ts
                break

        if not ts_match:
            return None

        local_id = gid - ts_match["firstgid"]
        tw = ts_match["tilewidth"]
        th = ts_match["tileheight"]
        cols = ts_match["cols"]

        if cols <= 0:
            return None

        tx = (local_id % cols) * tw
        ty = (local_id // cols) * th
        full_surf = ts_match["surface"]

        if tx + tw > full_surf.get_width() or ty + th > full_surf.get_height():
            return None

        tile_surf = full_surf.subsurface((tx, ty, tw, th)).copy()

        # Handle Tiled Transformations
        if flip_d:
            # Transpose = rotate 90 CCW then flip horizontal
            tile_surf = pygame.transform.rotate(tile_surf, 90)
            tile_surf = pygame.transform.flip(tile_surf, True, False)
        if flip_h or flip_v:
            tile_surf = pygame.transform.flip(tile_surf, flip_h, flip_v)

        self.tile_cache[raw_gid] = tile_surf
        return tile_surf

    def _pre_render_surfaces(self):
        self.ground_surface = pygame.Surface((self.map_width_px, self.map_height_px), pygame.SRCALPHA)
        self.ground_surface.fill((30, 30, 30, 255))

        for _, data in self.layers.items():
            for idx, raw_gid in enumerate(data):
                if raw_gid == 0:
                    continue
                gx = (idx % self.map_width_tiles) * self.tile_width
                gy = (idx // self.map_width_tiles) * self.tile_height
                tile = self.get_tile_surface(raw_gid)
                if tile:
                    draw_y = gy + self.tile_height - tile.get_height() if tile.get_height() != self.tile_height else gy
                    self.ground_surface.blit(tile, (gx, draw_y))

        print("[MapLoader] Pre-rendered ground surface created successfully.")

    def _add_collider(self, col, row, rect):
        self.colliders.append(rect)
        self.collider_grid.setdefault((col, row), []).append(rect)

    def _build_colliders(self):
        """Membangun collider rect dari layer rintangan untuk peta outdoor maupun dungeon."""
        has_terrain_water = any(ts["name"] == "terrain" and ts["firstgid"] == 486 for ts in self.tilesets)
        water_gids = {496, 497, 498, 508} if has_terrain_water else set()

        bridges = {i for i, gid in enumerate(self.layers.get("jembatan", [])) if gid != 0}
        doors = set()
        for dl in DOOR_LAYER_NAMES:
            doors.update(i for i, gid in enumerate(self.layers.get(dl, [])) if gid != 0)

        tile1 = self.layers.get("Tile Layer 1", [])
        tebing = self.layers.get("tebing", [])
        trees = self.layers.get("tree", [])
        structural_walls = [
            self.layers.get(name, [])
            for name in WALL_LAYER_NAMES if name != "tebing"
        ]
        prop_layers = [self.layers.get(name, []) for name in PROP_LAYER_NAMES]

        self.colliders = []
        self.collider_grid = {}
        total_tiles = self.map_width_tiles * self.map_height_tiles

        for i in range(total_tiles):
            col = i % self.map_width_tiles
            row = i // self.map_width_tiles
            tx = col * self.tile_width
            ty = row * self.tile_height

            # Air pada peta outdoor
            if water_gids and i < len(tile1) and (tile1[i] & FLAGS_MASK) in water_gids:
                self._add_collider(col, row, pygame.Rect(tx, ty, self.tile_width, self.tile_height))
                continue

            # Tebing (kecuali jembatan)
            if i < len(tebing) and tebing[i] != 0 and i not in bridges:
                self._add_collider(col, row, pygame.Rect(tx, ty, self.tile_width, self.tile_height))
                continue

            # Dinding bangunan/dungeon (kecuali pintu/door)
            is_wall = i not in doors and any(i < len(layer) and layer[i] != 0 for layer in structural_walls)
            if is_wall:
                self._add_collider(col, row, pygame.Rect(tx, ty, self.tile_width, self.tile_height))
                continue

            # Batang pohon
            if i < len(trees) and trees[i] != 0:
                self._add_collider(col, row, pygame.Rect(tx + 8, ty + 14, 16, 16))
                continue

            # Properti/furnitur padat di dungeon (meja, patung, chest, pot, kursi, rak)
            is_prop = i not in doors and i not in bridges and any(i < len(layer) and layer[i] != 0 for layer in prop_layers)
            if is_prop:
                self._add_collider(col, row, pygame.Rect(tx + 3, ty + 4, self.tile_width - 6, self.tile_height - 8))

        print(f"[MapLoader] Built {len(self.colliders)} collision tiles.")

    def _build_hazards(self):
        """Membangun peta hazard lingkungan per tile dari layer hazard_*.tmx."""
        self.hazard_grid = {}
        for lname, default_type in HAZARD_LAYER_MAP.items():
            data = self.layers.get(lname, [])
            for idx, raw_gid in enumerate(data):
                gid = raw_gid & FLAGS_MASK
                if gid == 0:
                    continue
                col = idx % self.map_width_tiles
                row = idx // self.map_width_tiles
                htype = default_type
                if lname == "hazard_mud":
                    if gid == 6:
                        htype = "sinkhole"
                    elif gid == 3:
                        htype = "acid"
                self.hazard_grid[(col, row)] = htype

    def get_hazards_at(self, rect):
        """Mengembalikan himpunan hazard aktif dan dorongan conveyor (vx, vy) di area rect."""
        hazards = set()
        conv_vx = 0.0
        if not self.hazard_grid:
            return hazards, conv_vx

        min_c = max(0, rect.left // self.tile_width)
        max_c = min(self.map_width_tiles - 1, max(0, rect.right - 1) // self.tile_width)
        min_r = max(0, rect.top // self.tile_height)
        max_r = min(self.map_height_tiles - 1, max(0, rect.bottom - 1) // self.tile_height)

        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                ht = self.hazard_grid.get((c, r))
                if ht:
                    hazards.add(ht)
                    if ht == "conv_right":
                        conv_vx = 95.0
                    elif ht == "conv_left":
                        conv_vx = -95.0
        return hazards, conv_vx

    def is_projectile_blocked(self, rect):
        """Proyektil terblokir tembok, pilar cover, dan batas dunia."""
        return self.is_blocked(rect)

    def is_blocked(self, rect):
        """Memeriksa apakah rect bertabrakan dengan rintangan map atau batas dunia dalam O(1)."""
        if rect.left < 0 or rect.right > self.map_width_px or rect.top < 0 or rect.bottom > self.map_height_px:
            return True

        min_c = max(0, rect.left // self.tile_width)
        max_c = min(self.map_width_tiles - 1, max(0, rect.right - 1) // self.tile_width)
        min_r = max(0, rect.top // self.tile_height)
        max_r = min(self.map_height_tiles - 1, max(0, rect.bottom - 1) // self.tile_height)

        for row in range(min_r, max_r + 1):
            for col in range(min_c, max_c + 1):
                for obstacle in self.collider_grid.get((col, row), ()):
                    if rect.colliderect(obstacle):
                        return True
        return False

    def draw(self, surface, camera_x, camera_y):
        """Merender bagian peta yang terlihat di kamera."""
        surface.blit(self.ground_surface, (-camera_x, -camera_y))
