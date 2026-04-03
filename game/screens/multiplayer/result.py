"""Multiplayer win / lose result screen."""

import pygame
import asyncio
from game.utils import animation_utils
from game.utils.button import Button


class MultiplayerResultScreen:
    """
    Shows a winner or loser screen with both scores.

    Returns:
        "lobby"  — play again (back to the lobby)
        "menu"   — return to main menu
        "quit"   — window closed
    """

    _AUTO_LOBBY_MS = 12_000  # auto-return to lobby after 12 s

    def __init__(
        self,
        screen,
        won: bool,
        my_score: int,
        opponent_score: int,
        my_name: str,
        opponent_name: str,
    ):
        self.screen         = screen
        self.won            = won
        self.my_score       = my_score
        self.opponent_score = opponent_score
        self.my_name        = my_name
        self.opponent_name  = opponent_name

        font_btn = pygame.font.Font(None, 36)
        W, H = screen.get_width(), screen.get_height()
        cx = W // 2

        self.btn_lobby = Button(
            pygame.Rect(cx - 210, H - 120, 190, 58),
            "Play Again",
            font_btn,
            color=(35, 95, 35),
            hover_color=(55, 145, 55),
        )
        self.btn_menu = Button(
            pygame.Rect(cx + 20, H - 120, 190, 58),
            "Main Menu",
            font_btn,
        )

        self.font_score = pygame.font.Font(None, 52)
        self.font_names = pygame.font.Font(None, 36)
        self.font_hint  = pygame.font.Font(None, 28)

    async def run(self):
        clock      = pygame.time.Clock()
        start_time = pygame.time.get_ticks()

        if self.won:
            animation_utils.play_music("assets/Typ0__Ending_Riff.ogg", loops=0)
        else:
            animation_utils.play_music("assets/Typ0__Ending_Riff.ogg", loops=0)

        W, H = self.screen.get_width(), self.screen.get_height()
        cx = W // 2

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    animation_utils.stop_music()
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_r):
                        animation_utils.stop_music()
                        return "lobby"
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        animation_utils.stop_music()
                        return "menu"

                if self.btn_lobby.handle_event(event):
                    animation_utils.stop_music()
                    return "lobby"
                if self.btn_menu.handle_event(event):
                    animation_utils.stop_music()
                    return "menu"

            elapsed = pygame.time.get_ticks() - start_time
            if elapsed >= self._AUTO_LOBBY_MS:
                animation_utils.stop_music()
                return "lobby"

            self._draw(cx, H, elapsed)
            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)

    # ------------------------------------------------------------------

    def _draw(self, cx: int, H: int, elapsed: int):
        # Background gradient
        if self.won:
            animation_utils.draw_gradient(
                self.screen, (10, 60, 10), (0, 20, 0)
            )
        else:
            animation_utils.draw_gradient(
                self.screen, (80, 10, 10), (20, 0, 0)
            )

        # Big animated title
        if self.won:
            animation_utils.wave_text(
                self.screen,
                "YOU WIN!",
                (cx, 140),
                font_size=100,
                color=(80, 255, 80),
                bounce_height=12,
                wave_speed=0.35,
            )
        else:
            animation_utils.wave_text(
                self.screen,
                "YOU LOSE",
                (cx, 140),
                font_size=100,
                color=(255, 70, 70),
                bounce_height=8,
                wave_speed=0.25,
            )

        # Score comparison
        W = self.screen.get_width()

        # My score
        my_col    = (120, 255, 120) if self.won else (255, 120, 120)
        opp_col   = (255, 120, 120) if self.won else (120, 255, 120)

        my_label  = self.font_names.render(f"{self.my_name}", True, (200, 200, 200))
        my_val    = self.font_score.render(str(self.my_score), True, my_col)
        opp_label = self.font_names.render(f"{self.opponent_name}", True, (200, 200, 200))
        opp_val   = self.font_score.render(str(self.opponent_score), True, opp_col)

        # Two columns
        left_x  = cx - 130
        right_x = cx + 130
        top_y   = 270

        self.screen.blit(my_label,  my_label.get_rect(center=(left_x,  top_y)))
        self.screen.blit(my_val,    my_val.get_rect(center=(left_x,  top_y + 54)))

        # VS separator
        vs_surf = self.font_score.render("VS", True, (160, 160, 160))
        self.screen.blit(vs_surf, vs_surf.get_rect(center=(cx, top_y + 54)))

        self.screen.blit(opp_label, opp_label.get_rect(center=(right_x, top_y)))
        self.screen.blit(opp_val,   opp_val.get_rect(center=(right_x, top_y + 54)))

        # Flavour text
        if self.won:
            flavour = f"{self.opponent_name} made a mistake — nice work!"
        else:
            flavour = f"Better luck next time, {self.my_name}!"
        fl_surf = self.font_names.render(flavour, True, (180, 180, 180))
        self.screen.blit(fl_surf, fl_surf.get_rect(center=(cx, top_y + 120)))

        # Auto-return countdown
        remaining_s = max(0, (self._AUTO_LOBBY_MS - elapsed) // 1000)
        cd_surf = self.font_hint.render(
            f"Returning to lobby in {remaining_s}s…",
            True,
            (120, 120, 140),
        )
        self.screen.blit(cd_surf, cd_surf.get_rect(center=(cx, H - 148)))

        self.btn_lobby.draw(self.screen)
        self.btn_menu.draw(self.screen)

        animation_utils.flashing_text(
            self.screen,
            "ENTER / R  play again   |   ESC / Q  main menu",
            (cx, H - 40),
            font_size=28,
            color_on=(160, 160, 200),
            color_off=(80, 80, 110),
        )
