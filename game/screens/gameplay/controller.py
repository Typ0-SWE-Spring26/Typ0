import pygame
import asyncio
from game.core.game_timer import GameTimer
from game.utils import animation_utils
from game.screens.credits import CreditsScreen  # noqa: F401 (used below)
from game.screens.how_to_play import HowToPlayScreen


class GameController:
    """Orchestrates input, model updates, and view rendering."""

    def __init__(self, screen, model, view, event_bus, keybinds, pause_overlay=None, menu_overlay=None):
        self.screen = screen
        self.model = model
        self.view = view
        self._bus = event_bus
        self.keybinds = keybinds
        self.pause_overlay = pause_overlay
        self.menu_overlay = menu_overlay
        self.paused = False
        self._menu_forced_pause = False

        self.game_timer = GameTimer(self._bus)
        self._bus.subscribe('timer_expired', self.model.on_timer_expired)

        if pause_overlay is not None:
            pause_overlay.subscribe(self._bus)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_paused(self, paused: bool) -> None:
        """Set pause state, emitting events and pausing/unpausing music."""
        if paused == self.paused:
            return
        self.paused = paused
        now_tick = pygame.time.get_ticks()
        if self.paused:
            self._bus.emit('game_paused', {'now': now_tick})
            animation_utils.pause_music()
        else:
            self._bus.emit('game_resumed', {'now': now_tick})
            animation_utils.unpause_music()

    def _exit_overlay_screen(self) -> None:
        """Restore gameplay state after a full-screen overlay (e.g. credits).

        Closes the menu overlay, resumes the game, and replays the gameplay
        music in case the overlay stopped or drifted it.
        """
        if self.menu_overlay:
            self.menu_overlay.open = False
            self.menu_overlay.active_submenu = None
        self._menu_forced_pause = False
        self._set_paused(False)
        # Restart gameplay music — unpauseMusic alone won't recover if the
        # overlay stopped the track entirely.
        if not animation_utils.is_music_playing():
            user_pick = animation_utils.get_user_music_selection()
            track = user_pick if user_pick and user_pick != "assets/Typ0__Intro_Theme.ogg" \
                    else "assets/Typ0__Main_Theme.ogg"
            animation_utils.play_music(track)

    @property
    def _menu_is_open(self) -> bool:
        return self.menu_overlay and (
            self.menu_overlay.open or self.menu_overlay.active_submenu is not None
        )

    def _process_input_result(self, name: str, now: int) -> bool:
        """Call model.handle_input, stop the timer on terminal results.

        Returns True so callers can ``break`` after a matched input.
        """
        animation_utils.play_sound("assets/TypoPressSFX.ogg")
        result = self.model.handle_input(name, now)
        if result in ('wrong', 'round_complete'):
            self.game_timer.stop()
        return True

    # ------------------------------------------------------------------
    # Public async entry point
    # Returns:
    #   ("gameover", score, reason)  — player lost
    #   "quit"                       — window was closed
    # ------------------------------------------------------------------

    async def run(self):
        self.model.reset()
        # Only switch to the main theme if the user hasn't chosen something else
        # during the start screen / menu.  If they picked Techno or a custom
        # track, let it keep playing seamlessly into gameplay.
        _INTRO = "assets/Typ0__Intro_Theme.ogg"
        _MAIN  = "assets/Typ0__Main_Theme.ogg"
        user_pick = animation_utils.get_user_music_selection()
        if user_pick is None or user_pick == _INTRO:
            animation_utils.stop_music()
            animation_utils.play_music(_MAIN)
        clock = pygame.time.Clock()

        while True:
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                # Handle menu events
                if self.menu_overlay:
                    was_active = self.menu_overlay.open or self.menu_overlay.active_submenu is not None
                    menu_action = self.menu_overlay.handle_event(event)
                    is_active = self.menu_overlay.open or self.menu_overlay.active_submenu is not None

                    # Pause when menu opens, unpause when menu closes
                    if is_active and not was_active:
                        self._menu_forced_pause = True
                        self._set_paused(True)
                    elif was_active and not is_active:
                        if self._menu_forced_pause:
                            self._menu_forced_pause = False
                            self._set_paused(False)

                    if menu_action == "credits":
                        self._set_paused(True)
                        from game.screens.credits import CreditsScreen
                        credits = CreditsScreen(self.screen)
                        cr = await credits.run()
                        if cr == "quit":
                            return "quit"
                        self._exit_overlay_screen()

                    if menu_action == "how_to_play":
                        self._set_paused(True)
                        how_to_play = HowToPlayScreen(self.screen)
                        how_result = await how_to_play.run()
                        if how_result == "quit":
                            return "quit"
                        if how_result == "credits":
                            credits = CreditsScreen(self.screen)
                            cr = await credits.run()
                            if cr == "quit":
                                return "quit"
                        self._exit_overlay_screen()

                    if menu_action == "switch_mode":
                        animation_utils.stop_music()
                        return ("switch_mode",)

                if event.type == pygame.KEYDOWN:
                    # P always toggles pause regardless of game state
                    if event.key == pygame.K_p:
                        self._set_paused(not self.paused)
                        continue

                    # Ctrl+E jumps to game over (debug shortcut)
                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")

                    # Game inputs are blocked while paused
                    if not self.paused and self.model.state == 'input':
                        for name, key in self.keybinds.button_keys.items():
                            if event.key == key:
                                self._process_input_result(name, now)
                                break

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not self.paused and self.model.state == 'input':
                        for name, rect in self.view.button_rects.items():
                            if rect.collidepoint(event.pos):
                                self._process_input_result(name, now)
                                break

            # Sync pause state with menu overlay
            if self._menu_is_open:
                if not self._menu_forced_pause:
                    self._menu_forced_pause = True
                    self._set_paused(True)
            elif self._menu_forced_pause:
                # Menu-owned pause should clear when the overlay closes.
                self._menu_forced_pause = False
                self._set_paused(False)

            # After the wrong-input press-flash expires, hand off to game over
            if self.model.state == 'gameover' and now >= self.model.flash_end:
                animation_utils.stop_music()
                return ("gameover", self.model.score, self.model.gameover_reason)

            if not self.paused:
                entered_input = self.model.update(now)
                if entered_input:
                    self.game_timer.start(now)
                # Let timer update during input phase
                if self.model.state == 'input':
                    self.game_timer.update(now)

            self.view.draw(self.model, self.game_timer.fraction)

            if self.pause_overlay:
                self.pause_overlay.draw()

            if self.menu_overlay:
                self.menu_overlay.draw()

            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)  # Required for pygbag
