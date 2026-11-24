(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;

  class AshParticleOverlay {
    constructor(count, viewW, viewH) {
      this.particles = [];
      const w = viewW || C.DEFAULT_WIDTH;
      const h = viewH || C.DEFAULT_HEIGHT;
      for (let i = 0; i < (count || 42); i++) {
        this.particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: -18 - Math.random() * 24,
          vy: 14 + Math.random() * 26,
          size: 1 + Math.floor(Math.random() * 3),
          alpha: 0.25 + Math.random() * 0.5,
        });
      }
    }

    update(dt, viewW, viewH) {
      const w = viewW || C.DEFAULT_WIDTH;
      const h = viewH || C.DEFAULT_HEIGHT;
      for (const p of this.particles) {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        if (p.y > h) {
          p.y = -4;
          p.x = Math.random() * (w + 100);
        }
        if (p.x < -8) p.x = w + 6;
      }
    }

    draw(ctx) {
      for (const p of this.particles) {
        ctx.fillStyle = `rgba(215, 200, 195, ${p.alpha.toFixed(2)})`;
        ctx.beginPath();
        ctx.arc(Math.round(p.x), Math.round(p.y), p.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }

  class TitleScreenScene {
    constructor(hasSave) {
      this.hasSave = Boolean(hasSave);
      this.showControls = false;
      this.ash = new AshParticleOverlay(46);
    }

    _getButtons(viewW, viewH) {
      const bx = Math.max(48, Math.floor(viewW * 0.08));
      const bw = 310;
      const bh = 46;
      const startY = Math.floor(viewH * 0.56);
      const btns = [];
      btns.push({ action: "new_game", label: "Mulai Petualangan Baru", rect: { x: bx, y: startY, w: bw, h: bh }, enabled: true });
      btns.push({
        action: "continue",
        label: this.hasSave ? "Lanjutkan Permainan" : "Lanjutkan (Belum Ada Save)",
        rect: { x: bx, y: startY + 58, w: bw, h: bh },
        enabled: this.hasSave,
      });
      btns.push({ action: "controls", label: "Panduan Kontrol [H]", rect: { x: bx, y: startY + 116, w: bw, h: bh }, enabled: true });
      return btns;
    }

    _getFullscreenButton(viewW) {
      return { x: viewW - 196, y: 20, w: 176, h: 38 };
    }

    update(dt, viewW, viewH) {
      this.ash.update(dt, viewW, viewH);
    }

    handleClick(lx, ly, viewW, viewH) {
      if (this.showControls) {
        this.showControls = false;
        return null;
      }
      if (C.pointInRect(lx, ly, this._getFullscreenButton(viewW))) {
        AudioMgr.playSound("accept");
        return "toggle_fullscreen";
      }
      for (const b of this._getButtons(viewW, viewH)) {
        if (C.pointInRect(lx, ly, b.rect) && b.enabled) {
          AudioMgr.playSound("accept");
          if (b.action === "controls") {
            this.showControls = true;
            return null;
          }
          return b.action;
        }
      }
      return null;
    }

    handleKey(code) {
      if (this.showControls) {
        this.showControls = false;
        return null;
      }
      if (code === "KeyH") {
        this.showControls = true;
        return null;
      }
      if (code === "Enter" || code === "Space") {
        AudioMgr.playSound("accept");
        return this.hasSave ? "continue" : "new_game";
      }
      return null;
    }

    draw(ctx, viewW, viewH, mx, my, isFullscreen) {
      if (Assets.titleBg) {
        ctx.drawImage(Assets.titleBg, 0, 0, viewW, viewH);
      } else {
        ctx.fillStyle = "#120e18";
        ctx.fillRect(0, 0, viewW, viewH);
      }

      const grad = ctx.createLinearGradient(0, 0, 0, viewH);
      grad.addColorStop(0, "rgba(10, 8, 16, 0.42)");
      grad.addColorStop(0.5, "rgba(10, 8, 16, 0.55)");
      grad.addColorStop(1, "rgba(10, 8, 16, 0.90)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, viewW, viewH);

      this.ash.draw(ctx);

      const bx = Math.max(48, Math.floor(viewW * 0.08));
      const titleY = Math.max(44, Math.floor(viewH * 0.14));

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(52, { bold: true });
      C.drawOutlinedText(ctx, "Ashes of Oakhaven", bx, titleY, C.COLOR_GOLD, "#120a08", "left");

      ctx.font = C.font(24, { bold: true });
      C.drawOutlinedText(ctx, "The Hollow Crown  —  2D Action RPG", bx + 3, titleY + 62, C.COLOR_WHITE, "#120a08", "left");

      ctx.font = C.font(13);
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.fillText("Aplikasi Perancangan Program Game — Kelompok 1 (Pure Web + PHP 7.2 Edition)", bx + 3, titleY + 98);

      for (const b of this._getButtons(viewW, viewH)) {
        const hover = C.pointInRect(mx, my, b.rect) && b.enabled;
        const bg = hover ? "rgba(165, 115, 35, 0.92)" : b.enabled ? "rgba(28, 30, 44, 0.86)" : "rgba(24, 24, 30, 0.68)";
        const border = b.enabled ? C.COLOR_GOLD : "#41414b";
        C.drawRoundedRect(ctx, b.rect.x, b.rect.y, b.rect.w, b.rect.h, 8, bg, border, 2);

        ctx.font = C.font(16, { bold: true });
        ctx.fillStyle = hover ? "#0f0f14" : b.enabled ? C.COLOR_WHITE : "#6e6e78";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(b.label, b.rect.x + b.rect.w / 2, b.rect.y + b.rect.h / 2);
      }

      const fsRect = this._getFullscreenButton(viewW);
      const fsHover = C.pointInRect(mx, my, fsRect);
      const fsLabel = isFullscreen ? "Ukuran Normal [F11]" : "Layar Penuh [F11]";
      C.drawRoundedRect(ctx, fsRect.x, fsRect.y, fsRect.w, fsRect.h, 8, fsHover ? "rgba(165, 115, 35, 0.92)" : "rgba(24, 28, 42, 0.85)", C.COLOR_GOLD, 2);
      ctx.font = C.font(13, { bold: true });
      ctx.fillStyle = fsHover ? "#0f0f14" : C.COLOR_WHITE;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(fsLabel, fsRect.x + fsRect.w / 2, fsRect.y + fsRect.h / 2);

      if (this.showControls) {
        ctx.fillStyle = "rgba(0, 0, 0, 0.78)";
        ctx.fillRect(0, 0, viewW, viewH);
        const pw = Math.min(600, viewW - 40);
        const ph = Math.min(430, viewH - 40);
        const px = Math.floor((viewW - pw) / 2);
        const py = Math.floor((viewH - ph) / 2);
        C.drawRoundedRect(ctx, px, py, pw, ph, 12, "#161822", C.COLOR_GOLD, 2);

        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.font = C.font(20, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fillText("PANDUAN KONTROL OAKHAVEN", px + 28, py + 22);

        const lines = [
          ["WASD / Panah", "Bergerak 8 arah (Top-Down)"],
          ["Shift Kiri (Tahan)", "Sprint (+40% Speed, konsumsi STA)"],
          ["Spasi", "Dodge Roll (15 STA, i-frame & Perfect Dodge Slow-Mo)"],
          ["Klik Kiri (LMB)", "Tebasan Pedang Ringan (5 STA)"],
          ["Klik Kanan (RMB)", "Skill Berat Ash Cleave (30 STA)"],
          ["E / B / 1-4 / TAB", "Interaksi / Tas / Item Hotbar / Minimap"],
          ["F11 / Alt+Enter", "Toggle Layar Penuh / Ukuran Normal"],
        ];
        for (let i = 0; i < lines.length; i++) {
          ctx.font = C.font(14, { bold: true });
          ctx.fillStyle = C.COLOR_GOLD;
          ctx.fillText(lines[i][0], px + 28, py + 72 + i * 38);
          ctx.font = C.font(14);
          ctx.fillStyle = C.COLOR_WHITE;
          ctx.fillText(lines[i][1], px + 205, py + 72 + i * 38);
        }

        ctx.font = C.font(12, { italic: true });
        ctx.fillStyle = C.COLOR_TEXT_MUTED;
        ctx.textAlign = "center";
        ctx.fillText("[Klik atau tekan tombol apa saja untuk kembali]", px + pw / 2, py + ph - 32);
      }
    }
  }

  class PrologScene {
    constructor() {
      this.slides = [
        {
          heading: "BABAK I: HUJAN ABU DI OAKHAVEN",
          speaker: "Ethan — Penyintas Terakhir",
          body1: "Langit berwarna merah berkarat tertutup asap pekat. Hujan abu menyelimuti puing-puing desa Oakhaven.",
          body2: "Ethan merangkak keluar dari reruntuhan kedai kayu. Di bawah kakinya tergeletak syal adiknya yang setengah hangus—ia mengikat syal itu erat di pergelangan tangannya.",
        },
        {
          heading: "BABAK II: BISIKAN ROH LELUHUR",
          speaker: "Roh Penjaga Oakhaven",
          body1: "\"Bangkitlah... Abu keluargamu menuntut jawaban. Angkat bilah leluhur ini atau biarkan namamu terkubur bersama bara.\"",
          body2: "Dari balik kabut, barisan monster berzirah leleh—para Karak—bergerak serentak menjaga empat Suar Kematian yang mengurung wilayah ini.",
        },
        {
          heading: "BABAK III: DINDING KEPUTUSASAAN",
          speaker: "Rawa Kematian & Jenderal Gargantua",
          body1: "Berbekal pedang usang, Ethan nekat menerobos Rawa Kematian demi membalas kehancuran kampung halamannya.",
          body2: "Namun tebasan Jenderal Gargantua menghantamnya hingga nyaris tak sadarkan diri! Tepat pada detik terakhir, ledakan asap hijau Aell membutakan monster itu dan menarik Ethan menjauh.",
        },
        {
          heading: "BABAK IV: SUAKA ORANG-ORANG BUANGAN",
          speaker: "Hub Rusty Anchor — Harapan Baru",
          body1: "Ethan terbangun di hadapan hangatnya Api Unggun Hub Rusty Anchor, tempat berkumpulnya para penyintas yang menolak tunduk pada kutukan.",
          body2: "Bicaralah dengan Vektor (Skill & Tempa), Aell (Peta), Gael (Toko Ramuan & Senjata), Elara, dan Brog untuk bersiap menaklukkan Dungeon 1 hingga Ruang Takhta!",
        },
      ];
      this.index = 0;
      this.ash = new AshParticleOverlay(55);
      this.elapsed = 0.0;
      this.slideTime = 0.0;
      this.charIdx = 0.0;
    }

    update(dt, viewW, viewH) {
      this.ash.update(dt, viewW, viewH);
      this.elapsed += dt;
      this.slideTime += dt;
      const cur = this.slides[this.index];
      const total = cur.body1.length + cur.body2.length;
      if (this.charIdx < total) {
        this.charIdx = Math.min(total, this.charIdx + 68.0 * dt);
      }
    }

    _next() {
      const cur = this.slides[this.index];
      const total = cur.body1.length + cur.body2.length;
      if (Math.floor(this.charIdx) < total) {
        this.charIdx = total;
        AudioMgr.playSound("dialogue_beep");
        return null;
      }
      AudioMgr.playSound("accept");
      this.index += 1;
      this.slideTime = 0.0;
      this.charIdx = 0.0;
      if (this.index >= this.slides.length) return "done";
      return null;
    }

    handleKey(code) {
      if (code === "Escape") return "done";
      if (code === "Space" || code === "Enter") return this._next();
      return null;
    }

    handleClick() {
      return this._next();
    }

    _drawStoryDiorama(ctx, px, dy, pw, dh) {
      const skyColors = ["#261012", "#161426", "#182218", "#221a14"];
      C.drawRoundedRect(ctx, px, dy, pw, dh, 12, skyColors[this.index % 4], C.COLOR_PANEL_BORDER_LIGHT, 2);

      // Ground strip
      ctx.fillStyle = "#121018";
      ctx.fillRect(px + 2, dy + dh - 36, pw - 4, 34);
      ctx.strokeStyle = "rgba(95, 78, 55, 0.72)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(px + 2, dy + dh - 36);
      ctx.lineTo(px + pw - 2, dy + dh - 36);
      ctx.stroke();

      const drawActor = (spriteKey, x, y, size, fps) => {
        Assets.drawSprite(ctx, spriteKey, this.elapsed, px + x, dy + y, size, size, fps || 6);
      };

      if (this.index === 0) {
        const glowR = 26 + Math.round(Math.sin(this.elapsed * 4) * 5);
        ctx.beginPath();
        ctx.arc(px + pw / 2 + 52, dy + dh - 28, glowR, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(180, 45, 35, 0.38)";
        ctx.fill();
        ctx.strokeStyle = "#dc3c32";
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(px + pw / 2 + 40, dy + dh - 28);
        ctx.lineTo(px + pw / 2 + 70, dy + dh - 34);
        ctx.stroke();
        const slideIn = Math.min(0.0, (this.slideTime - 0.5) * 80);
        drawActor("player_east", pw / 2 - 55 + slideIn, dh - 92, 76, 5);
      } else if (this.index === 1) {
        const pulse = 34 + Math.round(Math.sin(this.elapsed * 5) * 8);
        ctx.beginPath();
        ctx.arc(px + 150, dy + dh - 58, pulse, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(110, 210, 255, 0.28)";
        ctx.fill();
        drawActor("player_east", 112, dh - 92, 76, 6);
        for (let k = 0; k < 3; k++) {
          const kx = pw - 160 - k * 85 + Math.sin(this.elapsed * 2 + k) * 8;
          drawActor("monster1_west", kx, dh - 84, 68, 5.5);
        }
      } else if (this.index === 2) {
        const dash = Math.min(1.0, this.slideTime / 0.8);
        drawActor("player_east", 130 + dash * 95, dh - 92, 76, 8);
        drawActor("boss_gargantua_atk_west", pw - 220 - dash * 55, dh - 108, 96, 7);
        if (this.slideTime > 0.7) {
          const smokeR = 18 + Math.round((Math.sin(this.elapsed * 6) + 1) * 14);
          ctx.beginPath();
          ctx.arc(px + pw / 2 + 40, dy + dh - 56, smokeR, 0, Math.PI * 2);
          ctx.fillStyle = "rgba(95, 225, 130, 0.48)";
          ctx.fill();
          drawActor("npc_aell_east", 60 + Math.min(75, (this.slideTime - 0.7) * 90), dh - 88, 72, 7);
        }
      } else {
        const cx = pw / 2;
        const fr = 30 + Math.round(Math.sin(this.elapsed * 6) * 5);
        ctx.beginPath();
        ctx.arc(px + cx, dy + dh - 36, fr, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 145, 45, 0.30)";
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(px + cx - 10, dy + dh - 26);
        ctx.lineTo(px + cx + 10, dy + dh - 26);
        ctx.lineTo(px + cx, dy + dh - 56 - Math.round(Math.sin(this.elapsed * 9) * 5));
        ctx.closePath();
        ctx.fillStyle = "#ffc341";
        ctx.fill();

        drawActor("npc_vektor", cx - 170, dh - 94, 76, 4);
        drawActor("player_south", cx - 75, dh - 90, 76, 4);
        drawActor("npc_aell", cx + 35, dh - 88, 72, 3.5);
        drawActor("npc_gael", cx + 115, dh - 90, 72, 4);
      }
    }

    _drawWrapped(ctx, text, x, y, maxW, font, color) {
      ctx.font = font;
      ctx.fillStyle = color;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      const words = text.split(" ");
      const lines = [];
      let cur = "";
      for (const w of words) {
        const test = cur ? `${cur} ${w}` : w;
        if (ctx.measureText(test).width < maxW) cur = test;
        else {
          if (cur) lines.push(cur);
          cur = w;
        }
      }
      if (cur) lines.push(cur);
      for (let i = 0; i < Math.min(4, lines.length); i++) {
        ctx.fillText(lines[i], x, y + i * 24);
      }
    }

    draw(ctx, viewW, viewH) {
      ctx.fillStyle = "#0e0b12";
      ctx.fillRect(0, 0, viewW, viewH);
      this.ash.draw(ctx);

      const cur = this.slides[this.index];
      const pw = Math.min(920, viewW - 60);
      const dh = Math.min(148, Math.max(110, Math.round(viewH * 0.22)));
      const ph = Math.min(310, viewH - dh - 70);
      const totalH = dh + 14 + ph;
      const px = Math.floor((viewW - pw) / 2);
      const topY = Math.max(20, Math.floor((viewH - totalH) / 2));

      this._drawStoryDiorama(ctx, px, topY, pw, dh);

      const py = topY + dh + 14;
      ctx.save();
      ctx.globalAlpha = Math.min(1.0, this.slideTime / 0.25 + 0.35);
      C.drawRoundedRect(ctx, px, py, pw, ph, 14, C.COLOR_PANEL_BG, C.COLOR_GOLD, 2);
      ctx.restore();

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.font = C.font(21, { bold: true });
      ctx.fillStyle = C.COLOR_GOLD;
      ctx.fillText(cur.heading, px + 32, py + 24);

      ctx.font = C.font(13, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_ACCENT;
      ctx.fillText(cur.speaker, px + 32, py + 52);

      const shown = Math.floor(this.charIdx);
      const vis1 = cur.body1.slice(0, Math.min(cur.body1.length, shown));
      const vis2 = cur.body2.slice(0, Math.max(0, shown - cur.body1.length));
      this._drawWrapped(ctx, vis1, px + 32, py + 84, pw - 64, C.font(15), C.COLOR_WHITE);
      this._drawWrapped(ctx, vis2, px + 32, py + 166, pw - 64, C.font(14), "#d2d2e1");

      const bob = Math.round(Math.sin(this.elapsed * 5.0) * 3);
      ctx.font = C.font(12, { italic: true });
      ctx.fillStyle = C.COLOR_TEXT_MUTED;
      ctx.textAlign = "right";
      ctx.fillText(`Bab ${this.index + 1}/${this.slides.length}  |  [Klik / Spasi: Lanjut ->]  |  [ESC: Masuk ke Hub]`, px + pw - 28, py + ph - 32 + Math.floor(bob / 2));
    }
  }

  class EndingScene {
    constructor(player) {
      this.player = player;
      this.karma = player.karma || 0;
      this.isCursedWeapon = player.weapon_id === "bloodthirst_blade";
      this.qteProgress = 20.0;
      this.flashAlpha = 0.0;
      this.elapsed = 0.0;
      this.shakeTimer = 0.0;
      this.ash = new AshParticleOverlay(45);

      if (this.karma <= -30 || (this.isCursedWeapon && this.karma < 20)) {
        this.stage = "bad_epilogue";
        AudioMgr.stopMusic();
        AudioMgr.playSound("ending_bad");
      } else if (this.karma >= 20) {
        this.stage = "good_qte";
      } else {
        this.stage = "choice";
      }
    }

    _getLayout(viewW, viewH) {
      const pw = Math.min(900, viewW - 60);
      const ph = 480;
      const px = Math.floor((viewW - pw) / 2);
      const py = Math.max(24, Math.floor((viewH - 540) / 2));
      return { px, py, pw, ph };
    }

    _getChoiceRects(viewW, viewH) {
      const { py } = this._getLayout(viewW, viewH);
      return [
        { x: Math.floor(viewW / 2 - 330), y: py + 310, w: 300, h: 56 },
        { x: Math.floor(viewW / 2 + 30), y: py + 310, w: 300, h: 56 },
      ];
    }

    _getEndButtons(viewW, viewH) {
      const { py, ph } = this._getLayout(viewW, viewH);
      const by = py + ph + 16;
      return [
        { x: Math.floor(viewW / 2 - 260), y: by, w: 240, h: 48 },
        { x: Math.floor(viewW / 2 + 20), y: by, w: 240, h: 48 },
      ];
    }

    update(dt, viewW, viewH) {
      this.ash.update(dt, viewW, viewH);
      this.elapsed += dt;
      if (this.shakeTimer > 0) this.shakeTimer = Math.max(0.0, this.shakeTimer - dt);
      if (this.stage === "good_qte") {
        this.qteProgress = Math.max(0.0, this.qteProgress - 9.0 * dt);
      }
      if (this.flashAlpha > 0) this.flashAlpha = Math.max(0.0, this.flashAlpha - 180.0 * dt);
    }

    _triggerQteTap() {
      this.qteProgress = Math.min(100.0, this.qteProgress + 14.0);
      this.shakeTimer = 0.14;
      AudioMgr.playSound("slash1");
      if (this.qteProgress >= 100.0) {
        this.flashAlpha = 255.0;
        this.stage = "good_epilogue";
        AudioMgr.stopMusic();
        AudioMgr.playSound("ending_good");
      }
    }

    handleKey(code) {
      if (this.stage === "good_qte" && code === "Space") {
        this._triggerQteTap();
        return null;
      }
      if ((this.stage === "good_epilogue" || this.stage === "bad_epilogue") && code === "Escape") {
        return "hub";
      }
      return null;
    }

    handleClick(lx, ly, viewW, viewH) {
      if (this.stage === "choice") {
        const [btnGood, btnBad] = this._getChoiceRects(viewW, viewH);
        if (C.pointInRect(lx, ly, btnGood)) {
          AudioMgr.playSound("accept");
          this.stage = "good_qte";
        } else if (C.pointInRect(lx, ly, btnBad)) {
          AudioMgr.stopMusic();
          AudioMgr.playSound("ending_bad");
          this.stage = "bad_epilogue";
        }
        return null;
      }
      if (this.stage === "good_qte") {
        this._triggerQteTap();
        return null;
      }
      if (this.stage === "good_epilogue" || this.stage === "bad_epilogue") {
        const [btnHub, btnMenu] = this._getEndButtons(viewW, viewH);
        if (C.pointInRect(lx, ly, btnHub)) {
          AudioMgr.playSound("accept");
          return "hub";
        }
        if (C.pointInRect(lx, ly, btnMenu)) {
          AudioMgr.playSound("accept");
          return "menu";
        }
      }
      return null;
    }

    draw(ctx, viewW, viewH, mx, my) {
      ctx.fillStyle = this.stage === "good_epilogue" ? "#243048" : this.stage === "bad_epilogue" ? "#12080c" : "#0f0c16";
      ctx.fillRect(0, 0, viewW, viewH);
      this.ash.draw(ctx);

      const { px: basePx, py: basePy, pw, ph } = this._getLayout(viewW, viewH);
      const ox = this.shakeTimer > 0 ? Math.round(Math.random() * 8 - 4) : 0;
      const oy = this.shakeTimer > 0 ? Math.round(Math.random() * 8 - 4) : 0;
      const px = basePx + ox;
      const py = basePy + oy;

      const borderCol = this.stage === "good_epilogue" ? "#f0d278" : this.stage === "bad_epilogue" ? "#dc3c3c" : C.COLOR_GOLD;
      C.drawRoundedRect(ctx, px, py, pw, ph, 14, "rgba(18, 20, 30, 0.90)", borderCol, 2);

      if (this.stage === "choice" || this.stage === "good_qte") {
        const bob = Math.round(Math.sin(this.elapsed * 4.0) * 5);
        Assets.drawSprite(ctx, "boss_hollow_crown_walk_south", this.elapsed, px + pw - 138, py + 24 + bob, 88, 88, 6);
      } else if (this.stage === "good_epilogue") {
        ctx.beginPath();
        ctx.arc(px + pw - 95, py + 68, 42, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 225, 130, 0.32)";
        ctx.fill();
        Assets.drawSprite(ctx, "player_north", this.elapsed, px + pw - 130, py + 32, 72, 72, 5);
      } else {
        ctx.beginPath();
        ctx.arc(px + pw - 95, py + 68, 42, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(220, 30, 45, 0.35)";
        ctx.fill();
        Assets.drawSprite(ctx, "boss_hollow_crown_walk_south", this.elapsed, px + pw - 138, py + 24, 88, 88, 6);
      }

      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      if (this.stage === "choice") {
        ctx.font = C.font(24, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fillText("KLIMAKS: MAHKOTA KUTUKAN DI RUANG TAKHTA", px + 40, py + 36);

        ctx.font = C.font(15);
        ctx.fillStyle = C.COLOR_WHITE;
        const msg = "\"Wadah yang rapuh telah pecah... Kebencianmu menyala terang, Anak Oakhaven. Naiklah ke takhta, atau lawan dirimu sendiri.\"";
        ctx.fillText(msg.slice(0, 88), px + 40, py + 110);
        ctx.fillText(msg.slice(88), px + 40, py + 138);

        ctx.font = C.font(14, { italic: true });
        ctx.fillStyle = C.COLOR_TEXT_ACCENT;
        ctx.fillText(`Karma Saat Ini: ${this.karma}`, px + 40, py + 190);

        const [bGood, bBad] = this._getChoiceRects(viewW, viewH);
        for (const [r, lbl, col] of [
          [bGood, "Cabut Kutukan (Bilah Penebusan)", "#2d7391"],
          [bBad, "Raih Mahkota (Raja Iblis Baru)", "#91282d"],
        ]) {
          C.drawRoundedRect(ctx, r.x, r.y, r.w, r.h, 8, col, C.COLOR_GOLD, 2);
          ctx.font = C.font(14, { bold: true });
          ctx.fillStyle = C.COLOR_WHITE;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(lbl, r.x + r.w / 2, r.y + r.h / 2);
        }
      } else if (this.stage === "good_qte") {
        ctx.font = C.font(25, { bold: true });
        ctx.fillStyle = C.COLOR_TEXT_ACCENT;
        ctx.fillText("LAWAN TARIKAN MAHKOTA KUTUKAN!", px + 40, py + 40);

        ctx.font = C.font(15);
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.fillText("Siluet Vektor, Aell, dan Gael berdiri menopang punggung Ethan!", px + 40, py + 100);
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fillText("TEKAN [SPASI] ATAU [KLIK KIRI] BERKALI-KALI UNTUK MEMBELAH MAHKOTA!", px + 40, py + 145);

        ctx.save();
        ctx.globalAlpha = Math.min(1.0, (110 + this.qteProgress * 1.4) / 255);
        Assets.drawSprite(ctx, "npc_vektor", this.elapsed, px + pw / 2 - 140, py + 315, 64, 64, 4);
        Assets.drawSprite(ctx, "npc_aell", this.elapsed, px + pw / 2 - 40, py + 315, 60, 60, 4);
        Assets.drawSprite(ctx, "npc_gael", this.elapsed, px + pw / 2 + 60, py + 315, 64, 64, 4);
        ctx.restore();
        Assets.drawSprite(ctx, "player_north", this.elapsed, px + pw / 2 - 36, py + 322, 72, 72, 5);

        const barX = px + 90;
        const barY = py + 240;
        const barW = pw - 180;
        const barH = 38;
        C.drawRoundedRect(ctx, barX, barY, barW, barH, 8, "#232332", C.COLOR_GOLD, 2);
        const fillW = Math.round((barW - 4) * (this.qteProgress / 100.0));
        if (fillW > 0) C.drawRoundedRect(ctx, barX + 2, barY + 2, fillW, barH - 4, 6, "#6edcff", null);

        ctx.font = C.font(15, { bold: true });
        ctx.fillStyle = C.COLOR_WHITE;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(`${Math.floor(this.qteProgress)}%`, barX + barW / 2, barY + barH / 2);
      } else if (this.stage === "good_epilogue") {
        ctx.font = C.font(24, { bold: true });
        ctx.fillStyle = C.COLOR_GOLD;
        ctx.fillText("GOOD ENDING: BILAH PENEBUSAN (MENCABUT KUTUKAN)", px + 40, py + 36);
        const lines = [
          "Mahkota: \"KAU... KAU AKAN KOSONG TANPAKU! APA YANG TERSISA JIKA DENDAM INI MATI?!\"",
          "Ethan: \"...Sesuatu yang layak untuk dilindungi.\"",
          "",
          "Dengan ayunan vertikal Bilah Penebusan, Mahkota Abu terbelah dua. Cahaya matahari pagi menyinari",
          "ruang takhta untuk pertama kalinya. Syal adiknya kini bersih dari abu. Ethan melangkah pulang",
          "menuju Oakhaven Hub di mana Vektor, Aell, Gael, Elara, dan para penyintas menunggunya.",
          "",
          "\"Kutukan itu hancur bersama siklus kebencian. Kini saatnya untuk pulang.\"",
        ];
        ctx.font = C.font(15);
        for (let i = 0; i < lines.length; i++) {
          ctx.fillStyle = i === 7 ? C.COLOR_GOLD : C.COLOR_WHITE;
          ctx.fillText(lines[i], px + 40, py + 100 + i * 30);
        }
      } else {
        ctx.font = C.font(25, { bold: true });
        ctx.fillStyle = C.COLOR_CRIT;
        ctx.fillText("BAD ENDING: TAKHTA RAJA IBLIS BARU", px + 40, py + 36);
        const lines = [
          "Langkah Ethan membeku di luar kendali. Pedangnya jatuh berdenting di lantai cermin obsidian.",
          "Saat Mahkota Kutukan mendarat di kepalanya, syal adiknya terbakar menjadi abu dan tertiup angin.",
          "Mata Ethan menyala merah terang saat ia duduk di atas singgasana batu.",
          "",
          "Ethan / The Crown: \"Oakhaven telah menjadi abu... Biarkan seluruh dunia merasakan dingin yang sama.\"",
          "",
          "\"Dendam telah terbayar lunas. Sang Penguasa Abu telah mati... Hidup Raja yang baru.\"",
        ];
        ctx.font = C.font(15);
        for (let i = 0; i < lines.length; i++) {
          ctx.fillStyle = i === 6 ? C.COLOR_CRIT : C.COLOR_WHITE;
          ctx.fillText(lines[i], px + 40, py + 105 + i * 32);
        }
      }

      if (this.stage === "good_epilogue" || this.stage === "bad_epilogue") {
        ctx.font = C.font(12, { italic: true });
        ctx.fillStyle = C.COLOR_TEXT_MUTED;
        ctx.textAlign = "left";
        ctx.textBaseline = "top";
        ctx.fillText("Credits: Kelompok 1 — Aplikasi Perancangan Program Game", px + 40, py + ph - 45);

        const [btnHub, btnMenu] = this._getEndButtons(viewW, viewH);
        for (const [r, lbl] of [
          [btnHub, "Kembali ke Hub Oakhaven"],
          [btnMenu, "Menu Utama"],
        ]) {
          const hover = C.pointInRect(mx, my, r);
          C.drawRoundedRect(ctx, r.x, r.y, r.w, r.h, 8, hover ? "#a57323" : "#23283a", C.COLOR_GOLD, 2);
          ctx.font = C.font(14, { bold: true });
          ctx.fillStyle = C.COLOR_WHITE;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(lbl, r.x + r.w / 2, r.y + r.h / 2);
        }
      }

      if (this.flashAlpha > 0) {
        ctx.fillStyle = `rgba(255, 255, 255, ${(this.flashAlpha / 255).toFixed(3)})`;
        ctx.fillRect(0, 0, viewW, viewH);
      }
    }
  }

  global.OakhavenScenes = {
    AshParticleOverlay,
    TitleScreenScene,
    PrologScene,
    EndingScene,
  };
})(window);
