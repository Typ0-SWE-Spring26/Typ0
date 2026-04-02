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
from game.screens.gameplay.bopit_display import BopItScreen
from game.screens.gameover import GameOverScreen
from game.screens.credits import CreditsScreen
from game.screens.name_entry import NameEntryScreen
from game.screens.high_scores import HighScoresScreen
from game.core.keybinds import KeybindManager
from game.core.high_scores import is_high_score, add_score
from game.screens.gameplay.pause_overlay import PauseOverlay
from game.screens.menu import MenuOverlay
from game.network.client import WebSocketClient
from game.screens.multiplayer.login import MultiplayerLoginScreen
from game.screens.multiplayer.lobby import MultiplayerLobbyScreen
from game.screens.multiplayer.game import MultiplayerGameScreen
from game.screens.multiplayer.result import MultiplayerResultScreen


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


async def _run_multiplayer(screen, keybinds):
    """Full multiplayer flow: login → lobby → game → result → repeat."""
    client = WebSocketClient()

    # Login
    login = MultiplayerLoginScreen(screen, client)
    login_result = await login.run()

    if login_result == "quit":
        return "quit"
    if login_result == "back":
        return "menu"

    _, my_name = login_result  # ("lobby", name)

    # Lobby → Game → Result loop (stays in multiplayer until player leaves)
    while True:
        lobby = MultiplayerLobbyScreen(screen, client, my_name)
        lobby_result = await lobby.run()

        if lobby_result == "quit":
            return "quit"
        if lobby_result == "menu":
            return "menu"

        # lobby_result == ("game", seed, settings, opponent_name)
        _, seed, settings, opponent = lobby_result

        game = MultiplayerGameScreen(
            screen, client, my_name, opponent, seed, settings, keybinds
        )
        game_result = await game.run()

        if game_result == "quit":
            return "quit"

        # game_result == ("win"|"lose", my_score, opponent_score)
        outcome, my_score, opp_score = game_result
        result_screen = MultiplayerResultScreen(
            screen,
            won=(outcome == "win"),
            my_score=my_score,
            opponent_score=opp_score,
            my_name=my_name,
            opponent_name=opponent,
        )
        res = await result_screen.run()

        if res == "quit":
            return "quit"
        if res == "menu":
            await client.close()
            return "menu"
        # res == "lobby" → loop back to lobby screen


async def main():
    pygame.init()
    _seed_session_randomness()
    window = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TYP0")
    screen = ScaledScreen(window)

    keybinds = KeybindManager()

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
            break  # "start_simon", "start_bopit", "multiplayer", or "quit"

    if result == "multiplayer":
        result = await _run_multiplayer(screen, keybinds)
        # result is now "menu", "quit", etc.

    if result in ("start", "start_simon", "start_bopit"):
        game_mode = "bopit" if result == "start_bopit" else "simon"
        pause_overlay = PauseOverlay(screen)

        while True:
            if game_mode == "bopit":
                game_screen = BopItScreen(screen, keybinds, pause_overlay=pause_overlay)
            else:
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
