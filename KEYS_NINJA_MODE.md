# Keys Ninja Mode

## Overview
Keys Ninja is a fast-paced typing game mode inspired by Fruit Ninja. Keys pop up from the bottom of the screen, and players must press the correct keys before they fall off-screen.

## Gameplay

### Core Mechanics
- Keys spawn from the bottom of the screen
- They rise upward, slow down, then fall back down
- Press the matching keyboard key (A-Z) before it falls off-screen
- Missing a key = Game Over
- Keys slowly rotate/spin as they move

### Visual Design
- **Purple Theme**: Keys are rendered in purple with a neon glow effect
- **3D Effect**: Keys have shadows and highlights for depth
- **Smooth Animation**: Keys rotate slowly and scale up when hit
- **Grid Background**: Subtle grid pattern for visual interest

### Scoring System
- **Base Score**: 10 points per key
- **Combo System**: Consecutive hits build a combo multiplier
  - Combo bonus: +2 points per combo level
  - Missing a key resets the combo
- **Max Combo**: Tracks your best combo streak

### Special Keys
- **Bomb Keys (Red X)**: 
  - Appear after score > 5
  - Must NOT be pressed
  - Pressing a bomb = Game Over
  - Letting bombs fall off-screen is safe

### Difficulty Levels

Keys Ninja features **auto-scaling difficulty** - no need to select a difficulty level! The game starts easy and progressively gets harder as you score more points.

#### Progression System

**Spawn Rate:**
- Starts at 2000ms between keys (slower, more forgiving)
- Decreases by 15ms per point scored
- Minimum: 800ms

**Simultaneous Keys:**
- Starts with max 2 keys on screen
- +1 key every 15 points
- Maximum: 6 keys

**Rise/Fall Speed:**
- Rise speed: 7.0 → 9.0 (increases 0.03 per point, keys go higher!)
- Fall speed: 3.5 → 5.5 (increases 0.03 per point)

**Bomb Keys:**
- No bombs for first 10 points
- After 10 points: 0.8% chance per point scored
- Maximum: 12% chance

**Level Indicators:**
- Score 0-14: Beginner (Green)
- Score 15-29: Intermediate (Yellow)
- Score 30-49: Advanced (Orange)
- Score 50+: MASTER (Red)

## Controls
- **A-Z Keys**: Press the matching key on screen
- **P**: Pause game
- **ESC**: Open menu
- **Ctrl+E**: Debug shortcut to end game

## Integration
Keys Ninja is fully integrated with the existing game infrastructure:
- **No difficulty selection** - jumps straight to gameplay with auto-scaling difficulty
- High scores tracking (separate leaderboard)
- Menu system with mode switching
- Pause overlay support
- Music and sound effects
- Progressive difficulty that increases with each correct key press

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
