import pygame

class AboutMenu:
    def __init__(self, screen, font_manager):
        self.screen = screen
        self.font_manager = font_manager
        
        # Colors
        self.text_color = (255, 255, 255)
        self.highlight_color = (255, 255, 255)
        
        # Scrolling
        self.scroll_offset = 0
        self.max_scroll_offset = 0
        self.scrolling = False
        self.last_mouse_y = 0
        
        # Back button
        self.back_button_width = 140
        self.back_button_height = 45

        # Credits button (opens the credits screen from within About)
        self.credits_button_width = 140
        self.credits_button_height = 45
        self.credits_button_rect = None
        
        # Game info - make sure all text is safe to render
        self.game_info = [
            "TYP0: LET'S PLAY",
            "",
            "A memory and reflex game. Match the prompts as",
            "they appear — don't miss a beat!",
            "",
            "==============================================",
            "",
            "GAME MODES:",
            "",
            "> SIMON SAYS MODE",
            "  Watch the sequence of lit buttons and repeat",
            "  them in the exact order. Each round adds one",
            "  more button to the sequence.",
            "",
            "> BOP IT MODE",
            "  One command at a time. Press the right button",
            "  before the timer runs out. Speeds up as you go.",
            "",
            "> MULTIPLAYER",
            "  Challenge another player to a head-to-head",
            "  Simon match on the same seed.",
            "",
            "==============================================",
            "",
            "CONTROLS:",
            "",
            "KEYBOARD:",
            "  - W / UP-arrow      - Up button",
            "  - S / DOWN-arrow    - Down button",
            "  - A / LEFT-arrow    - Left button",
            "  - D / RIGHT-arrow   - Right button",
            "  - SPACEBAR          - Space button",
            "  - P                 - Pause / Resume",
            "  - ESC               - Close menus / Back",
            "",
            "MOUSE:",
            "  - Click the on-screen buttons",
            "",
            "==============================================",
            "",
            "IN-GAME MENU:",
            "",
            "  - VOLUME    adjust music volume",
            "  - MUSIC     pick a track or upload your own",
            "  - ABOUT     this screen",
            "  - SWITCH    jump to the other game mode",
            "",
            "==============================================",
            "",
            "TIPS:",
            "",
            "  - Try Inverted Controls for a twist",
            "  - Pick a harder difficulty for faster rounds",
            "  - High scores are tracked per mode",
            "",
            "==============================================",
            "",
            "Have fun and challenge your friends!",
            "",
        ]
        
        # Add fallback attributes to avoid AttributeError
        self.back_button_rect = None
        self.content_rect = None
        
    def draw(self, bg_rect):
        # Safety check - ensure bg_rect is valid
        if bg_rect is None:
            return
            
        # Content area that fits inside brick background
        content_rect = pygame.Rect(
            bg_rect.x + 15,
            bg_rect.y + 60,
            bg_rect.width - 30,
            bg_rect.height - 90
        )
        
        # Title font - smaller to fit
        try:
            title_surf = self.font_manager.render_text(self.game_info[0], (255, 255, 255), 24)
            title_rect = title_surf.get_rect(centerx=bg_rect.centerx, y=bg_rect.y + 22)
            self.screen.blit(title_surf, title_rect)
        except Exception:
            # Fallback if font rendering fails
            pass
        
        # Calculate line heights - compact but readable
        line_heights = []
        for line in self.game_info[1:]:
            if line == "":
                line_heights.append(12)
            else:
                if line.startswith("==="):
                    line_heights.append(16)
                elif line.startswith(">"):
                    line_heights.append(22)
                elif line.endswith(":") or line in ["GAME MODES:", "HOW TO PLAY:", "CONTROLS:", "TIPS:"]:
                    line_heights.append(22)
                else:
                    line_heights.append(18)
        
        total_height = sum(line_heights)
        visible_height = content_rect.height
        self.max_scroll_offset = max(0, total_height - visible_height)
        
        # Create scroll surface
        scroll_surface = pygame.Surface((content_rect.width, max(total_height, 1)), pygame.SRCALPHA)
        scroll_surface.fill((0, 0, 0, 0))
        
        # Draw text with appropriate font sizes
        y_pos = 0
        for i, line in enumerate(self.game_info[1:]):
            if line == "":
                y_pos += line_heights[i]
                continue
            
            try:
                if line.startswith("==="):
                    text_surf = self.font_manager.render_text(line, (100, 100, 100), 14)
                elif line.startswith(">"):
                    text_surf = self.font_manager.render_text(line, (255, 255, 255), 18)
                elif line.endswith(":") or line in ["GAME MODES:", "HOW TO PLAY:", "CONTROLS:", "TIPS:"]:
                    text_surf = self.font_manager.render_text(line, (255, 255, 255), 20)
                else:
                    text_surf = self.font_manager.render_text(line, (255, 255, 255), 16)
                
                scroll_surface.blit(text_surf, (10, y_pos))
            except Exception:
                # Skip rendering this line if there's an error
                pass
                
            y_pos += line_heights[i]
        
        # Draw visible portion if there's content
        if total_height > 0 and visible_height > 0:
            try:
                visible_portion = scroll_surface.subsurface(
                    pygame.Rect(0, self.scroll_offset, content_rect.width, min(visible_height, scroll_surface.get_height() - self.scroll_offset))
                )
                self.screen.blit(visible_portion, content_rect)
            except (ValueError, pygame.error):
                # Fallback: blit the whole surface if subsurface fails
                self.screen.blit(scroll_surface, content_rect, 
                               area=pygame.Rect(0, self.scroll_offset, content_rect.width, visible_height))
        
        # Back + Credits buttons side-by-side
        gap = 12
        row_w = self.back_button_width + self.credits_button_width + gap
        row_left = bg_rect.centerx - row_w // 2
        back_button_rect = pygame.Rect(
            row_left,
            bg_rect.bottom - 55,
            self.back_button_width,
            self.back_button_height,
        )
        credits_button_rect = pygame.Rect(
            row_left + self.back_button_width + gap,
            bg_rect.bottom - 55,
            self.credits_button_width,
            self.credits_button_height,
        )

        mouse_pos = pygame.mouse.get_pos()
        for rect, label in (
            (back_button_rect,    "BACK"),
            (credits_button_rect, "CREDITS"),
        ):
            hover = rect.collidepoint(mouse_pos)
            color = (120, 120, 120) if hover else (80, 80, 80)
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2, border_radius=10)
            try:
                text_surf = self.font_manager.render_text(label, (255, 255, 255), 22)
            except Exception:
                text_surf = pygame.font.Font(None, 22).render(label, True, (255, 255, 255))
            self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        self.back_button_rect = back_button_rect
        self.credits_button_rect = credits_button_rect
        self.content_rect = content_rect
    
    def handle_event(self, event):
        # Mouse wheel scrolling
        if event.type == pygame.MOUSEWHEEL and hasattr(self, 'content_rect') and self.content_rect:
            if self.content_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 25
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
                return None
        
        # Mouse button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'back_button_rect') and self.back_button_rect and self.back_button_rect.collidepoint(event.pos):
                return "Back"
            if self.credits_button_rect and self.credits_button_rect.collidepoint(event.pos):
                return "credits"
            if hasattr(self, 'content_rect') and self.content_rect and self.content_rect.collidepoint(event.pos):
                self.scrolling = True
                self.last_mouse_y = event.pos[1]
                return None
        
        elif event.type == pygame.MOUSEMOTION and self.scrolling:
            if hasattr(self, 'content_rect') and self.content_rect and self.max_scroll_offset > 0:
                dy = event.pos[1] - self.last_mouse_y
                scroll_factor = self.max_scroll_offset / self.content_rect.height if self.content_rect.height > 0 else 1
                self.scroll_offset += dy * scroll_factor
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
                self.last_mouse_y = event.pos[1]
            return None
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.scrolling = False
            return None
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "Back"
        
        return None