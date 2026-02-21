# /// script
# [pygbag]
# autorun = true
# width = 800
# height = 600
# ///

import asyncio
import pygame
from game_screens.startscreen import StartScreen
from game_screens.display import GameScreen
from game_screens.gameover import GameOverScreen
from Keybinds import KeybindManager
from game_screens.pause_overlay import PauseOverlay

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TYP0")

    # Show start screen
    start_screen = StartScreen(screen)
    result = await start_screen.run()

    if result == "quit":
        pygame.quit()
        return

    # Game → Game Over → Retry loop
    while result != "quit":
        game_screen = GameScreen(screen)
        result = await game_screen.run()

        if result == "quit":
            break

        # result is ("gameover", score) — show game over screen
        _, score = result
        game_over = GameOverScreen(screen, score=score, reason="Wrong input!")
        result = await game_over.run()
        # "retry" loops back to a new GameScreen; "quit" exits

    pygame.quit()


asyncio.run(main())
