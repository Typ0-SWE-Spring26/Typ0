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

interface UserTrack {
  name: string;
  url: string;
}

export class AudioManager {
  private musicEl: HTMLAudioElement | null = null;
  private _volume: number = 0.7;
  private _paused: boolean = false;

  // ── User-uploaded tracks ──────────────────────────────────────────────────
  private _userTracks: UserTrack[] = [];
  private _uploadBtn: HTMLButtonElement | null = null;
  private _fileInput: HTMLInputElement | null = null;

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

  /** volume: 0.0-1.0 */
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

  // ── User-upload API (called from Python via JS bridge) ────────────────────

  /** Show the HTML upload button overlay above the canvas. */
  showUploadButton(): void {
    if (!this._uploadBtn) this._initUploadElements();
    if (this._uploadBtn) this._uploadBtn.style.display = "block";
  }

  /** Hide the HTML upload button overlay. */
  hideUploadButton(): void {
    if (this._uploadBtn) this._uploadBtn.style.display = "none";
  }

  /** Number of tracks the user has uploaded this session. */
  getUserTrackCount(): number {
    return this._userTracks.length;
  }

  /** Display name of user track at index (e.g. "MY SONG"). */
  getUserTrackName(index: number): string {
    return this._userTracks[index]?.name ?? "";
  }

  /** Blob URL of user track at index — pass directly to playMusic(). */
  getUserTrackUrl(index: number): string {
    return this._userTracks[index]?.url ?? "";
  }

  // ── Private helpers ───────────────────────────────────────────────────────

  /**
   * Create the hidden file input and the visible upload button.
   * Called lazily on first showUploadButton() so the DOM is guaranteed ready.
   */
  private _initUploadElements(): void {
    // Hidden file input — reused across selections
    this._fileInput = document.createElement("input");
    this._fileInput.type = "file";
    this._fileInput.accept = "audio/*";
    this._fileInput.multiple = true;
    this._fileInput.style.display = "none";
    this._fileInput.addEventListener("change", () => this._onFilesSelected());
    document.body.appendChild(this._fileInput);

    // Visible upload button — styled to match the game's aesthetic
    this._uploadBtn = document.createElement("button");
    this._uploadBtn.id = "typ0-upload-btn";
    this._uploadBtn.textContent = "\u2B06 UPLOAD MUSIC";
    Object.assign(this._uploadBtn.style, {
      display: "none",
      position: "fixed",
      bottom: "24px",
      left: "50%",
      transform: "translateX(-50%)",
      padding: "10px 24px",
      background: "#0d0d2b",
      color: "#ffffff",
      border: "2px solid #aaaaaa",
      borderRadius: "8px",
      fontFamily: "monospace, sans-serif",
      fontSize: "13px",
      fontWeight: "bold",
      letterSpacing: "2px",
      cursor: "pointer",
      zIndex: "9999",
      userSelect: "none",
    } as Partial<CSSStyleDeclaration>);

    this._uploadBtn.addEventListener("mouseenter", () => {
      if (this._uploadBtn) this._uploadBtn.style.background = "#1a1a5e";
    });
    this._uploadBtn.addEventListener("mouseleave", () => {
      if (this._uploadBtn) this._uploadBtn.style.background = "#0d0d2b";
    });

    // Direct user click on the button triggers the file picker — this is a
    // trusted gesture so the browser always allows it.
    this._uploadBtn.addEventListener("click", () => {
      this._fileInput?.click();
    });

    document.body.appendChild(this._uploadBtn);
  }

  /** Handle files chosen by the user. */
  private _onFilesSelected(): void {
    const input = this._fileInput;
    if (!input?.files?.length) return;

    for (const file of Array.from(input.files)) {
      const name = this._trackDisplayName(file.name);

      // Replace any existing track with the same display name
      const existing = this._userTracks.findIndex((t) => t.name === name);
      if (existing >= 0) {
        URL.revokeObjectURL(this._userTracks[existing].url);
        this._userTracks.splice(existing, 1);
      }

      this._userTracks.push({ name, url: URL.createObjectURL(file) });
      console.log(`[typAudio] User track added: ${name}`);
    }

    // Reset so the same file(s) can be re-selected if needed
    input.value = "";
  }

  /**
   * Convert a filename to a short uppercase display name.
   * "my cool song.mp3" → "MY COOL SONG"  (capped at 24 chars)
   */
  private _trackDisplayName(filename: string): string {
    return filename
      .replace(/\.[^.]+$/, "")
      .toUpperCase()
      .slice(0, 24)
      .trim();
  }

  /**
   * Normalize Python asset paths to web-relative URLs.
   * "assets\\Techno.ogg" → "assets/Techno.ogg"
   * Blob URLs are returned unchanged.
   */
  private _toUrl(file: string): string {
    return file.replace(/\\/g, "/");
  }
}

// Expose globally — Python calls window.typAudio.* via pygbag's JS bridge
(window as any).typAudio = new AudioManager();
console.log("[typAudio] Audio manager ready");
