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
from Keybinds import KeybindManager
from game_screens.pause_overlay import PauseOverlay

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TYP0")

    # Show start screen
    start_screen = StartScreen(screen)
    result = await start_screen.run()

    if result == "start":
        pass

    if result == "quit":
        pygame.quit()
        return

    # Your game loop here
    clock = pygame.time.Clock()
    keybinds = KeybindManager()
    running = True
    paused = False
    pause_overlay = PauseOverlay(screen)

    while running:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                # Toggle pause with P key
                if event.key == pygame.K_p:
                    paused = not paused # always will work
                elif not paused:
                    keybinds.process_event(event) #blocked while paused
                    #... other game inputs
                
                # Ctrl + E to jump to game over screen (testing shortcut)
                if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    game_over = GameOverScreen(
                        screen,
                        score=0,
                        reason="Testing - Ctrl+E shortcut"
                    )
                    result = await game_over.run()
                    if result == "quit":
                        running = False
                    # If result == "retry", continue the game loop

        # Only update game logic if not paused
        if not paused:
            # game logic should go here (when implemented)
            pass

        # Draw the game (always draw, even when paused)
        screen.fill((0, 0, 0))
        
        
        # Draw pause overlay on top if paused
        if paused:
            pause_overlay.draw_pause_start()
        
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()


asyncio.run(main())
