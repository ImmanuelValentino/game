"""
Generate dungeon1.tmx menggunakan tileset yang sama dengan map1safeworld.tmx
GID Reference:
  487 = tanah gelap bebatuan (terrain)
  537 = rumput biasa
  499 = lantai terang / jalan
  530 = tebing (dipakai sebagai dinding dungeon)
"""

W, H = 40, 40

def make_floor_set():
    """Kumpulan (r,c) yang merupakan lantai (bisa dilewati)."""
    floor = set()
    # Koridor horizontal utama (baris 10-14)
    for r in range(9, 15):
        for c in range(2, 38):
            floor.add((r, c))
    # Koridor vertikal utama (kolom 19-20)
    for r in range(2, 38):
        for c in range(19, 21):
            floor.add((r, c))
    # Room 1 - kiri atas
    for r in range(3, 9):
        for c in range(3, 16):
            floor.add((r, c))
    # Room 2 - kanan atas
    for r in range(3, 9):
        for c in range(24, 37):
            floor.add((r, c))
    # Room 3 - kiri bawah
    for r in range(25, 33):
        for c in range(3, 16):
            floor.add((r, c))
    # Room 4 - boss room kanan bawah
    for r in range(25, 37):
        for c in range(24, 37):
            floor.add((r, c))
    # Koridor ke room bawah kiri
    for r in range(15, 25):
        for c in range(6, 9):
            floor.add((r, c))
    # Koridor ke room bawah kanan
    for r in range(15, 25):
        for c in range(31, 34):
            floor.add((r, c))
    return floor

floor_set = make_floor_set()

# Layer 1: Tile Layer 1 - semua tile gelap (487) sebagai latar dungeon
base_rows = []
for r in range(H):
    row_vals = []
    for c in range(W):
        row_vals.append("487")
    base_rows.append(",".join(row_vals))
base_csv = "\n".join(base_rows)

# Layer jalan: lantai dungeon (499) di area floor_set
floor_rows = []
for r in range(H):
    row_vals = []
    for c in range(W):
        if (r, c) in floor_set:
            row_vals.append("499")
        else:
            row_vals.append("0")
    floor_rows.append(",".join(row_vals))
floor_csv = "\n".join(floor_rows)

# Layer tebing: GID 530 di sel yang bukan lantai tapi bersebelahan dengan lantai (dinding)
wall_rows = []
for r in range(H):
    row_vals = []
    for c in range(W):
        if (r, c) not in floor_set:
            # cek tetangga
            is_wall = False
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if (nr, nc) in floor_set:
                    is_wall = True
                    break
            row_vals.append("530" if is_wall else "0")
        else:
            row_vals.append("0")
    wall_rows.append(",".join(row_vals))
wall_csv = "\n".join(wall_rows)

# Layer kosong
empty_csv = "\n".join([",".join(["0"]*W) for _ in range(H)])

# Tileset header sama persis dengan map1safeworld.tmx
tmx_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
tmx_content += '<map version="1.10" tiledversion="1.12.2" orientation="orthogonal" renderorder="right-down" '
tmx_content += 'width="40" height="40" tilewidth="32" tileheight="32" infinite="0" nextlayerid="10" nextobjectid="1">\n'
tmx_content += ' <tileset firstgid="1" source="../Project_Asli/Asset/TilesetField.tsx"/>\n'
tmx_content += ' <tileset firstgid="15" source="../Project_Asli/Map/grass.tsx"/>\n'
tmx_content += ' <tileset firstgid="16" source="../Project_Asli/Map/plains.tsx"/>\n'
tmx_content += ' <tileset firstgid="88" source="../Project_Asli/Map/tiles.tsx"/>\n'
tmx_content += ' <tileset firstgid="244" source="../Project_Asli/Map/doors.tsx"/>\n'
tmx_content += ' <tileset firstgid="248" source="../Project_Asli/Map/bridges.tsx"/>\n'
tmx_content += ' <tileset firstgid="269" source="../Project_Asli/Map/buildings-blue.tsx"/>\n'
tmx_content += ' <tileset firstgid="304" source="../Project_Asli/Map/buildings-green.tsx"/>\n'
tmx_content += ' <tileset firstgid="339" source="../Project_Asli/Map/buildings-neutral.tsx"/>\n'
tmx_content += ' <tileset firstgid="374" source="../Project_Asli/Map/buildings-red.tsx"/>\n'
tmx_content += ' <tileset firstgid="409" source="../Project_Asli/Map/buildings-yellow.tsx"/>\n'
tmx_content += ' <tileset firstgid="444" source="../Project_Asli/Map/castle.tsx"/>\n'
tmx_content += ' <tileset firstgid="486" source="../Project_Asli/Map/terrain.tsx"/>\n'
tmx_content += ' <tileset firstgid="616" source="../Project_Asli/Map/trees.tsx"/>\n'

def make_layer(lid, name, csv_data):
    return (
        f' <layer id="{lid}" name="{name}" width="40" height="40">\n'
        f'  <data encoding="csv">\n'
        f'{csv_data}\n'
        f'</data>\n'
        f' </layer>\n'
    )

tmx_content += make_layer(1, "Tile Layer 1", base_csv)
tmx_content += make_layer(3, "jalan", floor_csv)
tmx_content += make_layer(4, "tebing", wall_csv)
tmx_content += make_layer(5, "jembatan", empty_csv)
tmx_content += make_layer(2, "rumah", empty_csv)
tmx_content += make_layer(6, "castle", empty_csv)
tmx_content += make_layer(7, "door", empty_csv)
tmx_content += make_layer(8, "tree", empty_csv)
tmx_content += '</map>'

with open("dungeon1.tmx", "w", encoding="utf-8") as f:
    f.write(tmx_content)

print("dungeon1.tmx berhasil dibuat!")
print(f"Floor tiles: {len(floor_set)}")
