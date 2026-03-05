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
from game.core.keybinds import KeybindManager, from_flags
from game.screens.gameplay.pause_overlay import PauseOverlay
from game.screens.menu import MenuOverlay
from game.screens.multiplayer_lobby import MultiplayerLobby
from game.core.websocket import MultiplayerClient

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

    elif result == "multiplayer":
        pause_overlay = PauseOverlay(screen)

        while True:
            # --- Lobby ---
            mp_client = MultiplayerClient()
            lobby = MultiplayerLobby(screen, mp_client)
            lobby_result = await lobby.run()

            if lobby_result == "quit":
                break
            if lobby_result == "menu":
                break

            # lobby_result == ("game_start", role, opp_settings_flags)
            _, role, opp_settings_flags = lobby_result

            # Configure game screen — mp_role ensures guest_mode is set after reset()
            game_screen = GameScreen(screen, KeybindManager(), pause_overlay=pause_overlay,
                                     mp_client=mp_client, mp_role=role)

            result = await game_screen.run()

            if mp_client.connected:
                await mp_client.disconnect()

            if result == "quit":
                break

            _, score, reason = result
            game_over = GameOverScreen(screen, score=score, reason=reason)
            go_result = await game_over.run()

            if go_result == "quit":
                break
            # "retry" → loops back to lobby for a rematch

    pygame.quit()


asyncio.run(main())
