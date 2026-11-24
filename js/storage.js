(function (global) {
  "use strict";

  const LS_PLAYER_ID_KEY = "oakhaven_player_id";
  const LS_SAVE_KEY = "oakhaven_save_v1";

  function generatePlayerId() {
    const rand = Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-6);
    return `oak_${rand}`.replace(/[^a-zA-Z0-9_-]/g, "").slice(0, 32);
  }

  const SaveSystem = {
    serverCachedData: null,

    getPlayerId() {
      let pid = "";
      try {
        pid = global.localStorage.getItem(LS_PLAYER_ID_KEY) || "";
      } catch (_) {}
      if (!/^[a-zA-Z0-9_-]{8,48}$/.test(pid)) {
        pid = generatePlayerId();
        try {
          global.localStorage.setItem(LS_PLAYER_ID_KEY, pid);
        } catch (_) {}
      }
      return pid;
    },

    buildPayload(player, inventory, questMgr, currentMap) {
      return {
        current_map: currentMap || "map1safeworld.tmx",
        player: {
          x: player.x,
          y: player.y,
          hp: player.hp,
          max_hp: player.max_hp,
          stamina: player.stamina,
          max_stamina: player.max_stamina,
          level: player.level,
          exp: player.exp,
          exp_to_next: player.exp_to_next,
          base_damage: player.base_damage,
          armor: player.armor,
          bonus_damage: player.bonus_damage,
          speed_bonus: player.speed_bonus,
          gold: player.gold,
          monster_ash: player.monster_ash,
          skill_points: player.skill_points,
          karma: player.karma,
          weapon_id: player.weapon_id,
          skill_levels: Object.assign({}, player.skill_levels),
          beacons_cleared: Array.from(player.beacons_cleared || []),
        },
        inventory: inventory.slots.map((s) => (s ? [s.id, s.count] : null)),
        hotbar_ids: inventory.hotbarIds.slice(0, 4),
        quests: questMgr.quests.map((q) => ({
          id: q.id,
          current_count: q.current_count,
          is_completed: q.is_completed,
          is_claimed: q.is_claimed,
        })),
        saved_at: new Date().toISOString(),
      };
    },

    hasSave() {
      if (this.serverCachedData) return true;
      try {
        const raw = global.localStorage.getItem(LS_SAVE_KEY);
        return Boolean(raw && JSON.parse(raw));
      } catch (_) {
        return false;
      }
    },

    getLocalSave() {
      try {
        const raw = global.localStorage.getItem(LS_SAVE_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch (_) {
        return null;
      }
    },

    async syncFromServer() {
      const pid = this.getPlayerId();
      try {
        const resp = await fetch(`api/load.php?player_id=${encodeURIComponent(pid)}`, {
          cache: "no-store",
        });
        if (!resp.ok) return this.getLocalSave();
        const json = await resp.json();
        if (json && json.ok && json.data) {
          this.serverCachedData = json.data;
          try {
            global.localStorage.setItem(LS_SAVE_KEY, JSON.stringify(json.data));
          } catch (_) {}
          return json.data;
        }
      } catch (_) {}
      return this.getLocalSave();
    },

    saveGame(player, inventory, questMgr, currentMap) {
      const payload = this.buildPayload(player, inventory, questMgr, currentMap);
      this.serverCachedData = payload;
      try {
        global.localStorage.setItem(LS_SAVE_KEY, JSON.stringify(payload));
      } catch (_) {}

      const pid = this.getPlayerId();
      fetch("api/save.php", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_id: pid, data: payload }),
      }).catch(() => {});
      return true;
    },

    async loadGame() {
      const local = this.getLocalSave();
      const server = await this.syncFromServer();
      return server || local;
    },

    applySaveData(data, player, inventory, questMgr) {
      if (!data) return "map1safeworld.tmx";
      const p = data.player || {};
      if (p.level !== undefined) player.level = p.level;
      if (p.exp !== undefined) player.exp = p.exp;
      if (p.exp_to_next !== undefined) player.exp_to_next = p.exp_to_next;
      if (p.max_hp !== undefined) player.max_hp = p.max_hp;
      player.hp = Math.min(player.max_hp, p.hp !== undefined ? p.hp : player.max_hp);
      player.hp_trail = player.hp;
      if (p.max_stamina !== undefined) player.max_stamina = p.max_stamina;
      player.stamina = Math.min(player.max_stamina, p.stamina !== undefined ? p.stamina : player.max_stamina);
      if (p.base_damage !== undefined) player.base_damage = p.base_damage;
      if (p.armor !== undefined) player.armor = p.armor;
      if (p.bonus_damage !== undefined) player.bonus_damage = p.bonus_damage;
      if (p.speed_bonus !== undefined) player.speed_bonus = p.speed_bonus;
      if (p.gold !== undefined) player.gold = p.gold;
      if (p.monster_ash !== undefined) player.monster_ash = p.monster_ash;
      if (p.skill_points !== undefined) player.skill_points = p.skill_points;
      if (p.karma !== undefined) player.karma = p.karma;
      if (p.weapon_id) player.equipWeapon(p.weapon_id);
      if (p.skill_levels) Object.assign(player.skill_levels, p.skill_levels);
      player.beacons_cleared = new Set(p.beacons_cleared || []);
      if (p.x !== undefined) player.x = Number(p.x);
      if (p.y !== undefined) player.y = Number(p.y);

      if (Array.isArray(data.inventory)) {
        inventory.slots = new Array(inventory.maxSlots).fill(null);
        for (let i = 0; i < Math.min(inventory.maxSlots, data.inventory.length); i++) {
          const entry = data.inventory[i];
          if (entry && entry[0]) {
            inventory.slots[i] = { id: entry[0], count: entry[1] || 1 };
          }
        }
      }
      if (Array.isArray(data.hotbar_ids)) {
        inventory.hotbarIds = data.hotbar_ids.slice(0, 4);
      }

      if (Array.isArray(data.quests)) {
        const qMap = {};
        for (const qs of data.quests) {
          qMap[qs.id] = qs;
        }
        for (const q of questMgr.quests) {
          const saved = qMap[q.id];
          if (saved) {
            q.current_count = saved.current_count || 0;
            q.is_completed = Boolean(saved.is_completed);
            q.is_claimed = Boolean(saved.is_claimed);
          }
        }
      }

      return data.current_map || "map1safeworld.tmx";
    },
  };

  global.OakhavenSave = SaveSystem;
})(window);
