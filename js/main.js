(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;
  const SaveSys = global.OakhavenSave;
  const { Inventory } = global.OakhavenInventory;
  const { CombatManager } = global.OakhavenCombat;
  const { Player, WhiteFlame, MapPortal, createMapEntities } = global.OakhavenEntities;
  const { QuestManager, DialogueSystem, CartographyMapUI } = global.OakhavenQuest;
  const ShopManager = global.OakhavenShop;
  const UIManager = global.OakhavenUI;
  const { TitleScreenScene, PrologScene, EndingScene } = global.OakhavenScenes;

  const LOBBY_SPAWN = [584, 232];

  class GameEngine {
    constructor() {
      this.canvas = document.getElementById("game-canvas");
      this.ctx = this.canvas.getContext("2d");

      this.viewW = C.DEFAULT_WIDTH;
      this.viewH = C.DEFAULT_HEIGHT;
      this.isFullscreen = false;
      this.mousePos = [this.viewW / 2, this.viewH / 2];
      this.keys = {};

      this.gameState = "TITLE";
      this.currentMap = "map1safeworld.tmx";
      this.map = null;
      this.npcs = [];
      this.targets = [];

      this.player = null;
      this.inventory = null;
      this.combatMgr = null;
      this.questMgr = null;
      this.shopMgr = null;
      this.uiMgr = null;
      this.dialogueSys = null;
      this.worldMapUi = null;

      this.titleScene = null;
      this.prologScene = null;
      this.endingScene = null;

      this.lastTs = performance.now();
    }

    async init() {
      this._resizeCanvas();
      this._bindEvents();

      const overlay = document.getElementById("loading-overlay");
      const bar = document.getElementById("loading-bar");
      const status = document.getElementById("loading-status");

      await Assets.loadAll((pct, label) => {
        if (bar) bar.style.width = `${Math.round(pct * 100)}%`;
        if (status) status.textContent = `Memuat ${label}... ${Math.round(pct * 100)}%`;
      });

      await SaveSys.syncFromServer();
      this.titleScene = new TitleScreenScene(SaveSys.hasSave());

      if (overlay) {
        overlay.classList.add("hidden");
        setTimeout(() => {
          if (overlay && overlay.parentNode) overlay.style.display = "none";
        }, 400);
      }

      this._loop(performance.now());
    }

    _resizeCanvas() {
      const [lw, lh] = C.computeLogicalSize(window.innerWidth, window.innerHeight);
      this.viewW = lw;
      this.viewH = lh;
      if (this.canvas.width !== lw) this.canvas.width = lw;
      if (this.canvas.height !== lh) this.canvas.height = lh;
      this.ctx.imageSmoothingEnabled = false;
    }

    _toLogical(clientX, clientY) {
      const r = this.canvas.getBoundingClientRect();
      const lx = ((clientX - r.left) / Math.max(1, r.width)) * this.viewW;
      const ly = ((clientY - r.top) / Math.max(1, r.height)) * this.viewH;
      return [lx, ly];
    }

    toggleFullscreen() {
      if (!document.fullscreenElement) {
        const el = document.documentElement;
        if (el.requestFullscreen) {
          el.requestFullscreen().catch(() => {});
        }
      } else if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      }
    }

    _createNewWorld() {
      this.player = new Player(LOBBY_SPAWN[0], LOBBY_SPAWN[1]);
      this.inventory = new Inventory();
      this.combatMgr = new CombatManager();
      this.questMgr = new QuestManager();
      this.shopMgr = new ShopManager();
      this.uiMgr = new UIManager();
      this.dialogueSys = new DialogueSystem();
      this.worldMapUi = new CartographyMapUI();
    }

    switchMap(targetMap, targetX, targetY) {
      this.currentMap = targetMap;
      this.map = Assets.maps[targetMap] || Assets.maps["map1safeworld.tmx"];
      const spawned = createMapEntities(targetMap);
      this.npcs = spawned.npcs;
      this.targets = spawned.enemies;

      const cfg = C.STAGE_CONFIGS[targetMap] || {};
      const sx = targetX !== undefined && targetX !== null ? targetX : (cfg.spawn ? cfg.spawn[0] : LOBBY_SPAWN[0]);
      const sy = targetY !== undefined && targetY !== null ? targetY : (cfg.spawn ? cfg.spawn[1] : LOBBY_SPAWN[1]);
      this.player.x = sx;
      this.player.y = sy;
      this.player.vel_x = 0.0;
      this.player.vel_y = 0.0;
      this.combatMgr.clearTransientEntities();

      const bgmName = cfg.bgm || (targetMap === "map1safeworld.tmx" ? "bgm_village" : "bgm_dungeon");
      AudioMgr.playMusic(bgmName, targetMap === "map1safeworld.tmx" ? 0.28 : 0.25);

      const zoneName = cfg.name || targetMap;
      if (targetMap !== "map1safeworld.tmx") {
        this.uiMgr.showNotification(`${zoneName} — ${cfg.hazard || "Waspada Monster!"}`, 3.6);
      } else {
        this.uiMgr.showNotification(zoneName, 2.5);
      }
    }

    async _startNewGame() {
      this._createNewWorld();
      this.switchMap("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1]);
      this.prologScene = new PrologScene();
      this.gameState = "PROLOG";
      AudioMgr.playMusic("bgm_village", 0.22);
    }

    async _continueGame() {
      this._createNewWorld();
      const data = await SaveSys.loadGame();
      const mapName = SaveSys.applySaveData(data, this.player, this.inventory, this.questMgr);
      this.switchMap(mapName, this.player.x, this.player.y);
      this.gameState = "PLAYING";
      this.uiMgr.showNotification("Progress permainan berhasil dimuat!", 3.0);
    }

    _handleNpcInteraction(nearbyNpc) {
      if (!nearbyNpc) return;

      if (nearbyNpc instanceof MapPortal) {
        if (nearbyNpc.target_map === "stage2_spore.tmx" || nearbyNpc.target_map === "dungeon2.tmx") {
          const bossAlive = this.targets.some((t) => t.isBoss && t.isAlive());
          if (bossAlive) {
            this.uiMgr.showNotification("Kalahkan bos area ini terlebih dahulu untuk membuka portal lanjut!", 3.0);
            AudioMgr.playSound("cancel");
            return;
          }
        }
        AudioMgr.playSound("accept");
        this.switchMap(nearbyNpc.target_map, nearbyNpc.target_x, nearbyNpc.target_y);
        return;
      }

      if (nearbyNpc instanceof WhiteFlame) {
        this.uiMgr.showNotification("Api Putih: Tetap di dekat aura cahaya ini untuk memulihkan HP secara bertahap.", 3.0);
        return;
      }

      const name = nearbyNpc.name || "";
      if (name === "Api Unggun Oakhaven") {
        this.player.heal(this.player.max_hp);
        this.player.restoreStamina(this.player.max_stamina);
        AudioMgr.playSound("heal");
        SaveSys.saveGame(this.player, this.inventory, this.questMgr, "map1safeworld.tmx");
        this.uiMgr.showNotification("HP & Stamina pulih! Progress disimpan di Api Unggun.", 3.0);
        return;
      }

      if (name.startsWith("Vektor")) {
        this.shopMgr.openVektor();
        return;
      }
      if (name.startsWith("Aell")) {
        this.worldMapUi.open();
        return;
      }
      if (name.startsWith("Gael")) {
        this.shopMgr.openGael();
        return;
      }
      if (name.startsWith("Brog")) {
        this.shopMgr.openBrog();
        return;
      }

      if (name.startsWith("Elara")) {
        const pages = [
          "Ethan... Syukurlah Aell berhasil membawamu keluar dari Rawa Kematian.",
          "Para penyintas tersebar di seluruh kota: Vektor di barat laut (Bengkel Skill), Brog di kedai barat, Gael di pelabuhan barat daya (Toko Boost), dan Aell di pos timur!",
          "Perhatikan Minimap [TAB] di pojok kanan atas untuk melihat ikon mereka. Di dalam Dungeon 1-4, HP tidak pulih otomatis—cari Api Putih di sudut map atau bawa Ramuan dari Gael!",
        ];
        const choices = [
          [
            "Terima Petunjuk Misi",
            () => {
              this.questMgr.advanceProgress("q1_awaken", 1, this.player, this.combatMgr);
              this.dialogueSys.close();
              this.uiMgr.showNotification("Quest selesai! Buka Peta Aell atau kunjungi Vektor/Gael.");
            },
          ],
          [
            "Janji Lindungi Warga (+Karma)",
            () => {
              if (!this.player._helped_elara) {
                this.player._helped_elara = true;
                this.player.karma += 15;
                this.uiMgr.showNotification("Kau berjanji melindungi para penyintas Oakhaven (+Karma)!", 3.0);
              }
              this.questMgr.advanceProgress("q1_awaken", 1, this.player, this.combatMgr);
              this.dialogueSys.close();
            },
          ],
        ];
        this.dialogueSys.startDialogue(name, pages, nearbyNpc.portraitKey, choices);
        return;
      }

      if (name === "Kapten Penjaga Gerbang") {
        const pages = [
          "Gerbang Ekspedisi ini menuju Stage 1: Rawa Kematian tempat Jenderal Gargantua menunggu.",
          "Manfaatkan pohon mati/pilar untuk berlindung dari proyektil musuh, dan gunakan [Spasi] untuk Perfect Dodge Slow-Mo!",
          "Kau juga bisa menggunakan Peta Kartografi Aell untuk melompat cepat ke bioma yang sudah terbuka.",
        ];
        const choices = [
          [
            "Masuk Stage 1: Rawa Kematian",
            () => {
              this.dialogueSys.close();
              this.switchMap("stage1_swamp.tmx", 96, 608);
            },
          ],
          ["Tutup", () => this.dialogueSys.close()],
        ];
        this.dialogueSys.startDialogue(name, pages, nearbyNpc.portraitKey, choices);
        return;
      }

      if (name.startsWith("Leo")) {
        const pages = [
          "Kak Ethan! Api Unggun di alun-alun itu selalu menghangatkan kami sejak desa terbakar.",
          "Kalau stamina kakak habis di bawah 10, serangan bakal tertahan (Fatigue)! Tekan [2] buat minum Tonik Stamina cepat.",
        ];
        this.dialogueSys.startDialogue(name, pages, nearbyNpc.portraitKey);
        return;
      }

      if (name.startsWith("Aria")) {
        const pages = [
          "Desa Oakhaven hancur saat hujan abu turun... Tolong padamkan empat Suar Kematian agar kami bisa pulang.",
          "Vektor bilang jika kau memilih jalan Penebusan tanpa tergoda senjata terlarang Gael, fajar baru akan kembali.",
        ];
        this.dialogueSys.startDialogue(name, pages, nearbyNpc.portraitKey);
      }
    }

    _processKillQuests(killed) {
      for (const t of killed) {
        if (this.currentMap === "map1safeworld.tmx") {
          this.questMgr.advanceProgress("q2_training", 1, this.player, this.combatMgr);
        } else if (t.isBoss) {
          this.player.beacons_cleared.add(this.currentMap);
          SaveSys.saveGame(this.player, this.inventory, this.questMgr, this.currentMap);
          if (this.currentMap === "stage1_swamp.tmx") {
            this.questMgr.advanceProgress("q4_stage1", 1, this.player, this.combatMgr);
            this.uiMgr.showNotification("Suar Kematian 1 Padam! Stage 2: Hutan Spora kini terbuka di Peta Aell!", 4.5);
          } else if (this.currentMap === "stage2_spore.tmx") {
            this.questMgr.advanceProgress("q5_stage2", 1, this.player, this.combatMgr);
            this.uiMgr.showNotification("Suar Kematian 2 Padam! Stage 3: Tungku Gehenna terbuka di Peta Aell!", 4.5);
          } else if (this.currentMap === "stage3_gehenna.tmx") {
            this.questMgr.advanceProgress("q6_stage3", 1, this.player, this.combatMgr);
            this.uiMgr.showNotification("Suar Kematian 3 Padam! Stage 4: Benteng Salju Hitam terbuka!", 4.5);
          } else if (this.currentMap === "stage4_frost.tmx") {
            this.questMgr.advanceProgress("q7_stage4", 1, this.player, this.combatMgr);
            this.uiMgr.showNotification("Suar Kematian 4 Padam! Gerbang Ruang Takhta Obsidian terbuka!", 4.5);
          } else if (this.currentMap === "stage5_throne.tmx") {
            this.questMgr.advanceProgress("q8_stage5", 1, this.player, this.combatMgr);
            return "trigger_ending";
          } else if (this.currentMap === "dungeon1.tmx") {
            this.uiMgr.showNotification("Bos Dungeon 1 tumbang! Gerbang ke Dungeon 2 terbuka!", 4.0);
          } else if (this.currentMap === "dungeon2.tmx") {
            this.uiMgr.showNotification("Raja Iblis Dungeon 2 berhasil dikalahkan!", 4.0);
          }
        }
      }
      return null;
    }

    _findNearbyNpc() {
      let best = null;
      let bestDist = Infinity;
      const pcx = this.player.x + 24;
      const pcy = this.player.y + 24;
      for (const npc of this.npcs) {
        if (npc.isPlayerNear(this.player)) {
          const [nx, ny] = npc.getCenter();
          const d = Math.hypot(nx - pcx, ny - pcy);
          if (d < bestDist) {
            bestDist = d;
            best = npc;
          }
        }
      }
      return best;
    }

    _bindEvents() {
      window.addEventListener("resize", () => this._resizeCanvas());
      document.addEventListener("fullscreenchange", () => {
        this.isFullscreen = Boolean(document.fullscreenElement);
        this._resizeCanvas();
      });

      this.canvas.addEventListener("contextmenu", (e) => e.preventDefault());

      this.canvas.addEventListener("pointermove", (e) => {
        this.mousePos = this._toLogical(e.clientX, e.clientY);
      });

      this.canvas.addEventListener("mousedown", (e) => {
        AudioMgr.unlock();
        const [lx, ly] = this._toLogical(e.clientX, e.clientY);
        this.mousePos = [lx, ly];

        if (this.gameState === "TITLE" && this.titleScene && e.button === 0) {
          const act = this.titleScene.handleClick(lx, ly, this.viewW, this.viewH);
          if (act === "toggle_fullscreen") this.toggleFullscreen();
          else if (act === "new_game") this._startNewGame();
          else if (act === "continue") this._continueGame();
          return;
        }

        if (this.gameState === "PROLOG" && this.prologScene && e.button === 0) {
          if (this.prologScene.handleClick() === "done") {
            this.gameState = "PLAYING";
            AudioMgr.playMusic("bgm_village", 0.28);
            this.uiMgr.showNotification("Selamat datang di Hub Oakhaven! Bicara dengan Elara atau jelajahi kota [TAB].", 4.5);
          }
          return;
        }

        if (this.gameState === "ENDING" && this.endingScene && e.button === 0) {
          const act = this.endingScene.handleClick(lx, ly, this.viewW, this.viewH);
          if (act === "hub") {
            this.player.heal(this.player.max_hp);
            this.switchMap("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1]);
            SaveSys.saveGame(this.player, this.inventory, this.questMgr, "map1safeworld.tmx");
            this.gameState = "PLAYING";
          } else if (act === "menu") {
            SaveSys.saveGame(this.player, this.inventory, this.questMgr, "map1safeworld.tmx");
            this.titleScene = new TitleScreenScene(SaveSys.hasSave());
            this.gameState = "TITLE";
          }
          return;
        }

        if (this.gameState !== "PLAYING") return;

        if (this.player.is_dead) {
          if (e.button === 0 && C.pointInRect(lx, ly, this.uiMgr.getRespawnButtonRect(this.viewW, this.viewH))) {
            this._doRespawn();
          }
          return;
        }

        if (this.uiMgr.showHelp) {
          this.uiMgr.showHelp = false;
          return;
        }

        if (this.dialogueSys.isOpen) {
          this.dialogueSys.handleClick(lx, ly, this.viewW, this.viewH);
          return;
        }
        if (this.worldMapUi.isOpen) {
          this.worldMapUi.handleClick(lx, ly, this.player, (m, x, y) => this.switchMap(m, x, y), this.uiMgr, this.viewW, this.viewH);
          return;
        }
        if (this.shopMgr.isAnyOpen()) {
          this.shopMgr.handleClick(lx, ly, this.player, this.inventory, this.combatMgr, this.questMgr, this.viewW, this.viewH);
          return;
        }
        if (this.inventory.isOpen) {
          this.inventory.handleClick(lx, ly, this.player, this.combatMgr, this.viewW, this.viewH);
          return;
        }

        if (e.button === 0 && this.uiMgr.showTutorialCard && this.viewW >= 820) {
          if (C.pointInRect(lx, ly, this.uiMgr.getTutorialCloseRect(this.viewW, this.viewH))) {
            this.uiMgr.showTutorialCard = false;
            return;
          }
        }

        if (e.button === 0) {
          const hbRects = this.uiMgr.getHotbarItemRects(this.viewW, this.viewH);
          for (let i = 0; i < hbRects.length; i++) {
            if (C.pointInRect(lx, ly, hbRects[i])) {
              this.inventory.useHotbarSlot(i, this.player, this.combatMgr);
              return;
            }
          }
        }

        // Combat click
        const [camX, camY] = C.computeClampedCamera(
          this.player.x + 24 - this.viewW / 2,
          this.player.y + 24 - this.viewH / 2,
          this.map.width,
          this.map.height,
          this.viewW,
          this.viewH
        );
        const tierMult = (C.STAGE_CONFIGS[this.currentMap] && C.STAGE_CONFIGS[this.currentMap].tier_mult) || 1.0;
        const aliveBefore = new Set(this.targets.filter((t) => t.isAlive()));

        let attacked = false;
        if (e.button === 0) {
          attacked = this.combatMgr.performAttack(this.player, this.mousePos, camX, camY, this.targets, this.inventory, tierMult);
        } else if (e.button === 2) {
          attacked = this.combatMgr.performSkill(this.player, this.mousePos, camX, camY, this.targets, this.inventory, tierMult);
        }

        if (attacked) {
          const killedNow = [];
          for (const t of aliveBefore) {
            if (!t.isAlive()) killedNow.push(t);
          }
          if (killedNow.length > 0 && this._processKillQuests(killedNow) === "trigger_ending") {
            this.endingScene = new EndingScene(this.player);
            this.gameState = "ENDING";
          }
        }
      });

      window.addEventListener("keydown", (e) => {
        AudioMgr.unlock();
        const code = e.code;

        if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Tab", "F1"].includes(code)) {
          e.preventDefault();
        }
        this.keys[code] = true;

        if (code === "F11" || (e.altKey && code === "Enter")) {
          e.preventDefault();
          this.toggleFullscreen();
          return;
        }
        if (code === "KeyM") {
          AudioMgr.toggleMute();
          return;
        }

        if (this.gameState === "TITLE" && this.titleScene) {
          const act = this.titleScene.handleKey(code);
          if (act === "new_game") this._startNewGame();
          else if (act === "continue") this._continueGame();
          return;
        }

        if (this.gameState === "PROLOG" && this.prologScene) {
          if (this.prologScene.handleKey(code) === "done") {
            this.gameState = "PLAYING";
            AudioMgr.playMusic("bgm_village", 0.28);
            this.uiMgr.showNotification("Selamat datang di Hub Oakhaven! Bicara dengan Elara atau jelajahi kota [TAB].", 4.5);
          }
          return;
        }

        if (this.gameState === "ENDING" && this.endingScene) {
          const act = this.endingScene.handleKey(code);
          if (act === "hub") {
            this.player.heal(this.player.max_hp);
            this.switchMap("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1]);
            SaveSys.saveGame(this.player, this.inventory, this.questMgr, "map1safeworld.tmx");
            this.gameState = "PLAYING";
          }
          return;
        }

        if (this.gameState !== "PLAYING") return;

        if (this.player.is_dead) {
          if (code === "KeyR") this._doRespawn();
          return;
        }

        if (code === "Escape") {
          if (this.uiMgr.showHelp) this.uiMgr.showHelp = false;
          else if (this.dialogueSys.isOpen) this.dialogueSys.close();
          else if (this.worldMapUi.isOpen) this.worldMapUi.close();
          else if (this.shopMgr.isAnyOpen()) this.shopMgr.closeAll();
          else if (this.inventory.isOpen) this.inventory.toggle();
          return;
        }

        if (code === "KeyH") {
          this.uiMgr.toggleHelp();
          return;
        }
        if (code === "F1") {
          this.uiMgr.toggleTutorial();
          return;
        }
        if (code === "Tab") {
          if (this.worldMapUi.isOpen) this.worldMapUi.close();
          else this.uiMgr.toggleMinimap();
          return;
        }
        if (code === "KeyB" || code === "KeyI") {
          if (!this.dialogueSys.isOpen && !this.shopMgr.isAnyOpen() && !this.worldMapUi.isOpen) {
            this.inventory.toggle();
          }
          return;
        }

        if (this.dialogueSys.isOpen) {
          if (code === "Space" || code === "Enter" || code === "KeyE") this.dialogueSys.advance();
          return;
        }

        if (code === "KeyE") {
          if (this.worldMapUi.isOpen) {
            this.worldMapUi.close();
          } else if (this.shopMgr.isAnyOpen()) {
            this.shopMgr.closeAll();
          } else {
            this._handleNpcInteraction(this._findNearbyNpc());
          }
          return;
        }

        if (!this.shopMgr.isAnyOpen() && !this.worldMapUi.isOpen && !this.inventory.isOpen) {
          if (code === "Digit1") this.inventory.useHotbarSlot(0, this.player, this.combatMgr);
          else if (code === "Digit2") this.inventory.useHotbarSlot(1, this.player, this.combatMgr);
          else if (code === "Digit3") this.inventory.useHotbarSlot(2, this.player, this.combatMgr);
          else if (code === "Digit4") this.inventory.useHotbarSlot(3, this.player, this.combatMgr);
        }
      });

      window.addEventListener("keyup", (e) => {
        this.keys[e.code] = false;
      });
    }

    _doRespawn() {
      this.player.respawn(LOBBY_SPAWN[0], LOBBY_SPAWN[1], this.inventory);
      this.switchMap("map1safeworld.tmx", LOBBY_SPAWN[0], LOBBY_SPAWN[1]);
      SaveSys.saveGame(this.player, this.inventory, this.questMgr, "map1safeworld.tmx");
      this.uiMgr.showNotification("Kau bangkit di Api Unggun (-30% Ash & -50% Material).", 3.5);
    }

    _updatePlaying(dt) {
      this.uiMgr.update(dt);
      this.dialogueSys.update(dt);

      const overlayBlocking =
        this.dialogueSys.isOpen ||
        this.shopMgr.isAnyOpen() ||
        this.inventory.isOpen ||
        this.worldMapUi.isOpen ||
        this.uiMgr.showHelp;

      const enemyDt = this.player.perfect_dodge_slowmo_timer > 0 ? dt * 0.38 : dt;

      if (!overlayBlocking && !this.player.is_dead) {
        const moveDir = this.player.handleInput(this.keys);
        this.player.update(dt, this.map, moveDir, this.combatMgr);
      } else {
        this.player.update(dt, this.map, null, this.combatMgr);
      }

      for (const npc of this.npcs) {
        if (npc instanceof WhiteFlame) npc.update(dt, this.player, this.combatMgr);
        else npc.update(dt);
      }

      if (!overlayBlocking) {
        for (const t of this.targets) {
          t.update(enemyDt, this.player, this.map, this.combatMgr);
        }
        this.combatMgr.update(enemyDt, this.player, this.map);
      } else {
        this.combatMgr.update(dt * 0.25, this.player, this.map);
      }
    }

    _renderPlaying() {
      const ctx = this.ctx;
      ctx.fillStyle = C.COLOR_BG;
      ctx.fillRect(0, 0, this.viewW, this.viewH);

      const [baseCamX, baseCamY] = C.computeClampedCamera(
        this.player.x + 24 - this.viewW / 2,
        this.player.y + 24 - this.viewH / 2,
        this.map.width,
        this.map.height,
        this.viewW,
        this.viewH
      );
      const [sx, sy] = this.combatMgr.getShakeOffset();
      const camX = baseCamX + sx;
      const camY = baseCamY + sy;

      this.map.draw(ctx, camX, camY);

      const nearbyNpc = this._findNearbyNpc();
      for (const npc of this.npcs) {
        npc.draw(ctx, camX, camY, this.player);
      }
      for (const t of this.targets) {
        t.draw(ctx, camX, camY);
      }
      this.player.draw(ctx, camX, camY);
      this.combatMgr.draw(ctx, camX, camY);

      this.uiMgr.draw(
        ctx,
        this.viewW,
        this.viewH,
        this.player,
        this.combatMgr,
        this.questMgr,
        nearbyNpc,
        this.map,
        this.npcs,
        this.targets,
        this.inventory,
        this.currentMap
      );

      if (this.inventory.isOpen) {
        this.inventory.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1], this.player);
      }
      if (this.shopMgr.isAnyOpen()) {
        this.shopMgr.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1], this.player, this.inventory);
      }
      if (this.worldMapUi.isOpen) {
        this.worldMapUi.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1], this.player, this.currentMap);
      }
      if (this.dialogueSys.isOpen) {
        this.dialogueSys.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1]);
      }
    }

    _loop(now) {
      const dt = Math.min(0.05, Math.max(0.001, (now - this.lastTs) / 1000.0));
      this.lastTs = now;

      const ctx = this.ctx;
      ctx.imageSmoothingEnabled = false;

      if (this.gameState === "TITLE" && this.titleScene) {
        this.titleScene.update(dt, this.viewW, this.viewH);
        this.titleScene.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1], this.isFullscreen);
      } else if (this.gameState === "PROLOG" && this.prologScene) {
        this.prologScene.update(dt, this.viewW, this.viewH);
        this.prologScene.draw(ctx, this.viewW, this.viewH);
      } else if (this.gameState === "ENDING" && this.endingScene) {
        this.endingScene.update(dt, this.viewW, this.viewH);
        this.endingScene.draw(ctx, this.viewW, this.viewH, this.mousePos[0], this.mousePos[1]);
      } else if (this.gameState === "PLAYING") {
        this._updatePlaying(dt);
        this._renderPlaying();
      }

      requestAnimationFrame((ts) => this._loop(ts));
    }
  }

  window.addEventListener("DOMContentLoaded", () => {
    const engine = new GameEngine();
    global.OakhavenGame = engine;
    engine.init().catch((err) => {
      console.error("[Oakhaven] Init error:", err);
    });
  });
})(window);
