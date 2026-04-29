# Keys Ninja Mode

## Overview
Keys Ninja is a fast-paced typing game mode inspired by Fruit Ninja. Keys pop up from the bottom of the screen, and players must press the correct keys before they fall off-screen.

## Gameplay

### Core Mechanics
- Keys spawn from the bottom of the screen with a Fruit-Ninja-style arc trajectory
- They rise upward, slow down under gravity, then fall back down
- Press the matching keyboard key (A-Z) before it falls off-screen
- Missing a key costs one life — you start with 3 lives
- Keys slowly rotate/spin as they move

### Visual Design
- **Purple Theme**: Keys are rendered in purple with a neon glow effect
- **3D Effect**: Keys have shadows and highlights for depth
- **Smooth Animation**: Keys rotate slowly and scale up when hit
- **Grid Background**: Subtle grid pattern for visual interest

### Scoring System
- **Base Score**: 10 points per key (flat — no combo bonus)
- **Combo Tracking**: Consecutive hits build a combo counter
  - Wrong/missed key resets the combo to 0
- **Max Combo**: Tracks your best combo streak

### Special Keys
- **Bomb Keys (Red)**:
  - Start appearing once your score reaches 100
  - Must NOT be pressed
  - Pressing a bomb = instant Game Over
  - Letting bombs fall off-screen is safe

### Difficulty

Keys Ninja runs at a single fixed pacing — there is no difficulty selection. Spawn cadence and key counts are tuned by score:

**Spawn Rate:** constant 2500ms between spawn waves (`_get_spawn_interval`).

**Simultaneous Spawns:** governed by `_get_keys_per_spawn()`:
- Score < 60: always 1 key
- Score 60–199: 60% one key / 40% two keys
- Score 200+: random mix of 1, 2, or 3 keys

**Max Keys On Screen:** capped at `_MAX_KEYS_ON_SCREEN = 8`.

**Movement:** keys launch upward at `_BASE_RISE_SPEED = 11.0` with a small horizontal velocity for arc, and gravity (`+0.15` per frame to vertical velocity) brings them back down.

**Bomb Chance:** 0% before score 100, then 15% per spawn (`_get_bomb_chance`).

## Controls
- **A-Z Keys**: Press the matching key on screen (the letter `P` is reserved and never spawns)
- **ESC**: Open menu
- **Ctrl+E**: Debug shortcut to end game

## Integration
Keys Ninja is integrated with the existing game infrastructure:
- **No difficulty selection** — jumps straight to gameplay (config screen is skipped)
- High scores tracking (separate leaderboard)
- Menu system with mode switching
- Music and sound effects

## Files Created
- `game/core/keys_ninja_model.py` - Game logic
- `game/screens/gameplay/keys_ninja_view.py` - Rendering
- `game/screens/gameplay/keys_ninja_controller.py` - Input handling
- `game/screens/gameplay/keys_ninja_display.py` - Screen wrapper
- `keys_ninja_scores.json` - High scores storage

## Files Modified
- `main.py` - Added mode routing
- `game/screens/startmenu.py` - Added menu button
- `game/screens/menu.py` - Added mode switching
- `game/screens/config_screen.py` - Added difficulty hints

## Future Enhancements
- Power-up keys (bonus points, slow motion, etc.)
- Particle effects on key hits
- Sound effects for hits and combos
- Multiple key types (numbers, special characters)
- Challenge modes (time attack, survival, etc.)
