(function (global) {
  "use strict";

  const MAP_NAMES = [
    "map1safeworld",
    "stage1_swamp",
    "stage2_spore",
    "stage3_gehenna",
    "stage4_frost",
    "stage5_throne",
    "dungeon1",
    "dungeon2",
  ];

  const ITEM_ICON_FILES = [
    "AttackUpgrade.png",
    "Axe.png",
    "BookDarkness.png",
    "BookDeath.png",
    "BookFire.png",
    "BookIce.png",
    "BookRock.png",
    "Hammer.png",
    "Katana.png",
    "MagicWeapon.png",
    "OrbDarkness.png",
    "OrbFire.png",
    "OrbPlant.png",
    "potion_atk.png",
    "potion_crit.png",
    "potion_def.png",
    "potion_hp.png",
    "potion_stamina.png",
  ];

  function loadImage(src) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => resolve(null);
      img.src = src;
    });
  }

  class WebMap {
    constructor(meta, img) {
      this.id = meta.id;
      this.tileW = meta.tileW || 32;
      this.tileH = meta.tileH || 32;
      this.cols = meta.cols || 40;
      this.rows = meta.rows || 40;
      this.width = meta.width || 1280;
      this.height = meta.height || 1280;
      this.mapWidthPx = this.width;
      this.mapHeightPx = this.height;
      this.image = img;
      this.colliders = meta.colliders || [];
      this.hazards = meta.hazards || {};
    }

    isBlocked(rect) {
      const rx = rect.x;
      const ry = rect.y;
      const rw = rect.w;
      const rh = rect.h;
      if (rx < 0 || ry < 0 || rx + rw > this.width || ry + rh > this.height) {
        return true;
      }
      for (let i = 0; i < this.colliders.length; i++) {
        const c = this.colliders[i];
        if (rx < c[0] + c[2] && rx + rw > c[0] && ry < c[1] + c[3] && ry + rh > c[1]) {
          return true;
        }
      }
      return false;
    }

    isProjectileBlocked(rect) {
      return this.isBlocked(rect);
    }

    getHazardsAt(rect) {
      const found = new Set();
      let convVx = 0.0;
      const minC = Math.max(0, Math.floor(rect.x / this.tileW));
      const maxC = Math.min(this.cols - 1, Math.floor((rect.x + rect.w) / this.tileW));
      const minR = Math.max(0, Math.floor(rect.y / this.tileH));
      const maxR = Math.min(this.rows - 1, Math.floor((rect.y + rect.h) / this.tileH));
      for (let c = minC; c <= maxC; c++) {
        for (let r = minR; r <= maxR; r++) {
          const h = this.hazards[`${c},${r}`];
          if (h) {
            found.add(h);
            if (h === "conv_right") convVx = Math.max(convVx, 115.0);
            if (h === "conv_left") convVx = Math.min(convVx, -115.0);
          }
        }
      }
      return [found, convVx];
    }

    draw(ctx, camX, camY) {
      if (this.image) {
        ctx.drawImage(this.image, -Math.round(camX), -Math.round(camY));
      } else {
        ctx.fillStyle = "#14141e";
        ctx.fillRect(-Math.round(camX), -Math.round(camY), this.width, this.height);
      }
    }
  }

  class AssetStore {
    constructor() {
      this.sprites = {}; // key -> { img, frameW, frameH, frameCount, fps }
      this.maps = {}; // "map1safeworld.tmx" -> WebMap
      this.itemIcons = {}; // icon_file -> HTMLImageElement
      this.titleBg = null;
      this.ready = false;
    }

    async loadAll(onProgress) {
      const spriteResp = await fetch("assets/data/sprites.json");
      const spriteMeta = spriteResp.ok ? await spriteResp.json() : {};
      const spriteKeys = Object.keys(spriteMeta);
      const total = 1 + spriteKeys.length + ITEM_ICON_FILES.length + MAP_NAMES.length * 2;
      let done = 0;

      const tick = (label) => {
        done++;
        if (onProgress) onProgress(Math.min(1, done / Math.max(1, total)), label);
      };

      const tasks = [];
      tasks.push(
        loadImage("assets/ui/title_bg.png").then((img) => {
          this.titleBg = img;
          tick("Latar Judul");
        })
      );

      for (const key of spriteKeys) {
        const spec = spriteMeta[key];
        tasks.push(
          loadImage(spec.src).then((img) => {
            this.sprites[key] = Object.assign({}, spec, { img });
            tick(`Sprite ${key}`);
          })
        );
      }

      for (const file of ITEM_ICON_FILES) {
        tasks.push(
          loadImage(`assets/items_web/${file}`).then((img) => {
            this.itemIcons[file] = img;
            tick(`Ikon ${file}`);
          })
        );
      }

      for (const mname of MAP_NAMES) {
        tasks.push(
          (async () => {
            const [metaResp, img] = await Promise.all([
              fetch(`assets/data/maps/${mname}.json`),
              loadImage(`assets/data/maps/${mname}.png`),
            ]);
            tick(`Data ${mname}`);
            if (metaResp.ok) {
              const meta = await metaResp.json();
              this.maps[meta.id] = new WebMap(meta, img);
            }
            tick(`Peta ${mname}`);
          })()
        );
      }

      await Promise.all(tasks);
      this.ready = true;
    }

    drawSprite(ctx, key, elapsedSec, dx, dy, dw, dh, fpsOverride) {
      const sp = this.sprites[key];
      if (!sp || !sp.img) return false;
      const count = Math.max(1, sp.frameCount || 1);
      const fps = fpsOverride !== undefined ? fpsOverride : sp.fps || 6;
      const idx = count > 1 ? Math.floor(Math.max(0, elapsedSec) * fps) % count : 0;
      const sx = idx * sp.frameW;
      ctx.drawImage(
        sp.img,
        sx,
        0,
        sp.frameW,
        sp.frameH,
        Math.round(dx),
        Math.round(dy),
        Math.round(dw !== undefined ? dw : sp.frameW),
        Math.round(dh !== undefined ? dh : sp.frameH)
      );
      return true;
    }

    drawSpriteFrame(ctx, key, frameIdx, dx, dy, dw, dh) {
      const sp = this.sprites[key];
      if (!sp || !sp.img) return false;
      const count = Math.max(1, sp.frameCount || 1);
      const idx = ((frameIdx | 0) % count + count) % count;
      ctx.drawImage(
        sp.img,
        idx * sp.frameW,
        0,
        sp.frameW,
        sp.frameH,
        Math.round(dx),
        Math.round(dy),
        Math.round(dw !== undefined ? dw : sp.frameW),
        Math.round(dh !== undefined ? dh : sp.frameH)
      );
      return true;
    }
  }

  global.OakhavenAssets = new AssetStore();
})(window);
