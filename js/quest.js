(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;
  const { FloatingText } = global.OakhavenCombat;

  const QUEST_DEFS = [
    { id: "q1_awaken", title: "1. Suaka Oakhaven (Rusty Anchor)", desc: "Bicaralah dengan Elara atau Vektor di aula Hub untuk memahami Suar Kematian.", target_count: 1, exp_reward: 40, gold_reward: 25, karma_reward: 5 },
    { id: "q2_training", title: "2. Uji Kemampuan Tempur", desc: "Latih tebasan (LMB), Ash Cleave (RMB), & Dodge (Spasi) di Training Yard.", target_count: 3, exp_reward: 75, gold_reward: 40, karma_reward: 0 },
    { id: "q3_supplies", title: "3. Persiapan Bengkel & Perlengkapan", desc: "Tukar Abu di Brog, serahkan material ke Vektor, atau belanja di Gael.", target_count: 1, exp_reward: 80, gold_reward: 50, karma_reward: 0 },
    { id: "q4_stage1", title: "4. Bab 1: Rawa Kematian (Gargantua)", desc: "Masuki Stage 1 lewat Aell/Gerbang Utara & kalahkan Jenderal Gargantua.", target_count: 1, exp_reward: 140, gold_reward: 90, karma_reward: 5 },
    { id: "q5_stage2", title: "5. Bab 2: Hutan Spora (Vespa)", desc: "Masuki Stage 2 dan tumbangkan Ratu Spora Vespa (Mycelia).", target_count: 1, exp_reward: 220, gold_reward: 140, karma_reward: 5 },
    { id: "q6_stage3", title: "6. Bab 3: Tungku Gehenna (Ignis)", desc: "Lintasi conveyor & lahar Stage 3 untuk mengalahkan Ignis Executioner.", target_count: 1, exp_reward: 320, gold_reward: 200, karma_reward: 5 },
    { id: "q7_stage4", title: "7. Bab 4: Salju Hitam (Valerius)", desc: "Taklukkan arena es licin Stage 4 melawan Jenderal Valerius.", target_count: 1, exp_reward: 460, gold_reward: 280, karma_reward: 5 },
    { id: "q8_stage5", title: "8. Bab 5: Ruang Takhta Obsidian", desc: "Hadapi Sang Penguasa Abu & Mahkota Kutukan dalam pertarungan 2 fase.", target_count: 1, exp_reward: 800, gold_reward: 500, karma_reward: 0 },
  ];

  class QuestManager {
    constructor() {
      this.quests = QUEST_DEFS.map((d) =>
        Object.assign({ current_count: 0, is_completed: false, is_claimed: false }, d)
      );
    }

    getCurrentQuest() {
      return this.quests.find((q) => !q.is_completed) || null;
    }

    advanceProgress(questId, amount, player, combatMgr) {
      const q = this.quests.find((item) => item.id === questId);
      if (!q || q.is_completed) return;
      q.current_count = Math.min(q.target_count, q.current_count + (amount || 1));
      if (q.current_count >= q.target_count) {
        q.is_completed = true;
        if (!q.is_claimed) {
          q.is_claimed = true;
          player.gainExp(q.exp_reward);
          player.gold += q.gold_reward;
          if (q.karma_reward) player.karma += q.karma_reward;
          AudioMgr.playSound("levelup");
          if (combatMgr) {
            combatMgr.floatingTexts.push(
              new FloatingText(player.x + 24, player.y - 45, `QUEST SELESAI! +${q.exp_reward} EXP +${q.gold_reward}G`, C.COLOR_GOLD, 16, true)
            );
          }
        }
      }
    }
  }

  class DialogueSystem {
    constructor() {
      this.isOpen = false;
      this.npcName = "";
      this.pages = [];
      this.pageIndex = 0;
      this.portraitKey = null;
      this.choices = [];
      this.charIdx = 0.0;
      this.openAnim = 0.0;
      this.elapsed = 0.0;
      this.beepCd = 0.0;
    }

    startDialogue(npcName, pages, portraitKey, choices) {
      this.isOpen = true;
      this.npcName = npcName;
      this.pages = Array.isArray(pages) ? pages : [String(pages)];
      this.pageIndex = 0;
      this.portraitKey = portraitKey || null;
      this.choices = choices || [];
      this.charIdx = 0.0;
      this.openAnim = 0.0;
      AudioMgr.playSound("accept");
    }

    close() {
      this.isOpen = false;
      this.choices = [];
      AudioMgr.playSound("cancel");
    }

    _getBoxLayout(viewW, viewH) {
      const boxW = Math.min(780, viewW - 60);
      const boxH = 200;
      const boxX = Math.floor((viewW - boxW) / 2);
      const targetY = viewH - boxH - 28;
      const slide = Math.round((1.0 - Math.min(1.0, this.openAnim / 0.22)) * 28);
      return { boxX, boxY: targetY + slide, boxW, boxH };
    }

    _getChoiceRects(viewW, viewH) {
      const L = this._getBoxLayout(viewW, viewH);
      const rects = [];
      const bw = 205;
      const bh = 34;
      const startX = L.boxX + L.boxW - this.choices.length * (bw + 10) - 10;
      const by = L.boxY + L.boxH - 44;
      for (let i = 0; i < this.choices.length; i++) {
        rects.push({ x: startX + i * (bw + 10), y: by, w: bw, h: bh });
      }
      return rects;
    }

    advance() {
      const curText = this.pages[this.pageIndex] || "";
      if (this.charIdx < curText.length) {
        this.charIdx = curText.length;
        return;
      }
      if (this.pageIndex < this.pages.length - 1) {
        this.pageIndex += 1;
        this.charIdx = 0.0;
        AudioMgr.playSound("accept");
      } else if (this.choices.length === 0) {
        this.close();
      }
    }

    update(dt) {
      if (!this.isOpen) return;
      this.elapsed += dt;
      this.openAnim = Math.min(0.25, this.openAnim + dt);
      if (this.beepCd > 0) this.beepCd = Math.max(0.0, this.beepCd - dt);

      const cur = this.pages[this.pageIndex] || "";
      if (this.charIdx < cur.length) {
        const prev = Math.floor(this.charIdx);
        this.charIdx = Math.min(cur.length, this.charIdx + 55.0 * dt);
        if (Math.floor(this.charIdx) > prev && this.beepCd <= 0) {
          this.beepCd = 0.07;
          AudioMgr.playSound("dialogue_beep");
        }
      }
    }

    handleClick(lx, ly, viewW, viewH) {
      if (!this.isOpen) return false;
      const L = this._getBoxLayout(viewW, viewH);
      const isLast = this.pageIndex === this.pages.length - 1;
      const fullShown = this.charIdx >= (this.pages[this.pageIndex] || "").length;

      if (isLast && fullShown && this.choices.length > 0) {
        const rects = this._getChoiceRects(viewW, viewH);
        for (let i = 0; i < rects.length; i++) {
          if (C.pointInRect(lx, ly, rects[i])) {
            const fn = this.choices[i][1];
            if (typeof fn === "function") fn();
            return true;
          }
        }
      }
      if (C.pointInRect(lx, ly, { x: L.boxX, y: L.boxY, w: L.boxW, h: L.boxH })) {
        this.advance();
        return true;
      }
      return true;
    }

    _wrapLines(ctx, text, maxW) {
      const words = text.split(" ");
      const lines = [];
      let line = "";
      for (const w of words) {
        const test = line ? `${line} ${w}` : w;
        if (ctx.measureText(test).width <= maxW) line = test;
        else {
          if (line) lines.push(line);
          line = w;
        }
      }
      if (line) lines.push(line);
      return lines;
    }

    draw(ctx, viewW, viewH, mx, my) {
      if (!this.isOpen) return;
      const L = this._getBoxLayout(viewW, viewH);
      const alpha = Math.min(1.0, this.openAnim / 0.16);
      ctx.save();
      ctx.globalAlpha = alpha;

      C.drawRoundedRect(ctx, L.boxX, L.boxY, L.boxW, L.boxH, 12, "rgba(18, 20, 30, 0.94)", C.COLOR_PANEL_BORDER_LIGHT, 2);

      let textX = L.boxX + 24;
      if (this.portraitKey) {
        const bob = Math.round(Math.sin(this.elapsed * 4.5) * 2.5);
        C.drawRoundedRect(ctx, L.boxX + 18, L.boxY + 22 + bob, 86, 86, 8, "#282b3a", C.COLOR_GOLD, 2);
        Assets.drawSpriteFrame(ctx, this.portraitKey, 0, L.boxX + 21, L.boxY + 25 + bob, 80, 80);
        textX = L.boxX + 122;
      }

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textBaseline = "top";
      ctx.textAlign = "left";
      ctx.fillText(this.npcName, textX, L.boxY + 18);

      const cur = this.pages[this.pageIndex] || "";
      const visible = cur.slice(0, Math.floor(this.charIdx));
      ctx.font = C.font(14);
      ctx.fillStyle = C.COLOR_WHITE;
      const lines = this._wrapLines(ctx, visible, L.boxX + L.boxW - textX - 24);
      for (let i = 0; i < Math.min(4, lines.length); i++) {
        ctx.fillText(lines[i], textX, L.boxY + 48 + i * 24);
      }

      const isLast = this.pageIndex === this.pages.length - 1;
      const fullShown = this.charIdx >= cur.length;

      if (isLast && fullShown && this.choices.length > 0) {
        const rects = this._getChoiceRects(viewW, viewH);
        ctx.font = C.font(12, { bold: true });
        for (let i = 0; i < this.choices.length; i++) {
          const r = rects[i];
          const hover = C.pointInRect(mx, my, r);
          C.drawRoundedRect(ctx, r.x, r.y, r.w, r.h, 7, hover ? "#a57323" : "#263246", C.COLOR_GOLD, 1);
          ctx.fillStyle = C.COLOR_WHITE;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(this.choices[i][0], r.x + r.w / 2, r.y + r.h / 2);
        }
      } else {
        const prompt = !isLast ? "[Spasi / Klik] Lanjut >>>" : "[Spasi / Klik] Tutup";
        ctx.font = C.font(11, { italic: true });
        ctx.fillStyle = C.COLOR_TEXT_ACCENT;
        ctx.textAlign = "right";
        ctx.textBaseline = "top";
        ctx.fillText(prompt, L.boxX + L.boxW - 22, L.boxY + L.boxH - 28);
      }

      ctx.restore();
    }
  }

  class CartographyMapUI {
    constructor() {
      this.isOpen = false;
      this.nodes = [
        { id: "stage4_frost.tmx", title: "4. Dungeon 4: Salju Hitam", sub: "Bos: Valerius (Lv.41-55)", rx: 0.5, ry: 0.22, col: [130, 205, 250], req: "stage3_gehenna.tmx" },
        { id: "stage3_gehenna.tmx", title: "3. Dungeon 3: Tungku Gehenna", sub: "Bos: Ignis (Lv.26-40)", rx: 0.21, ry: 0.5, col: [240, 120, 45], req: "stage2_spore.tmx" },
        { id: "stage5_throne.tmx", title: "5. Final Boss Domain", sub: "Mahkota Kutukan (Laser!)", rx: 0.5, ry: 0.5, col: [220, 60, 75], req: "stage4_frost.tmx" },
        { id: "stage2_spore.tmx", title: "2. Dungeon 2: Hutan Spora", sub: "Bos: Vespa (Lv.11-25)", rx: 0.79, ry: 0.5, col: [185, 95, 235], req: "stage1_swamp.tmx" },
        { id: "stage1_swamp.tmx", title: "1. Dungeon 1: Rawa Kematian", sub: "Bos: Gargantua (Lv.1-10)", rx: 0.5, ry: 0.77, col: [110, 195, 115], req: null },
        { id: "dungeon1.tmx", title: "Labirin Dungeon 1", sub: "Ekspedisi Klasik", rx: 0.19, ry: 0.8, col: [140, 160, 195], req: null },
        { id: "dungeon2.tmx", title: "Labirin Dungeon 2", sub: "Aula Raja Iblis", rx: 0.81, ry: 0.8, col: [180, 140, 210], req: null },
      ];
    }

    open() {
      this.isOpen = true;
      AudioMgr.playSound("accept");
    }

    close() {
      this.isOpen = false;
      AudioMgr.playSound("cancel");
    }

    toggle() {
      if (this.isOpen) this.close();
      else this.open();
    }

    _getLayout(viewW, viewH) {
      const pw = Math.min(820, viewW - 60);
      const ph = Math.min(540, viewH - 60);
      const px = Math.floor((viewW - pw) / 2);
      const py = Math.floor((viewH - ph) / 2);
      const closeRect = { x: px + pw - 38, y: py + 14, w: 26, h: 26 };
      return { px, py, pw, ph, closeRect };
    }

    _getNodeRects(L) {
      return this.nodes.map((n) => ({
        node: n,
        rect: {
          x: Math.round(L.px + n.rx * L.pw - 108),
          y: Math.round(L.py + n.ry * L.ph - 30),
          w: 216,
          h: 60,
        },
      }));
    }

    handleClick(lx, ly, player, switchMapFn, uiMgr, viewW, viewH) {
      if (!this.isOpen) return false;
      const L = this._getLayout(viewW, viewH);
      if (C.pointInRect(lx, ly, L.closeRect)) {
        this.close();
        return true;
      }
      if (!C.pointInRect(lx, ly, { x: L.px, y: L.py, w: L.pw, h: L.ph })) {
        this.close();
        return true;
      }

      const items = this._getNodeRects(L);
      for (const { node, rect } of items) {
        if (C.pointInRect(lx, ly, rect)) {
          const unlocked = !node.req || (player.beacons_cleared && player.beacons_cleared.has(node.req));
          if (!unlocked) {
            AudioMgr.playSound("cancel");
            if (uiMgr) uiMgr.showNotification("Kalahkan jenderal bioma sebelumnya untuk membuka jalur ini!", 2.8);
            return true;
          }
          const cfg = C.STAGE_CONFIGS[node.id] || {};
          const spawn = cfg.spawn || [96, 608];
          this.close();
          AudioMgr.playSound("accept");
          switchMapFn(node.id, spawn[0], spawn[1]);
          return true;
        }
      }
      return true;
    }

    draw(ctx, viewW, viewH, mx, my, player, currentMap) {
      if (!this.isOpen) return;
      const L = this._getLayout(viewW, viewH);

      ctx.fillStyle = "rgba(0, 0, 0, 0.65)";
      ctx.fillRect(0, 0, viewW, viewH);

      C.drawRoundedRect(ctx, L.px, L.py, L.pw, L.ph, 12, C.COLOR_PANEL_BG, C.COLOR_PANEL_BORDER, 2);
      C.drawRoundedRect(ctx, L.px + 4, L.py + 4, L.pw - 8, L.ph - 8, 10, null, C.COLOR_PANEL_BORDER_LIGHT, 1);

      ctx.font = C.font(18, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText("PETA DUNIA KARTOGRAFI AELL (PILIH STAGE)", L.px + 24, L.py + 16);

      ctx.font = C.font(11, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText("Klik zona yang sudah terbuka untuk ekspedisi cepat menuju Suar Kematian.", L.px + 24, L.py + 42);

      ctx.font = C.font(16, { bold: true });
      ctx.fillStyle = "#dc5050";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("X", L.closeRect.x + L.closeRect.w / 2, L.closeRect.y + L.closeRect.h / 2);

      // Connecting ritual lines
      const cx = L.px + L.pw * 0.5;
      const cy = L.py + L.ph * 0.5;
      ctx.strokeStyle = "#484e66";
      ctx.lineWidth = 2;
      for (const n of this.nodes) {
        if (!n.id.startsWith("dungeon")) {
          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(L.px + n.rx * L.pw, L.py + n.ry * L.ph);
          ctx.stroke();
        }
      }

      const items = this._getNodeRects(L);
      for (const { node, rect } of items) {
        const unlocked = !node.req || (player.beacons_cleared && player.beacons_cleared.has(node.req));
        const cleared = player.beacons_cleared && player.beacons_cleared.has(node.id);
        const isCurrent = currentMap === node.id;
        const hover = C.pointInRect(mx, my, rect) && unlocked;

        const bg = !unlocked ? "#181a24" : hover ? "#2d3448" : "#1e2230";
        const border = isCurrent ? "#78dcff" : cleared ? "#5ad882" : unlocked ? C.rgbStr(node.col) : "#484c5e";
        C.drawRoundedRect(ctx, rect.x, rect.y, rect.w, rect.h, 8, bg, border, 2);

        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.font = C.font(12, { bold: true });
        ctx.fillStyle = unlocked ? C.COLOR_WHITE : "#7e8296";
        ctx.fillText(node.title, rect.x + 12, rect.y + 10);

        ctx.font = C.font(10);
        const statusStr = !unlocked ? "Terkunci (Padamkan suar sblmnya)" : cleared ? "Suar Padam — Siap Ulang" : node.sub;
        ctx.fillStyle = cleared ? "#78ebb4" : unlocked ? C.rgbStr(node.col) : "#6e7282";
        ctx.fillText(statusStr, rect.x + 12, rect.y + 32);
      }

      ctx.font = C.font(11);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.textAlign = "center";
      ctx.fillText("[TAB] / [ESC] Tutup Peta", L.px + L.pw / 2, L.py + L.ph - 26);
    }
  }

  global.OakhavenQuest = {
    QUEST_DEFS,
    QuestManager,
    DialogueSystem,
    CartographyMapUI,
  };
})(window);
