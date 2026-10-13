"""
Audio Manager untuk mengelola BGM dan SFX.
Dilengkapi graceful degradation (tidak pernah crash jika audio device bermasalah).
"""
import os
import pygame

class AudioManager:
    def __init__(self):
        self.enabled = True
        self.muted = False
        self.sounds = {}
        self.current_bgm = None
        self.sfx_volume = 0.7
        self.music_volume = 0.4
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"[Audio] Gagal menginisialisasi pygame.mixer: {e}")
            self.enabled = False
            return

        self._load_sounds()

    def _load_sounds(self):
        if not self.enabled:
            return

        audio_dir = "assets/audio"
        sound_files = {
            "slash1": "slash1.wav",
            "slash2": "slash2.wav",
            "skill_slash": "skill_slash.wav",
            "hit1": "hit1.wav",
            "hit2": "hit2.wav",
            "impact": "impact.wav",
            "skill_fx": "skill_fx.wav",
            "heal": "heal.wav",
            "coin": "coin.wav",
            "gold": "gold.wav",
            "powerup": "powerup.wav",
            "levelup": "levelup.wav",
            "roll": "roll.wav",
            "accept": "menu_accept.wav",
            "cancel": "menu_cancel.wav",
            "dialogue_beep": "dialogue_beep.wav",
            "gameover": "gameover.wav",
        }

        for key, filename in sound_files.items():
            path = os.path.join(audio_dir, filename)
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(self.sfx_volume)
                    self.sounds[key] = snd
                except Exception as e:
                    print(f"[Audio] Error loading sound {filename}: {e}")

    def play_sound(self, name):
        if not self.enabled or self.muted:
            return
        snd = self.sounds.get(name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def play_music(self, name="bgm_lobby", loop=-1):
        if not self.enabled or self.muted:
            return
        
        path = f"assets/audio/{name}.ogg"
        if not os.path.exists(path):
            path = f"assets/audio/bgm_peaceful.ogg"
        
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(loop)
                self.current_bgm = name
            except Exception as e:
                print(f"[Audio] Error playing music {path}: {e}")

    def stop_music(self):
        if self.enabled:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        if self.enabled:
            try:
                if self.muted:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
            except Exception:
                pass
        return self.muted

# Singleton instance
audio_manager = AudioManager()
