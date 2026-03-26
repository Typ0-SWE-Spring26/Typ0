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
        
        # Game info
        self.game_info = [
            "TYP0: LET'S PLAY",
            "",
            "A classic memory and reflex game where you must",
            "repeat the sequence of button presses!",
            "",
            "══════════════════════════════════════════════",
            "",
            "GAME MODES:",
            "",
            "> SIMON SAYS MODE",
            "  Watch the sequence of lit buttons and repeat",
            "  them in the exact order. Each correct round",
            "  adds a new button to the sequence.",
            "",
            "> BOP IT MODE (Coming Soon!)",
            "  A fast-paced mode where you'll need to react",
            "  quickly to voice commands.",
            "",
            "══════════════════════════════════════════════",
            "",
            "HOW TO PLAY:",
            "",
            "1. Watch the sequence of buttons light up",
            "2. Memorize the order carefully",
            "3. Repeat the sequence by clicking the buttons",
            "   or pressing the corresponding keys",
            "4. Each correct round adds one more button",
            "5. One wrong move ends the game!",
            "",
            "══════════════════════════════════════════════",
            "",
            "CONTROLS:",
            "",
            "MOUSE:",
            "  • Click directly on the on-screen buttons",
            "",
            "KEYBOARD:",
            "  • W / UP      - Top button",
            "  • S / DOWN    - Bottom button", 
            "  • A / LEFT    - Left button",
            "  • D / RIGHT   - Right button",
            "  • SPACEBAR    - Space button",
            "",
            "  • ESC         - Close all menus",
            "",
            "══════════════════════════════════════════════",
            "",
            "TIPS:",
            "",
            "  • Take your time!",
            "  • Say the sequence out loud",
            "  • Practice makes perfect!",
            "",
            "══════════════════════════════════════════════",
            "",
            "Have fun and challenge your friends!",
            ""
        ]
        
    def draw(self, bg_rect):
        # Content area that fits inside brick background
        content_rect = pygame.Rect(
            bg_rect.x + 15,
            bg_rect.y + 60,
            bg_rect.width - 30,
            bg_rect.height - 90
        )
        
        # Title font - smaller to fit
        title_surf = self.font_manager.render_text(self.game_info[0], (255, 255, 255), 24)
        title_rect = title_surf.get_rect(centerx=bg_rect.centerx, y=bg_rect.y + 22)
        self.screen.blit(title_surf, title_rect)
        
        # Calculate line heights - compact but readable
        line_heights = []
        for line in self.game_info[1:]:
            if line == "":
                line_heights.append(12)
            else:
                if line.startswith("═══"):
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
        scroll_surface = pygame.Surface((content_rect.width, total_height), pygame.SRCALPHA)
        scroll_surface.fill((0, 0, 0, 0))
        
        # Draw text with appropriate font sizes
        y_pos = 0
        for i, line in enumerate(self.game_info[1:]):
            if line == "":
                y_pos += line_heights[i]
                continue
            
            if line.startswith("═══"):
                text_surf = self.font_manager.render_text(line, (100, 100, 100), 14)
            elif line.startswith(">"):
                text_surf = self.font_manager.render_text(line, (255, 255, 255), 18)
            elif line.endswith(":") or line in ["GAME MODES:", "HOW TO PLAY:", "CONTROLS:", "TIPS:"]:
                text_surf = self.font_manager.render_text(line, (255, 255, 255), 20)
            else:
                text_surf = self.font_manager.render_text(line, (255, 255, 255), 16)
            
            scroll_surface.blit(text_surf, (10, y_pos))
            y_pos += line_heights[i]
        
        # Draw visible portion
        visible_portion = scroll_surface.subsurface(
            pygame.Rect(0, self.scroll_offset, content_rect.width, visible_height)
        )
        self.screen.blit(visible_portion, content_rect)
        
        # Back button
        back_button_rect = pygame.Rect(
            bg_rect.centerx - self.back_button_width // 2,
            bg_rect.bottom - 55,
            self.back_button_width,
            self.back_button_height
        )
        
        mouse_pos = pygame.mouse.get_pos()
        button_color = (120, 120, 120) if back_button_rect.collidepoint(mouse_pos) else (80, 80, 80)
        pygame.draw.rect(self.screen, button_color, back_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 200, 200), back_button_rect, 2, border_radius=10)
        
        back_text = self.font_manager.render_text("BACK", (255, 255, 255), 22)
        self.screen.blit(back_text, back_text.get_rect(center=back_button_rect.center))
        
        self.back_button_rect = back_button_rect
        self.content_rect = content_rect
    
    def handle_event(self, event):
        # Mouse wheel scrolling
        if event.type == pygame.MOUSEWHEEL and hasattr(self, 'content_rect'):
            if self.content_rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 25
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
                return None
        
        # Mouse button
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'back_button_rect') and self.back_button_rect.collidepoint(event.pos):
                return "Back"
            if hasattr(self, 'content_rect') and self.content_rect.collidepoint(event.pos):
                self.scrolling = True
                self.last_mouse_y = event.pos[1]
                return None
        
        elif event.type == pygame.MOUSEMOTION and self.scrolling:
            dy = event.pos[1] - self.last_mouse_y
            self.scroll_offset += dy * (self.max_scroll_offset / self.content_rect.height) if self.max_scroll_offset > 0 else 0
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
            self.last_mouse_y = event.pos[1]
            return None
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.scrolling = False
            return None
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "Back"
        
        return None