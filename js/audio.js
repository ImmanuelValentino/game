(function (global) {
  "use strict";

  const SOUND_FILES = {
    slash1: "assets/audio/slash1.wav",
    slash2: "assets/audio/slash2.wav",
    skill_slash: "assets/audio/skill_slash.wav",
    hit1: "assets/audio/hit1.wav",
    hit2: "assets/audio/hit2.wav",
    impact: "assets/audio/impact.wav",
    skill_fx: "assets/audio/skill_fx.wav",
    heal: "assets/audio/heal.wav",
    coin: "assets/audio/coin.wav",
    gold: "assets/audio/gold.wav",
    powerup: "assets/audio/powerup.wav",
    levelup: "assets/audio/levelup.wav",
    roll: "assets/audio/roll.wav",
    accept: "assets/audio/menu_accept.wav",
    cancel: "assets/audio/menu_cancel.wav",
    dialogue_beep: "assets/audio/dialogue_beep.wav",
    gameover: "assets/audio/gameover.wav",
    projectile: "assets/audio/projectile.wav",
    explosion: "assets/audio/explosion.wav",
    parry: "assets/audio/parry.wav",
    laser: "assets/audio/laser.wav",
    ending_good: "assets/audio/ending_good.wav",
    ending_bad: "assets/audio/ending_bad.wav",
  };

  class WebAudioManager {
    constructor() {
      this.muted = false;
      this.unlocked = false;
      this.sfxVolume = 0.45;
      this.bgmVolume = 0.28;
      this.ctx = null;
      this.buffers = {};
      this.bgmEl = null;
      this.currentBgm = null;
      this.pendingBgm = null;
      this._loadingBuffers = {};
    }

    unlock() {
      if (!this.ctx) {
        const AC = global.AudioContext || global.webkitAudioContext;
        if (AC) {
          try {
            this.ctx = new AC();
          } catch (_) {
            this.ctx = null;
          }
        }
      }
      if (this.ctx && this.ctx.state === "suspended") {
        this.ctx.resume().catch(() => {});
      }
      if (!this.unlocked) {
        this.unlocked = true;
        this._preloadSfx();
      }
      if (this.pendingBgm) {
        const p = this.pendingBgm;
        this.pendingBgm = null;
        this.playMusic(p.name, p.volume);
      }
    }

    _preloadSfx() {
      if (!this.ctx) return;
      for (const [name, url] of Object.entries(SOUND_FILES)) {
        if (this.buffers[name] || this._loadingBuffers[name]) continue;
        this._loadingBuffers[name] = true;
        fetch(url)
          .then((r) => (r.ok ? r.arrayBuffer() : null))
          .then((buf) => (buf && this.ctx ? this.ctx.decodeAudioData(buf) : null))
          .then((decoded) => {
            if (decoded) this.buffers[name] = decoded;
          })
          .catch(() => {});
      }
    }

    playSound(name) {
      if (this.muted) return;
      const url = SOUND_FILES[name];
      if (!url) return;

      if (this.ctx && this.buffers[name]) {
        try {
          const src = this.ctx.createBufferSource();
          const gain = this.ctx.createGain();
          gain.gain.value = this.sfxVolume;
          src.buffer = this.buffers[name];
          src.connect(gain);
          gain.connect(this.ctx.destination);
          src.start(0);
          return;
        } catch (_) {}
      }

      if (this.unlocked) {
        try {
          const a = new Audio(url);
          a.volume = this.sfxVolume;
          a.play().catch(() => {});
        } catch (_) {}
      }
    }

    playMusic(name, volume) {
      const targetVol = volume !== undefined ? volume : 0.28;
      this.bgmVolume = targetVol;
      if (this.currentBgm === name && this.bgmEl) {
        this.bgmEl.volume = this.muted ? 0 : targetVol;
        if (this.bgmEl.paused && this.unlocked && !this.muted) {
          this.bgmEl.play().catch(() => {});
        }
        return;
      }

      this.currentBgm = name;
      if (!this.unlocked) {
        this.pendingBgm = { name, volume: targetVol };
        return;
      }

      this._stopBgmElement();
      const src = `assets/audio/${name}.wav`;
      const el = new Audio(src);
      el.loop = true;
      el.volume = this.muted ? 0 : targetVol;
      this.bgmEl = el;
      if (!this.muted) {
        el.play().catch(() => {
          this.pendingBgm = { name, volume: targetVol };
        });
      }
    }

    _stopBgmElement() {
      if (this.bgmEl) {
        try {
          this.bgmEl.pause();
          this.bgmEl.currentTime = 0;
        } catch (_) {}
        this.bgmEl = null;
      }
    }

    stopMusic() {
      this.currentBgm = null;
      this.pendingBgm = null;
      this._stopBgmElement();
    }

    toggleMute() {
      this.muted = !this.muted;
      if (this.bgmEl) {
        this.bgmEl.volume = this.muted ? 0 : this.bgmVolume;
        if (!this.muted && this.bgmEl.paused) {
          this.bgmEl.play().catch(() => {});
        }
      }
      return this.muted;
    }
  }

  global.OakhavenAudio = new WebAudioManager();
})(window);
