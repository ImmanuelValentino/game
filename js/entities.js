(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;
  const { FloatingText, SlashEffect } = global.OakhavenCombat;

  class Player {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.width = 48;
      this.height = 48;
      this.hitbox_offset_x = 17;
      this.hitbox_offset_y = 36;
      this.hitbox_w = 14;
      this.hitbox_h = 10;

      const s1 = C.computeLevelStats(1);
      this.level = 1;
      this.exp = 0;
      this.exp_to_next = s1.exp_to_next;

      this.max_hp = s1.max_hp;
      this.hp = s1.max_hp;
      this.hp_trail = s1.max_hp;
      this.max_stamina = s1.max_stamina;
      this.stamina = s1.max_stamina;
      this.stamina_regen = C.STAMINA_REGEN_RATE;
      this.stamina_regen_delay = 0.0;

      this.base_damage = s1.base_atk;
      this._armor = s1.base_def;
      this.bonus_damage = 0;
      this.crit_chance = 0.22;

      this.atk_boost_mult = 1.0;
      this.atk_boost_timer = 0.0;
      this.def_boost_flat = 0;
      this.def_boost_timer = 0.0;
      this.crit_boost_flat = 0.0;
      this.crit_boost_timer = 0.0;
      this.in_white_fire = false;

      this.base_speed = 185.0;
      this.speed_bonus = 0.0;
      this.is_sprinting = false;

      this.gold = 80;
      this.monster_ash = 15;
      this.skill_points = 0;
      this.karma = 0;
      this.weapon_id = "ancestral_blade";
      this.skill_levels = { power: 0, stamina: 0, defense: 0, blade: 0 };
      this.beacons_cleared = new Set();

      this.direction = "south";
      this.frame_index = 0.0;
      this.anim_speed = 10.0;
      this.is_moving = false;
      this.vel_x = 0.0;
      this.vel_y = 0.0;

      this.is_rolling = false;
      this.roll_speed = 420.0;
      this.roll_duration = 0.25;
      this.roll_timer = 0.0;
      this.roll_cooldown = 0.45;
      this.roll_cd_timer = 0.0;
      this.roll_dir_x = 0.0;
      this.roll_dir_y = 0.0;
      this.ghost_trails = [];

      this.is_invincible = false;
      this.invincible_timer = 0.0;
      this.perfect_dodge_ready = false;
      this.dodged_last_hit = false;
      this.perfect_dodge_slowmo_timer = 0.0;
      this.next_attack_crit_buff = false;
      this.hurt_flash_timer = 0.0;
      this.stagger_timer = 0.0;
      this.is_dead = false;

      this.knockback_vx = 0.0;
      this.knockback_vy = 0.0;

      this.active_hazards = new Set();
      this.has_hazard_debuff = false;
      this.hazard_dot_timer = 0.0;
      this.lava_dot_timer = 0.0;
      this._helped_elara = false;
    }

    get armor() {
      return this._armor + this.skill_levels.defense * 5 + (this.def_boost_timer > 0 ? this.def_boost_flat : 0);
    }

    set armor(val) {
      this._armor = val | 0;
    }

    get weaponInfo() {
      return C.WEAPON_DATABASE[this.weapon_id] || C.WEAPON_DATABASE.ancestral_blade;
    }

    get weaponAtk() {
      return this.weaponInfo.weapon_atk;
    }

    get dropMultiplier() {
      return this.weaponInfo.drop_mult;
    }

    get totalDamage() {
      const raw = this.base_damage + this.weaponAtk + this.bonus_damage + this.skill_levels.power * 12;
      return Math.round(raw * this.atk_boost_mult);
    }

    get effectiveCritChance() {
      return Math.min(0.95, this.crit_chance + this.crit_boost_flat);
    }

    applyAtkBoost(mult, duration) {
      this.atk_boost_mult = Math.max(this.atk_boost_mult, mult || C.ATTACK_BOOST_MULT);
      this.atk_boost_timer = duration || C.ATTACK_BOOST_DURATION;
    }

    applyDefBoost(bonus, duration) {
      this.def_boost_flat = Math.max(this.def_boost_flat, bonus || C.DEFENSE_BOOST_FLAT);
      this.def_boost_timer = duration || C.DEFENSE_BOOST_DURATION;
    }

    applyCritBoost(bonus, duration) {
      this.crit_boost_flat = Math.max(this.crit_boost_flat, bonus || C.CRIT_BOOST_FLAT);
      this.crit_boost_timer = duration || C.CRIT_BOOST_DURATION;
    }

    get skillLevel() {
      return 1 + Object.values(this.skill_levels).reduce((a, b) => a + b, 0);
    }

    get is_fatigued() {
      return this.stamina < 10.0;
    }

    get speed() {
      let spd = this.base_speed + this.speed_bonus;
      if (this.is_sprinting) spd *= 1.4;
      if (this.active_hazards.has("sinkhole")) spd *= 0.45;
      else if (this.active_hazards.has("mud")) spd *= 0.7;
      return spd;
    }

    equipWeapon(weaponId) {
      if (C.WEAPON_DATABASE[weaponId]) {
        this.weapon_id = weaponId;
        return true;
      }
      return false;
    }

    consumeStamina(amount) {
      this.stamina = Math.max(0.0, this.stamina - amount);
      this.stamina_regen_delay = C.STAMINA_REGEN_DELAY;
    }

    getHitbox() {
      return {
        x: Math.round(this.x + this.hitbox_offset_x),
        y: Math.round(this.y + this.hitbox_offset_y),
        w: this.hitbox_w,
        h: this.hitbox_h,
      };
    }

    handleInput(keys) {
      if (this.is_dead || this.is_rolling || this.stagger_timer > 0) {
        this.is_sprinting = false;
        return null;
      }
      let dx = 0.0;
      let dy = 0.0;
      if (keys.KeyW || keys.ArrowUp) dy -= 1.0;
      if (keys.KeyS || keys.ArrowDown) dy += 1.0;
      if (keys.KeyA || keys.ArrowLeft) dx -= 1.0;
      if (keys.KeyD || keys.ArrowRight) dx += 1.0;

      if (dx !== 0 && dy !== 0) {
        dx *= 0.7071;
        dy *= 0.7071;
      }
      this.is_moving = dx !== 0 || dy !== 0;

      if (dx > 0) this.direction = "east";
      else if (dx < 0) this.direction = "west";
      else if (dy < 0) this.direction = "north";
      else if (dy > 0) this.direction = "south";

      const wantsSprint = (keys.ShiftLeft || keys.ShiftRight) && this.is_moving && this.stamina > 2.0;
      this.is_sprinting = Boolean(wantsSprint);

      if (keys.Space && this.roll_cd_timer <= 0) {
        if (this.stamina >= C.DODGE_ROLL_STAMINA) {
          this.startRoll(dx, dy);
          return null;
        }
      }
      return [dx, dy];
    }

    startRoll(moveDx, moveDy) {
      this.is_rolling = true;
      this.is_sprinting = false;
      this.roll_timer = this.roll_duration;
      this.roll_cd_timer = this.roll_cooldown;
      this.is_invincible = true;
      this.invincible_timer = this.roll_duration + 0.08;
      this.perfect_dodge_ready = true;
      this.consumeStamina(C.DODGE_ROLL_STAMINA);
      AudioMgr.playSound("roll");

      if (moveDx !== 0 || moveDy !== 0) {
        this.roll_dir_x = moveDx;
        this.roll_dir_y = moveDy;
      } else {
        const dirs = { east: [1, 0], west: [-1, 0], north: [0, -1], south: [0, 1] };
        const v = dirs[this.direction] || [0, 1];
        this.roll_dir_x = v[0];
        this.roll_dir_y = v[1];
      }
    }

    update(dt, map, moveDir, combatMgr) {
      if (this.is_dead) return;

      if (this.roll_cd_timer > 0) this.roll_cd_timer = Math.max(0.0, this.roll_cd_timer - dt);
      if (this.invincible_timer > 0) {
        this.invincible_timer = Math.max(0.0, this.invincible_timer - dt);
        if (this.invincible_timer === 0) this.is_invincible = false;
      }
      if (this.hurt_flash_timer > 0) this.hurt_flash_timer = Math.max(0.0, this.hurt_flash_timer - dt);
      if (this.stagger_timer > 0) this.stagger_timer = Math.max(0.0, this.stagger_timer - dt);
      if (this.perfect_dodge_slowmo_timer > 0) this.perfect_dodge_slowmo_timer = Math.max(0.0, this.perfect_dodge_slowmo_timer - dt);

      if (this.atk_boost_timer > 0) {
        this.atk_boost_timer = Math.max(0.0, this.atk_boost_timer - dt);
        if (this.atk_boost_timer === 0.0) this.atk_boost_mult = 1.0;
      }
      if (this.def_boost_timer > 0) {
        this.def_boost_timer = Math.max(0.0, this.def_boost_timer - dt);
        if (this.def_boost_timer === 0.0) this.def_boost_flat = 0;
      }
      if (this.crit_boost_timer > 0) {
        this.crit_boost_timer = Math.max(0.0, this.crit_boost_timer - dt);
        if (this.crit_boost_timer === 0.0) this.crit_boost_flat = 0.0;
      }

      this.in_white_fire = false;

      const [hazards, convVx] = map ? map.getHazardsAt(this.getHitbox()) : [new Set(), 0];
      this.active_hazards = hazards;
      this.has_hazard_debuff = hazards.has("poison") || hazards.has("acid");

      if (this.is_sprinting && !this.is_rolling) {
        const drainRate = hazards.has("mud") ? 20.0 : 10.0;
        this.consumeStamina(drainRate * dt);
        if (this.stamina <= 0) this.is_sprinting = false;
      }

      let regenDt = dt;
      if (this.stamina_regen_delay > 0) {
        const usedDt = Math.min(dt, this.stamina_regen_delay);
        this.stamina_regen_delay = Math.max(0.0, this.stamina_regen_delay - usedDt);
        regenDt = dt - usedDt;
      }
      if (regenDt > 0 && !this.is_rolling && !this.is_sprinting) {
        const regen = this.stamina_regen + this.skill_levels.stamina * 2.5;
        this.stamina = Math.min(this.max_stamina, this.stamina + regen * regenDt);
      }

      if (this.hp_trail > this.hp) this.hp_trail = Math.max(this.hp, this.hp_trail - 35.0 * dt);
      else this.hp_trail = this.hp;

      if (this.is_rolling) {
        this._moveWithCollision(this.roll_dir_x * this.roll_speed * dt, this.roll_dir_y * this.roll_speed * dt, map);
        this.ghost_trails.push({
          x: this.x,
          y: this.y,
          dir: this.direction,
          frameIdx: Math.floor(this.frame_index),
          alpha: 0.7,
        });
        this.roll_timer -= dt;
        if (this.roll_timer <= 0) this.is_rolling = false;
      } else if (hazards.has("ice")) {
        const tvx = moveDir ? moveDir[0] * this.speed : 0.0;
        const tvy = moveDir ? moveDir[1] * this.speed : 0.0;
        const accel = Math.min(1.0, 3.2 * dt);
        this.vel_x += (tvx - this.vel_x) * accel;
        this.vel_y += (tvy - this.vel_y) * accel;
        if (Math.abs(this.vel_x) > 1.0 || Math.abs(this.vel_y) > 1.0) {
          this._moveWithCollision(this.vel_x * dt, this.vel_y * dt, map);
        }
      } else if (moveDir) {
        this.vel_x = moveDir[0] * this.speed;
        this.vel_y = moveDir[1] * this.speed;
        this._moveWithCollision(this.vel_x * dt, this.vel_y * dt, map);
      } else {
        this.vel_x = 0.0;
        this.vel_y = 0.0;
      }

      if (convVx !== 0.0) {
        this._moveWithCollision(convVx * dt, 0.0, map);
      }

      if (Math.abs(this.knockback_vx) > 1.0 || Math.abs(this.knockback_vy) > 1.0) {
        this._moveWithCollision(this.knockback_vx * dt, this.knockback_vy * dt, map);
        const decay = Math.max(0.0, 1.0 - 10.0 * dt);
        this.knockback_vx *= decay;
        this.knockback_vy *= decay;
      } else {
        this.knockback_vx = 0.0;
        this.knockback_vy = 0.0;
      }

      if (this.has_hazard_debuff) {
        this.hazard_dot_timer += dt;
        if (this.hazard_dot_timer >= 1.5) {
          this.hazard_dot_timer = 0.0;
          this._applyHazardDamage(3, "RACUN", "#8ce678", combatMgr);
        }
      } else {
        this.hazard_dot_timer = 0.0;
      }

      if (hazards.has("lava") && !this.is_invincible) {
        this.lava_dot_timer += dt;
        if (this.lava_dot_timer >= 0.75) {
          this.lava_dot_timer = 0.0;
          this._applyHazardDamage(10, "LAHAR!", "#ff6e28", combatMgr);
        }
      } else {
        this.lava_dot_timer = 0.0;
      }

      if (this.is_moving || this.is_rolling) {
        this.frame_index += this.anim_speed * (this.is_sprinting ? 1.3 : 1.0) * dt;
      } else {
        this.frame_index = 0.0;
      }

      for (const g of this.ghost_trails) g.alpha -= 2.35 * dt;
      this.ghost_trails = this.ghost_trails.filter((g) => g.alpha > 0);
    }

    _applyHazardDamage(rawDmg, label, color, combatMgr) {
      if (this.is_dead) return;
      this.hp = Math.max(0, this.hp - rawDmg);
      this.hurt_flash_timer = 0.14;
      if (combatMgr) {
        combatMgr.floatingTexts.push(new FloatingText(this.x + 24, this.y - 12, `-${rawDmg} ${label}`, color, 15));
      }
      if (this.hp <= 0) {
        this.is_dead = true;
        AudioMgr.playSound("gameover");
      }
    }

    _moveWithCollision(stepX, stepY, map) {
      if (!map) {
        this.x += stepX;
        this.y += stepY;
        return;
      }
      const cur = this.getHitbox();
      if (map.isBlocked(cur)) {
        for (let r = 2; r < 60; r += 4) {
          let found = false;
          const offsets = [[0, -r], [0, r], [-r, 0], [r, 0], [-r, -r], [r, -r], [-r, r], [r, r]];
          for (const [ox, oy] of offsets) {
            if (!map.isBlocked({ x: cur.x + ox, y: cur.y + oy, w: cur.w, h: cur.h })) {
              this.x += ox;
              this.y += oy;
              found = true;
              break;
            }
          }
          if (found) break;
        }
      }

      if (stepX !== 0) {
        this.x += stepX;
        if (map.isBlocked(this.getHitbox())) {
          this.x -= stepX;
          this.vel_x = 0.0;
        }
      }
      if (stepY !== 0) {
        this.y += stepY;
        if (map.isBlocked(this.getHitbox())) {
          this.y -= stepY;
          this.vel_y = 0.0;
        }
      }
    }

    gainExp(amount) {
      this.exp += amount;
      let leveled = false;
      while (this.exp >= this.exp_to_next) {
        this.exp -= this.exp_to_next;
        this.level += 1;
        const prev = C.computeLevelStats(this.level - 1);
        const next = C.computeLevelStats(this.level);
        this.exp_to_next = next.exp_to_next;

        this.max_hp += Math.max(10, next.max_hp - prev.max_hp);
        this.max_stamina += Math.max(2, next.max_stamina - prev.max_stamina);
        this.base_damage += Math.max(2, next.base_atk - prev.base_atk);
        this._armor += Math.max(1, next.base_def - prev.base_def);

        this.hp = this.max_hp;
        this.hp_trail = this.max_hp;
        this.stamina = this.max_stamina;
        leveled = true;
        AudioMgr.playSound("levelup");
      }
      return leveled;
    }

    heal(amount) {
      const old = this.hp;
      this.hp = Math.min(this.max_hp, this.hp + amount);
      this.hp_trail = this.hp;
      AudioMgr.playSound("heal");
      return this.hp - old;
    }

    restoreStamina(amount) {
      this.stamina = Math.min(this.max_stamina, this.stamina + amount);
    }

    applyKnockback(vx, vy) {
      if (!this.is_invincible && !this.is_dead) {
        this.knockback_vx = vx;
        this.knockback_vy = vy;
      }
    }

    takeDamage(enemyAtk) {
      if (this.is_dead) return 0;
      if (this.is_invincible) {
        if (this.perfect_dodge_ready) {
          this.perfect_dodge_ready = false;
          this.dodged_last_hit = true;
          this.restoreStamina(15.0);
          this.perfect_dodge_slowmo_timer = 1.5;
          this.next_attack_crit_buff = true;
          AudioMgr.playSound("parry");
        }
        return 0;
      }
      this.dodged_last_hit = false;
      const fatiguePen = this.is_fatigued ? 1.2 : 1.0;
      const hazardPen = this.has_hazard_debuff ? 1.15 : 1.0;
      const denom = this.armor * 0.5 + 10.0;
      const eff = Math.max(1, Math.round((enemyAtk / denom) * hazardPen * fatiguePen));

      this.hp = Math.max(0, this.hp - eff);
      this.hurt_flash_timer = 0.2;
      AudioMgr.playSound(Math.random() < 0.5 ? "hit1" : "hit2");
      if (this.hp <= 0) {
        this.is_dead = true;
        AudioMgr.playSound("gameover");
      }
      return eff;
    }

    respawn(spawnX, spawnY, inventory) {
      this.x = spawnX !== undefined ? spawnX : 584;
      this.y = spawnY !== undefined ? spawnY : 232;
      this.vel_x = 0.0;
      this.vel_y = 0.0;
      this.hp = this.max_hp;
      this.hp_trail = this.max_hp;
      this.stamina = this.max_stamina;
      this.stamina_regen_delay = 0.0;
      this.is_dead = false;
      this.is_rolling = false;
      this.roll_timer = 0.0;
      this.is_invincible = false;
      this.invincible_timer = 0.0;
      this.hurt_flash_timer = 0.0;
      this.knockback_vx = 0.0;
      this.knockback_vy = 0.0;
      this.monster_ash = Math.floor(this.monster_ash * 0.7);
      if (inventory) inventory.penalizeOnDeath();
    }

    draw(ctx, camX, camY) {
      for (const g of this.ghost_trails) {
        ctx.save();
        ctx.globalAlpha = Math.max(0, g.alpha);
        Assets.drawSpriteFrame(ctx, `player_${g.dir}`, g.frameIdx, g.x - camX, g.y - camY, 48, 48);
        ctx.restore();
      }

      const dx = Math.round(this.x - camX);
      const dy = Math.round(this.y - camY);

      ctx.beginPath();
      ctx.ellipse(dx + 24, dy + 42, 13, 5, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,0,0,0.4)";
      ctx.fill();

      if (this.atk_boost_timer > 0) {
        ctx.beginPath();
        ctx.arc(dx + 24, dy + 24, 24, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 110, 50, 0.25)";
        ctx.fill();
      }
      if (this.def_boost_timer > 0) {
        ctx.beginPath();
        ctx.arc(dx + 24, dy + 24, 22, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(110, 185, 255, 0.75)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      if (this.next_attack_crit_buff || this.crit_boost_timer > 0) {
        ctx.beginPath();
        ctx.arc(dx + 24, dy + 24, 20, 0, Math.PI * 2);
        ctx.strokeStyle = "#ffe664";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      ctx.save();
      if (this.is_invincible && Math.floor(this.invincible_timer * 20) % 2 === 0) {
        ctx.globalAlpha = 0.5;
      }
      Assets.drawSpriteFrame(ctx, `player_${this.direction}`, Math.floor(this.frame_index), dx, dy, 48, 48);
      if (this.hurt_flash_timer > 0) {
        ctx.fillStyle = "rgba(255, 70, 70, 0.45)";
        ctx.fillRect(dx + 8, dy + 6, 32, 38);
      }
      ctx.restore();
    }
  }

  class BaseNPC {
    constructor(name, x, y, width, height, interactRadius, mapRole) {
      this.name = name;
      this.x = x;
      this.y = y;
      this.width = width || 32;
      this.height = height || 32;
      this.interact_radius = interactRadius || 52;
      this.map_role = mapRole || "npc";
      this.spriteKey = null;
      this.portraitKey = null;
      this.elapsed = Math.random() * 5;
      this.fps = 4;
    }

    getCenter() {
      return [this.x + this.width / 2, this.y + this.height / 2];
    }

    isPlayerNear(player) {
      const [cx, cy] = this.getCenter();
      return Math.hypot(cx - (player.x + 24), cy - (player.y + 24)) <= this.interact_radius;
    }

    update(dt) {
      this.elapsed += dt;
    }

    draw(ctx, camX, camY, player) {
      const dx = Math.round(this.x - camX);
      const dy = Math.round(this.y - camY);

      ctx.beginPath();
      ctx.ellipse(dx + this.width / 2, dy + this.height - 2, this.width * 0.38, 4, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,0,0,0.38)";
      ctx.fill();

      if (this.spriteKey) {
        Assets.drawSprite(ctx, this.spriteKey, this.elapsed, dx, dy, this.width, this.height, this.fps);
      }

      if (this.name) {
        ctx.font = C.font(11, { bold: true });
        C.drawOutlinedText(ctx, this.name, dx + this.width / 2, dy - 16, C.COLOR_GOLD, "#000000", "center");
      }

      if (player && this.isPlayerNear(player)) {
        ctx.font = C.font(11, { bold: true });
        C.drawOutlinedText(ctx, "[E] Interaksi", dx + this.width / 2, dy - 32, C.COLOR_TEXT_ACCENT, "#000000", "center");
      }
    }
  }

  class Campfire extends BaseNPC {
    constructor(x, y) {
      super("Api Unggun Oakhaven", x, y, 36, 36, 58, "campfire");
    }

    draw(ctx, camX, camY, player) {
      const cx = Math.round(this.x + 18 - camX);
      const cy = Math.round(this.y + 20 - camY);
      const p = 0.5 + 0.5 * Math.sin(this.elapsed * 7);

      ctx.beginPath();
      ctx.arc(cx, cy, 24 + p * 6, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 145, 45, ${(0.22 + 0.08 * p).toFixed(2)})`;
      ctx.fill();

      ctx.fillStyle = "#5a3d28";
      ctx.fillRect(cx - 10, cy + 4, 20, 5);
      ctx.beginPath();
      ctx.moveTo(cx, cy - 14 - p * 4);
      ctx.lineTo(cx + 9, cy + 6);
      ctx.lineTo(cx - 9, cy + 6);
      ctx.closePath();
      ctx.fillStyle = "#ff7828";
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(cx, cy - 7 - p * 3);
      ctx.lineTo(cx + 5, cy + 5);
      ctx.lineTo(cx - 5, cy + 5);
      ctx.closePath();
      ctx.fillStyle = "#ffe66e";
      ctx.fill();

      ctx.font = C.font(11, { bold: true });
      C.drawOutlinedText(ctx, this.name, cx, Math.round(this.y - camY - 14), C.COLOR_GOLD, "#000000", "center");
      if (player && this.isPlayerNear(player)) {
        C.drawOutlinedText(ctx, "[E] Pulihkan HP & Save", cx, Math.round(this.y - camY - 30), "#a8ffba", "#000000", "center");
      }
    }
  }

  class WhiteFlame extends BaseNPC {
    constructor(x, y) {
      super("Api Putih", x, y, 40, 40, 62, "white_fire");
      this.spriteKey = "white_fire";
      this.fps = 10;
      this.healRadius = 74.0;
      this.healRate = 12.0;
      this.maxEnergy = 140.0;
      this.energy = 140.0;
      this.rechargeDelay = 16.0;
      this.rechargeTimer = 0.0;
      this._healAccum = 0.0;
      this._sfxTimer = 0.0;
    }

    update(dt, player, combatMgr) {
      super.update(dt);
      if (this._sfxTimer > 0) this._sfxTimer = Math.max(0.0, this._sfxTimer - dt);

      if (this.rechargeTimer > 0) {
        this.rechargeTimer = Math.max(0.0, this.rechargeTimer - dt);
        if (this.rechargeTimer === 0.0) this.energy = this.maxEnergy;
      } else if (player && !player.is_dead) {
        const [cx, cy] = this.getCenter();
        const px = player.x + 24;
        const py = player.y + 24;
        const dist = Math.hypot(cx - px, cy - py);
        if (dist <= this.healRadius && this.energy > 0) {
          player.in_white_fire = true;
          if (player.hp < player.max_hp) {
            const gain = Math.min(this.energy, this.healRate * dt);
            this.energy -= gain;
            this._healAccum += gain;
            const pts = Math.floor(this._healAccum);
            if (pts >= 1) {
              this._healAccum -= pts;
              const healed = Math.min(player.max_hp - player.hp, pts);
              if (healed > 0) {
                player.hp = Math.min(player.max_hp, player.hp + healed);
                player.hp_trail = player.hp;
                if (this._sfxTimer <= 0) {
                  this._sfxTimer = 0.75;
                  AudioMgr.playSound("heal");
                  if (combatMgr) {
                    combatMgr.floatingTexts.push(new FloatingText(px, player.y - 14, `+${healed} HP (Api Putih)`, "#c8f8ff", 15));
                  }
                }
              }
            }
            if (this.energy <= 0.5) {
              this.energy = 0.0;
              this.rechargeTimer = this.rechargeDelay;
            }
          }
        } else if (this.energy < this.maxEnergy) {
          this.energy = Math.min(this.maxEnergy, this.energy + 6.0 * dt);
        }
      }
    }

    draw(ctx, camX, camY, player) {
      const [cxWorld, cyWorld] = this.getCenter();
      const cx = Math.round(cxWorld - camX);
      const cy = Math.round(cyWorld - camY);
      const pulse = 0.5 + 0.5 * Math.sin(this.elapsed * 2.8);

      if (this.rechargeTimer <= 0) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(cx, cy, this.healRadius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(205, 248, 255, ${(0.07 + 0.05 * pulse).toFixed(3)})`;
        ctx.fill();
        ctx.strokeStyle = "rgba(215, 252, 255, 0.42)";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, 24 + pulse * 5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
        ctx.fill();
        ctx.restore();

        Assets.drawSprite(ctx, "white_fire", this.elapsed, cx - 22, cy - 26, 44, 44, 10);
      } else {
        ctx.beginPath();
        ctx.arc(cx, cy, 14, 0, Math.PI * 2);
        ctx.strokeStyle = "rgba(150, 170, 185, 0.55)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      const barW = 36;
      const bx = cx - barW / 2;
      const by = cy - 30;
      ctx.fillStyle = "#182028";
      ctx.fillRect(bx, by, barW, 4);
      const ratio = this.rechargeTimer > 0 ? 1 - this.rechargeTimer / this.rechargeDelay : this.energy / this.maxEnergy;
      ctx.fillStyle = this.rechargeTimer > 0 ? "#8ea2b8" : "#d8fbff";
      ctx.fillRect(bx, by, Math.round(barW * Math.max(0, Math.min(1, ratio))), 4);

      ctx.font = C.font(10, { bold: true });
      const label = this.rechargeTimer > 0 ? `Api Putih (${Math.ceil(this.rechargeTimer)}s)` : "Api Putih (+HP)";
      C.drawOutlinedText(ctx, label, cx, by - 14, "#d2f8ff", "#000000", "center");

      if (player && this.isPlayerNear(player)) {
        C.drawOutlinedText(ctx, "Dekati untuk Pulihkan HP", cx, cy + 24, "#9ef7ff", "#000000", "center");
      }
    }
  }

  class MapPortal extends BaseNPC {
    constructor(name, x, y, targetMap, targetX, targetY, color) {
      super(name, x, y, 40, 40, 56, "portal");
      this.target_map = targetMap;
      this.target_x = targetX;
      this.target_y = targetY;
      this.color = color || [110, 210, 255];
    }

    draw(ctx, camX, camY, player) {
      const [cxWorld, cyWorld] = this.getCenter();
      const cx = Math.round(cxWorld - camX);
      const cy = Math.round(cyWorld - camY);
      const pulse = 0.5 + 0.5 * Math.sin(this.elapsed * 4.2);

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, 20 + pulse * 4, 0, Math.PI * 2);
      ctx.fillStyle = C.rgbStr(this.color, 0.24);
      ctx.fill();
      ctx.strokeStyle = C.rgbStr(this.color, 0.92);
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, 10 + pulse * 2, this.elapsed * 2.5, this.elapsed * 2.5 + Math.PI * 1.4);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();

      ctx.font = C.font(11, { bold: true });
      C.drawOutlinedText(ctx, this.name, cx, Math.round(this.y - camY - 16), C.rgbStr(this.color), "#000000", "center");
      if (player && this.isPlayerNear(player)) {
        C.drawOutlinedText(ctx, "[E] Masuki Portal", cx, Math.round(this.y - camY - 32), C.COLOR_GOLD, "#000000", "center");
      }
    }
  }

  class TrainingTarget {
    constructor(name, x, y, maxHp, defense, isMonster, canRespawn) {
      this.name = name;
      this.x = x;
      this.y = y;
      this.spawnX = x;
      this.spawnY = y;
      this.width = 36;
      this.height = 36;
      this.max_hp = maxHp || 35;
      this.hp = this.max_hp;
      this.defense = defense || 0;
      this.isMonster = Boolean(isMonster);
      this.canRespawn = canRespawn !== undefined ? canRespawn : true;
      this.isBoss = false;
      this.map_role = "enemy";
      this.hurt_flash = 0.0;
      this.respawnTimer = 0.0;
      this.exp_reward = 25;
      this.ash_range = [4, 8];
      this.gold_range = [5, 12];
      this.elapsed = 0.0;
    }

    isAlive() {
      return this.hp > 0;
    }

    getCenter() {
      return [this.x + this.width / 2, this.y + this.height / 2];
    }

    getHitbox() {
      return { x: this.x + 4, y: this.y + 4, w: this.width - 8, h: this.height - 8 };
    }

    takeDamage(amount) {
      if (!this.isAlive()) return 0;
      const dealt = Math.min(this.hp, amount);
      this.hp -= dealt;
      this.hurt_flash = 0.16;
      AudioMgr.playSound("impact");
      return dealt;
    }

    getRewards() {
      const ash = this.ash_range[0] + Math.floor(Math.random() * (this.ash_range[1] - this.ash_range[0] + 1));
      const gold = this.gold_range[0] + Math.floor(Math.random() * (this.gold_range[1] - this.gold_range[0] + 1));
      return [this.exp_reward, ash, gold];
    }

    update(dt) {
      this.elapsed += dt;
      if (this.hurt_flash > 0) this.hurt_flash = Math.max(0.0, this.hurt_flash - dt);
      if (!this.isAlive() && this.canRespawn) {
        this.respawnTimer += dt;
        if (this.respawnTimer >= 4.0) {
          this.respawnTimer = 0.0;
          this.hp = this.max_hp;
          this.x = this.spawnX;
          this.y = this.spawnY;
        }
      }
    }

    draw(ctx, camX, camY) {
      if (!this.isAlive()) return;
      const dx = Math.round(this.x - camX);
      const dy = Math.round(this.y - camY);

      ctx.beginPath();
      ctx.ellipse(dx + this.width / 2, dy + this.height - 2, this.width * 0.45, 4, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,0,0,0.36)";
      ctx.fill();

      if (this.isMonster) {
        Assets.drawSprite(ctx, "slime", this.elapsed, dx, dy, this.width, this.height, 6);
      } else {
        // Training dummy
        C.drawRoundedRect(ctx, dx + 8, dy + 6, 20, 26, 6, "#8c6239", "#d4a672", 2);
        ctx.fillStyle = "#5a3b20";
        ctx.fillRect(dx + 4, dy + 13, 28, 5);
      }

      if (this.hurt_flash > 0) {
        ctx.fillStyle = "rgba(255, 80, 80, 0.5)";
        ctx.fillRect(dx + 4, dy + 4, this.width - 8, this.height - 8);
      }

      const barW = Math.max(34, this.width);
      const bx = Math.round(this.x + this.width / 2 - camX - barW / 2);
      const by = Math.round(this.y - 12 - camY);
      ctx.fillStyle = "#141419";
      ctx.fillRect(bx - 1, by - 1, barW + 2, 7);
      ctx.fillStyle = C.COLOR_HP_BG;
      ctx.fillRect(bx, by, barW, 5);
      ctx.fillStyle = C.COLOR_HP;
      ctx.fillRect(bx, by, Math.round(barW * Math.max(0, Math.min(1, this.hp / this.max_hp))), 5);

      ctx.font = C.font(11, { bold: true });
      C.drawOutlinedText(ctx, this.name, dx + this.width / 2, by - 15, C.COLOR_WHITE, "#000000", "center");
    }
  }

  class Enemy extends TrainingTarget {
    constructor(opts) {
      const spriteKind = opts.spriteKind || "monster1";
      const isBoss = Boolean(opts.isBoss);
      const size = isBoss ? 60 : spriteKind === "monster1" || spriteKind === "monster_ranged" ? 44 : 36;
      super(opts.name, opts.x, opts.y, opts.maxHp || 36, opts.defense || 4, true, false);
      this.width = size;
      this.height = size;
      this.attack_damage = opts.attackDamage || 120;
      this.speed = opts.speed || 82.0;
      this.aggro_range = opts.aggroRange || 250.0;
      this.attack_range = opts.attackRange || 44.0;
      this.sprite_kind = spriteKind;
      this.exp_reward = opts.expReward || 55;
      this.ash_range = opts.ashRange || [6, 12];
      this.gold_range = opts.goldRange || [10, 22];
      this.isBoss = isBoss;
      this.map_role = isBoss ? "boss" : "enemy";
      this.is_ranged = Boolean(opts.isRanged);
      this.proj_color = opts.projColor || [220, 90, 255];

      this.direction = "south";
      this.state = "idle";
      this.windup_duration = isBoss ? 0.65 : 0.55;
      this.windup_timer = 0.0;
      this.attack_cooldown = isBoss ? 1.45 : 1.55;
      this.attack_cd_timer = 0.0;
      this.knockback_vx = 0.0;
      this.knockback_vy = 0.0;
      this.frameIndex = 0.0;
      this.animSpeed = 7.0;
    }

    getHitbox() {
      const hw = Math.max(16, Math.floor(this.width * 0.45));
      const hh = Math.max(12, Math.floor(this.height * 0.3));
      return {
        x: Math.round(this.x + (this.width - hw) / 2),
        y: Math.round(this.y + this.height - hh - 2),
        w: hw,
        h: hh,
      };
    }

    applyKnockback(vx, vy) {
      const mult = this.isBoss ? 0.4 : 1.0;
      this.knockback_vx = vx * mult;
      this.knockback_vy = vy * mult;
    }

    _moveWithCollision(stepX, stepY, map) {
      if (!map) {
        this.x += stepX;
        this.y += stepY;
        return;
      }
      if (stepX !== 0) {
        this.x += stepX;
        if (map.isBlocked(this.getHitbox())) this.x -= stepX;
      }
      if (stepY !== 0) {
        this.y += stepY;
        if (map.isBlocked(this.getHitbox())) this.y -= stepY;
      }
    }

    _updateDirection(dx, dy) {
      if (Math.abs(dx) >= Math.abs(dy)) this.direction = dx >= 0 ? "east" : "west";
      else this.direction = dy >= 0 ? "south" : "north";
    }

    _executeAttack(player, combatMgr) {
      if (!player || player.is_dead) return;
      const [ecx, ecy] = this.getCenter();
      const pcx = player.x + 24;
      const pcy = player.y + 24;

      if (this.is_ranged && combatMgr) {
        const ang = Math.atan2(pcy - ecy, pcx - ecx);
        combatMgr.spawnProjectile(ecx, ecy, ang, 200.0, this.attack_damage, 6, this.proj_color);
        AudioMgr.playSound("projectile");
        return;
      }

      const dist = Math.hypot(pcx - ecx, pcy - ecy);
      if (dist <= this.attack_range + 16) {
        const dealt = player.takeDamage(this.attack_damage);
        if (dealt > 0) {
          if (dist > 0) {
            player.applyKnockback(((pcx - ecx) / dist) * 165.0, ((pcy - ecy) / dist) * 165.0);
          }
          if (combatMgr) {
            combatMgr.triggerShake(0.16, 4.5);
            combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 12, `-${dealt}`, C.COLOR_CRIT, 18, true));
          }
        } else if (player.dodged_last_hit) {
          player.dodged_last_hit = false;
          if (combatMgr) {
            combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 18, "PERFECT DODGE! +15 ST", "#6edcff", 16, true));
          }
        }
      }
    }

    update(dt, player, map, combatMgr) {
      if (!this.isAlive()) return;
      this.elapsed += dt;
      if (this.hurt_flash > 0) this.hurt_flash = Math.max(0.0, this.hurt_flash - dt);
      if (this.attack_cd_timer > 0) this.attack_cd_timer = Math.max(0.0, this.attack_cd_timer - dt);

      if (Math.abs(this.knockback_vx) > 2.0 || Math.abs(this.knockback_vy) > 2.0) {
        this._moveWithCollision(this.knockback_vx * dt, this.knockback_vy * dt, map);
        const decay = Math.max(0.0, 1.0 - 9.0 * dt);
        this.knockback_vx *= decay;
        this.knockback_vy *= decay;
      } else {
        this.knockback_vx = 0.0;
        this.knockback_vy = 0.0;
      }

      if (player && !player.is_dead) {
        const [ecx, ecy] = this.getCenter();
        const pcx = player.x + 24;
        const pcy = player.y + 24;
        const dx = pcx - ecx;
        const dy = pcy - ecy;
        const dist = Math.hypot(dx, dy);

        if (this.state === "windup") {
          this._updateDirection(dx, dy);
          this.windup_timer -= dt;
          if (this.windup_timer <= 0) {
            this._executeAttack(player, combatMgr);
            this.attack_cd_timer = this.attack_cooldown;
            this.state = "cooldown";
          }
        } else if (this.is_ranged && dist <= this.aggro_range && this.attack_cd_timer <= 0) {
          this._updateDirection(dx, dy);
          this.state = "windup";
          this.windup_timer = this.windup_duration;
        } else if (!this.is_ranged && dist <= this.attack_range && this.attack_cd_timer <= 0) {
          this._updateDirection(dx, dy);
          this.state = "windup";
          this.windup_timer = this.windup_duration;
        } else if (dist <= this.aggro_range) {
          this.state = "chase";
          if (this.is_ranged) {
            if (dist < 110 && dist > 0) {
              this._moveWithCollision(-(dx / dist) * this.speed * 0.6 * dt, -(dy / dist) * this.speed * 0.6 * dt, map);
            } else if (dist > 200 && dist > 0) {
              this._moveWithCollision((dx / dist) * this.speed * dt, (dy / dist) * this.speed * dt, map);
            }
            this._updateDirection(dx, dy);
          } else if (dist > this.attack_range * 0.75 && dist > 0) {
            this._updateDirection(dx, dy);
            this._moveWithCollision((dx / dist) * this.speed * dt, (dy / dist) * this.speed * dt, map);
          }
        } else {
          this.state = "idle";
        }
      } else {
        this.state = "idle";
      }

      const spd = this.state === "windup" ? 11.0 : this.animSpeed;
      this.frameIndex += spd * dt;
    }

    _getSpriteKey() {
      if (this.sprite_kind === "slime") return "slime";
      if (this.sprite_kind === "monster1" || this.sprite_kind === "monster_ranged") {
        return `${this.sprite_kind}_${this.direction}`;
      }
      const mode = this.state === "windup" ? "atk" : "walk";
      if (this.sprite_kind === "boss_hollow_crown") {
        return `boss_hollow_crown_walk_${this.direction}`;
      }
      return `${this.sprite_kind}_${mode}_${this.direction}`;
    }

    draw(ctx, camX, camY) {
      if (!this.isAlive()) return;
      if (this.state === "windup" && !this.is_ranged) {
        const cx = Math.round(this.x + this.width / 2 - camX);
        const cy = Math.round(this.y + this.height / 2 - camY);
        ctx.beginPath();
        ctx.arc(cx, cy, this.attack_range, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 50, 40, 0.18)";
        ctx.fill();
        ctx.strokeStyle = "rgba(255, 90, 60, 0.7)";
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      const dx = Math.round(this.x - camX);
      const dy = Math.round(this.y - camY);

      ctx.beginPath();
      ctx.ellipse(dx + this.width / 2, dy + this.height - 2, this.width * 0.44, 5, 0, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(0,0,0,0.4)";
      ctx.fill();

      Assets.drawSpriteFrame(ctx, this._getSpriteKey(), Math.floor(this.frameIndex), dx, dy, this.width, this.height);

      if (this.hurt_flash > 0) {
        ctx.fillStyle = "rgba(255, 80, 80, 0.45)";
        ctx.fillRect(dx + 4, dy + 4, this.width - 8, this.height - 8);
      }

      const barW = Math.max(34, this.width);
      const bx = Math.round(this.x + this.width / 2 - camX - barW / 2);
      const by = Math.round(this.y - 12 - camY);
      ctx.fillStyle = "#141419";
      ctx.fillRect(bx - 1, by - 1, barW + 2, 7);
      ctx.fillStyle = C.COLOR_HP_BG;
      ctx.fillRect(bx, by, barW, 5);
      ctx.fillStyle = C.COLOR_HP;
      ctx.fillRect(bx, by, Math.round(barW * Math.max(0, Math.min(1, this.hp / this.max_hp))), 5);

      ctx.font = C.font(11, { bold: true });
      C.drawOutlinedText(ctx, this.name, dx + this.width / 2, by - 15, C.COLOR_WHITE, "#000000", "center");
    }
  }

  const BOSS_SPECS = {
    gargantua: ["Jenderal Gargantua (Dungeon 1)", "boss_gargantua", 95, 6, 95, 78.0, [110, 170, 75], 180],
    vespa: ["Ratu Spora Vespa (Dungeon 2)", "boss_vespa", 230, 14, 155, 90.0, [185, 95, 245], 320],
    ignis: ["Ignis Executioner (Dungeon 3)", "boss_ignis", 420, 24, 240, 102.0, [255, 125, 40], 500],
    valerius: ["Jenderal Valerius (Dungeon 4)", "boss_valerius", 680, 36, 330, 114.0, [150, 230, 255], 740],
    ash_lord: ["Sang Penguasa Abu (Fase 1)", "boss_demonKing", 560, 32, 300, 106.0, [255, 70, 55], 1100],
    demon_king: ["Raja Iblis: Penguasa Abu", "boss_demonKing", 240, 15, 175, 88.0, [255, 70, 55], 400],
  };

  class BossEntity extends Enemy {
    constructor(bossId, x, y) {
      const spec = BOSS_SPECS[bossId] || BOSS_SPECS.demon_king;
      super({
        name: spec[0],
        x,
        y,
        maxHp: spec[2],
        defense: spec[3],
        attackDamage: spec[4],
        speed: spec[5],
        aggroRange: 400.0,
        attackRange: 58.0,
        spriteKind: spec[1],
        expReward: spec[7],
        ashRange: [20, 35],
        goldRange: [45, 80],
        isBoss: true,
        projColor: spec[6],
      });
      this.boss_id = bossId;
      this.phase = 1;
      this.special_timer = 2.8;
      this.skull_barrage_timer = 4.2;
      this.skull_formation_idx = 0;
      this.spiral_angle = 0.0;
    }

    takeDamage(amount) {
      if (!this.isAlive()) return 0;
      const actual = Math.min(this.hp, amount);
      this.hp -= actual;
      this.hurt_flash = 0.18;
      AudioMgr.playSound("impact");

      if (this.hp <= 0 && this.boss_id === "ash_lord" && this.phase === 1) {
        this.phase = 2;
        this.name = "Mahkota Kutukan: The Hollow Crown (Fase 2)";
        this.max_hp = 720;
        this.hp = 720;
        this.attack_damage = 350;
        this.speed = 118.0;
        this.skull_barrage_timer = 2.0;
        this.sprite_kind = "boss_hollow_crown";
        AudioMgr.playSound("explosion");
      }
      return actual;
    }

    update(dt, player, map, combatMgr) {
      super.update(dt, player, map, combatMgr);
      if (!this.isAlive() || !player || player.is_dead || !combatMgr) return;

      const [ecx, ecy] = this.getCenter();
      const pcx = player.x + 24;
      const pcy = player.y + 24;
      if (Math.hypot(pcx - ecx, pcy - ecy) > this.aggro_range) return;

      const baseAng = Math.atan2(pcy - ecy, pcx - ecx);
      if (this.boss_id === "ash_lord") {
        this.skull_barrage_timer -= dt;
        if (this.skull_barrage_timer <= 0) {
          if (this.phase === 2 || this.hp <= this.max_hp * 0.82) {
            const formation = this.skull_formation_idx % 2 === 0 ? "top_bottom" : "left_right";
            this.skull_formation_idx += 1;
            const mw = map ? map.width : 1280;
            const mh = map ? map.height : 1280;
            combatMgr.triggerSkullLasers(
              formation,
              Math.round(this.attack_damage * (this.phase === 1 ? 0.9 : 1.05)),
              mw,
              mh,
              pcx,
              pcy
            );
            this.skull_barrage_timer = this.phase === 1 ? 9.5 : 6.8;
          }
        }
      }

      this.special_timer -= dt;
      if (this.special_timer > 0) return;

      if (this.boss_id === "gargantua") {
        this.special_timer = 4.2;
        combatMgr.slashEffects.push(new SlashEffect(ecx, ecy, 0, 80, true));
        for (let k = 0; k < 4; k++) {
          combatMgr.spawnProjectile(ecx, ecy, baseAng + k * (Math.PI / 2), 150.0, this.attack_damage, 8, this.proj_color);
        }
      } else if (this.boss_id === "vespa") {
        this.special_timer = 3.8;
        combatMgr.spawnSporeTrap(pcx + (Math.random() * 90 - 45), pcy + (Math.random() * 90 - 45), this.attack_damage);
        for (const off of [-0.32, 0.0, 0.32]) {
          combatMgr.spawnProjectile(ecx, ecy, baseAng + off, 170.0, this.attack_damage, 7, this.proj_color);
        }
      } else if (this.boss_id === "ignis") {
        this.special_timer = 3.4;
        for (const off of [-0.35, 0.0, 0.35]) {
          combatMgr.spawnProjectile(ecx, ecy, baseAng + off, 195.0, this.attack_damage, 8, this.proj_color);
        }
      } else if (this.boss_id === "valerius") {
        this.special_timer = 3.0;
        for (const off of [-0.25, 0.0, 0.25]) {
          combatMgr.spawnProjectile(ecx, ecy, baseAng + off, 230.0, this.attack_damage, 7, this.proj_color);
        }
      } else if (this.boss_id === "ash_lord") {
        if (this.phase === 1) {
          this.special_timer = 3.2;
          for (let k = 0; k < 5; k++) {
            combatMgr.spawnProjectile(ecx, ecy, baseAng + k * ((Math.PI * 2) / 5), 195.0, this.attack_damage, 8, [255, 85, 65]);
          }
        } else {
          this.special_timer = 1.7;
          this.spiral_angle += 0.55;
          const elemColors = [[110, 175, 75], [185, 95, 245], [255, 125, 40], [150, 230, 255]];
          for (let k = 0; k < 6; k++) {
            combatMgr.spawnProjectile(
              ecx,
              ecy,
              this.spiral_angle + k * (Math.PI / 3),
              220.0,
              this.attack_damage,
              7,
              elemColors[k % elemColors.length]
            );
          }
        }
      }
    }
  }

  function makeNPC(opts) {
    const npc = new BaseNPC(opts.name, opts.x, opts.y, opts.w, opts.h, opts.radius || 55, opts.role);
    npc.spriteKey = opts.spriteKey;
    npc.portraitKey = opts.portraitKey || null;
    npc.fps = opts.fps || 4;
    return npc;
  }

  function createWhiteFlames(coords) {
    return coords.map(([x, y]) => new WhiteFlame(x, y));
  }

  function createMapEntities(mapName) {
    if (mapName === "map1safeworld.tmx") {
      return {
        npcs: [
          new Campfire(544, 256),
          makeNPC({ name: "Elara (Arsiparis & Quest)", x: 320, y: 192, w: 32, h: 32, radius: 55, role: "quest", spriteKey: "npc_elara", portraitKey: "portrait_elara" }),
          makeNPC({ name: "Vektor (Guildmaster & Skill)", x: 128, y: 224, w: 52, h: 52, radius: 60, role: "skill", spriteKey: "npc_vektor", portraitKey: "portrait_vektor" }),
          makeNPC({ name: "Brog (Barman Rusty Anchor)", x: 192, y: 544, w: 32, h: 32, radius: 55, role: "bar", spriteKey: "npc_brog", portraitKey: "portrait_brog" }),
          makeNPC({ name: "Gael (Pedagang Senjata & Shop)", x: 224, y: 704, w: 48, h: 48, radius: 58, role: "shop", spriteKey: "npc_gael", portraitKey: "portrait_gael" }),
          makeNPC({ name: "Aell (Map Reader)", x: 928, y: 288, w: 48, h: 48, radius: 55, role: "map", spriteKey: "npc_aell" }),
          makeNPC({ name: "Kapten Penjaga Gerbang", x: 864, y: 120, w: 32, h: 32, radius: 55, role: "guard", spriteKey: "npc_guard", portraitKey: "portrait_guard" }),
          makeNPC({ name: "Leo (Anak Oakhaven)", x: 160, y: 736, w: 44, h: 44, radius: 48, role: "villager", spriteKey: "npc_boy" }),
          makeNPC({ name: "Aria (Penyintas)", x: 800, y: 672, w: 44, h: 44, radius: 48, role: "villager", spriteKey: "npc_girl" }),
          new MapPortal("Gerbang Ekspedisi (Dungeon 1: Rawa Kematian)", 864, 96, "stage1_swamp.tmx", 96, 608, [90, 210, 120]),
        ],
        enemies: [
          new TrainingTarget("Boneka Latihan A", 480, 832, 32, 0, false, true),
          new TrainingTarget("Boneka Latihan B", 544, 832, 32, 0, false, true),
          new TrainingTarget("Karak Rawa (Scout)", 544, 768, 40, 2, true, true),
        ],
      };
    }

    if (mapName === "stage1_swamp.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Hub Rusty Anchor", 32, 608, "map1safeworld.tmx", 864, 152, [120, 230, 140]),
          new MapPortal("Menuju Dungeon 2: Hutan Spora", 1216, 608, "stage2_spore.tmx", 96, 608, [190, 100, 240]),
          ...createWhiteFlames([[128, 128], [1120, 128], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Karak Rawa", x: 256, y: 580, maxHp: 26, defense: 3, attackDamage: 75, speed: 76, spriteKind: "monster1", expReward: 60 }),
          new Enemy({ name: "Kultis Rawa (Ranged)", x: 320, y: 420, maxHp: 22, defense: 2, attackDamage: 70, speed: 62, spriteKind: "monster_ranged", isRanged: true, expReward: 65, projColor: [120, 185, 85] }),
          new Enemy({ name: "Slime Lumpur", x: 576, y: 300, maxHp: 24, defense: 2, attackDamage: 65, speed: 68, spriteKind: "slime", expReward: 50 }),
          new Enemy({ name: "Karak Penjaga Rawa", x: 600, y: 820, maxHp: 32, defense: 4, attackDamage: 82, speed: 80, spriteKind: "monster1", expReward: 70 }),
          new Enemy({ name: "Kultis Penembak", x: 880, y: 700, maxHp: 24, defense: 2, attackDamage: 75, speed: 64, spriteKind: "monster_ranged", isRanged: true, expReward: 70, projColor: [120, 185, 85] }),
          new BossEntity("gargantua", 1040, 580),
        ],
      };
    }

    if (mapName === "stage2_spore.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Hub Rusty Anchor", 32, 608, "map1safeworld.tmx", 584, 232, [120, 230, 140]),
          ...createWhiteFlames([[128, 128], [1120, 128], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Karak Spora", x: 260, y: 540, maxHp: 59, defense: 6, attackDamage: 142, speed: 92, spriteKind: "monster1", expReward: 105 }),
          new Enemy({ name: "Penebar Spora (Ranged)", x: 320, y: 360, maxHp: 52, defense: 5, attackDamage: 129, speed: 75.9, spriteKind: "monster_ranged", isRanged: true, expReward: 110, projColor: [185, 95, 245] }),
          new Enemy({ name: "Karak Pembusuk", x: 640, y: 640, maxHp: 70, defense: 7, attackDamage: 148, speed: 96.6, spriteKind: "monster1", expReward: 115 }),
          new Enemy({ name: "Penyihir Spora (Ranged)", x: 780, y: 460, maxHp: 56, defense: 5, attackDamage: 139, speed: 78.2, spriteKind: "monster_ranged", isRanged: true, expReward: 125, projColor: [185, 95, 245] }),
          new BossEntity("vespa", 1020, 580),
        ],
      };
    }

    if (mapName === "stage3_gehenna.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Hub Rusty Anchor", 32, 608, "map1safeworld.tmx", 584, 232, [120, 230, 140]),
          ...createWhiteFlames([[128, 128], [1120, 128], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Prajurit Tungku", x: 280, y: 560, maxHp: 130, defense: 10, attackDamage: 245, speed: 109.2, spriteKind: "monster1", expReward: 170 }),
          new Enemy({ name: "Penembak Bara (Ranged)", x: 360, y: 460, maxHp: 105, defense: 8, attackDamage: 229, speed: 91, spriteKind: "monster_ranged", isRanged: true, expReward: 180, projColor: [255, 135, 45] }),
          new Enemy({ name: "Algojo Gehenna", x: 640, y: 600, maxHp: 149, defense: 12, attackDamage: 260, speed: 114.4, spriteKind: "monster1", expReward: 195 }),
          new Enemy({ name: "Penyihir Api (Ranged)", x: 840, y: 720, maxHp: 112, defense: 9, attackDamage: 235, speed: 93.6, spriteKind: "monster_ranged", isRanged: true, expReward: 195, projColor: [255, 135, 45] }),
          new BossEntity("ignis", 1020, 580),
        ],
      };
    }

    if (mapName === "stage4_frost.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Hub Rusty Anchor", 608, 1216, "map1safeworld.tmx", 584, 232, [120, 230, 140]),
          ...createWhiteFlames([[128, 128], [1120, 128], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Ksatria Salju", x: 560, y: 880, maxHp: 259, defense: 15, attackDamage: 389, speed: 130.5, spriteKind: "monster1", expReward: 255 }),
          new Enemy({ name: "Pemanah Es (Ranged)", x: 320, y: 720, maxHp: 211, defense: 12, attackDamage: 353, speed: 107.3, spriteKind: "monster_ranged", isRanged: true, expReward: 265, projColor: [150, 230, 255] }),
          new Enemy({ name: "Penjaga Kristal", x: 740, y: 640, maxHp: 288, defense: 18, attackDamage: 410, speed: 133.4, spriteKind: "monster1", expReward: 285 }),
          new Enemy({ name: "Penyihir Salju (Ranged)", x: 920, y: 480, maxHp: 230, defense: 13, attackDamage: 367, speed: 110.2, spriteKind: "monster_ranged", isRanged: true, expReward: 285, projColor: [150, 230, 255] }),
          new BossEntity("valerius", 608, 220),
        ],
      };
    }

    if (mapName === "stage5_throne.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Hub Rusty Anchor", 608, 1216, "map1safeworld.tmx", 584, 232, [120, 230, 140]),
          ...createWhiteFlames([[128, 1120], [1120, 1120]]),
        ],
        enemies: [new BossEntity("ash_lord", 608, 280)],
      };
    }

    if (mapName === "dungeon1.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Lobby Oakhaven", 112, 232, "map1safeworld.tmx", 864, 152, [120, 230, 140]),
          new MapPortal("Gerbang Takhta Dungeon 2", 1096, 128, "dungeon2.tmx", 1120, 288, [220, 90, 255]),
          ...createWhiteFlames([[128, 128], [1120, 128], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Slime Beracun", x: 384, y: 96, maxHp: 30, defense: 3, attackDamage: 78, speed: 70, spriteKind: "slime", expReward: 75 }),
          new Enemy({ name: "Karak Pengintai", x: 384, y: 416, maxHp: 38, defense: 4, attackDamage: 88, speed: 78, spriteKind: "monster1", expReward: 95 }),
          new Enemy({ name: "Kultis Labirin (Ranged)", x: 960, y: 544, maxHp: 30, defense: 3, attackDamage: 82, speed: 68, spriteKind: "monster_ranged", isRanged: true, expReward: 100 }),
          new Enemy({ name: "Slime Rawa Gelap", x: 320, y: 864, maxHp: 32, defense: 3, attackDamage: 82, speed: 72, spriteKind: "slime", expReward: 80 }),
          new BossEntity("gargantua", 1076, 192),
        ],
      };
    }

    if (mapName === "dungeon2.tmx") {
      return {
        npcs: [
          new MapPortal("Kembali ke Dungeon 1", 1120, 224, "dungeon1.tmx", 1076, 192, [120, 230, 140]),
          ...createWhiteFlames([[96, 96], [1152, 96], [128, 1120], [1120, 1120]]),
        ],
        enemies: [
          new Enemy({ name: "Karak Terkutuk", x: 320, y: 448, maxHp: 68, defense: 9, attackDamage: 135, speed: 86, spriteKind: "monster1", expReward: 145 }),
          new Enemy({ name: "Penjaga Ruang Abu (Ranged)", x: 768, y: 672, maxHp: 54, defense: 7, attackDamage: 125, speed: 76, spriteKind: "monster_ranged", isRanged: true, expReward: 155 }),
          new Enemy({ name: "Slime Obsidian", x: 192, y: 864, maxHp: 60, defense: 8, attackDamage: 122, speed: 78, spriteKind: "slime", expReward: 130 }),
          new BossEntity("demon_king", 640, 160),
        ],
      };
    }

    return { npcs: [], enemies: [] };
  }

  global.OakhavenEntities = {
    Player,
    BaseNPC,
    Campfire,
    WhiteFlame,
    MapPortal,
    TrainingTarget,
    Enemy,
    BossEntity,
    createMapEntities,
  };
})(window);
