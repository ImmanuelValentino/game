(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const { RARITY_COLORS } = global.OakhavenInventory;

  class UIManager {
    constructor() {
      this.notificationText = "";
      this.notificationTimer = 0.0;
      this.showHelp = false;
      this.showMinimap = true;
      this.showTutorialCard = true;
    }

    showNotification(text, duration) {
      this.notificationText = text;
      this.notificationTimer = duration || 2.5;
    }

    toggleHelp() {
      this.showHelp = !this.showHelp;
    }

    toggleMinimap() {
      this.showMinimap = !this.showMinimap;
    }

    toggleTutorial() {
      this.showTutorialCard = !this.showTutorialCard;
    }

    update(dt) {
      if (this.notificationTimer > 0) {
        this.notificationTimer = Math.max(0.0, this.notificationTimer - dt);
      }
    }

    getHotbarGeometry(viewW, viewH) {
      const slotW = 46;
      const slotH = 46;
      const spacing = 8;
      const dividerW = 14;
      const numItems = 4;
      const numActions = 3;
      const barW = 22 + (numItems + numActions) * slotW + (numItems + numActions - 1) * spacing + dividerW;
      const barH = 64;
      const barX = Math.floor((viewW - barW) / 2);
      const barY = viewH - barH - 16;
      return { barX, barY, barW, barH, slotW, slotH, spacing, dividerW };
    }

    getHotbarItemRects(viewW, viewH) {
      const g = this.getHotbarGeometry(viewW, viewH);
      const rects = [];
      for (let idx = 0; idx < 4; idx++) {
        rects.push({
          x: g.barX + 11 + idx * (g.slotW + g.spacing),
          y: g.barY + 9,
          w: g.slotW,
          h: g.slotH,
        });
      }
      return rects;
    }

    getTutorialCloseRect(viewW, viewH) {
      const cw = 285;
      const ch = 166;
      const cx = 20;
      const cy = viewH - ch - 20;
      return { x: cx + cw - 24, y: cy + 4, w: 20, h: 20 };
    }

    getRespawnButtonRect(viewW, viewH) {
      return {
        x: Math.floor(viewW / 2 - 130),
        y: Math.floor(viewH / 2 + 55),
        w: 260,
        h: 46,
      };
    }

    draw(ctx, viewW, viewH, player, combatMgr, questMgr, nearbyNpc, map, npcs, targets, inventory, currentMap) {
      this._drawPlayerHud(ctx, player, viewW);
      this._drawCurrency(ctx, viewW, player, currentMap);
      this._drawQuestTracker(ctx, viewW, questMgr);
      this._drawBossBar(ctx, viewW, targets);
      this._drawHotbar(ctx, viewW, viewH, player, combatMgr, inventory);

      if (this.showTutorialCard && viewW >= 820) {
        this._drawTutorialCard(ctx, viewW, viewH);
      }
      if (this.showMinimap && map) {
        this._drawMinimap(ctx, viewW, player, map, npcs || [], targets || []);
      }
      if (nearbyNpc && !player.is_dead) {
        this._drawInteractionPrompt(ctx, viewW, viewH, nearbyNpc);
      }
      if (this.notificationTimer > 0) {
        this._drawNotification(ctx, viewW);
      }
      if (this.showHelp) {
        this._drawHelpOverlay(ctx, viewW, viewH);
      }
      if (player.is_dead) {
        this._drawGameOver(ctx, viewW, viewH);
      }
    }

    _drawPlayerHud(ctx, player) {
      const boxW = 310;
      const boxH = 114;
      const x = 20;
      const y = 20;

      C.drawRoundedRect(ctx, x, y, boxW, boxH, 8, "rgba(18, 20, 28, 0.85)", C.COLOR_PANEL_BORDER, 1);

      const cx = x + 32;
      const cy = y + 36;
      ctx.beginPath();
      ctx.arc(cx, cy, 22, 0, Math.PI * 2);
      ctx.fillStyle = "#282a38";
      ctx.fill();
      ctx.strokeStyle = C.COLOR_GOLD;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.font = C.font(14, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(`Lv.${player.level}`, cx, cy);

      const barX = x + 66;
      const barW = 228;

      // HP Bar + trail
      const hpY = y + 16;
      const hpPct = Math.max(0.0, Math.min(1.0, player.hp / Math.max(1, player.max_hp)));
      const trailPct = Math.max(0.0, Math.min(1.0, player.hp_trail / Math.max(1, player.max_hp)));
      C.drawRoundedRect(ctx, barX, hpY, barW, 18, 4, C.COLOR_HP_BG, null);
      if (trailPct > hpPct) {
        C.drawRoundedRect(ctx, barX, hpY, Math.round(barW * trailPct), 18, 4, C.COLOR_HP_TRAIL, null);
      }
      C.drawRoundedRect(ctx, barX, hpY, Math.round(barW * hpPct), 18, 4, C.COLOR_HP, null);
      ctx.font = C.font(11, { bold: true });
      ctx.fillStyle = C.COLOR_WHITE;
      ctx.fillText(`HP ${Math.floor(player.hp)}/${player.max_hp}`, barX + barW / 2, hpY + 9);

      // Stamina Bar
      const stY = y + 39;
      const stPct = Math.max(0.0, Math.min(1.0, player.stamina / Math.max(1, player.max_stamina)));
      C.drawRoundedRect(ctx, barX, stY, barW, 14, 3, C.COLOR_STAMINA_BG, null);
      C.drawRoundedRect(ctx, barX, stY, Math.round(barW * stPct), 14, 3, player.is_fatigued ? "#b4462d" : C.COLOR_STAMINA, null);
      ctx.font = C.font(10, { bold: true });
      const stText = player.is_fatigued ? "FATIGUE (<10 ST)" : `ST ${Math.floor(player.stamina)}/${player.max_stamina}`;
      ctx.fillStyle = player.is_fatigued ? "#ffdca0" : C.COLOR_WHITE;
      ctx.fillText(stText, barX + barW / 2, stY + 7);

      // EXP Bar
      const expY = y + 58;
      const expPct = Math.max(0.0, Math.min(1.0, player.exp / Math.max(1, player.exp_to_next)));
      C.drawRoundedRect(ctx, barX, expY, barW, 10, 2, C.COLOR_EXP_BG, null);
      C.drawRoundedRect(ctx, barX, expY, Math.round(barW * expPct), 10, 2, C.COLOR_EXP, null);
      ctx.font = C.font(9, { bold: true });
      ctx.fillStyle = C.COLOR_WHITE;
      ctx.fillText(`EXP ${player.exp}/${player.exp_to_next}`, barX + barW / 2, expY + 5);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(11);
      ctx.fillStyle = C.COLOR_TEXT_ACCENT;
      ctx.fillText(`ATK:${player.totalDamage}  DEF:${player.armor}  SKL:${player.skillLevel}`, x + 14, y + 73);
      ctx.font = C.font(10);
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText(`Senjata: ${player.weaponInfo.name}`, x + 14, y + 92);

      // Status Badges (Buffs, Hazards, White Flame, Perfect Dodge)
      const badges = [];
      if (player.perfect_dodge_slowmo_timer > 0) badges.push(["SLOW-MO DODGE! (CRIT 150%)", "rgba(80,180,255,0.82)"]);
      if (player.atk_boost_timer > 0) badges.push([`ATK +50% (${player.atk_boost_timer.toFixed(1)}s)`, "rgba(235,105,45,0.85)"]);
      if (player.def_boost_timer > 0) badges.push([`DEF +${player.def_boost_flat} (${player.def_boost_timer.toFixed(1)}s)`, "rgba(75,145,235,0.85)"]);
      if (player.crit_boost_timer > 0) badges.push([`CRIT +35% (${player.crit_boost_timer.toFixed(1)}s)`, "rgba(225,180,45,0.85)"]);
      if (player.in_white_fire) badges.push(["API PUTIH: MEMULIHKAN HP (+12/s)", "rgba(110,205,230,0.85)"]);
      if (player.active_hazards.has("sinkhole")) badges.push(["JEBAKAN HISAP (-55% SPD)", "rgba(170,115,45,0.8)"]);
      else if (player.active_hazards.has("mud")) badges.push(["LUMPUR PEKAT (-30% SPD)", "rgba(130,100,60,0.8)"]);
      if (player.has_hazard_debuff) badges.push(["KABUT RACUN (DoT +15% DMG)", "rgba(125,195,95,0.8)"]);
      if (player.active_hazards.has("lava")) badges.push(["TERBAKAR LAHAR!", "rgba(240,95,35,0.85)"]);
      if (player.active_hazards.has("ice")) badges.push(["ES LICIN (Inersia)", "rgba(125,200,245,0.8)"]);
      if (player.active_hazards.has("conv_right") || player.active_hazards.has("conv_left")) badges.push(["CONVEYOR BELT", "rgba(220,155,55,0.8)"]);

      let by = 140;
      ctx.font = C.font(11, { bold: true });
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      for (const [text, bg] of badges) {
        const bw = ctx.measureText(text).width + 18;
        C.drawRoundedRect(ctx, 20, by, bw, 22, 5, bg, null);
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.fillText(text, 29, by + 4);
        by += 26;
      }
    }

    _drawCurrency(ctx, viewW, player, currentMap) {
      const boxW = 300;
      const boxH = 44;
      const boxX = viewW - boxW - 20;
      const boxY = 20;

      C.drawRoundedRect(ctx, boxX, boxY, boxW, boxH, 8, "rgba(18, 20, 28, 0.85)", C.COLOR_PANEL_BORDER, 1);

      const drawPill = (cx, cy, col, label, textCol) => {
        ctx.beginPath();
        ctx.arc(cx, cy, 6, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
        ctx.font = C.font(13, { bold: true });
        ctx.fillStyle = textCol;
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(label, cx + 12, cy);
      };

      drawPill(boxX + 18, boxY + 22, C.COLOR_GOLD, `${player.gold} G`, C.COLOR_GOLD);
      drawPill(boxX + 112, boxY + 22, C.COLOR_ASH, `${player.monster_ash} Ash`, C.COLOR_ASH);
      drawPill(boxX + 208, boxY + 22, C.COLOR_TEXT_ACCENT, `${player.skill_points} SKL`, C.COLOR_TEXT_ACCENT);

      const hStr = "[F1]: Tutorial | [H]: Bantuan | [TAB]: Peta | [F11]: Layar";
      const locName = (C.STAGE_CONFIGS[currentMap] && C.STAGE_CONFIGS[currentMap].name) || currentMap;
      ctx.font = C.font(11);
      const hw = Math.max(ctx.measureText(hStr).width, ctx.measureText(locName).width) + 16;
      C.drawRoundedRect(ctx, boxX + boxW - hw, boxY + boxH + 4, hw, 36, 6, "rgba(14, 16, 24, 0.78)", null);

      ctx.textAlign = "right";
      ctx.textBaseline = "top";
      ctx.fillStyle = C.COLOR_WHITE;
      ctx.fillText(hStr, boxX + boxW - 6, boxY + boxH + 6);
      ctx.fillStyle = C.COLOR_TEXT_ACCENT;
      ctx.fillText(locName, boxX + boxW - 6, boxY + boxH + 22);
    }

    _drawQuestTracker(ctx, viewW, questMgr) {
      const q = questMgr.getCurrentQuest();
      const qText = q ? `${q.title} (${q.current_count}/${q.target_count})` : "Semua Quest Utama Selesai!";
      ctx.font = C.font(13, { bold: true });
      const tw = ctx.measureText(qText).width;
      const boxW = Math.min(viewW - 40, tw + 50);
      const boxH = 32;
      const boxX = Math.floor((viewW - boxW) / 2);
      const boxY = viewW >= 1060 ? 20 : 142;

      C.drawRoundedRect(ctx, boxX, boxY, boxW, boxH, 6, "rgba(18, 20, 28, 0.82)", "#8c733c", 1);

      const dx = boxX + 18;
      const dy = boxY + boxH / 2;
      ctx.beginPath();
      ctx.moveTo(dx, dy - 6);
      ctx.lineTo(dx + 6, dy);
      ctx.lineTo(dx, dy + 6);
      ctx.lineTo(dx - 6, dy);
      ctx.closePath();
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fill();

      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText(qText, boxX + 32, boxY + boxH / 2);
    }

    _drawBossBar(ctx, viewW, targets) {
      const boss = targets.find((t) => t.isBoss && t.isAlive());
      if (!boss) return;

      const barW = Math.min(500, viewW - 80);
      const barH = 16;
      const bx = Math.floor((viewW - barW) / 2);
      const by = viewW >= 1060 ? 62 : 182;

      ctx.font = C.font(13, { bold: true });
      ctx.fillStyle = "#ff735f";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(boss.name, viewW / 2, by);

      const ry = by + 20;
      C.drawRoundedRect(ctx, bx - 2, ry - 2, barW + 4, barH + 4, 5, "#140c10", C.COLOR_GOLD, 1);
      C.drawRoundedRect(ctx, bx, ry, barW, barH, 4, C.COLOR_HP_BG, null);
      const pct = Math.max(0.0, Math.min(1.0, boss.hp / Math.max(1, boss.max_hp)));
      C.drawRoundedRect(ctx, bx, ry, Math.round(barW * pct), barH, 4, "#c82832", null);
    }

    _drawHotbar(ctx, viewW, viewH, player, combatMgr, inventory) {
      const g = this.getHotbarGeometry(viewW, viewH);
      C.drawRoundedRect(ctx, g.barX, g.barY, g.barW, g.barH, 10, "rgba(18, 20, 28, 0.88)", C.COLOR_PANEL_BORDER, 1);

      const entries = inventory.getHotbarEntries();
      for (let i = 0; i < entries.length; i++) {
        const e = entries[i];
        const sx = g.barX + 11 + i * (g.slotW + g.spacing);
        const sy = g.barY + 9;
        const hasItem = Boolean(e.item && e.count > 0);
        const bg = hasItem ? "#202434" : "#161822";
        const border = hasItem ? (RARITY_COLORS[e.item.rarity] || C.COLOR_GOLD) : "#373c4e";
        C.drawRoundedRect(ctx, sx, sy, g.slotW, g.slotH, 6, bg, border, 1);

        if (e.item && Assets.itemIcons[e.item.icon_file]) {
          ctx.save();
          if (e.count <= 0) ctx.globalAlpha = 0.35;
          ctx.drawImage(Assets.itemIcons[e.item.icon_file], sx + 8, sy + 8, 30, 30);
          ctx.restore();
        }
        if (e.item && e.count > 0) {
          ctx.font = C.font(11, { bold: true });
          C.drawOutlinedText(ctx, String(e.count), sx + g.slotW - 4, sy + g.slotH - 14, C.COLOR_WHITE, "#000000", "right");
        }
        ctx.font = C.font(10, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText(e.key, sx + 4, sy + 3);
      }

      const divX = g.barX + 11 + 4 * (g.slotW + g.spacing) - Math.floor(g.spacing / 2) + Math.floor(g.dividerW / 2);
      ctx.beginPath();
      ctx.moveTo(divX, g.barY + 12);
      ctx.lineTo(divX, g.barY + g.barH - 12);
      ctx.strokeStyle = "#55504b";
      ctx.lineWidth = 2;
      ctx.stroke();

      const actionStartX = divX + Math.floor(g.dividerW / 2) + 4;
      const actions = [
        { key: "LMB", cd: combatMgr.attackCdTimer / combatMgr.attackCooldown, color: "#f0be32" },
        { key: "RMB", cd: combatMgr.skillCdTimer / combatMgr.skillCooldown, color: "#e65028" },
        { key: "Space", cd: player.roll_cd_timer / player.roll_cooldown, color: "#64aaff" },
      ];
      for (let j = 0; j < actions.length; j++) {
        const a = actions[j];
        const sx = actionStartX + j * (g.slotW + g.spacing);
        const sy = g.barY + 9;
        C.drawRoundedRect(ctx, sx, sy, g.slotW, g.slotH, 6, "#1e202d", "#3c4155", 1);

        ctx.beginPath();
        ctx.arc(sx + g.slotW / 2, sy + g.slotH / 2 + 2, 11, 0, Math.PI * 2);
        ctx.fillStyle = a.color;
        ctx.fill();

        if (a.cd > 0) {
          const cdH = Math.round(g.slotW * Math.min(1.0, a.cd));
          ctx.fillStyle = "rgba(0, 0, 0, 0.68)";
          ctx.fillRect(sx + 1, sy + g.slotH - cdH, g.slotW - 2, cdH);
        }

        ctx.font = C.font(10, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText(a.key, sx + 4, sy + 3);
      }
    }

    _drawMinimapIcon(ctx, role, x, y) {
      if (role === "shop") {
        C.drawRoundedRect(ctx, x - 4, y - 4, 8, 8, 2, "#f5c32d", "#28190a", 1);
        ctx.strokeStyle = "#fff5b4";
        ctx.beginPath();
        ctx.moveTo(x, y - 2);
        ctx.lineTo(x, y + 2);
        ctx.stroke();
      } else if (role === "skill") {
        ctx.beginPath();
        ctx.moveTo(x, y - 5);
        ctx.lineTo(x + 5, y);
        ctx.lineTo(x, y + 5);
        ctx.lineTo(x - 5, y);
        ctx.closePath();
        ctx.fillStyle = "#50c8ff";
        ctx.fill();
        ctx.strokeStyle = "#dcf8ff";
        ctx.lineWidth = 1;
        ctx.stroke();
      } else if (role === "map") {
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = "#5fe1a5";
        ctx.fill();
        ctx.strokeStyle = "#143223";
        ctx.beginPath();
        ctx.moveTo(x - 3, y);
        ctx.lineTo(x + 3, y);
        ctx.moveTo(x, y - 3);
        ctx.lineTo(x, y + 3);
        ctx.stroke();
      } else if (role === "quest") {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffdc41";
        ctx.fill();
        ctx.fillStyle = "#23140a";
        ctx.fillRect(x - 1, y - 3, 2, 4);
        ctx.fillRect(x - 1, y + 2, 2, 2);
      } else if (role === "bar") {
        C.drawRoundedRect(ctx, x - 3, y - 4, 6, 7, 1, "#e18c32", null);
        ctx.fillStyle = "#ffebc8";
        ctx.fillRect(x - 2, y - 4, 4, 1);
      } else if (role === "campfire") {
        ctx.beginPath();
        ctx.moveTo(x, y - 5);
        ctx.lineTo(x + 4, y + 4);
        ctx.lineTo(x - 4, y + 4);
        ctx.closePath();
        ctx.fillStyle = "#ff7d23";
        ctx.fill();
      } else if (role === "white_fire") {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = "#c3f8ff";
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.beginPath();
        ctx.moveTo(x - 3, y);
        ctx.lineTo(x + 3, y);
        ctx.moveTo(x, y - 3);
        ctx.lineTo(x, y + 3);
        ctx.stroke();
      } else if (role === "portal") {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.strokeStyle = "#af6eff";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fillStyle = "#ebd2ff";
        ctx.fill();
      } else if (role === "guard" || role === "villager") {
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#b9c3d7";
        ctx.fill();
      } else {
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fill();
      }
    }

    _drawMinimap(ctx, viewW, player, map, npcs, targets) {
      const mmSize = 160;
      const mmX = viewW - mmSize - 20;
      const mmY = 112;

      C.drawRoundedRect(ctx, mmX, mmY, mmSize, mmSize, 4, "rgba(16, 18, 26, 0.85)", C.COLOR_PANEL_BORDER_LIGHT, 2);

      const sx = mmSize / Math.max(1, map.width);
      const sy = mmSize / Math.max(1, map.height);

      ctx.fillStyle = "rgba(75, 80, 95, 0.85)";
      for (const c of map.colliders) {
        ctx.fillRect(
          mmX + Math.round(c[0] * sx),
          mmY + Math.round(c[1] * sy),
          Math.max(2, Math.round(c[2] * sx)),
          Math.max(2, Math.round(c[3] * sy))
        );
      }

      const rolesPresent = new Set();
      for (const npc of npcs) {
        const [nx, ny] = npc.getCenter();
        const role = npc.map_role || (npc.target_map ? "portal" : "npc");
        rolesPresent.add(role);
        this._drawMinimapIcon(ctx, role, mmX + Math.round(nx * sx), mmY + Math.round(ny * sy));
      }

      let hasBoss = false;
      let hasEnemy = false;
      for (const t of targets) {
        if (!t.isAlive()) continue;
        const [tx, ty] = t.getCenter();
        const px = mmX + Math.round(tx * sx);
        const py = mmY + Math.round(ty * sy);
        if (t.isBoss) {
          hasBoss = true;
          C.drawRoundedRect(ctx, px - 4, py - 4, 8, 8, 1, "#ff3741", C.COLOR_GOLD, 1);
        } else {
          hasEnemy = true;
          ctx.beginPath();
          ctx.arc(px, py, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = "#dc5f5f";
          ctx.fill();
        }
      }

      const ppx = mmX + Math.round((player.x + 24) * sx);
      const ppy = mmY + Math.round((player.y + 24) * sy);
      ctx.beginPath();
      ctx.moveTo(ppx, ppy - 5);
      ctx.lineTo(ppx + 4, ppy + 4);
      ctx.lineTo(ppx - 4, ppy + 4);
      ctx.closePath();
      ctx.fillStyle = "#5fff82";
      ctx.fill();
      ctx.strokeStyle = C.COLOR_WHITE;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Legend below minimap
      const legendItems = [];
      const labels = [
        ["shop", "Toko Gael"],
        ["skill", "Skill Vektor"],
        ["map", "Peta Aell"],
        ["quest", "Quest/Info"],
        ["bar", "Kedai Brog"],
        ["white_fire", "Api Putih (+HP)"],
        ["portal", "Portal"],
      ];
      for (const [k, txt] of labels) {
        if (rolesPresent.has(k)) legendItems.push([k, txt]);
      }
      if (hasBoss) legendItems.push(["boss", "Bos Domain"]);
      else if (hasEnemy) legendItems.push(["enemy", "Musuh"]);

      if (legendItems.length > 0) {
        const rowH = 15;
        const legH = legendItems.length * rowH + 10;
        const legY = mmY + mmSize + 6;
        C.drawRoundedRect(ctx, mmX, legY, mmSize, legH, 6, "rgba(16, 18, 26, 0.8)", C.COLOR_PANEL_BORDER, 1);
        ctx.font = C.font(10);
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        for (let i = 0; i < legendItems.length; i++) {
          const [rk, rtxt] = legendItems[i];
          const ly = legY + 11 + i * rowH;
          if (rk === "boss") {
            C.drawRoundedRect(ctx, mmX + 9, ly - 4, 8, 8, 1, "#ff3741", C.COLOR_GOLD, 1);
          } else if (rk === "enemy") {
            ctx.beginPath();
            ctx.arc(mmX + 13, ly, 3, 0, Math.PI * 2);
            ctx.fillStyle = "#dc5f5f";
            ctx.fill();
          } else {
            this._drawMinimapIcon(ctx, rk, mmX + 13, ly);
          }
          ctx.fillStyle = C.COLOR_WHITE;
          ctx.fillText(rtxt, mmX + 26, ly);
        }
      }
    }

    _drawTutorialCard(ctx, viewW, viewH) {
      const cw = 285;
      const ch = 166;
      const cx = 20;
      const cy = viewH - ch - 20;

      C.drawRoundedRect(ctx, cx, cy, cw, ch, 9, "rgba(16, 18, 28, 0.85)", C.COLOR_PANEL_BORDER_LIGHT, 1);
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(11, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText("TUTORIAL & KONTROL [F1]", cx + 10, cy + 8);

      ctx.fillStyle = "#e15a5a";
      ctx.fillText("X", cx + cw - 18, cy + 8);

      const tips = [
        ["WASD + Shift", "Bergerak & Sprint | [E] Interaksi NPC"],
        ["LMB / RMB", "Tebasan (5 STA) & Ash Cleave (30 STA)"],
        ["Spasi", "Dodge Roll (15 STA) / Slow-Mo"],
        ["Tombol 1-4", "Pakai Item/Boost di Kotak Bawah"],
        ["TAB / F11", "Ikon Peta NPC & Layar Penuh"],
        ["Api Putih", "Dekati Api Putih di sudut Dungeon (+HP)"],
      ];
      ctx.font = C.font(10);
      for (let i = 0; i < tips.length; i++) {
        const ry = cy + 29 + i * 22;
        ctx.fillStyle = C.COLOR_TEXT_ACCENT;
        ctx.fillText(tips[i][0], cx + 10, ry);
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.fillText(tips[i][1], cx + 88, ry);
      }
    }

    _drawInteractionPrompt(ctx, viewW, viewH, nearbyNpc) {
      let str = "";
      if (nearbyNpc.map_role === "white_fire") str = "Api Putih: Berdiri di dalam aura untuk regenerasi HP";
      else if (nearbyNpc.target_map) str = `[E] ${nearbyNpc.name}`;
      else if (nearbyNpc.name === "Api Unggun Oakhaven") str = "[E] Istirahat & Simpan Game";
      else str = `[E] Bicara dengan ${nearbyNpc.name}`;

      ctx.font = C.font(14, { bold: true });
      const pw = ctx.measureText(str).width + 32;
      const ph = 36;
      const px = Math.floor((viewW - pw) / 2);
      const py = viewH - 135;

      C.drawRoundedRect(ctx, px, py, pw, ph, 8, "rgba(18, 20, 28, 0.88)", C.COLOR_GOLD, 2);
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(str, px + pw / 2, py + ph / 2);
    }

    _drawNotification(ctx, viewW) {
      ctx.font = C.font(16, { bold: true });
      const nw = ctx.measureText(this.notificationText).width + 40;
      const nh = 40;
      const nx = Math.floor((viewW - nw) / 2);
      const ny = 98;

      C.drawRoundedRect(ctx, nx, ny, nw, nh, 8, "rgba(20, 22, 32, 0.92)", C.COLOR_GOLD, 1);
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(this.notificationText, nx + nw / 2, ny + nh / 2);
    }

    _drawHelpOverlay(ctx, viewW, viewH) {
      ctx.fillStyle = "rgba(0, 0, 0, 0.72)";
      ctx.fillRect(0, 0, viewW, viewH);

      const hw = Math.min(640, viewW - 40);
      const hh = Math.min(500, viewH - 40);
      const hx = Math.floor((viewW - hw) / 2);
      const hy = Math.floor((viewH - hh) / 2);

      C.drawRoundedRect(ctx, hx, hy, hw, hh, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, hx + 4, hy + 4, hw - 8, hh - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(20, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText("PANDUAN KONTROL & MEKANIKA", hx + 24, hy + 18);

      const controls = [
        ["W / A / S / D", "Bergerak 8 arah (Top-Down)"],
        ["Shift Kiri (Tahan)", "Sprint (+40% Speed, 10 STA/s; 2x di lumpur)"],
        ["Mouse Kursor", "Membidik arah tebasan dan skill"],
        ["Klik Kiri (LMB)", "Serangan Pedang Ringan (5 STA, ditolak saat STA < 10)"],
        ["Klik Kanan (RMB)", "Skill Berat Ash Cleave (30 STA)"],
        ["Spasi", "Dodge Roll (15 STA) & Perfect Dodge Slow-Mo 1.5s"],
        ["Tombol [E]", "Interaksi NPC, Peta Aell, Vektor, Gael, Portal"],
        ["Tombol [B] / [I]", "Buka / Tutup Tas (Pakai potion / Equip senjata)"],
        ["Tombol [1] - [4]", "Pakai Item/Boost di Kotak Hotbar Bawah (atau klik)"],
        ["Tombol [TAB] / [F1]", "Ikon Minimap & Legenda / Tutorial Cepat"],
        ["F11 / Tombol Layar", "Toggle Layar Penuh <-> Ukuran Normal (Responsif)"],
        ["Tombol [ESC] / [H]", "Tutup menu / Buka Bantuan ini"],
      ];

      for (let i = 0; i < controls.length; i++) {
        const cy = hy + 56 + i * 31;
        ctx.font = C.font(13, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fillText(controls[i][0], hx + 28, cy);
        ctx.font = C.font(13);
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.fillText(controls[i][1], hx + 195, cy);
      }

      ctx.font = C.font(12, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.textAlign = "center";
      ctx.fillText("[Tekan [H], [ESC], atau klik mana saja untuk kembali]", hx + hw / 2, hy + hh - 28);
    }

    _drawGameOver(ctx, viewW, viewH) {
      ctx.fillStyle = "rgba(25, 5, 5, 0.82)";
      ctx.fillRect(0, 0, viewW, viewH);

      const gw = 520;
      const gh = 260;
      const gx = Math.floor((viewW - gw) / 2);
      const gy = Math.floor((viewH - gh) / 2);

      C.drawRoundedRect(ctx, gx, gy, gw, gh, 12, "#1c0f12", "#b43232", 2);
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.font = C.font(26, { bold: true });
      ctx.fillStyle = "#ff5050";
      ctx.fillText("KAU TELAH GUGUR...", gx + gw / 2, gy + 30);

      ctx.font = C.font(13);
      ctx.fillStyle = C.COLOR_WHITE;
      ctx.fillText("Nafas abu memadamkan kesadaranmu. Kau kembali ke Hub Rusty Anchor.", gx + gw / 2, gy + 85);
      ctx.fillStyle = "#dcb4b4";
      ctx.fillText("Konsekuensi GDD: kehilangan 30% Abu Monster & 50% material belum terjual.", gx + gw / 2, gy + 110);

      const btn = this.getRespawnButtonRect(viewW, viewH);
      C.drawRoundedRect(ctx, btn.x, btn.y, btn.w, btn.h, 8, "#a02828", "#ff7878", 2);
      ctx.font = C.font(15, { bold: true });
      ctx.fillStyle = C.COLOR_WHITE;
      ctx.textBaseline = "middle";
      ctx.fillText("Bangkit di Api Unggun [R]", btn.x + btn.w / 2, btn.y + btn.h / 2);
    }
  }

  global.OakhavenUI = UIManager;
})(window);
