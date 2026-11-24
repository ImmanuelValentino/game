(function (global) {
  "use strict";

  const C = global.OakhavenConfig;
  const Assets = global.OakhavenAssets;
  const AudioMgr = global.OakhavenAudio;
  const { ITEM_DATABASE } = global.OakhavenInventory;

  const DROP_TABLE_TIERS = [
    ["epic", 0.03, ["general_core", "broken_crown"]],
    ["rare", 0.1, ["karak_blood", "pure_steel"]],
    ["uncommon", 0.24, ["spore_intact", "ice_core"]],
    ["common", 0.63, ["bone_shard", "rust_iron"]],
  ];

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function rollConsumableDrop(isBoss, tierMult, playerDropMult) {
    if (isBoss) {
      return pick(["hp_potion", "attack_boost_potion", "defense_potion", "crit_elixir"]);
    }
    const chance = Math.min(0.55, 0.28 * Math.max(1.0, (tierMult || 1.0) * 0.85) * (playerDropMult || 1.0));
    if (Math.random() > chance) return null;
    const roll = Math.random();
    if (roll < 0.38) return "hp_potion";
    if (roll < 0.62) return "attack_boost_potion";
    if (roll < 0.8) return "stamina_tonic";
    if (roll < 0.92) return "defense_potion";
    return "crit_elixir";
  }

  function rollMaterialDrop(tierMult, isBoss, playerDropMult) {
    if (isBoss) return pick(["general_core", "broken_crown"]);
    const mult = (tierMult || 1.0) * (playerDropMult || 1.0);
    const roll = Math.random();
    let acc = 0.0;
    for (const [, baseRate, pool] of DROP_TABLE_TIERS) {
      acc += Math.min(0.95, baseRate * mult);
      if (roll <= acc) return pick(pool);
    }
    return pick(["bone_shard", "rust_iron"]);
  }

  class FloatingText {
    constructor(x, y, text, color, fontSize, isCrit) {
      this.x = x;
      this.y = y;
      this.text = text;
      this.color = color || C.COLOR_WHITE;
      this.fontSize = fontSize || 18;
      this.isCrit = Boolean(isCrit);
      this.lifetime = 0.85;
      this.elapsed = 0.0;
      this.vy = isCrit ? -65.0 : -45.0;
      this.alpha = 1.0;
    }

    update(dt) {
      this.elapsed += dt;
      this.y += this.vy * dt;
      this.vy += 25.0 * dt;
      this.alpha = Math.max(0.0, 1.0 - this.elapsed / this.lifetime);
      return this.elapsed < this.lifetime;
    }

    draw(ctx, camX, camY) {
      if (this.alpha <= 0) return;
      ctx.save();
      ctx.globalAlpha = this.alpha;
      ctx.font = C.font(this.fontSize, { bold: this.isCrit });
      C.drawOutlinedText(ctx, this.text, Math.round(this.x - camX), Math.round(this.y - camY), this.color, "rgba(0,0,0,0.75)", "center");
      ctx.restore();
    }
  }

  class SlashEffect {
    constructor(x, y, angleRad, radius, isSkill) {
      this.x = x;
      this.y = y;
      this.angle = angleRad;
      this.radius = radius || 60;
      this.isSkill = Boolean(isSkill);
      this.lifetime = isSkill ? 0.35 : 0.22;
      this.elapsed = 0.0;
    }

    update(dt) {
      this.elapsed += dt;
      return this.elapsed < this.lifetime;
    }

    draw(ctx, camX, camY) {
      const p = Math.min(1.0, this.elapsed / this.lifetime);
      const alpha = 1.0 - p;
      const cx = Math.round(this.x - camX);
      const cy = Math.round(this.y - camY);
      ctx.save();
      ctx.globalAlpha = alpha;
      if (this.isSkill) {
        const curR = Math.max(6, Math.round(this.radius * (0.4 + 0.6 * p)));
        ctx.beginPath();
        ctx.arc(cx, cy, curR, 0, Math.PI * 2);
        ctx.strokeStyle = "#ffaa28";
        ctx.lineWidth = Math.max(2, Math.round(12 * (1 - p)));
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, Math.max(4, curR - 6), 0, Math.PI * 2);
        ctx.strokeStyle = "#fff5c8";
        ctx.lineWidth = Math.max(1, Math.round(4 * (1 - p)));
        ctx.stroke();
      } else {
        const arcSpan = Math.PI * 0.75;
        const start = this.angle - arcSpan / 2;
        const end = this.angle + arcSpan / 2;
        ctx.beginPath();
        ctx.arc(cx, cy, this.radius, start, end);
        ctx.strokeStyle = "#b4e1ff";
        ctx.lineWidth = Math.max(2, Math.round(9 * (1 - p)));
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(cx, cy, Math.max(4, this.radius - 5), start, end);
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = Math.max(1, Math.round(4 * (1 - p)));
        ctx.stroke();
      }
      ctx.restore();
    }
  }

  class Projectile {
    constructor(x, y, angleRad, speed, damage, radius, color, lifetime) {
      this.x = x;
      this.y = y;
      this.vx = Math.cos(angleRad) * (speed || 220);
      this.vy = Math.sin(angleRad) * (speed || 220);
      this.damage = damage || 20;
      this.radius = radius || 6;
      this.color = color || [220, 90, 255];
      this.lifetime = lifetime || 3.2;
      this.alive = true;
    }

    getRect() {
      return { x: this.x - this.radius, y: this.y - this.radius, w: this.radius * 2, h: this.radius * 2 };
    }

    update(dt, player, map, combatMgr) {
      if (!this.alive) return false;
      this.lifetime -= dt;
      if (this.lifetime <= 0) {
        this.alive = false;
        return false;
      }
      this.x += this.vx * dt;
      this.y += this.vy * dt;
      const rect = this.getRect();
      if (map && map.isProjectileBlocked(rect)) {
        this.alive = false;
        return false;
      }
      if (player && !player.is_dead) {
        const hb = player.getHitbox();
        if (C.rectsOverlap(rect.x, rect.y, rect.w, rect.h, hb.x, hb.y, hb.w, hb.h)) {
          const dealt = player.takeDamage(this.damage);
          const pcx = player.x + 24;
          if (dealt > 0) {
            combatMgr.triggerShake(0.12, 3.5);
            combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 12, `-${dealt}`, C.COLOR_CRIT, 17));
          } else if (player.dodged_last_hit) {
            player.dodged_last_hit = false;
            combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 18, "PERFECT DODGE! +15 ST", "#6edcff", 16, true));
          }
          this.alive = false;
          return false;
        }
      }
      return true;
    }

    draw(ctx, camX, camY) {
      const cx = Math.round(this.x - camX);
      const cy = Math.round(this.y - camY);
      ctx.beginPath();
      ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = C.rgbStr(this.color);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, cy, Math.max(2, Math.floor(this.radius / 2)), 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
    }
  }

  class SporeTrap {
    constructor(x, y, damage, radius) {
      this.x = x;
      this.y = y;
      this.damage = damage || 25;
      this.radius = radius || 58;
      this.triggered = false;
      this.fuseTimer = 1.05;
      this.alive = true;
      this.pulse = 0.0;
    }

    update(dt, player, combatMgr) {
      if (!this.alive) return false;
      this.pulse += dt * 4.0;
      if (player && !player.is_dead) {
        const dist = Math.hypot(player.x + 24 - this.x, player.y + 24 - this.y);
        if (!this.triggered && dist <= this.radius * 0.9) this.triggered = true;
      }
      if (this.triggered) {
        this.fuseTimer -= dt;
        if (this.fuseTimer <= 0) {
          AudioMgr.playSound("explosion");
          combatMgr.slashEffects.push(new SlashEffect(this.x, this.y, 0, this.radius, true));
          if (player && !player.is_dead) {
            const dist = Math.hypot(player.x + 24 - this.x, player.y + 24 - this.y);
            if (dist <= this.radius) {
              const dealt = player.takeDamage(this.damage);
              if (dealt > 0) {
                combatMgr.floatingTexts.push(new FloatingText(player.x + 24, player.y - 12, `-${dealt} SPORA`, "#be78ff", 17));
              } else if (player.dodged_last_hit) {
                player.dodged_last_hit = false;
                combatMgr.floatingTexts.push(new FloatingText(player.x + 24, player.y - 18, "PERFECT DODGE!", "#6edcff", 15, true));
              }
            }
          }
          this.alive = false;
          return false;
        }
      }
      return true;
    }

    draw(ctx, camX, camY) {
      const cx = Math.round(this.x - camX);
      const cy = Math.round(this.y - camY);
      if (this.triggered) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(cx, cy, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(210, 80, 240, 0.22)";
        ctx.fill();
        ctx.strokeStyle = "rgba(255, 110, 255, 0.85)";
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.restore();
      }
      const r = 10 + Math.round(Math.sin(this.pulse) * 3);
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fillStyle = "#b45ae6";
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, Math.PI * 2);
      ctx.fillStyle = "#fae1ff";
      ctx.fill();
    }
  }

  class SkullLaserBarrage {
    constructor(formation, damage, mapW, mapH, focusX, focusY) {
      this.formation = formation || "top_bottom";
      this.damage = damage || 260;
      this.mapW = mapW || 1280;
      this.mapH = mapH || 1280;
      this.focusX = focusX || 640;
      this.focusY = focusY || 640;
      this.elapsed = 0.0;
      this.telegraphDuration = 1.35;
      this.fireDuration = 1.05;
      this.fadeDuration = 0.35;
      this.alive = true;
      this.state = "telegraph";
      this.hitCd = 0.0;
      this.firedSfx = false;
      this.skulls = [];
      this._buildFormation();
    }

    _buildFormation() {
      const beamHalf = 13;
      const halfVh = 265.0;
      const halfVw = 470.0;
      const topY = Math.max(92.0, Math.min(this.mapH - 620.0, this.focusY - halfVh));
      const botY = Math.min(this.mapH - 92.0, Math.max(topY + 440.0, this.focusY + halfVh));
      const leftX = Math.max(92.0, Math.min(this.mapW - 760.0, this.focusX - halfVw));
      const rightX = Math.min(this.mapW - 92.0, Math.max(leftX + 760.0, this.focusX + halfVw));

      if (this.formation === "top_bottom") {
        const spanH = Math.max(120, Math.round(botY - topY));
        const cx0 = Math.max(180.0, this.focusX - 380.0);
        const stepX = 180.0;
        for (let i = 0; i < 3; i++) {
          const x = Math.min(this.mapW - 140.0, cx0 + i * (stepX * 2));
          this.skulls.push({ x, y: topY, dx: 0, dy: 1, rect: { x: x - beamHalf, y: topY, w: beamHalf * 2, h: spanH } });
        }
        for (let i = 0; i < 3; i++) {
          const x = Math.min(this.mapW - 100.0, cx0 + stepX + i * (stepX * 2));
          this.skulls.push({ x, y: botY, dx: 0, dy: -1, rect: { x: x - beamHalf, y: topY, w: beamHalf * 2, h: spanH } });
        }
      } else {
        const spanW = Math.max(120, Math.round(rightX - leftX));
        const cy0 = Math.max(160.0, this.focusY - 220.0);
        const stepY = 95.0;
        for (let i = 0; i < 3; i++) {
          const y = Math.min(this.mapH - 140.0, cy0 + i * (stepY * 2));
          this.skulls.push({ x: leftX, y, dx: 1, dy: 0, rect: { x: leftX, y: y - beamHalf, w: spanW, h: beamHalf * 2 } });
        }
        for (let i = 0; i < 3; i++) {
          const y = Math.min(this.mapH - 100.0, cy0 + stepY + i * (stepY * 2));
          this.skulls.push({ x: rightX, y, dx: -1, dy: 0, rect: { x: leftX, y: y - beamHalf, w: spanW, h: beamHalf * 2 } });
        }
      }
    }

    update(dt, player, combatMgr) {
      if (!this.alive) return false;
      this.elapsed += dt;
      if (this.hitCd > 0) this.hitCd = Math.max(0.0, this.hitCd - dt);

      const tFire = this.telegraphDuration;
      const tFade = tFire + this.fireDuration;
      const tEnd = tFade + this.fadeDuration;

      if (this.elapsed < tFire) {
        this.state = "telegraph";
      } else if (this.elapsed < tFade) {
        if (!this.firedSfx) {
          this.firedSfx = true;
          AudioMgr.playSound("laser");
          if (combatMgr) combatMgr.triggerShake(0.25, 5.0);
        }
        this.state = "firing";
        if (player && !player.is_dead && this.hitCd <= 0) {
          const phb = player.getHitbox();
          const hit = this.skulls.some((sk) => C.rectsOverlap(phb.x, phb.y, phb.w, phb.h, sk.rect.x, sk.rect.y, sk.rect.w, sk.rect.h));
          if (hit) {
            const dealt = player.takeDamage(this.damage);
            const pcx = player.x + 24;
            if (dealt > 0) {
              this.hitCd = 0.45;
              if (combatMgr) combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 14, `-${dealt} LASER!`, "#ff4678", 18, true));
            } else if (player.dodged_last_hit) {
              player.dodged_last_hit = false;
              this.hitCd = 0.45;
              if (combatMgr) combatMgr.floatingTexts.push(new FloatingText(pcx, player.y - 20, "PERFECT DODGE LASER! +15 ST", "#6edcff", 16, true));
            }
          }
        }
      } else if (this.elapsed < tEnd) {
        this.state = "fadeout";
      } else {
        this.alive = false;
        return false;
      }
      return true;
    }

    draw(ctx, camX, camY) {
      const spriteKey = this.state !== "fadeout" ? "boss_skull_charge" : "boss_skull_idle";
      let alpha = 1.0;
      if (this.state === "fadeout") {
        const p = (this.elapsed - (this.telegraphDuration + this.fireDuration)) / Math.max(0.01, this.fadeDuration);
        alpha = Math.max(0, 1 - p);
      }

      ctx.save();
      ctx.globalAlpha = alpha;
      for (const sk of this.skulls) {
        const r = sk.rect;
        const rx = Math.round(r.x - camX);
        const ry = Math.round(r.y - camY);

        if (this.state === "telegraph") {
          const blink = 0.45 + 0.5 * Math.abs(Math.sin(this.elapsed * 12));
          ctx.fillStyle = `rgba(255, 55, 85, ${(0.22 * blink).toFixed(3)})`;
          ctx.fillRect(rx, ry, r.w, r.h);
          ctx.strokeStyle = "rgba(255, 110, 140, 0.85)";
          ctx.lineWidth = 2;
          ctx.strokeRect(rx, ry, r.w, r.h);
        } else if (this.state === "firing") {
          const pulse = 1.0 + 0.14 * Math.sin(this.elapsed * 32);
          if (sk.dy !== 0) {
            const cx = rx + r.w / 2;
            const bw = Math.round(r.w * pulse);
            ctx.fillStyle = "rgba(255, 35, 90, 0.72)";
            ctx.fillRect(cx - bw / 2 - 4, ry, bw + 8, r.h);
            ctx.fillStyle = "rgba(255, 115, 155, 0.95)";
            ctx.fillRect(cx - bw / 2, ry, bw, r.h);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(cx - 4, ry, 8, r.h);
          } else {
            const cy = ry + r.h / 2;
            const bh = Math.round(r.h * pulse);
            ctx.fillStyle = "rgba(255, 35, 90, 0.72)";
            ctx.fillRect(rx, cy - bh / 2 - 4, r.w, bh + 8);
            ctx.fillStyle = "rgba(255, 115, 155, 0.95)";
            ctx.fillRect(rx, cy - bh / 2, r.w, bh);
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(rx, cy - 4, r.w, 8);
          }
        } else {
          ctx.fillStyle = `rgba(255, 65, 110, ${(0.45 * alpha).toFixed(3)})`;
          ctx.fillRect(rx, ry, r.w, r.h);
        }

        const sx = Math.round(sk.x - camX);
        const sy = Math.round(sk.y - camY);
        ctx.beginPath();
        ctx.arc(sx, sy, 32, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 45, 85, 0.25)";
        ctx.fill();
        if (!Assets.drawSprite(ctx, spriteKey, this.elapsed, sx - 32, sy - 32, 64, 64, 9)) {
          ctx.beginPath();
          ctx.arc(sx, sy, 22, 0, Math.PI * 2);
          ctx.fillStyle = "#ebdde6";
          ctx.fill();
        }
      }
      ctx.restore();
    }
  }

  class CombatManager {
    constructor() {
      this.floatingTexts = [];
      this.slashEffects = [];
      this.projectiles = [];
      this.traps = [];
      this.skullBarrages = [];
      this.attackCooldown = 0.26;
      this.attackCdTimer = 0.0;
      this.skillCooldown = 1.4;
      this.skillCdTimer = 0.0;
      this.screenShakeTimer = 0.0;
      this.screenShakeIntensity = 0.0;
    }

    addFloatingText(x, y, text, color, fontSize, isCrit) {
      this.floatingTexts.push(new FloatingText(x, y, text, color, fontSize, isCrit));
    }

    triggerShake(duration, intensity) {
      this.screenShakeTimer = Math.max(this.screenShakeTimer, duration || 0.2);
      this.screenShakeIntensity = Math.max(this.screenShakeIntensity, intensity || 5.0);
    }

    getShakeOffset() {
      if (this.screenShakeTimer <= 0) return [0, 0];
      const v = this.screenShakeIntensity;
      return [Math.round((Math.random() * 2 - 1) * v), Math.round((Math.random() * 2 - 1) * v)];
    }

    spawnProjectile(x, y, angleRad, speed, damage, radius, color) {
      this.projectiles.push(new Projectile(x, y, angleRad, speed, damage, radius, color));
    }

    spawnSporeTrap(x, y, damage) {
      this.traps.push(new SporeTrap(x, y, damage));
    }

    triggerSkullLasers(formation, damage, mapW, mapH, focusX, focusY) {
      this.skullBarrages.push(new SkullLaserBarrage(formation, damage, mapW, mapH, focusX, focusY));
    }

    clearTransientEntities() {
      this.projectiles = [];
      this.traps = [];
      this.slashEffects = [];
      this.skullBarrages = [];
    }

    update(dt, player, map) {
      if (this.attackCdTimer > 0) this.attackCdTimer = Math.max(0.0, this.attackCdTimer - dt);
      if (this.skillCdTimer > 0) this.skillCdTimer = Math.max(0.0, this.skillCdTimer - dt);
      if (this.screenShakeTimer > 0) this.screenShakeTimer = Math.max(0.0, this.screenShakeTimer - dt);

      this.floatingTexts = this.floatingTexts.filter((ft) => ft.update(dt));
      this.slashEffects = this.slashEffects.filter((fx) => fx.update(dt));
      this.projectiles = this.projectiles.filter((pr) => pr.update(dt, player, map, this));
      this.traps = this.traps.filter((tr) => tr.update(dt, player, this));
      this.skullBarrages = this.skullBarrages.filter((sb) => sb.update(dt, player, this));
    }

    _checkStaminaForAttack(player, cost) {
      if (player.is_fatigued) {
        AudioMgr.playSound("cancel");
        this.floatingTexts.push(new FloatingText(player.x + 24, player.y - 12, "FATIGUE! (STA < 10)", "#f05a5a", 15));
        return false;
      }
      if (player.stamina < cost) {
        AudioMgr.playSound("cancel");
        this.floatingTexts.push(new FloatingText(player.x + 24, player.y - 12, `Butuh ${Math.floor(cost)} STA!`, "#f08c5a", 15));
        return false;
      }
      return true;
    }

    performAttack(player, mouseLogicalPos, camX, camY, targets, inventory, tierMult) {
      if (this.attackCdTimer > 0 || player.is_dead || player.is_rolling || player.stagger_timer > 0) return false;
      if (!this._checkStaminaForAttack(player, C.BASIC_ATTACK_STAMINA)) return false;

      player.consumeStamina(C.BASIC_ATTACK_STAMINA);
      this.attackCdTimer = this.attackCooldown;

      const cx = player.x + 24;
      const cy = player.y + 24;
      const wx = mouseLogicalPos[0] + camX;
      const wy = mouseLogicalPos[1] + camY;
      const angle = Math.atan2(wy - cy, wx - cx);

      this.slashEffects.push(new SlashEffect(cx, cy, angle, 62, false));
      AudioMgr.playSound(Math.random() < 0.5 ? "slash1" : "slash2");

      const attackRange = 78.0;
      const arcWidth = Math.PI * 0.85;
      let usedCritBuff = false;

      for (const target of targets) {
        if (!target.isAlive()) continue;
        const [tcx, tcy] = target.getCenter();
        const dist = Math.hypot(tcx - cx, tcy - cy);
        if (dist <= attackRange) {
          const targetAng = Math.atan2(tcy - cy, tcx - cx);
          const diff = (((targetAng - angle + Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
          if (Math.abs(diff) <= arcWidth / 2) {
            if (this._applyDamageToTarget(player, target, false, inventory, tierMult)) {
              usedCritBuff = true;
            }
          }
        }
      }
      if (usedCritBuff) player.next_attack_crit_buff = false;
      return true;
    }

    performSkill(player, mouseLogicalPos, camX, camY, targets, inventory, tierMult) {
      if (this.skillCdTimer > 0 || player.is_dead || player.is_rolling || player.stagger_timer > 0) return false;
      if (!this._checkStaminaForAttack(player, C.SKILL_ATTACK_STAMINA)) return false;

      player.consumeStamina(C.SKILL_ATTACK_STAMINA);
      this.skillCdTimer = this.skillCooldown;

      const cx = player.x + 24;
      const cy = player.y + 24;
      this.slashEffects.push(new SlashEffect(cx, cy, 0, 96, true));
      this.triggerShake(0.25, 6.0);
      AudioMgr.playSound("skill_slash");
      AudioMgr.playSound("skill_fx");

      const skillRange = 102.0;
      let usedCritBuff = false;
      for (const target of targets) {
        if (!target.isAlive()) continue;
        const [tcx, tcy] = target.getCenter();
        const dist = Math.hypot(tcx - cx, tcy - cy);
        if (dist <= skillRange) {
          if (this._applyDamageToTarget(player, target, true, inventory, tierMult)) {
            usedCritBuff = true;
          }
        }
      }
      if (usedCritBuff) player.next_attack_crit_buff = false;
      return true;
    }

    _applyDamageToTarget(player, target, isSkill, inventory, tierMult) {
      const enemyDef = target.defense || 0;
      const atkSum = player.totalDamage * (isSkill ? 1.85 : 1.0);

      let usedPerfectCrit = false;
      let isCrit = false;
      let mod = 1.0;
      const critRate = player.effectiveCritChance;
      if (player.next_attack_crit_buff) {
        isCrit = true;
        mod = 1.5;
        usedPerfectCrit = true;
      } else if (Math.random() < critRate || isSkill) {
        isCrit = true;
        mod = 1.5;
      }

      const denom = enemyDef * 0.5 + 10.0;
      const variance = 0.94 + Math.random() * 0.14;
      const rawDamage = Math.max(1, Math.round((atkSum / denom) * C.PLAYER_DAMAGE_SCALING * mod * variance));

      const dmgDealt = target.takeDamage(rawDamage);
      const [tcx, tcy] = target.getCenter();

      if (typeof target.applyKnockback === "function") {
        const pcx = player.x + 24;
        const pcy = player.y + 24;
        const dx = tcx - pcx;
        const dy = tcy - pcy;
        const dist = Math.hypot(dx, dy);
        if (dist > 0) {
          const force = isSkill ? 190.0 : 130.0;
          target.applyKnockback((dx / dist) * force, (dy / dist) * force);
        }
      }

      const text = isCrit ? `CRIT! ${dmgDealt}` : String(dmgDealt);
      const color = isCrit ? C.COLOR_CRIT : C.COLOR_WHITE;
      this.floatingTexts.push(new FloatingText(tcx, tcy - 20, text, color, isCrit ? 20 : 17, isCrit));

      if (!target.isAlive()) {
        const [rewardExp, rewardAsh, rewardGold] = target.getRewards();
        if (rewardExp > 0) {
          const leveled = player.gainExp(rewardExp);
          this.floatingTexts.push(new FloatingText(tcx, tcy - 40, `+${rewardExp} EXP`, C.COLOR_EXP, 18, true));
          if (leveled) {
            this.floatingTexts.push(new FloatingText(player.x + 24, player.y - 50, "LEVEL UP!", C.COLOR_GOLD, 24, true));
          }
        }
        if (rewardAsh > 0) {
          player.monster_ash += rewardAsh;
          this.floatingTexts.push(new FloatingText(tcx, tcy - 58, `+${rewardAsh} Ash`, C.COLOR_ASH, 15));
        }
        if (rewardGold > 0) {
          player.gold += rewardGold;
          this.floatingTexts.push(new FloatingText(tcx, tcy - 74, `+${rewardGold} Gold`, C.COLOR_GOLD, 15));
        }

        if (inventory && target.isMonster) {
          const isBossTarget = Boolean(target.isBoss);
          const dropId = rollMaterialDrop(tierMult, isBossTarget, player.dropMultiplier);
          if (dropId && inventory.addItem(dropId, 1)) {
            const dItem = ITEM_DATABASE[dropId];
            if (dItem) {
              const col = global.OakhavenInventory.RARITY_COLORS[dItem.rarity] || C.COLOR_WHITE;
              this.floatingTexts.push(new FloatingText(tcx, tcy - 90, `+1 ${dItem.name}`, col, 14, true));
            }
          }
          const consDrop = rollConsumableDrop(isBossTarget, tierMult, player.dropMultiplier);
          if (consDrop && inventory.addItem(consDrop, 1)) {
            const cItem = ITEM_DATABASE[consDrop];
            if (cItem) {
              this.floatingTexts.push(new FloatingText(tcx, tcy - 108, `+1 ${cItem.name} [Hotbar]`, "#82f5c3", 13, true));
            }
          }
        }
      }

      return usedPerfectCrit;
    }

    draw(ctx, camX, camY) {
      for (const tr of this.traps) tr.draw(ctx, camX, camY);
      for (const fx of this.slashEffects) fx.draw(ctx, camX, camY);
      for (const pr of this.projectiles) pr.draw(ctx, camX, camY);
      for (const sb of this.skullBarrages) sb.draw(ctx, camX, camY);
      for (const ft of this.floatingTexts) ft.draw(ctx, camX, camY);
    }
  }

  global.OakhavenCombat = {
    DROP_TABLE_TIERS,
    rollConsumableDrop,
    rollMaterialDrop,
    FloatingText,
    SlashEffect,
    Projectile,
    SporeTrap,
    SkullLaserBarrage,
    CombatManager,
  };
})(window);
