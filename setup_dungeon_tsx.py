import os
import xml.etree.ElementTree as ET
from PIL import Image

map_dir = 'map'
tree = ET.parse('dungeon1.tmx')
root = tree.getroot()

for ts in root.findall('tileset'):
    src = ts.attrib['source']
    tsx_name = os.path.basename(src)
    base = os.path.splitext(tsx_name)[0]
    png_name = base + '.png'
    png_path = os.path.join(map_dir, png_name)
    tsx_path = os.path.join(map_dir, tsx_name)
    
    if os.path.exists(png_path):
        with Image.open(png_path) as img:
            w, h = img.size
        # tile size is 32x32 unless image is smaller than 32
        tw = 32
        th = 32
        if w < 32 or h < 32 or (w % 32 != 0 and w < 64) or (h % 32 != 0 and h < 64):
            tw = w
            th = h
            cols = 1
            count = 1
        else:
            cols = max(1, w // 32)
            rows = max(1, h // 32)
            count = cols * rows
            
        content = f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2" name="{base}" tilewidth="{tw}" tileheight="{th}" tilecount="{count}" columns="{cols}">
 <image source="{png_name}" width="{w}" height="{h}"/>
</tileset>
'''
        with open(tsx_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # Also copy to root so any path resolves easily
        with open(tsx_name, 'w', encoding='utf-8') as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2" name="{base}" tilewidth="{tw}" tileheight="{th}" tilecount="{count}" columns="{cols}">
 <image source="map/{png_name}" width="{w}" height="{h}"/>
</tileset>
''')
        print(f'Generated TSX: {tsx_name} (tw={tw}, th={th}, count={count}, cols={cols})')
    else:
        # Create a dummy 1x1 transparent png and tsx so missing unused tilesets don't error
        dummy_png = f'dummy_{base}.png'
        dummy_png_path = os.path.join(map_dir, dummy_png)
        if not os.path.exists(dummy_png_path):
            d_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            d_img.save(dummy_png_path)
        content = f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2" name="{base}" tilewidth="32" tileheight="32" tilecount="1" columns="1">
 <image source="{dummy_png}" width="32" height="32"/>
</tileset>
'''
        with open(tsx_path, 'w', encoding='utf-8') as f:
            f.write(content)
        with open(tsx_name, 'w', encoding='utf-8') as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.10" tiledversion="1.12.2" name="{base}" tilewidth="32" tileheight="32" tilecount="1" columns="1">
 <image source="map/{dummy_png}" width="32" height="32"/>
</tileset>
''')
        print(f'Generated dummy TSX: {tsx_name}')
