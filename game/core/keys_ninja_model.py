import random
import string

# Base settings - simple and slow
_BASE_RISE_SPEED = 11.0      # Rise speed
_MAX_KEYS_ON_SCREEN = 8      # Maximum keys that can be on screen at once


# Difficulty presets — Easy is gentler, Hard ratchets up the pressure.
# Each preset tunes the auto-scaling curves (it doesn't replace them) so the
# in-run ramp still happens, just from a different starting point.
#
#   starting_lives    — initial life count
#   spawn_base        — starting ms between spawn waves (before score reduction)
#   spawn_floor       — minimum ms between spawn waves once fully ramped
#   spawn_step_score  — how many points before the spawn interval drops 100ms
#   speed_cap         — maximum fall-speed multiplier
#   speed_per_point   — how quickly the fall-speed multiplier climbs with score
#   bomb_start_score  — score at which bombs start appearing
#   bomb_chance       — bomb spawn probability past the start threshold
_DIFFICULTY_PRESETS = {
    'easy':   {
        'starting_lives':   4,
        'spawn_base':       3000,
        'spawn_floor':      1400,
        'spawn_step_score': 75,
        'speed_cap':        1.4,
        'speed_per_point':  1 / 1400,
        'bomb_start_score': 200,
        'bomb_chance':      0.10,
    },
    'normal': {
        'starting_lives':   3,
        'spawn_base':       2500,
        'spawn_floor':      1000,
        'spawn_step_score': 50,
        'speed_cap':        1.6,
        'speed_per_point':  1 / 1000,
        'bomb_start_score': 100,
        'bomb_chance':      0.15,
    },
    'hard':   {
        'starting_lives':   2,
        'spawn_base':       2000,
        'spawn_floor':      700,
        'spawn_step_score': 35,
        'speed_cap':        1.8,
        'speed_per_point':  1 / 700,
        'bomb_start_score': 50,
        'bomb_chance':      0.22,
    },
}


class KeyObject:
    """Represents a single key falling on screen."""
    
    def __init__(self, char, x, y, is_bomb=False):
        self.char = char
        self.x = x
        self.y = y
        self.is_bomb = is_bomb
        self.velocity_y = 0
        self.velocity_x = 0  # Horizontal velocity for arc motion
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-0.5, 0.5)  # Much slower rotation
        self.state = 'rising'  # rising | falling | hit
        self.alpha = 255
        self.hit_time = 0
        self.scale = 1.0  # For hit animation


class KeysNinjaModel:
    """Keys Ninja game mode: keys pop up from bottom, player must press them before they fall.
    
    Spawns multiple keys at once. Speed increases at score thresholds.
    States: playing | gameover
    """
    
    def __init__(self, event_bus, difficulty: str = 'normal'):
        self._bus = event_bus
        self._preset = _DIFFICULTY_PRESETS.get(
            difficulty, _DIFFICULTY_PRESETS['normal']
        )
        self.difficulty = difficulty if difficulty in _DIFFICULTY_PRESETS else 'normal'
        self.reset()

    @property
    def time_limit(self) -> int:
        """No timer in Keys Ninja mode, but needed for compatibility."""
        return 999999

    def _get_keys_per_spawn(self) -> int:
        """How many keys to spawn at once based on score - random selection."""
        if self.score < 60:
            # Early game: only 1 key
            return 1
        elif self.score < 200:
            # Mid game: 60% chance of 1 key, 40% chance of 2 keys
            return random.choices([1, 2], weights=[60, 40])[0]
        else:
            # Late game: randomly 1, 2, or 3 keys
            return random.choice([1, 2, 2, 3])  # 25% 1-key, 50% 2-keys, 25% 3-keys

    def _get_spawn_interval(self) -> int:
        """Spawn interval shrinks as score climbs — more keys, faster."""
        step = self._preset['spawn_step_score']
        reduction = (self.score // step) * 100
        return max(self._preset['spawn_floor'],
                   self._preset['spawn_base'] - reduction)

    def _get_speed_multiplier(self) -> float:
        """Rise/fall speed multiplier — keys move faster at higher scores."""
        return min(self._preset['speed_cap'],
                   1.0 + self.score * self._preset['speed_per_point'])

    def _get_stagger_window(self) -> int:
        """Max ms to spread a wave's keys across — wider window at higher scores."""
        # 600ms baseline, +200ms per 100 points, capped at 1400ms.
        # Wider window means waves drip in over a longer span instead of
        # arriving as a wall.
        return min(1400, 600 + (self.score // 100) * 200)

    def _get_bomb_chance(self) -> float:
        """Bomb chance based on score."""
        if self.score < self._preset['bomb_start_score']:
            return 0.0
        return self._preset['bomb_chance']

    def reset(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.lives = self._preset['starting_lives']
        self.state = 'playing'
        self.keys: list[KeyObject] = []
        self.last_spawn_time = 0
        # Pending (spawn_time_ms, position) tuples — lets a wave's keys arrive
        # at staggered random times instead of all at the same instant.
        self._pending_spawns: list[tuple[int, str]] = []
        self.gameover_reason = "Out of lives!"
        
        # Visual state
        self.flash_button = None
        self.flash_state = 'normal'
        self.flash_end = 0
        
        # For compatibility with existing views
        self.sequence = []
        self.player_index = 0
        self.current_command = None
    
    def _spawn_key_at_position(self, screen_width: int, screen_height: int, position: str):
        """Spawn a key at a specific position to avoid overlap."""
        # Random character (A-Z, excluding P, excluding letters already on screen
        # so handle_input always has an unambiguous match).
        active_letters = {k.char for k in self.keys}
        available_chars = [c for c in string.ascii_uppercase
                           if c != 'P' and c not in active_letters]
        if not available_chars:
            return
        char = random.choice(available_chars)
        
        # Position-based x coordinate with more spacing
        if position == 'left':
            x = random.randint(80, screen_width // 3 - 40)
        elif position == 'right':
            x = random.randint(2 * screen_width // 3 + 40, screen_width - 80)
        else:  # center
            x = random.randint(screen_width // 3 + 40, 2 * screen_width // 3 - 40)
        
        # Start from bottom
        y = screen_height - 30
        
        # Small chance for bomb key based on score
        is_bomb = random.random() < self._get_bomb_chance()
        # Bombs keep their random letter - they just look red
        
        key_obj = KeyObject(char, x, y, is_bomb)

        speed_mult = self._get_speed_multiplier()

        # Set initial velocities for arc motion (like Fruit Ninja)
        key_obj.velocity_y = -_BASE_RISE_SPEED * speed_mult

        # Add horizontal velocity for arc effect
        center_x = screen_width // 2
        if x < center_x:
            key_obj.velocity_x = random.uniform(0.5, 2.0) * speed_mult  # Move right
        else:
            key_obj.velocity_x = random.uniform(-2.0, -0.5) * speed_mult  # Move left
        
        self.keys.append(key_obj)
        # Note: wave timing (`last_spawn_time`) is owned by the update loop now,
        # so individual staggered spawns inside a wave don't reset the clock.
    
    def update(self, now: int, screen_width: int, screen_height: int) -> bool:
        """Update all keys positions and spawn new ones."""
        if self.state != 'playing':
            return False
        
        # On interval tick, schedule a wave of keys to arrive at staggered
        # random times (instead of all at once).
        spawn_interval = self._get_spawn_interval()
        if now - self.last_spawn_time >= spawn_interval:
            keys_to_spawn = self._get_keys_per_spawn()
            if keys_to_spawn == 1:
                positions = [random.choice(['left', 'center', 'right'])]
            elif keys_to_spawn == 2:
                positions = ['left', 'right']
            else:
                positions = ['left', 'center', 'right']
            random.shuffle(positions)

            stagger_window = self._get_stagger_window()
            for i, position in enumerate(positions):
                # First key in the wave arrives immediately so the cadence
                # never stalls; the rest land at random offsets within the
                # stagger window.
                offset = 0 if i == 0 else random.randint(120, stagger_window)
                self._pending_spawns.append((now + offset, position))
            self.last_spawn_time = now

        # Drain any pending spawns whose time has come.
        if self._pending_spawns:
            still_pending = []
            active_keys = sum(
                1 for key in self.keys if key.state in ('rising', 'falling')
            )
            for spawn_at, position in self._pending_spawns:
                if spawn_at <= now and active_keys < _MAX_KEYS_ON_SCREEN:
                    self._spawn_key_at_position(screen_width, screen_height, position)
                    active_keys += 1
                elif spawn_at > now:
                    still_pending.append((spawn_at, position))
                # else: screen is full at the scheduled moment — drop it.
            self._pending_spawns = still_pending
        
        # Update existing keys
        speed_mult = self._get_speed_multiplier()
        # Square the multiplier on gravity so total flight time scales down
        # (v*s, g*s^2 keeps apex height stable while shrinking flight time by s).
        gravity = 0.15 * speed_mult * speed_mult
        keys_to_remove = []
        for key in self.keys:
            if key.state == 'hit':
                # Fade out and scale up hit keys
                key.alpha -= 15
                key.scale += 0.05
                if key.alpha <= 0:
                    keys_to_remove.append(key)
                continue

            # Update position (arc motion like Fruit Ninja)
            key.y += key.velocity_y
            key.x += key.velocity_x
            key.rotation += key.rotation_speed

            key.velocity_y += gravity
            
            # State transitions based on velocity
            if key.state == 'rising' and key.velocity_y >= 0:
                key.state = 'falling'
            
            # Check if key fell off screen (bottom)
            if key.y > screen_height + 50:
                if not key.is_bomb:
                    # Missed a key - lose a life
                    self.lives -= 1
                    self.combo = 0  # Reset combo on miss
                    keys_to_remove.append(key)
                    
                    if self.lives <= 0:
                        # Out of lives - game over
                        self.state = 'gameover'
                        self.gameover_reason = "Out of lives!"
                        return False
                else:
                    # Bomb fell off - that's good!
                    keys_to_remove.append(key)
            
            # Remove keys that went too high off screen (shouldn't happen but safety check)
            if key.y < -100:
                keys_to_remove.append(key)
        
        # Remove dead keys
        for key in keys_to_remove:
            self.keys.remove(key)
        
        # Clear flash state
        if self.flash_button and now >= self.flash_end:
            self.flash_button = None
            self.flash_state = 'normal'
        
        return False
    
    def handle_input(self, char: str, now: int) -> str:
        """Process a key press."""
        if self.state != 'playing':
            return 'wrong'
        
        char = char.upper()
        
        # Find matching key
        hit_key = None
        for key in self.keys:
            if key.state in ('rising', 'falling') and key.char == char:
                hit_key = key
                break
        
        if hit_key:
            if hit_key.is_bomb:
                # Hit a bomb - instant game over!
                self.lives = 0
                self.state = 'gameover'
                self.gameover_reason = "Hit a bomb!"
                self._bus.emit('input_result', {'result': 'wrong', 'name': char})
                return 'wrong'
            else:
                # Correct key!
                hit_key.state = 'hit'
                hit_key.hit_time = now
                hit_key.scale = 1.0  # Reset scale for animation
                self.score += 10  # Always 10 points per key
                self.combo += 1
                self.max_combo = max(self.max_combo, self.combo)
                
                # No bonus points - keep it simple at 10 per key
                
                self._bus.emit('input_result', {'result': 'correct', 'name': char})
                return 'correct'
        else:
            # Wrong key or no matching key
            self.combo = 0
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 0
                self.state = 'gameover'
                self.gameover_reason = "Out of lives!"
                self._bus.emit('input_result', {'result': 'wrong', 'name': char})
                return 'wrong'
            # Don't end game, just reset combo
            return 'wrong'
    
    def on_timer_expired(self, data) -> None:
        """No timer in Keys Ninja mode."""
        pass
