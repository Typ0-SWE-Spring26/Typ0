# /// script
# [pygbag]
# autorun = true
# width = 800
# height = 600
# ///

import asyncio
import pygame
from game.screens.startscreen import StartScreen
from game.screens.startmenu import StartMenu
from game.screens.gameplay.display import GameScreen
from game.screens.gameover import GameOverScreen
from game.core.keybinds import KeybindManager
from game.screens.gameplay.pause_overlay import PauseOverlay

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
    if result == "menu":
        menu_screen = StartMenu(screen)
        result = await menu_screen.run()
    if result == "start":
        pause_overlay = PauseOverlay(screen)
        keybinds = KeybindManager()

        while True:
            game_screen = GameScreen(screen, keybinds, pause_overlay=pause_overlay)
            result = await game_screen.run()

            if result == "quit":
                break

            # result is ("gameover", score, reason)
            _, score, reason = result
            game_over = GameOverScreen(screen, score=score, reason=reason)
            result = await game_over.run()

            if result == "quit":
                break
            # "retry" loops back to a new GameScreen

    pygame.quit()


asyncio.run(main())
