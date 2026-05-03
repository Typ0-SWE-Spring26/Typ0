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
from game.screens.startmenu import StartMenu
from game.screens.gameplay.display import GameScreen
from game.screens.gameplay.bopit_display import BopItScreen
from game.screens.gameplay.keys_ninja_display import KeysNinjaScreen
from game.screens.gameover import GameOverScreen
from game.screens.credits import CreditsScreen
from game.screens.how_to_play import HowToPlayScreen
from game.screens.name_entry import NameEntryScreen
from game.screens.high_scores import HighScoresScreen
from game.core.keybinds import KeybindManager
from game.core.high_scores import is_high_score_async, add_score_async
from game.screens.gameplay.pause_overlay import PauseOverlay
from game.screens.menu import MenuOverlay
from game.screens.config_screen import ConfigScreen
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

        # Persist multiplayer score (name already known from login)
        if await is_high_score_async(my_score, "multiplayer"):
            await add_score_async(my_name, my_score, "multiplayer")

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


async def _run_single_player_post_game(screen, game_mode, difficulty, score, reason, hs_name):
    """Run the game-over/high-scores/credits loop and return next navigation state."""
    result = "high_scores"

    while result in ("high_scores", "credits"):
        if result == "high_scores":
            game_over = GameOverScreen(screen, score=score, reason=reason)
            result = await game_over.run()

            if result == "high_scores":
                hs_screen = HighScoresScreen(
                    screen,
                    game_mode=game_mode,
                    difficulty=difficulty,
                    highlight_name=hs_name,
                    highlight_score=score if hs_name else None,
                )
                result = await hs_screen.run()

        if result == "credits":
            credits = CreditsScreen(screen)
            cr = await credits.run()
            if cr == "quit":
                return "quit"
            result = "high_scores"

    return result


async def _run_single_player(screen, keybinds, game_mode):
    
    """Run config -> gameplay -> post-game loop for one single-player mode."""
    pause_overlay = PauseOverlay(screen)

    # Persist previous selection across retries so the config screen feels continuous.
    selected_inverted = False
    selected_difficulty = "normal"
    result = "retry"

    while result == "retry":
        config_screen = ConfigScreen(
            screen,
            game_mode,
            initial_inverted=selected_inverted,
            initial_difficulty=selected_difficulty,
        )
        config_result = await config_screen.run()
        if config_result == "quit":
            return "quit"
        if config_result == "back":
            return "menu"

        selected_inverted = config_result["inverted"]
        selected_difficulty = config_result["difficulty"]

        # Apply user choices
        keybinds.inverted = selected_inverted

        if game_mode == "bopit":
            game_screen = BopItScreen(
                screen,
                keybinds,
                pause_overlay=pause_overlay,
                difficulty=selected_difficulty,
            )
        elif game_mode == "keys_ninja":
            game_screen = KeysNinjaScreen(
                screen,
                keybinds,
                pause_overlay=pause_overlay,
                difficulty=selected_difficulty,
            )
        else:
            game_screen = GameScreen(
                screen,
                keybinds,
                pause_overlay=pause_overlay,
                difficulty=selected_difficulty,
            )
        game_result = await game_screen.run()

        if game_result == "quit":
            return "quit"

        # Player used the in-game menu to go to main menu
        if isinstance(game_result, tuple) and game_result and game_result[0] == "main_menu":
            return "menu"

        # Player used the in-game menu to switch modes — bubble up so the
        # outer loop can restart in the other mode.
        if isinstance(game_result, tuple) and game_result and game_result[0] == "switch_mode":
            if len(game_result) > 1:
                return f"start_{game_result[1]}"
            if game_mode == "simon":
                other = "bopit"
            elif game_mode == "bopit":
                other = "keys_ninja"
            else:
                other = "simon"
            return f"start_{other}"

        # game_result is ("gameover", score, reason)
        _, score, reason = game_result

        # Per-difficulty leaderboard: each difficulty has its own bucket so
        # easy-mode runs don't compete against hard-mode runs.
        leaderboard_id = f"{game_mode}_{selected_difficulty}"

        # Arcade-style: name entry if high score
        hs_name = None
        if await is_high_score_async(score, leaderboard_id):
            name_entry = NameEntryScreen(screen, score)
            name_result = await name_entry.run()
            if name_result == "quit":
                return "quit"
            hs_name = name_result
            await add_score_async(hs_name, score, leaderboard_id)

        result = await _run_single_player_post_game(
            screen, game_mode, selected_difficulty, score, reason, hs_name
        )

    return result


async def main():
    pygame.init()
    _seed_session_randomness()
    window = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("TYP0")
    screen = ScaledScreen(window)

    keybinds = KeybindManager()

    # Start on the main menu.
    result = "menu"

    # ------------------------------------------------------------------ #
    # Main navigation loop — allows returning to the menu from anywhere.  #
    # ------------------------------------------------------------------ #
    while result != "quit":

        # --- Start menu ---
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
                if result == "how_to_play":
                    how_to_play = HowToPlayScreen(screen)
                    about_result = await how_to_play.run()
                    if about_result == "quit":
                        result = "quit"
                        break
                    if about_result == "credits":
                        credits = CreditsScreen(screen)
                        cr = await credits.run()
                        if cr == "quit":
                            result = "quit"
                            break
                    continue  # back to menu
                break  # "start_simon", "start_bopit", "multiplayer", or "quit"

        if result == "quit":
            break

        # --- Multiplayer ---
        if result == "multiplayer":
            result = await _run_multiplayer(screen, keybinds)
            # result is "menu", "quit", etc. — loop back to top
            continue

        # --- Single-player game modes ---
        if result in ("start", "start_simon", "start_bopit", "start_keys_ninja"):
            if result == "start_bopit":
                game_mode = "bopit"
            elif result == "start_keys_ninja":
                game_mode = "keys_ninja"
            else:
                game_mode = "simon"
            result = await _run_single_player(screen, keybinds, game_mode)
            continue

        # Unknown result — fall back to menu
        result = "menu"

    pygame.quit()


asyncio.run(main())
