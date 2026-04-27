import pygame
import asyncio
from game.utils import animation_utils
from game.screens.credits import CreditsScreen
from game.screens.how_to_play import HowToPlayScreen


class KeysNinjaController:
    """Controller for Keys Ninja mode - handles keyboard input for falling keys."""
    
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
        
        if pause_overlay is not None:
            pause_overlay.subscribe(self._bus)
    
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
        """Restore gameplay state after a full-screen overlay."""
        if self.menu_overlay:
            self.menu_overlay.open = False
            self.menu_overlay.active_submenu = None
        self._menu_forced_pause = False
        self._set_paused(False)
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
    
    async def run(self):
        self.model.reset()
        
        # Start music
        _INTRO = "assets/Typ0__Intro_Theme.ogg"
        _MAIN = "assets/Typ0__Main_Theme.ogg"
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
                    
                    if is_active and not was_active:
                        self._menu_forced_pause = True
                        self._set_paused(True)
                    elif was_active and not is_active:
                        if self._menu_forced_pause:
                            self._menu_forced_pause = False
                            self._set_paused(False)
                    
                    if menu_action == "credits":
                        self._set_paused(True)
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
                    
                    if menu_action == "main_menu":
                        animation_utils.stop_music()
                        return ("main_menu",)
                
                if event.type == pygame.KEYDOWN:
                    # P key is disabled in Keys Ninja mode - ignore it completely
                    if event.key == pygame.K_p:
                        continue
                    
                    # Ctrl+E debug shortcut
                    if event.key == pygame.K_e and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        return ("gameover", 0, "Testing - Ctrl+E shortcut")
                    
                    # Handle letter keys (A-Z) for gameplay
                    if not self.paused and self.model.state == 'playing':
                        if pygame.K_a <= event.key <= pygame.K_z:
                            char = chr(event.key).upper()
                            animation_utils.play_sound("assets/TypoPressSFX.ogg")
                            self.model.handle_input(char, now)
            
            # Sync pause state with menu
            if self._menu_is_open:
                if not self._menu_forced_pause:
                    self._menu_forced_pause = True
                    self._set_paused(True)
            elif self._menu_forced_pause:
                self._menu_forced_pause = False
                self._set_paused(False)
            
            # Check for game over
            if self.model.state == 'gameover':
                animation_utils.stop_music()
                return ("gameover", self.model.score, self.model.gameover_reason)
            
            # Update game state
            if not self.paused:
                W = self.screen.get_width()
                H = self.screen.get_height()
                self.model.update(now, W, H)
            
            # Render
            self.view.draw(self.model, 1.0)
            
            if self.pause_overlay:
                self.pause_overlay.draw()
            
            if self.menu_overlay:
                self.menu_overlay.draw()
            
            self.screen.present()
            clock.tick(60)
            await asyncio.sleep(0)
