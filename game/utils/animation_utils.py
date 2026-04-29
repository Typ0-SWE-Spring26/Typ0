import pygame
import math
import sys
import platform as _p

# ── Web audio bridge ──────────────────────────────────────────────────────────
# When running as a pygbag/WASM web build, pygame.mixer is broken.
# Instead we delegate to window.typAudio — a JS AudioManager injected via a
# <script> tag in index.html by the CI build process.
_IS_WEB = sys.platform == "emscripten"

# ── Music selection tracking ──────────────────────────────────────────────────
# Tracks whether the user has explicitly chosen a music track from the in-game
# music menu.  None means the user hasn't made a choice — gameplay will default
# to the main theme.  A path means we should preserve that choice when
# transitioning into gameplay.
_user_selected_music: str | None = None


def set_user_music_selection(path: str) -> None:
    """Record an explicit user music choice (called from MusicMenu.play_music)."""
    global _user_selected_music
    _user_selected_music = path


def get_user_music_selection() -> "str | None":
    """Return the user's explicit track choice, or None if they haven't picked."""
    return _user_selected_music


# ── Music override lock ──────────────────────────────────────────────────────
# When True, the in-game music menu must not start a new track (used on the
# game-over screen so the ending riff isn't clobbered by a user track pick).
_music_menu_locked: bool = False


def set_music_menu_locked(locked: bool) -> None:
    global _music_menu_locked
    _music_menu_locked = bool(locked)


def is_music_menu_locked() -> bool:
    return _music_menu_locked


def _web_audio(method, *args):
    """Call window.typAudio.<method>(*args) in the browser.

    Returns the JS return value on success; True when the method returns void
    (JS undefined → Python None). Returns None on any exception so callers can
    distinguish success from failure without crashing the game.
    """
    try:
        result = getattr(_p.window.typAudio, method)(*args)
        return result if result is not None else True
    except Exception as _exc:
        print(f"[Web Audio] {method} failed: {_exc}")
        return None


# ── Audio helpers ─────────────────────────────────────────────────────────────

# Cache for pre-rendered gradient surfaces, keyed by (size, top_color, bottom_color)
_gradient_cache = {}

# Cache for loaded pygame.mixer.Sound objects, keyed by filename. Avoids
# reconstructing a Sound on every play_sound() call in hot paths like the
# Keys Ninja keypress handler.
_sound_cache = {}


def draw_gradient(screen, gradient_top=(25, 25, 112), gradient_bottom=(0, 0, 0)):
    """Draw a vertical gradient from top to bottom.

    To avoid expensive per-frame drawing (one draw call per pixel row),
    the gradient is pre-rendered into a cached Surface keyed by size and colors.
    """
    size = screen.get_size()
    cache_key = (size, gradient_top, gradient_bottom)

    gradient_surface = _gradient_cache.get(cache_key)
    if gradient_surface is None:
        width, height = size
        # Create a surface compatible with the display for fast blitting
        gradient_surface = pygame.Surface(size).convert()
        for y in range(height):
            # Calculate the color at this y position
            ratio = y / height
            r = int(gradient_top[0] * (1 - ratio) + gradient_bottom[0] * ratio)
            g = int(gradient_top[1] * (1 - ratio) + gradient_bottom[1] * ratio)
            b = int(gradient_top[2] * (1 - ratio) + gradient_bottom[2] * ratio)
            pygame.draw.line(gradient_surface, (r, g, b), (0, y), (width, y))
        _gradient_cache[cache_key] = gradient_surface

    screen.blit(gradient_surface, (0, 0))

def wave_text(screen, text, position=None, font_size=72, color=(255, 255, 255), bounce_height=15, wave_speed=0.3, font=None, font_name=None):
    """Draw text with each letter bouncing in a wave pattern"""
    if font is None:
        font = pygame.font.SysFont(font_name, font_size) if font_name else pygame.font.Font(None, font_size)
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() // 2)

    # Calculate total width of text to center it
    total_width = sum(font.size(char)[0] for char in text)
    current_x = position[0] - total_width // 2

    # Draw each letter with its own bounce offset
    for i, char in enumerate(text):
        # Each letter bounces with a time offset based on its position
        time_offset = i * wave_speed
        bounce = math.sin((pygame.time.get_ticks() / 500) + time_offset) * bounce_height

        char_surface = font.render(char, True, color)
        char_width = font.size(char)[0]
        char_rect = char_surface.get_rect(center=(current_x + char_width // 2, position[1] + bounce))
        screen.blit(char_surface, char_rect)

        current_x += char_width


def draw_animated_icons(screen, string="TYP0!", position=None, radius=100, font_size=48, color=(255, 255, 255), rotation_speed=2, font=None, font_name=None):
    """Draw animated icons around the title"""
    if not string:
        return
    if position is None:
        position = (screen.get_width() // 2, 200)

    time = pygame.time.get_ticks() / 1000  # Time in seconds
    angle = time * rotation_speed  # Rotate based on rotation_speed
    count = len(string)
    if font is None:
        icon_font = pygame.font.SysFont(font_name, font_size) if font_name else pygame.font.Font(None, font_size)
    else:
        icon_font = font
    for i in range(count):
        icon_x = position[0] + radius * math.cos(angle + i * (2 * math.pi / count))
        icon_y = position[1] + radius * math.sin(angle + i * (2 * math.pi / count))
        # Draw a letter from the string as an icon
        icon_text = icon_font.render(string[i % len(string)], True, color)
        icon_rect = icon_text.get_rect(center=(icon_x, icon_y))
        screen.blit(icon_text, icon_rect)


def float_offset(amplitude=8, speed=2.0, phase=0.0):
    """Return a vertical offset for gentle bobbing animations."""
    time = pygame.time.get_ticks() / 1000
    return math.sin((time * speed) + phase) * amplitude


def flashing_text(screen, text, position=None, font_size=36, color_on=(255, 255, 255), color_off=(100, 100, 100), flash_speed=500, font=None, font_name=None):
    """Draw flashing text at the bottom of the screen"""
    if font is None:
        font = pygame.font.SysFont(font_name, font_size) if font_name else pygame.font.Font(None, font_size)
    flash = (pygame.time.get_ticks() // flash_speed) % 2 == 0
    color = color_on if flash else color_off
    text_surface = font.render(text, True, color)
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() - 30)
    text_rect = text_surface.get_rect(center=position)
    screen.blit(text_surface, text_rect)


def loading_bar(screen, start_time, position=None, width=400, height=20, color=(255, 255, 255), load_time=5000):
    """Draw a loading bar at the bottom of the screen"""
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() - 50)

    bar_x = position[0] - width // 2
    bar_y = position[1]

    pygame.draw.rect(screen, color, (bar_x, bar_y, width, height), 2)
    # Calculate progress based on elapsed time
    elapsed = pygame.time.get_ticks() - start_time
    progress = min(elapsed / load_time, 1.0)
    fill_width = progress * width
    pygame.draw.rect(screen, color, (bar_x, bar_y, fill_width, height))
    return progress >= 1.0  # Return True when bar is full

def play_music(file, loops=-1):
    """Play background music.  loops=-1 repeats forever; loops=0 plays once."""
    if _IS_WEB:
        return _web_audio("playMusic", file, loops) is not None
    try:
        if not pygame.mixer.get_init():
            return False
        pygame.mixer.music.load(file)
        pygame.mixer.music.play(loops)
        return True
    except pygame.error as exc:
        print(f"Warning: failed to load music {file}: {exc}")
        return False


def stop_music():
    """Stop background music."""
    if _IS_WEB:
        _web_audio("stopMusic")
        return
    if not pygame.mixer.get_init():
        return
    pygame.mixer.music.stop()


def pause_music():
    """Pause background music."""
    if _IS_WEB:
        _web_audio("pauseMusic")
        return
    if not pygame.mixer.get_init():
        return
    pygame.mixer.music.pause()


def unpause_music():
    """Resume paused background music."""
    if _IS_WEB:
        _web_audio("unpauseMusic")
        return
    if not pygame.mixer.get_init():
        return
    pygame.mixer.music.unpause()


def set_volume(volume):
    """Set music volume (0.0-1.0)."""
    if _IS_WEB:
        _web_audio("setVolume", volume)
        return
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(volume)


def get_volume():
    """Get current music volume (0.0-1.0)."""
    if _IS_WEB:
        result = _web_audio("getVolume")
        return float(result) if result is not None else 0.5
    if pygame.mixer.get_init():
        return pygame.mixer.music.get_volume()
    return 0.5


# ── User-upload bridge (web only) ────────────────────────────────────────────

def show_upload_button():
    """Show the HTML upload-music button overlay (web builds only)."""
    if _IS_WEB:
        _web_audio("showUploadButton")


def hide_upload_button():
    """Hide the HTML upload-music button overlay (web builds only)."""
    if _IS_WEB:
        _web_audio("hideUploadButton")


def get_user_track_count():
    """Return the number of tracks the user has uploaded this session."""
    if not _IS_WEB:
        return 0
    result = _web_audio("getUserTrackCount")
    try:
        return int(result) if result is not None and result is not True else 0
    except (TypeError, ValueError):
        return 0


def get_user_track_name(index):
    """Return the display name of user track at index."""
    if not _IS_WEB:
        return ""
    result = _web_audio("getUserTrackName", index)
    return str(result) if result is not None and result is not True else ""


def get_user_track_url(index):
    """Return the blob URL of user track at index (pass to play_music)."""
    if not _IS_WEB:
        return ""
    result = _web_audio("getUserTrackUrl", index)
    return str(result) if result is not None and result is not True else ""


def try_unlock_audio():
    """Explicitly unlock web audio — call on any pygame event so music starts
    as soon as the user interacts with the game canvas."""
    if _IS_WEB:
        _web_audio("tryUnlock")


def has_new_user_track():
    """Return True if a track was uploaded since the last clear_new_track_flag()."""
    if not _IS_WEB:
        return False
    result = _web_audio("hasNewTrack")
    return bool(result) if result is not None else False


def get_last_added_track_index():
    """Return the _userTracks index of the most recently uploaded track."""
    if not _IS_WEB:
        return -1
    result = _web_audio("getLastAddedTrackIndex")
    try:
        return int(result) if result is not None and result is not True else -1
    except (TypeError, ValueError):
        return -1


def clear_new_track_flag():
    """Reset the new-track flag after auto-selecting the uploaded track."""
    if _IS_WEB:
        _web_audio("clearNewTrackFlag")


def is_music_playing() -> bool:
    """Return True if music is currently playing (not stopped or paused)."""
    if _IS_WEB:
        result = _web_audio("isPlaying")
        return bool(result) if result is not None else False
    if not pygame.mixer.get_init():
        return False
    return bool(pygame.mixer.music.get_busy())


def play_sound(file):
    """Play a one-shot sound effect."""
    if _IS_WEB:
        _web_audio("playSound", file)
        return
    try:
        sound = _sound_cache.get(file)
        if sound is None:
            sound = pygame.mixer.Sound(file)
            _sound_cache[file] = sound
        sound.play()
    except pygame.error as exc:
        print(f"Warning: failed to play sound {file}: {exc}")


def draw_shadowed_text(screen, font, text, center, color=(255, 255, 255), shadow_color=(0, 0, 0), shadow_offset=1):
    """Draw text centered at a position with a drop shadow."""
    shadow_surf = font.render(text, True, shadow_color)
    screen.blit(shadow_surf, shadow_surf.get_rect(center=(center[0] + shadow_offset, center[1] + shadow_offset)))
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, text_surf.get_rect(center=center))


# Physical Countdown Timer
def draw_countdown_timer(screen, time_left, position=None, font_size=48, color=(255, 255, 255), font=None, font_name=None):
    """Draw a countdown timer with a circular progress bar"""
    if font is None:
        font = pygame.font.SysFont(font_name, font_size) if font_name else pygame.font.Font(None, font_size)
    if position is None:
        position = (screen.get_width() // 2, screen.get_height() // 2)

    # Draw circular progress bar
    radius = 60
    thickness = 10
    end_angle = (time_left / 10000) * 360  # Assuming time_left is in milliseconds and max is 10 seconds
    pygame.draw.circle(screen, (100, 100, 100), position, radius, thickness)  # Background circle
    pygame.draw.arc(screen, (255, 255, 255), (position[0] - radius, position[1] - radius, radius * 2, radius * 2), -math.pi / 2, math.radians(end_angle - 90), thickness)

    # Draw time left as text
    seconds_left = max(0, int(time_left / 1000))
    text_surf = font.render(str(seconds_left), True, color)
    text_rect = text_surf.get_rect(center=position)
    screen.blit(text_surf, text_rect)
