# /// script
# [pygbag]
# autorun = true
# width = 800
# height = 600
# ///

import asyncio
import random
import time
import pygame
from game.utils.scaled_screen import ScaledScreen
from game.screens.startscreen import StartScreen
from game.screens.startmenu import StartMenu
from game.screens.gameplay.display import GameScreen
from game.screens.gameover import GameOverScreen
from game.screens.credits import CreditsScreen
from game.screens.name_entry import NameEntryScreen
from game.screens.high_scores import HighScoresScreen
from game.core.keybinds import KeybindManager
from game.core.high_scores import is_high_score, add_score
from game.screens.gameplay.pause_overlay import PauseOverlay
from game.screens.menu import MenuOverlay


def _seed_session_randomness():
    """Seed RNG once per app launch so browser reloads get a fresh sequence."""
    seed = None
    try:
        import os
        seed = int.from_bytes(os.urandom(16), "big")
    except Exception:
        # Fallback for environments without os.urandom support.
        seed = time.time_ns() ^ time.perf_counter_ns()
    random.seed(seed)

async def main():
    pygame.init()
    _seed_session_randomness()
    window = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("TYP0")
    screen = ScaledScreen(window)

    # Show start screen
    start_screen = StartScreen(screen)
    result = await start_screen.run()

    if result == "quit":
        pygame.quit()
        return
    if result == "menu":
        while True:
            menu_screen = StartMenu(screen)
            result = await menu_screen.run()
            if result == "credits":
                credits = CreditsScreen(screen)
                cr = await credits.run()
                if cr == "quit":
                    result = "quit"
                    break
                continue  # back to menu
            break  # "start" or "quit"
    if result in ("start", "start_simon", "start_bopit"):
        pause_overlay = PauseOverlay(screen)
        keybinds = KeybindManager()

        while True:
            game_screen = GameScreen(screen, keybinds, pause_overlay=pause_overlay)
            result = await game_screen.run()

            if result == "quit":
                break

            # result is ("gameover", score, reason)
            _, score, reason = result

            # Arcade-style: name entry if high score
            hs_name = None
            if is_high_score(score):
                name_entry = NameEntryScreen(screen, score)
                name_result = await name_entry.run()
                if name_result == "quit":
                    result = "quit"
                    break
                hs_name = name_result
                add_score(hs_name, score)

            # Game over screen (auto-switches to high scores after 10s)
            result = "high_scores"  # enter loop
            while result == "high_scores" or result == "credits":
                if result == "high_scores":
                    game_over = GameOverScreen(screen, score=score, reason=reason)
                    result = await game_over.run()

                    if result == "high_scores":
                        hs_screen = HighScoresScreen(
                            screen,
                            highlight_name=hs_name,
                            highlight_score=score if hs_name else None,
                        )
                        result = await hs_screen.run()

                if result == "credits":
                    credits = CreditsScreen(screen)
                    cr = await credits.run()
                    if cr == "quit":
                        result = "quit"
                        break
                    result = "high_scores"
                    continue

            if result == "quit":
                break
            # "retry" loops back to a new GameScreen

    pygame.quit()


asyncio.run(main())
