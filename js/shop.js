(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const AudioMgr = global.OakhavenAudio;
  const { ITEM_DATABASE } = global.OakhavenInventory;

  class ShopManager {
    constructor() {
      this.isMerchantOpen = false;
      this.isBrogOpen = false;
      this.isVektorOpen = false;

      this.merchantGoods = [
        { id: "hp_potion", name: "Ramuan Pemulih HP", desc: "Pulihkan 80 HP instan (Hotbar).", cost: 20, type: "item", count: 1 },
        { id: "stamina_tonic", name: "Tonik Stamina", desc: "Pulihkan 60 STA instan (Hotbar).", cost: 15, type: "item", count: 1 },
        { id: "attack_boost_potion", name: "Ramuan Amarah (ATK+)", desc: "+50% Attack Power selama 15 detik.", cost: 35, type: "item", count: 1 },
        { id: "defense_potion", name: "Ramuan Zirah (DEF+)", desc: "+18 DEF selama 20 detik.", cost: 30, type: "item", count: 1 },
        { id: "crit_elixir", name: "Eliksir Fokus (Crit+)", desc: "+35% Crit Chance selama 20 detik.", cost: 40, type: "item", count: 1 },
        { id: "armor_up", name: "Pelindung Zirah (+4 DEF)", desc: "Kurangi damage musuh permanen.", cost: 70, type: "upgrade_armor", val: 4 },
        { id: "boots_up", name: "Sepatu Bayangan (+26 SPD)", desc: "Kecepatan gerak & dodge lincah.", cost: 65, type: "upgrade_speed", val: 26.0 },
        { id: "redemption_blade_1", name: "Bilah Penebusan +1", desc: "ATK +115, +10 Karma Good Ending.", cost: 120, type: "weapon", karma: 10 },
        { id: "bloodthirst_blade", name: "Pedang Haus Darah", desc: "ATK +320, Drop x1.5, -50 Karma.", cost: 220, type: "weapon", karma: -50 },
      ];
    }

    isAnyOpen() {
      return this.isMerchantOpen || this.isBrogOpen || this.isVektorOpen;
    }

    openMerchant() {
      this.isMerchantOpen = true;
      this.isBrogOpen = false;
      this.isVektorOpen = false;
      AudioMgr.playSound("accept");
    }

    openGael() {
      this.openMerchant();
    }

    openBrog() {
      this.isBrogOpen = true;
      this.isMerchantOpen = false;
      this.isVektorOpen = false;
      AudioMgr.playSound("accept");
    }

    openVektor() {
      this.isVektorOpen = true;
      this.isMerchantOpen = false;
      this.isBrogOpen = false;
      AudioMgr.playSound("accept");
    }

    closeAll() {
      if (this.isAnyOpen()) AudioMgr.playSound("cancel");
      this.isMerchantOpen = false;
      this.isBrogOpen = false;
      this.isVektorOpen = false;
    }

    _getMerchantLayout(viewW, viewH) {
      const panelW = 790;
      const panelH = 490;
      const panelX = Math.floor((viewW - panelW) / 2);
      const panelY = Math.floor((viewH - panelH) / 2);
      const closeRect = { x: panelX + panelW - 40, y: panelY + 14, w: 26, h: 26 };
      const colW = 362;
      const rowH = 58;
      const rows = [];
      for (let i = 0; i < this.merchantGoods.length; i++) {
        const col = i % 2;
        const row = Math.floor(i / 2);
        const rx = panelX + 22 + col * (colW + 20);
        const ry = panelY + 80 + row * (rowH + 10);
        const rRect = { x: rx, y: ry, w: colW, h: rowH };
        const buyBtn = { x: rx + colW - 84, y: ry + 12, w: 74, h: 34 };
        rows.push({ item: this.merchantGoods[i], rRect, buyBtn });
      }
      return { panelX, panelY, panelW, panelH, closeRect, rows };
    }

    _getBrogLayout(viewW, viewH) {
      const panelW = 520;
      const panelH = 300;
      const panelX = Math.floor((viewW - panelW) / 2);
      const panelY = Math.floor((viewH - panelH) / 2);
      const closeRect = { x: panelX + panelW - 40, y: panelY + 14, w: 26, h: 26 };
      const btn1 = { x: panelX + 40, y: panelY + 130, w: panelW - 80, h: 48 };
      const btn2 = { x: panelX + 40, y: panelY + 194, w: panelW - 80, h: 48 };
      return { panelX, panelY, panelW, panelH, closeRect, btn1, btn2 };
    }

    _getVektorLayout(viewW, viewH) {
      const panelW = 640;
      const panelH = 450;
      const panelX = Math.floor((viewW - panelW) / 2);
      const panelY = Math.floor((viewH - panelH) / 2);
      const closeRect = { x: panelX + panelW - 40, y: panelY + 14, w: 26, h: 26 };
      const sellBtn = { x: panelX + 24, y: panelY + 102, w: panelW - 48, h: 46 };
      const skillBtns = [];
      for (let i = 0; i < 4; i++) {
        skillBtns.push({ x: panelX + 24, y: panelY + 168 + i * 60, w: panelW - 48, h: 50 });
      }
      return { panelX, panelY, panelW, panelH, closeRect, sellBtn, skillBtns };
    }

    handleClick(lx, ly, player, inventory, combatMgr, questMgr, viewW, viewH) {
      if (this.isMerchantOpen) return this._handleMerchantClick(lx, ly, player, inventory, combatMgr, questMgr, viewW, viewH);
      if (this.isBrogOpen) return this._handleBrogClick(lx, ly, player, combatMgr, questMgr, viewW, viewH);
      if (this.isVektorOpen) return this._handleVektorClick(lx, ly, player, inventory, combatMgr, questMgr, viewW, viewH);
      return false;
    }

    _handleMerchantClick(lx, ly, player, inventory, combatMgr, questMgr, viewW, viewH) {
      const L = this._getMerchantLayout(viewW, viewH);
      if (C.pointInRect(lx, ly, L.closeRect) || !C.pointInRect(lx, ly, { x: L.panelX, y: L.panelY, w: L.panelW, h: L.panelH })) {
        this.closeAll();
        return true;
      }

      for (const { item, buyBtn } of L.rows) {
        if (!C.pointInRect(lx, ly, buyBtn)) continue;
        if (player.gold < item.cost) {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "Emas Tidak Cukup!", "#f05050", 16);
          return true;
        }
        player.gold -= item.cost;
        if (item.type === "item") {
          inventory.addItem(item.id, item.count);
          AudioMgr.playSound("coin");
          if (combatMgr) {
            const nm = ITEM_DATABASE[item.id] ? ITEM_DATABASE[item.id].name : item.name;
            combatMgr.addFloatingText(player.x + 24, player.y - 25, `+1 ${nm} [Hotbar]`, "#82f5c3", 15, true);
          }
        } else if (item.type === "upgrade_armor") {
          player.armor += item.val;
          AudioMgr.playSound("powerup");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, `+${item.val} DEF Permanen!`, C.COLOR_TEXT_ACCENT, 16, true);
        } else if (item.type === "upgrade_speed") {
          player.speed_bonus += item.val;
          AudioMgr.playSound("powerup");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, `+${Math.round(item.val)} SPD Permanen!`, C.COLOR_TEXT_ACCENT, 16, true);
        } else if (item.type === "weapon") {
          if (inventory.getCount(item.id) === 0) inventory.addItem(item.id, 1);
          player.equipWeapon(item.id);
          player.karma += item.karma || 0;
          AudioMgr.playSound("levelup");
          if (combatMgr) {
            const col = (item.karma || 0) < 0 ? "#ff6e6e" : C.COLOR_GOLD;
            combatMgr.addFloatingText(player.x + 24, player.y - 25, `Equip: ${item.name}!`, col, 16, true);
          }
        }
        if (questMgr) questMgr.advanceProgress("q3_supplies", 1, player, combatMgr);
        return true;
      }
      return true;
    }

    _handleBrogClick(lx, ly, player, combatMgr, questMgr, viewW, viewH) {
      const L = this._getBrogLayout(viewW, viewH);
      if (C.pointInRect(lx, ly, L.closeRect) || !C.pointInRect(lx, ly, { x: L.panelX, y: L.panelY, w: L.panelW, h: L.panelH })) {
        this.closeAll();
        return true;
      }
      if (C.pointInRect(lx, ly, L.btn1)) {
        if (player.monster_ash >= 10) {
          player.monster_ash -= 10;
          player.gold += 25;
          AudioMgr.playSound("coin");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "+25 Gold! (-10 Ash)", C.COLOR_GOLD, 16);
          if (questMgr) questMgr.advanceProgress("q3_supplies", 1, player, combatMgr);
        } else {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "Abu Monster Kurang! (Butuh 10)", "#f05050", 15);
        }
        return true;
      }
      if (C.pointInRect(lx, ly, L.btn2)) {
        if (player.monster_ash > 0) {
          const goldGained = Math.max(1, Math.floor(player.monster_ash * 2.5));
          const used = player.monster_ash;
          player.monster_ash = 0;
          player.gold += goldGained;
          AudioMgr.playSound("coin");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, `+${goldGained} Gold! (${used} Ash)`, C.COLOR_GOLD, 16);
          if (questMgr) questMgr.advanceProgress("q3_supplies", 1, player, combatMgr);
        } else {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "Tidak ada Abu Monster!", "#f05050", 15);
        }
        return true;
      }
      return true;
    }

    _handleVektorClick(lx, ly, player, inventory, combatMgr, questMgr, viewW, viewH) {
      const L = this._getVektorLayout(viewW, viewH);
      if (C.pointInRect(lx, ly, L.closeRect) || !C.pointInRect(lx, ly, { x: L.panelX, y: L.panelY, w: L.panelW, h: L.panelH })) {
        this.closeAll();
        return true;
      }
      if (C.pointInRect(lx, ly, L.sellBtn)) {
        const [cnt, goldGained, sklGained] = inventory.sellAllMaterials(player);
        if (cnt > 0) {
          AudioMgr.playSound("coin");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, `+${goldGained}G & +${sklGained} SKL!`, C.COLOR_GOLD, 17, true);
          if (questMgr) questMgr.advanceProgress("q3_supplies", 1, player, combatMgr);
        } else {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "Tidak ada material di tas!", "#f08c5a", 15);
        }
        return true;
      }

      const actions = [
        ["power", 1, 0, "Kekuatan Tebasan +12 ATK"],
        ["stamina", 1, 0, "Ketahanan +15 Max STA & +2.5 Regen"],
        ["defense", 1, 0, "Baja Pertahanan +25 Max HP & +5 DEF"],
        ["blade", 2, 40, "Tempa Bilah Penebusan (+Karma)"],
      ];
      for (let idx = 0; idx < L.skillBtns.length; idx++) {
        if (!C.pointInRect(lx, ly, L.skillBtns[idx])) continue;
        const [key, sklCost, goldCost, msg] = actions[idx];
        if (player.skill_points < sklCost || player.gold < goldCost) {
          AudioMgr.playSound("cancel");
          if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, `Butuh ${sklCost} SKL & ${goldCost}G!`, "#f05050", 15);
          return true;
        }
        if (key === "blade") {
          const nextMap = {
            ancestral_blade: "redemption_blade_1",
            redemption_blade_1: "redemption_blade_2",
            redemption_blade_2: "redemption_blade_3",
          };
          let nextWid = nextMap[player.weapon_id];
          if (!nextWid) {
            if (player.weapon_id === "redemption_blade_3") {
              AudioMgr.playSound("cancel");
              if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, "Bilah Penebusan Sudah Suci!", C.COLOR_GOLD, 16);
              return true;
            }
            nextWid = "redemption_blade_1";
          }
          player.skill_points -= sklCost;
          player.gold -= goldCost;
          player.skill_levels.blade += 1;
          player.karma += 20;
          if (inventory.getCount(nextWid) === 0) inventory.addItem(nextWid, 1);
          player.equipWeapon(nextWid);
          AudioMgr.playSound("levelup");
        } else {
          player.skill_points -= sklCost;
          player.gold -= goldCost;
          player.skill_levels[key] += 1;
          if (key === "stamina") {
            player.max_stamina += 15;
            player.stamina = player.max_stamina;
          } else if (key === "defense") {
            player.max_hp += 25;
            player.hp += 25;
            player.hp_trail = player.hp;
          }
          AudioMgr.playSound("powerup");
        }
        if (combatMgr) combatMgr.addFloatingText(player.x + 24, player.y - 25, msg, C.COLOR_TEXT_ACCENT, 16, true);
        if (questMgr) questMgr.advanceProgress("q3_supplies", 1, player, combatMgr);
        return true;
      }
      return true;
    }

    draw(ctx, viewW, viewH, mx, my, player, inventory) {
      if (this.isMerchantOpen) this._drawMerchantUI(ctx, viewW, viewH, mx, my, player);
      else if (this.isBrogOpen) this._drawBrogUI(ctx, viewW, viewH, mx, my, player);
      else if (this.isVektorOpen) this._drawVektorUI(ctx, viewW, viewH, mx, my, player, inventory);
    }

    _drawMerchantUI(ctx, viewW, viewH, mx, my, player) {
      const L = this._getMerchantLayout(viewW, viewH);
      ctx.fillStyle = "rgba(0, 0, 0, 0.58)";
      ctx.fillRect(0, 0, viewW, viewH);

      C.drawRoundedRect(ctx, L.panelX, L.panelY, L.panelW, L.panelH, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, L.panelX + 4, L.panelY + 4, L.panelW - 8, L.panelH - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(19, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText("GAEL - PEDAGANG SENJATA & ARTEFAK", L.panelX + 24, L.panelY + 18);

      ctx.font = C.font(12, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText('"Senjata yang tepat adalah pembeda hidup dan mati... asal kau sanggup membayarnya."', L.panelX + 24, L.panelY + 46);

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = "#dc5050";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X", L.closeRect.x + L.closeRect.w / 2, L.closeRect.y + L.closeRect.h / 2);

      for (const { item, rRect, buyBtn } of L.rows) {
        const hover = C.pointInRect(mx, my, rRect);
        const isCursed = (item.karma || 0) < 0;
        const bg = isCursed ? "#2c181e" : hover ? "#202230" : "#181a24";
        const border = isCursed ? "#a0323c" : "#32374b";
        C.drawRoundedRect(ctx, rRect.x, rRect.y, rRect.w, rRect.h, 8, bg, border, 1);

        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.font = C.font(12, { bold: true });
        ctx.fillStyle = isCursed ? "#ff6e6e" : C.COLOR_WHITE;
        ctx.fillText(item.name, rRect.x + 10, rRect.y + 8);

        ctx.font = C.font(10);
        ctx.fillStyle = C.COLOR_TEXT_MUTED;
        ctx.fillText(item.desc, rRect.x + 10, rRect.y + 28);

        const canAfford = player.gold >= item.cost;
        const bHover = C.pointInRect(mx, my, buyBtn);
        const btnBg = canAfford ? (bHover ? "#c89628" : "#a0781e") : "#3c3c46";
        C.drawRoundedRect(ctx, buyBtn.x, buyBtn.y, buyBtn.w, buyBtn.h, 6, btnBg, canAfford ? C.COLOR_GOLD : "#5a5a64", 1);

        ctx.font = C.font(12, { bold: true });
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${item.cost} G`, buyBtn.x + buyBtn.w / 2, buyBtn.y + buyBtn.h / 2);
      }

      ctx.textBaseline = "top";
      ctx.font = C.font(14, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textAlign = "left";
      ctx.fillText(`Emas: ${player.gold} Gold | Senjata: ${player.weaponInfo.name}`, L.panelX + 24, L.panelY + L.panelH - 34);

      ctx.font = C.font(11);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.textAlign = "right";
      ctx.fillText("[ESC] / [E] Tutup", L.panelX + L.panelW - 24, L.panelY + L.panelH - 32);
    }

    _drawBrogUI(ctx, viewW, viewH, mx, my, player) {
      const L = this._getBrogLayout(viewW, viewH);
      ctx.fillStyle = "rgba(0, 0, 0, 0.58)";
      ctx.fillRect(0, 0, viewW, viewH);

      C.drawRoundedRect(ctx, L.panelX, L.panelY, L.panelW, L.panelH, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, L.panelX + 4, L.panelY + 4, L.panelW - 8, L.panelH - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(19, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText("MEJA BAR BROG (PENUKARAN ABU)", L.panelX + 24, L.panelY + 18);

      ctx.font = C.font(12, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText('"Bawa abu monster Karak itu ke sini, akan ku bayar dengan koin emas!"', L.panelX + 24, L.panelY + 48);

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = "#dc5050";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X", L.closeRect.x + L.closeRect.w / 2, L.closeRect.y + L.closeRect.h / 2);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(14, { bold: true });
      ctx.fillStyle = C.COLOR_ASH;
      ctx.fillText(`Abu Monster: ${player.monster_ash} Ash`, L.panelX + 40, L.panelY + 90);
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText(`Emas: ${player.gold} Gold`, L.panelX + 260, L.panelY + 90);

      const can10 = player.monster_ash >= 10;
      const b1Hover = C.pointInRect(mx, my, L.btn1);
      C.drawRoundedRect(ctx, L.btn1.x, L.btn1.y, L.btn1.w, L.btn1.h, 8, can10 ? (b1Hover ? "#327841" : "#285a32") : "#32323c", can10 ? "#64b478" : "#50505a", 2);
      ctx.font = C.font(14, { bold: true });
      ctx.fillStyle = can10 ? C.COLOR_WHITE : C.COLOR_TEXT_MUTED;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("Tukar 10 Abu Monster  ->  25 Emas", L.btn1.x + L.btn1.w / 2, L.btn1.y + L.btn1.h / 2);

      const canAll = player.monster_ash > 0;
      const b2Hover = C.pointInRect(mx, my, L.btn2);
      const totalVal = canAll ? Math.max(1, Math.floor(player.monster_ash * 2.5)) : 0;
      C.drawRoundedRect(ctx, L.btn2.x, L.btn2.y, L.btn2.w, L.btn2.h, 8, canAll ? (b2Hover ? "#aa6e23" : "#825519") : "#32323c", canAll ? C.COLOR_GOLD : "#50505a", 2);
      ctx.fillStyle = canAll ? C.COLOR_WHITE : C.COLOR_TEXT_MUTED;
      ctx.fillText(`Tukar SEMUA Abu (${player.monster_ash} Ash)  ->  +${totalVal} Emas`, L.btn2.x + L.btn2.w / 2, L.btn2.y + L.btn2.h / 2);

      ctx.font = C.font(11);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText("[Klik tombol untuk menukar abu / [ESC] atau [E] untuk tutup]", L.panelX + L.panelW / 2, L.panelY + L.panelH - 22);
    }

    _drawVektorUI(ctx, viewW, viewH, mx, my, player, inventory) {
      const L = this._getVektorLayout(viewW, viewH);
      ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
      ctx.fillRect(0, 0, viewW, viewH);

      C.drawRoundedRect(ctx, L.panelX, L.panelY, L.panelW, L.panelH, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, L.panelX + 4, L.panelY + 4, L.panelW - 8, L.panelH - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(19, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText("VEKTOR - BENGKEL SKILL & TEMPA PENEBUSAN", L.panelX + 24, L.panelY + 18);

      ctx.font = C.font(12, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText('"Serahkan sisa monster buruanmu. Kita ubah menjadi teknik tempur & tempaan suci."', L.panelX + 24, L.panelY + 46);

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = "#dc5050";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X", L.closeRect.x + L.closeRect.w / 2, L.closeRect.y + L.closeRect.h / 2);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(13, { bold: true });
      ctx.fillStyle = C.COLOR_TEXT_ACCENT;
      ctx.fillText(`Poin Skill (SKL): ${player.skill_points}  |  Emas: ${player.gold} G  |  Level SKL: ${player.skillLevel}`, L.panelX + 24, L.panelY + 76);

      const [matCnt, matGold, matSkl] = inventory ? inventory.getMaterialSummary() : [0, 0, 0];
      const canSell = matCnt > 0;
      const sHover = C.pointInRect(mx, my, L.sellBtn);
      C.drawRoundedRect(ctx, L.sellBtn.x, L.sellBtn.y, L.sellBtn.w, L.sellBtn.h, 8, canSell ? (sHover ? "#32784b" : "#235537") : "#2d303a", canSell ? "#6ed28c" : "#464b5a", 2);

      ctx.font = C.font(13, { bold: true });
      ctx.fillStyle = canSell ? C.COLOR_WHITE : C.COLOR_TEXT_MUTED;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const sellTxt = canSell
        ? `Serahkan Semua Material (${matCnt} item) -> +${matGold} Gold & +${matSkl} SKL`
        : "Belum Ada Material Monster di Tas (Kalahkan Monster di Stage!)";
      ctx.fillText(sellTxt, L.sellBtn.x + L.sellBtn.w / 2, L.sellBtn.y + L.sellBtn.h / 2);

      const rowsInfo = [
        ["power", 1, 0, `Latih Kekuatan Tebasan (Lv.${player.skill_levels.power})`, "Meningkatkan +12 ATK permanen (Biaya: 1 SKL)"],
        ["stamina", 1, 0, `Latih Ketahanan Napas (Lv.${player.skill_levels.stamina})`, "Meningkatkan +15 Max STA & +2.5/s Regen (Biaya: 1 SKL)"],
        ["defense", 1, 0, `Latih Pertahanan Baja (Lv.${player.skill_levels.defense})`, "Meningkatkan +25 Max HP & +5 DEF (Biaya: 1 SKL)"],
        ["blade", 2, 40, `Tempa Bilah Penebusan (Tier ${player.skill_levels.blade}/3)`, "Upgrade senjata suci & +20 Karma Good Ending (Biaya: 2 SKL + 40G)"],
      ];

      for (let i = 0; i < L.skillBtns.length; i++) {
        const btn = L.skillBtns[i];
        const [key, sklCost, goldCost, titleStr, descStr] = rowsInfo[i];
        const canBuy = player.skill_points >= sklCost && player.gold >= goldCost;
        const hover = C.pointInRect(mx, my, btn);
        const bg = canBuy ? (hover ? "#2d344a" : "#1e2230") : "#181a24";
        C.drawRoundedRect(ctx, btn.x, btn.y, btn.w, btn.h, 8, bg, canBuy ? C.COLOR_GOLD : "#414655", 1);

        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.font = C.font(13, { bold: true });
        ctx.fillStyle = key === "blade" ? C.COLOR_GOLD : C.COLOR_WHITE;
        ctx.fillText(titleStr, btn.x + 14, btn.y + 7);

        ctx.font = C.font(11);
        ctx.fillStyle = C.COLOR_TEXT_MUTED;
        ctx.fillText(descStr, btn.x + 14, btn.y + 28);

        const tag = `${sklCost} SKL${goldCost > 0 ? ` + ${goldCost}G` : ""}`;
        ctx.font = C.font(13, { bold: true });
        ctx.fillStyle = canBuy ? "#6edcff" : "#787882";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText(tag, btn.x + btn.w - 14, btn.y + btn.h / 2);
      }

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(11);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText("[ESC] / [E] untuk menutup Bengkel Vektor", L.panelX + 24, L.panelY + L.panelH - 28);
    }
  }

  global.OakhavenShop = ShopManager;
})(window);
