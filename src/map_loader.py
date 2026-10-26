"""
Map Loader untuk memuat dan merender map1safeworld.tmx secara efisien di Pygame.
Mendukung flip tile Tiled (horizontal, vertikal, diagonal) dan collider otomatis.
"""
import os
import xml.etree.ElementTree as ET
import pygame
from src.config import TILE_SIZE, MAP_WIDTH_TILES, MAP_HEIGHT_TILES, SCREEN_WIDTH, SCREEN_HEIGHT

FLIPPED_HORIZONTALLY_FLAG = 0x80000000
FLIPPED_VERTICALLY_FLAG   = 0x40000000
FLIPPED_DIAGONALLY_FLAG   = 0x20000000
FLAGS_MASK                = 0x1FFFFFFF

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

        self.ground_surface = None
        self.overhead_surface = None

        self._load_tmx()
        self._pre_render_surfaces()
        self._build_colliders()

    def _resolve_file(self, primary_path, fallback_dir="assets/tilesets"):
        if os.path.exists(primary_path):
            return primary_path
        base = os.path.basename(primary_path)
        local_path = os.path.join(fallback_dir, base)
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
                        "firstgid": firstgid,
                        "tilewidth": ts_tw,
                        "tileheight": ts_th,
                        "surface": surf,
                        "cols": surf.get_width() // ts_tw,
                        "rows": surf.get_height() // ts_th
                    })
                else:
                    print(f"[MapLoader] Image not found: {img_path}")
                    # Create a placeholder magenta surface for missing tileset
                    placeholder_cols = 10
                    placeholder_rows = 10
                    surf = pygame.Surface((ts_tw * placeholder_cols, ts_th * placeholder_rows), pygame.SRCALPHA)
                    surf.fill((255, 0, 255, 255))  # Magenta
                    self.tilesets.append({
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
                import re
                raw_gids = [int(v) for v in re.split(r'[\s,]+', data_elem.text.strip()) if v]
                self.layers[name] = raw_gids

        print(f"[MapLoader] TMX loaded: {len(self.tilesets)} tilesets, {len(self.layers)} layers.")

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
        self.ground_surface.fill((30, 30, 30, 255))  # Dark gray background
        self.overhead_surface = pygame.Surface((self.map_width_px, self.map_height_px), pygame.SRCALPHA)

        # Layer order rendering
        # Render all layers in the order they appear in the TMX file (preserving original order)
        for layer_name, data in self.layers.items():
            for idx, raw_gid in enumerate(data):
                if raw_gid == 0:
                    continue
                gx = (idx % self.map_width_tiles) * self.tile_width
                gy = (idx // self.map_width_tiles) * self.tile_height
                tile = self.get_tile_surface(raw_gid)
                if tile:
                    self.ground_surface.blit(tile, (gx, gy))

        print("[MapLoader] Pre-rendered ground surface created successfully.")

    def _build_colliders(self):
        """Membangun collider rect dari layer rintangan.
        This method now supports multiple wall layer names (e.g., "dinding", "tebing",
        "castle", "rumah", "dinding bawah", "atas dinidng")."""
        water_gids = {496, 497, 498, 508}
        bridges = {i for i, gid in enumerate(self.layers.get("jembatan", [])) if gid != 0}
        # Treat both 'door' and 'pintu' layers as passable doors
        doors = {i for i, gid in enumerate(self.layers.get("door", [])) if gid != 0}
        doors.update({i for i, gid in enumerate(self.layers.get("pintu", [])) if gid != 0})

        blocked_indices = set()
        total_tiles = self.map_width_tiles * self.map_height_tiles

        tile1 = self.layers.get("Tile Layer 1", [])
        # Gather possible wall layers, default to empty list if missing.
        wall_layers = {
            "tebing": self.layers.get("tebing", []),
            "castle": self.layers.get("castle", []),
            "rumah": self.layers.get("rumah", []),
            "dinding": self.layers.get("dinding", []),
            "dinding bawah": self.layers.get("dinding bawah", []),
            "atas dinidng": self.layers.get("atas dinidng", []),
        }
        trees = self.layers.get("tree", [])

        for i in range(total_tiles):
            # Water blocks movement
            if i < len(tile1) and (tile1[i] & FLAGS_MASK) in water_gids:
                blocked_indices.add(i)
                continue
            # Cliff / tebing (except bridges)
            if i < len(wall_layers["tebing"]) and wall_layers["tebing"][i] != 0 and i not in bridges:
                blocked_indices.add(i)
                continue
            # Castle walls (except doors)
            if i < len(wall_layers["castle"]) and wall_layers["castle"][i] != 0 and i not in doors:
                blocked_indices.add(i)
                continue
            # Rumah walls (except doors)
            if i < len(wall_layers["rumah"]) and wall_layers["rumah"][i] != 0 and i not in doors:
                blocked_indices.add(i)
                continue
            # Generic wall layers
            for name in ("dinding", "dinding bawah", "atas dinidng"):
                layer = wall_layers.get(name, [])
                if i < len(layer) and layer[i] != 0:
                    blocked_indices.add(i)
                    break
            else:
                # Trees (trunk only)
                if i < len(trees) and trees[i] != 0:
                    blocked_indices.add(i)

        self.colliders = []
        for idx in blocked_indices:
            tx = (idx % self.map_width_tiles) * self.tile_width
            ty = (idx // self.map_width_tiles) * self.tile_height
            if idx < len(trees) and trees[idx] != 0:
                self.colliders.append(pygame.Rect(tx + 8, ty + 14, 16, 16))
            else:
                self.colliders.append(pygame.Rect(tx, ty, self.tile_width, self.tile_height))

        print(f"[MapLoader] Built {len(self.colliders)} collision tiles.")

    def is_blocked(self, rect):
        """Memeriksa apakah rect bertabrakan dengan rintangan map atau batas dunia."""
        # Batas dunia
        if rect.left < 0 or rect.right > self.map_width_px or rect.top < 0 or rect.bottom > self.map_height_px:
            return True
        
        # Cek tabrakan dengan tile rintangan
        for obstacle in self.colliders:
            if rect.colliderect(obstacle):
                return True
        return False

    def draw(self, surface, camera_x, camera_y):
        """Merender bagian peta yang terlihat di kamera."""
        surface.blit(self.ground_surface, (-camera_x, -camera_y))
        surface.blit(self.overhead_surface, (-camera_x, -camera_y))
