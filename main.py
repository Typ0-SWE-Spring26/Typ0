# /// script
# [pygbag]
# autorun = true
# width = 800
# height = 600
# ///

import asyncio
import pygame
from game_screens.startscreen import StartScreen
from game_screens.gameover import GameOverScreen

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TYP0")

    # Show start screen
    start_screen = StartScreen(screen)
    result = await start_screen.run()

    if result == "start":
        # Transition to main game screen (not implemented here) - remove pass and add your game loop
        pass

    if result == "quit":
        pygame.quit()
        return

    # Your game loop here
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Ctrl + E to jump to game over screen (testing shortcut)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    game_over = GameOverScreen(screen, score=0, reason="Testing - Ctrl+E shortcut")
                    result = await game_over.run()
                    if result == "quit":
                        running = False
                    # If result == "retry", continue the game loop

        screen.fill((0, 0, 0))
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)  # Required for pygbag

    pygame.quit()

asyncio.run(main())