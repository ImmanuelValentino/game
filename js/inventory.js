(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;

  const RARITY_COLORS = {
    common: "#b4b4c3",
    uncommon: "#50dc78",
    rare: "#5096ff",
    epic: "#be64ff",
    legendary: "#ffaa28",
  };

  const ITEM_DATABASE = {
    hp_potion: {
      id: "hp_potion",
      name: "Ramuan Pemulih (Health Potion)",
      desc: "Memulihkan 80 HP secara instan. Masuk ke Hotbar [1-4].",
      category: "consumable",
      rarity: "uncommon",
      icon_file: "potion_hp.png",
      max_stack: 99,
      sell_gold: 0,
      sell_skl: 0,
    },
    stamina_tonic: {
      id: "stamina_tonic",
      name: "Tonik Stamina (Stamina Tonic)",
      desc: "Memulihkan 60 Stamina secara instan. Masuk ke Hotbar [1-4].",
      category: "consumable",
      rarity: "common",
      icon_file: "potion_stamina.png",
      max_stack: 99,
      sell_gold: 0,
      sell_skl: 0,
    },
    attack_boost_potion: {
      id: "attack_boost_potion",
      name: "Ramuan Amarah (ATK Boost 15s)",
      desc: "Meningkatkan Attack Power +50% selama 15 detik. Berguna di Dungeon lanjut!",
      category: "consumable",
      rarity: "rare",
      icon_file: "potion_atk.png",
      max_stack: 99,
      sell_gold: 0,
      sell_skl: 0,
    },
    defense_potion: {
      id: "defense_potion",
      name: "Ramuan Zirah Baja (DEF Boost 20s)",
      desc: "Menambah +18 DEF selama 20 detik untuk menahan serangan berat Dungeon.",
      category: "consumable",
      rarity: "rare",
      icon_file: "potion_def.png",
      max_stack: 99,
      sell_gold: 0,
      sell_skl: 0,
    },
    crit_elixir: {
      id: "crit_elixir",
      name: "Eliksir Fokus Kritis (Crit+ 20s)",
      desc: "Meningkatkan peluang Critical Strike +35% selama 20 detik.",
      category: "consumable",
      rarity: "epic",
      icon_file: "potion_crit.png",
      max_stack: 99,
      sell_gold: 0,
      sell_skl: 0,
    },
    ancestral_blade: {
      id: "ancestral_blade",
      name: "Pedang Leluhur",
      desc: "Pedang tua peninggalan klan Oakhaven (ATK +65). Klik untuk memakai.",
      category: "weapon",
      rarity: "rare",
      icon_file: "Katana.png",
      max_stack: 1,
      sell_gold: 0,
      sell_skl: 0,
    },
    redemption_blade_1: {
      id: "redemption_blade_1",
      name: "Bilah Penebusan +1",
      desc: "Pedang hitam tempaan Vektor (ATK +115). Klik untuk memakai.",
      category: "weapon",
      rarity: "rare",
      icon_file: "MagicWeapon.png",
      max_stack: 1,
      sell_gold: 0,
      sell_skl: 0,
    },
    redemption_blade_2: {
      id: "redemption_blade_2",
      name: "Bilah Penebusan +2",
      desc: "Pedang bercahaya perak penumpas Karak (ATK +185). Klik untuk memakai.",
      category: "weapon",
      rarity: "epic",
      icon_file: "MagicWeapon.png",
      max_stack: 1,
      sell_gold: 0,
      sell_skl: 0,
    },
    redemption_blade_3: {
      id: "redemption_blade_3",
      name: "Bilah Penebusan Suci",
      desc: "Wujud puncak Bilah Penebusan pemutus kutukan (ATK +280). Klik untuk memakai.",
      category: "weapon",
      rarity: "legendary",
      icon_file: "MagicWeapon.png",
      max_stack: 1,
      sell_gold: 0,
      sell_skl: 0,
    },
    bloodthirst_blade: {
      id: "bloodthirst_blade",
      name: "Pedang Haus Darah",
      desc: "Artefak terlarang Gael (ATK +320, Drop x1.5). Memakainya mengunci jalan gelap.",
      category: "weapon",
      rarity: "legendary",
      icon_file: "Axe.png",
      max_stack: 1,
      sell_gold: 0,
      sell_skl: 0,
    },
    bone_shard: {
      id: "bone_shard",
      name: "Pecahan Tulang",
      desc: "Material Common (8G, +1 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "common",
      icon_file: "BookRock.png",
      max_stack: 99,
      sell_gold: 8,
      sell_skl: 1,
    },
    rust_iron: {
      id: "rust_iron",
      name: "Baja Karat",
      desc: "Material Common (10G, +1 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "common",
      icon_file: "Hammer.png",
      max_stack: 99,
      sell_gold: 10,
      sell_skl: 1,
    },
    spore_intact: {
      id: "spore_intact",
      name: "Spora Utuh",
      desc: "Material Uncommon (18G, +2 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "uncommon",
      icon_file: "OrbPlant.png",
      max_stack: 99,
      sell_gold: 18,
      sell_skl: 2,
    },
    ice_core: {
      id: "ice_core",
      name: "Inti Es",
      desc: "Material Uncommon (22G, +2 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "uncommon",
      icon_file: "BookIce.png",
      max_stack: 99,
      sell_gold: 22,
      sell_skl: 2,
    },
    karak_blood: {
      id: "karak_blood",
      name: "Darah Karak",
      desc: "Material Rare (40G, +4 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "rare",
      icon_file: "BookFire.png",
      max_stack: 99,
      sell_gold: 40,
      sell_skl: 4,
    },
    pure_steel: {
      id: "pure_steel",
      name: "Baja Murni",
      desc: "Material Rare (45G, +4 SKL). Serahkan ke Vektor di Hub.",
      category: "material",
      rarity: "rare",
      icon_file: "AttackUpgrade.png",
      max_stack: 99,
      sell_gold: 45,
      sell_skl: 4,
    },
    general_core: {
      id: "general_core",
      name: "Inti Jenderal",
      desc: "Material Epic Bos (90G, +8 SKL). Bukti tumbangnya Jenderal bioma.",
      category: "material",
      rarity: "epic",
      icon_file: "OrbFire.png",
      max_stack: 99,
      sell_gold: 90,
      sell_skl: 8,
    },
    broken_crown: {
      id: "broken_crown",
      name: "Mahkota Pecah",
      desc: "Relik Epic/Boss langka (160G, +12 SKL). Serahkan ke Vektor.",
      category: "material",
      rarity: "legendary",
      icon_file: "OrbDarkness.png",
      max_stack: 99,
      sell_gold: 160,
      sell_skl: 12,
    },
    monster_ash: {
      id: "monster_ash",
      name: "Abu Monster",
      desc: "Sisa abu jiwa monster Karak.",
      category: "material",
      rarity: "common",
      icon_file: "BookDarkness.png",
      max_stack: 99,
      sell_gold: 3,
      sell_skl: 0,
    },
    karak_core: {
      id: "karak_core",
      name: "Inti Monster Karak",
      desc: "Bahan langka untuk meracik ramuan tingkat tinggi.",
      category: "material",
      rarity: "uncommon",
      icon_file: "BookDeath.png",
      max_stack: 99,
      sell_gold: 20,
      sell_skl: 2,
    },
  };

  class Inventory {
    constructor(maxSlots) {
      this.maxSlots = maxSlots || 16;
      this.slots = new Array(this.maxSlots).fill(null);
      this.isOpen = false;
      this.hotbarIds = ["hp_potion", "stamina_tonic", "attack_boost_potion", "defense_potion"];

      this.addItem("ancestral_blade", 1);
      this.addItem("hp_potion", 2);
      this.addItem("stamina_tonic", 1);
    }

    toggle() {
      this.isOpen = !this.isOpen;
      AudioMgr.playSound(this.isOpen ? "accept" : "cancel");
    }

    bindToHotbar(itemId) {
      const item = ITEM_DATABASE[itemId];
      if (!item || item.category !== "consumable") return;
      if (this.hotbarIds.includes(itemId)) return;
      for (let i = 0; i < this.hotbarIds.length; i++) {
        if (!this.hotbarIds[i] || this.getCount(this.hotbarIds[i]) <= 0) {
          this.hotbarIds[i] = itemId;
          return;
        }
      }
      this.hotbarIds[3] = itemId;
    }

    getHotbarEntries() {
      const out = [];
      for (let idx = 0; idx < 4; idx++) {
        const iid = this.hotbarIds[idx];
        const count = iid ? this.getCount(iid) : 0;
        const item = iid ? ITEM_DATABASE[iid] : null;
        out.push({ key: String(idx + 1), itemId: iid, item, count });
      }
      return out;
    }

    addItem(itemId, count) {
      const amount = count || 1;
      const def = ITEM_DATABASE[itemId];
      if (!def) return false;
      let rem = amount;

      for (let i = 0; i < this.maxSlots; i++) {
        const s = this.slots[i];
        if (s && s.id === itemId && s.count < def.max_stack) {
          const take = Math.min(rem, def.max_stack - s.count);
          s.count += take;
          rem -= take;
          if (rem <= 0) break;
        }
      }
      while (rem > 0) {
        const emptyIdx = this.slots.findIndex((s) => s === null);
        if (emptyIdx === -1) break;
        const take = Math.min(rem, def.max_stack);
        this.slots[emptyIdx] = { id: itemId, count: take };
        rem -= take;
      }

      if (def.category === "consumable") {
        this.bindToHotbar(itemId);
      }
      return rem < amount;
    }

    consumeItem(itemId, count) {
      const need = count || 1;
      if (this.getCount(itemId) < need) return false;
      let rem = need;
      for (let i = 0; i < this.maxSlots; i++) {
        const s = this.slots[i];
        if (s && s.id === itemId) {
          const drop = Math.min(rem, s.count);
          s.count -= drop;
          rem -= drop;
          if (s.count <= 0) this.slots[i] = null;
          if (rem <= 0) return true;
        }
      }
      return true;
    }

    getCount(itemId) {
      let total = 0;
      for (let i = 0; i < this.maxSlots; i++) {
        if (this.slots[i] && this.slots[i].id === itemId) total += this.slots[i].count;
      }
      return total;
    }

    getMaterialSummary() {
      let count = 0;
      let gold = 0;
      let skl = 0;
      for (let i = 0; i < this.maxSlots; i++) {
        const s = this.slots[i];
        if (!s) continue;
        const item = ITEM_DATABASE[s.id];
        if (item && item.category === "material") {
          count += s.count;
          gold += item.sell_gold * s.count;
          skl += item.sell_skl * s.count;
        }
      }
      return [count, gold, skl];
    }

    sellAllMaterials(player) {
      const [count, gold, skl] = this.getMaterialSummary();
      if (count <= 0) return [0, 0, 0];
      for (let i = 0; i < this.maxSlots; i++) {
        const s = this.slots[i];
        if (!s) continue;
        const item = ITEM_DATABASE[s.id];
        if (item && item.category === "material") {
          this.slots[i] = null;
        }
      }
      player.gold += gold;
      player.skill_points += skl;
      return [count, gold, skl];
    }

    penalizeOnDeath() {
      let lost = 0;
      for (let i = 0; i < this.maxSlots; i++) {
        const s = this.slots[i];
        if (!s) continue;
        const item = ITEM_DATABASE[s.id];
        if (item && item.category === "material") {
          const drop = Math.max(1, Math.floor(s.count / 2));
          s.count -= drop;
          lost += drop;
          if (s.count <= 0) this.slots[i] = null;
        }
      }
      return lost;
    }

    useSlot(slotIdx, player, combatMgr) {
      if (slotIdx < 0 || slotIdx >= this.maxSlots) return false;
      const slot = this.slots[slotIdx];
      if (!slot) return false;
      const itemId = slot.id;
      const item = ITEM_DATABASE[itemId];
      if (!item) return false;

      if (item.category === "weapon") {
        player.equipWeapon(itemId);
        AudioMgr.playSound("powerup");
        if (combatMgr) {
          combatMgr.addFloatingText(player.x + 24, player.y - 20, `Equip: ${item.name}`, C.COLOR_GOLD, 14, true);
        }
        return true;
      }

      if (itemId === "hp_potion") {
        if (player.hp >= player.max_hp) {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 20, "HP Sudah Penuh!", C.COLOR_TEXT_ACCENT, 14);
          return false;
        }
        this.consumeItem(itemId, 1);
        const healed = player.heal(C.HP_POTION_HEAL);
        if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 20, `+${healed} HP`, "#50e678", 16, true);
        return true;
      }

      if (itemId === "stamina_tonic") {
        this.consumeItem(itemId, 1);
        player.restoreStamina(C.STAMINA_TONIC_RESTORE);
        AudioMgr.playSound("powerup");
        if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 20, `+${C.STAMINA_TONIC_RESTORE} Stamina`, C.COLOR_STAMINA, 16, true);
        return true;
      }

      if (itemId === "attack_boost_potion") {
        this.consumeItem(itemId, 1);
        player.applyAtkBoost(C.ATTACK_BOOST_MULT, C.ATTACK_BOOST_DURATION);
        AudioMgr.playSound("powerup");
        if (combatMgr) {
          combatMgr.addFloatingText(player.x + 24, player.y - 24, `ATK +50% (${Math.floor(C.ATTACK_BOOST_DURATION)}d)!`, "#ff8c50", 16, true);
        }
        return true;
      }

      if (itemId === "defense_potion") {
        this.consumeItem(itemId, 1);
        player.applyDefBoost(C.DEFENSE_BOOST_FLAT, C.DEFENSE_BOOST_DURATION);
        AudioMgr.playSound("powerup");
        if (combatMgr) {
          combatMgr.addFloatingText(player.x + 24, player.y - 24, `DEF +${C.DEFENSE_BOOST_FLAT} (${Math.floor(C.DEFENSE_BOOST_DURATION)}d)!`, "#78b4ff", 16, true);
        }
        return true;
      }

      if (itemId === "crit_elixir") {
        this.consumeItem(itemId, 1);
        player.applyCritBoost(C.CRIT_BOOST_FLAT, C.CRIT_BOOST_DURATION);
        AudioMgr.playSound("powerup");
        if (combatMgr) {
          combatMgr.addFloatingText(player.x + 24, player.y - 24, `CRIT +35% (${Math.floor(C.CRIT_BOOST_DURATION)}d)!`, "#ffe66e", 16, true);
        }
        return true;
      }

      return false;
    }

    useItemById(itemId, player, combatMgr) {
      for (let i = 0; i < this.maxSlots; i++) {
        if (this.slots[i] && this.slots[i].id === itemId) {
          return this.useSlot(i, player, combatMgr);
        }
      }
      AudioMgr.playSound("cancel");
      const name = ITEM_DATABASE[itemId] ? ITEM_DATABASE[itemId].name : itemId;
      if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 20, `${name} Habis!`, "#f05050", 14);
      return false;
    }

    useHotbarSlot(hotbarIdx, player, combatMgr) {
      if (hotbarIdx < 0 || hotbarIdx >= 4) return false;
      const itemId = this.hotbarIds[hotbarIdx];
      if (!itemId) {
        AudioMgr.playSound("cancel");
        return false;
      }
      return this.useItemById(itemId, player, combatMgr);
    }

    _getLayout(viewW, viewH) {
      const cols = 4;
      const rows = Math.floor(this.maxSlots / cols);
      const slotSize = 56;
      const spacing = 10;
      const padding = 24;
      const headerH = 44;
      const footerH = 54;
      const panelW = padding * 2 + cols * slotSize + (cols - 1) * spacing;
      const panelH = headerH + rows * slotSize + (rows - 1) * spacing + footerH + padding;
      const panelX = Math.floor((viewW - panelW) / 2);
      const panelY = Math.floor((viewH - panelH) / 2);
      const closeRect = { x: panelX + panelW - 36, y: panelY + 12, w: 24, h: 24 };
      const slotsStartX = panelX + padding;
      const slotsStartY = panelY + headerH;
      return { cols, rows, slotSize, spacing, panelW, panelH, panelX, panelY, closeRect, slotsStartX, slotsStartY };
    }

    handleClick(lx, ly, player, combatMgr, viewW, viewH) {
      if (!this.isOpen) return false;
      const L = this._getLayout(viewW, viewH);
      if (C.pointInRect(lx, ly, L.closeRect)) {
        this.toggle();
        return true;
      }
      if (!C.pointInRect(lx, ly, { x: L.panelX, y: L.panelY, w: L.panelW, h: L.panelH })) {
        this.toggle();
        return true;
      }
      for (let idx = 0; idx < this.maxSlots; idx++) {
        const col = idx % L.cols;
        const row = Math.floor(idx / L.cols);
        const sx = L.slotsStartX + col * (L.slotSize + L.spacing);
        const sy = L.slotsStartY + row * (L.slotSize + L.spacing);
        if (C.pointInRect(lx, ly, { x: sx, y: sy, w: L.slotSize, h: L.slotSize })) {
          this.useSlot(idx, player, combatMgr);
          return true;
        }
      }
      return true;
    }

    draw(ctx, viewW, viewH, mx, my, player) {
      if (!this.isOpen) return;
      const L = this._getLayout(viewW, viewH);

      ctx.fillStyle = "rgba(0, 0, 0, 0.52)";
      ctx.fillRect(0, 0, viewW, viewH);

      C.drawRoundedRect(ctx, L.panelX, L.panelY, L.panelW, L.panelH, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, L.panelX + 4, L.panelY + 4, L.panelW - 8, L.panelH - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textBaseline = "top";
      ctx.textAlign = "left";
      ctx.fillText("TAS PENYINTAS (BACKPACK)", L.panelX + 20, L.panelY + 13);

      ctx.font = C.font(15, { bold: true });
      ctx.fillStyle = "#dc5050";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X", L.closeRect.x + L.closeRect.w / 2, L.closeRect.y + L.closeRect.h / 2);

      let hoveredSlot = null;
      let hx = 0;
      let hy = 0;

      for (let idx = 0; idx < this.maxSlots; idx++) {
        const col = idx % L.cols;
        const row = Math.floor(idx / L.cols);
        const sx = L.slotsStartX + col * (L.slotSize + L.spacing);
        const sy = L.slotsStartY + row * (L.slotSize + L.spacing);
        const slot = this.slots[idx];
        const hover = C.pointInRect(mx, my, { x: sx, y: sy, w: L.slotSize, h: L.slotSize });

        let borderCol = "#414658";
        let bgCol = hover ? "#2d3244" : "#1c1e28";
        if (slot && ITEM_DATABASE[slot.id]) {
          borderCol = RARITY_COLORS[ITEM_DATABASE[slot.id].rarity] || C.COLOR_PANEL_BORDER_LIGHT;
        }
        if (hover) {
          borderCol = C.COLOR_GOLD;
          hoveredSlot = slot;
          hx = sx;
          hy = sy;
        }

        C.drawRoundedRect(ctx, sx, sy, L.slotSize, L.slotSize, 8, bgCol, borderCol, 2);

        if (slot && ITEM_DATABASE[slot.id]) {
          const item = ITEM_DATABASE[slot.id];
          const iconImg = Assets.itemIcons[item.icon_file];
          if (iconImg) {
            ctx.drawImage(iconImg, sx + 10, sy + 10, L.slotSize - 20, L.slotSize - 20);
          }
          if (item.category === "weapon" && player && player.weapon_id === slot.id) {
            ctx.font = C.font(10, { bold: true });
            ctx.fillStyle = C.COLOR_GOLD;
            ctx.textAlign = "left";
            ctx.textBaseline = "top";
            ctx.fillText("EQ", sx + 4, sy + 3);
          }
          if (slot.count > 1) {
            C.drawOutlinedText(ctx, String(slot.count), sx + L.slotSize - 5, sy + L.slotSize - 16, C.COLOR_WHITE, "#000000", "right");
          }
        }
      }

      const fy = L.panelY + L.panelH - 52;
      ctx.textBaseline = "top";
      ctx.font = C.font(12, { bold: true });
      ctx.textAlign = "left";
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText(`Gold: ${player.gold}`, L.panelX + 24, fy);
      ctx.fillStyle = C.COLOR_ASH;
      ctx.fillText(`Ash: ${player.monster_ash}`, L.panelX + 116, fy);
      ctx.fillStyle = C.COLOR_TEXT_ACCENT;
      ctx.fillText(`SKL: ${player.skill_points}`, L.panelX + 206, fy);

      ctx.font = C.font(10);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.textAlign = "center";
      ctx.fillText("[Klik Slot]: Pakai / Equip   |   [B]: Tutup", L.panelX + L.panelW / 2, fy + 22);

      if (hoveredSlot && ITEM_DATABASE[hoveredSlot.id]) {
        const item = ITEM_DATABASE[hoveredSlot.id];
        ctx.font = C.font(12, { bold: true });
        const nw = ctx.measureText(item.name).width;
        ctx.font = C.font(10);
        const dw = ctx.measureText(item.desc).width;
        const tw = Math.max(nw, dw) + 22;
        const th = 52;
        let tx = Math.min(viewW - tw - 12, hx + L.slotSize + 8);
        let ty = Math.min(viewH - th - 12, hy);
        C.drawRoundedRect(ctx, tx, ty, tw, th, 7, "rgba(14,16,24,0.96)", RARITY_COLORS[item.rarity] || C.COLOR_GOLD, 1);
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.font = C.font(12, { bold: true });
        ctx.fillStyle = RARITY_COLORS[item.rarity] || C.COLOR_GOLD;
        ctx.fillText(item.name, tx + 10, ty + 8);
        ctx.font = C.font(10);
        ctx.fillStyle = C.COLOR_TEXT;
        ctx.fillText(item.desc, tx + 10, ty + 28);
      }
    }
  }

  global.OakhavenInventory = {
    RARITY_COLORS,
    ITEM_DATABASE,
    Inventory,
  };
})(window);
