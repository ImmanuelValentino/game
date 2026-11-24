(function (global) {
  "use strict";

  const Config = {
    TITLE: "Ashes of Oakhaven: The Hollow Crown",
    DEFAULT_WIDTH: 1280,
    DEFAULT_HEIGHT: 720,
    MIN_VIEWPORT_WIDTH: 860,
    MIN_VIEWPORT_HEIGHT: 620,
    TILE_SIZE: 32,
    MAP_WIDTH_PX: 1280,
    MAP_HEIGHT_PX: 1280,

    COLOR_BG: "#0f0e17",
    COLOR_PANEL_BG: "rgba(22, 24, 34, 0.92)",
    COLOR_PANEL_BORDER: "#5a4e41",
    COLOR_PANEL_BORDER_LIGHT: "#b49b6e",
    COLOR_WHITE: "#f5f5f7",
    COLOR_GOLD: "#f5c542",
    COLOR_ASH: "#b4b4c3",
    COLOR_HP: "#dc3545",
    COLOR_HP_BG: "#3c1419",
    COLOR_HP_TRAIL: "#ff8c96",
    COLOR_STAMINA: "#28a745",
    COLOR_STAMINA_BG: "#0f3219",
    COLOR_EXP: "#ffc107",
    COLOR_EXP_BG: "#3c3214",
    COLOR_CRIT: "#ff5028",
    COLOR_TEXT: "#ebebf0",
    COLOR_TEXT_MUTED: "#a0a0af",
    COLOR_TEXT_ACCENT: "#6eb4ff",

    BASIC_ATTACK_STAMINA: 5.0,
    SKILL_ATTACK_STAMINA: 30.0,
    DODGE_ROLL_STAMINA: 15.0,
    STAMINA_REGEN_RATE: 24.0,
    STAMINA_REGEN_DELAY: 0.6,
    PLAYER_DAMAGE_SCALING: 1.15,

    HP_POTION_HEAL: 80,
    STAMINA_TONIC_RESTORE: 60,
    ATTACK_BOOST_MULT: 1.5,
    ATTACK_BOOST_DURATION: 15.0,
    DEFENSE_BOOST_FLAT: 18,
    DEFENSE_BOOST_DURATION: 20.0,
    CRIT_BOOST_FLAT: 0.35,
    CRIT_BOOST_DURATION: 20.0,

    LEVEL_ANCHORS: [
      [1, 100, 50, 15, 10, 120],
      [15, 350, 80, 45, 35, 650],
      [35, 800, 120, 110, 85, 2200],
      [55, 1500, 200, 240, 180, 5500],
      [70, 2100, 240, 320, 240, 9500],
    ],

    WEAPON_DATABASE: {
      ancestral_blade: {
        name: "Pedang Leluhur",
        weapon_atk: 65,
        drop_mult: 1.0,
        karma: 0,
        desc: "Pedang tua klan Oakhaven.",
      },
      redemption_blade_1: {
        name: "Bilah Penebusan +1",
        weapon_atk: 115,
        drop_mult: 1.1,
        karma: 10,
        desc: "Pedang hitam yang ditempa ulang oleh Vektor.",
      },
      redemption_blade_2: {
        name: "Bilah Penebusan +2",
        weapon_atk: 185,
        drop_mult: 1.25,
        karma: 15,
        desc: "Bilah tempaan bercahaya perak penumpas Karak.",
      },
      redemption_blade_3: {
        name: "Bilah Penebusan Suci",
        weapon_atk: 280,
        drop_mult: 1.4,
        karma: 20,
        desc: "Wujud puncak Bilah Penebusan pemutus kutukan.",
      },
      bloodthirst_blade: {
        name: "Pedang Haus Darah",
        weapon_atk: 320,
        drop_mult: 1.5,
        karma: -50,
        desc: "Senjata terlarang Gael: ATK dahsyat & +50% Drop, mengunci jalan gelap.",
      },
    },

    STAGE_CONFIGS: {
      "map1safeworld.tmx": {
        stage_num: 0,
        name: "Hub Oakhaven: Rusty Anchor",
        rec_level: "Safe Zone",
        hazard: "Aman (Api Unggun)",
        hp_mult: 1.0,
        dmg_mult: 1.0,
        spd_mult: 1.0,
        tier_mult: 1.0,
        spawn: [584, 232],
        bgm: "bgm_village",
      },
      "stage1_swamp.tmx": {
        stage_num: 1,
        name: "Dungeon 1: Rawa Kematian (Selatan)",
        rec_level: "Lv. 1 - 10",
        hazard: "Lumpur Pekat (-30% SPD) & Jebakan Hisap",
        hp_mult: 1.0,
        dmg_mult: 1.0,
        spd_mult: 1.0,
        tier_mult: 1.0,
        spawn: [96, 608],
        bgm: "bgm_dungeon",
      },
      "stage2_spore.tmx": {
        stage_num: 2,
        name: "Dungeon 2: Hutan Spora Membara (Timur)",
        rec_level: "Lv. 11 - 25",
        hazard: "Spora Peledak (AoE) & Kabut Racun (DoT)",
        hp_mult: 1.85,
        dmg_mult: 1.65,
        spd_mult: 1.15,
        tier_mult: 1.45,
        spawn: [96, 608],
        bgm: "bgm_dungeon",
      },
      "stage3_gehenna.tmx": {
        stage_num: 3,
        name: "Dungeon 3: Tungku Gehenna (Barat)",
        rec_level: "Lv. 26 - 40",
        hazard: "Conveyor Belt & Parit Lahar Panas",
        hp_mult: 3.1,
        dmg_mult: 2.55,
        spd_mult: 1.3,
        tier_mult: 1.9,
        spawn: [96, 608],
        bgm: "bgm_boss",
      },
      "stage4_frost.tmx": {
        stage_num: 4,
        name: "Dungeon 4: Benteng Salju Hitam (Utara)",
        rec_level: "Lv. 41 - 55",
        hazard: "Lantai Es Licin (Momentum Inersia)",
        hp_mult: 4.8,
        dmg_mult: 3.6,
        spd_mult: 1.45,
        tier_mult: 2.4,
        spawn: [608, 1120],
        bgm: "bgm_boss",
      },
      "stage5_throne.tmx": {
        stage_num: 5,
        name: "Final Boss Domain: Ruang Takhta Obsidian",
        rec_level: "Lv. 56 - 70",
        hazard: "Laser Tengkorak & Duel 2 Fase",
        hp_mult: 5.5,
        dmg_mult: 3.8,
        spd_mult: 1.55,
        tier_mult: 3.0,
        spawn: [608, 1100],
        bgm: "bgm_throne",
      },
      "dungeon1.tmx": {
        stage_num: 1,
        name: "Ruang Bawah Tanah 1 (Klasik)",
        rec_level: "Lv. 3+",
        hazard: "Lorong Labirin",
        hp_mult: 1.1,
        dmg_mult: 1.0,
        spd_mult: 1.0,
        tier_mult: 1.2,
        spawn: [128, 288],
        bgm: "bgm_dungeon",
      },
      "dungeon2.tmx": {
        stage_num: 2,
        name: "Ruang Bawah Tanah 2 (Klasik)",
        rec_level: "Lv. 8+",
        hazard: "Aula Penjaga Terkutuk",
        hp_mult: 2.2,
        dmg_mult: 1.85,
        spd_mult: 1.2,
        tier_mult: 1.6,
        spawn: [1120, 288],
        bgm: "bgm_boss",
      },
    },

    computeLevelStats(level) {
      const lv = Math.max(1, Math.min(70, level | 0));
      const anchors = Config.LEVEL_ANCHORS;
      for (let i = 0; i < anchors.length - 1; i++) {
        const a0 = anchors[i];
        const a1 = anchors[i + 1];
        if (lv >= a0[0] && lv <= a1[0]) {
          const t = (lv - a0[0]) / Math.max(1, a1[0] - a0[0]);
          const lerp = (u, v) => Math.round(u + (v - u) * t);
          return {
            max_hp: lerp(a0[1], a1[1]),
            max_stamina: lerp(a0[2], a1[2]),
            base_atk: lerp(a0[3], a1[3]),
            base_def: lerp(a0[4], a1[4]),
            exp_to_next: lerp(a0[5], a1[5]),
          };
        }
      }
      const last = anchors[anchors.length - 1];
      return {
        max_hp: last[1],
        max_stamina: last[2],
        base_atk: last[3],
        base_def: last[4],
        exp_to_next: last[5],
      };
    },

    computeLogicalSize(winW, winH) {
      const ww = Math.max(320, Math.round(winW));
      const wh = Math.max(240, Math.round(winH));
      let viewH = Math.max(Config.MIN_VIEWPORT_HEIGHT, Math.min(Config.DEFAULT_HEIGHT, wh));
      let viewW = Math.round(viewH * (ww / Math.max(1, wh)));
      if (viewW < Config.MIN_VIEWPORT_WIDTH) {
        viewW = Config.MIN_VIEWPORT_WIDTH;
        viewH = Math.round(viewW * (wh / Math.max(1, ww)));
      }
      return [viewW, viewH];
    },

    computeClampedCamera(targetCx, targetCy, mapW, mapH, viewW, viewH) {
      const camX = mapW <= viewW ? -(viewW - mapW) / 2.0 : Math.max(0.0, Math.min(mapW - viewW, targetCx));
      const camY = mapH <= viewH ? -(viewH - mapH) / 2.0 : Math.max(0.0, Math.min(mapH - viewH, targetCy));
      return [camX, camY];
    },

    rectsOverlap(ax, ay, aw, ah, bx, by, bw, bh) {
      return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;
    },

    pointInRect(px, py, r) {
      return r && px >= r.x && px <= r.x + r.w && py >= r.y && py <= r.y + r.h;
    },

    drawRoundedRect(ctx, x, y, w, h, radius, fillStyle, strokeStyle, lineWidth) {
      const r = Math.min(radius || 0, w / 2, h / 2);
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
      if (fillStyle) {
        ctx.fillStyle = fillStyle;
        ctx.fill();
      }
      if (strokeStyle) {
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = lineWidth || 1;
        ctx.stroke();
      }
    },

    font(size, opts) {
      const weight = opts && opts.bold ? "700 " : "";
      const style = opts && opts.italic ? "italic " : "";
      return `${style}${weight}${size}px "Segoe UI", Arial, sans-serif`;
    },

    drawOutlinedText(ctx, text, x, y, color, outlineColor, align) {
      ctx.save();
      ctx.textBaseline = "top";
      ctx.textAlign = align || "left";
      ctx.fillStyle = outlineColor || "rgba(0,0,0,0.85)";
      ctx.fillText(text, x - 1, y);
      ctx.fillText(text, x + 1, y);
      ctx.fillText(text, x, y - 1);
      ctx.fillText(text, x, y + 1);
      ctx.fillStyle = color || "#f5f5f7";
      ctx.fillText(text, x, y);
      ctx.restore();
    },

    rgbStr(arr, alpha) {
      if (!arr) return "#ffffff";
      if (alpha !== undefined) {
        return `rgba(${arr[0]}, ${arr[1]}, ${arr[2]}, ${alpha})`;
      }
      return `rgb(${arr[0]}, ${arr[1]}, ${arr[2]})`;
    },
  };

  global.OakhavenConfig = Config;
})(window);
