/**
 * Typ0 Web Audio Manager
 *
 * Replaces pygame.mixer for browser (pygbag/WASM) builds.
 * Exposed as window.typAudio and called from Python via the pygbag JS bridge:
 *
 *   import platform
 *   platform.window.typAudio.playMusic("assets/Typ0__Main_Theme.ogg", -1)
 *
 * Audio files must be served as static HTTP files alongside index.html.
 * The build process copies assets/*.ogg → build/web/assets/*.ogg.
 */

class AudioManager {
  private musicEl: HTMLAudioElement | null = null;
  private _volume: number = 0.7;
  private _paused: boolean = false;

  /**
   * Load and play background music.
   * loops: -1 = infinite loop, 0 = play once, n > 0 = loop n+1 times (pygame semantics)
   */
  playMusic(file: string, loops: number = -1): void {
    this.stopMusic();

    const audio = new Audio(this._toUrl(file));
    audio.volume = this._volume;

    if (loops === -1) {
      audio.loop = true;
    } else if (loops === 0) {
      audio.loop = false;
    } else {
      // Play loops+1 times total (pygame: play(1) means play twice)
      audio.loop = false;
      let count = 0;
      const onEnded = () => {
        count++;
        if (count <= loops && this.musicEl === audio) {
          audio.currentTime = 0;
          audio.play().catch(() => {});
        } else {
          audio.removeEventListener("ended", onEnded);
        }
      };
      audio.addEventListener("ended", onEnded);
    }

    this.musicEl = audio;
    this._paused = false;
    audio.play().catch((e) => console.warn("[typAudio] playMusic failed:", e));
  }

  stopMusic(): void {
    if (this.musicEl) {
      this.musicEl.pause();
      this.musicEl.src = "";
      this.musicEl = null;
    }
    this._paused = false;
  }

  pauseMusic(): void {
    if (this.musicEl && !this._paused) {
      this.musicEl.pause();
      this._paused = true;
    }
  }

  unpauseMusic(): void {
    if (this.musicEl && this._paused) {
      this.musicEl
        .play()
        .catch((e) => console.warn("[typAudio] unpauseMusic failed:", e));
      this._paused = false;
    }
  }

  /** volume: 0.0–1.0 */
  setVolume(v: number): void {
    this._volume = Math.max(0, Math.min(1, Number(v)));
    if (this.musicEl) {
      this.musicEl.volume = this._volume;
    }
  }

  getVolume(): number {
    return this._volume;
  }

  /** Play a one-shot sound effect (fire and forget). */
  playSound(file: string): void {
    const audio = new Audio(this._toUrl(file));
    audio.volume = this._volume;
    audio.play().catch((e) => console.warn("[typAudio] playSound failed:", e));
  }

  /**
   * Normalize Python asset paths to web-relative URLs.
   * "assets\\Techno.ogg" → "assets/Techno.ogg"
   */
  private _toUrl(file: string): string {
    return file.replace(/\\/g, "/");
  }
}

// Expose globally — Python calls window.typAudio.* via pygbag's JS bridge
(window as any).typAudio = new AudioManager();
console.log("[typAudio] Audio manager ready");
