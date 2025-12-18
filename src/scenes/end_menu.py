"""Victory screen with high score saving functionality."""
import pygame
import os
import json
from scenes.base import ScreenBase
from ui.button import Button


class EndMenuScreen(ScreenBase):
    """Victory screen shown after defeating the boss, allows saving high scores."""
    
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size)

        # Background
        base_path = os.path.dirname(__file__)
        bg_path = os.path.join(base_path, "..", "..", "assets", "ui", "MainMenu.jpg")
        try:
            bg = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.scale(bg, screen_size)
        except Exception:
            self.bg = None

        # Fonts
        self.font_title = pygame.font.SysFont(None, 56)
        self.font_text = pygame.font.SysFont(None, 36)
        self.font_input = pygame.font.SysFont(None, 32)
        self.font_button = pygame.font.SysFont(None, 28)
        self.font_error = pygame.font.SysFont(None, 24)

        # State variables (initialized in on_enter)
        self.boss_turns = 0
        self.player_name = ""
        self.saved = False
        self.input_active = True
        self.error_msg = ""

        # Input box dimensions
        cx = screen_size[0] // 2
        self.input_box = pygame.Rect(cx - 150, 280, 300, 40)
        self.input_color_active = (100, 200, 255)
        self.input_color_inactive = (150, 150, 150)
        self.input_color_error = (255, 100, 100)

        # Buttons - spaced vertically to avoid overlap
        btn_width = 200
        btn_height = 48
        btn_spacing = 60  # vertical spacing between buttons
        start_y = 370  # Adjusted to make room for error message
        
        self.save_btn = Button("Save Score", (cx, start_y), (btn_width, btn_height), self.save_score, self.font_button)
        self.menu_btn = Button("Main Menu", (cx, start_y + btn_spacing), (btn_width, btn_height), self.back_to_menu, self.font_button)
        self.quit_btn = Button("Quit Game", (cx, start_y + btn_spacing * 2), (btn_width, btn_height), self.quit_game, self.font_button)

    def on_enter(self):
        """Called when screen becomes active. Fetch total run turns and reset state."""
        # Check if player is defeated
        self.is_defeated = self.manager.player_stats['hp'] <= 0
        if self.is_defeated:
            print("Player is dead")
        
        # Get cumulative turn count for entire run (all battles)
        self.boss_turns = self.manager.total_run_turns
        
        if self.boss_turns == 0:
            print("✗ Warning: Total run turns is 0, this seems unusual")

        # Reset state
        self.player_name = ""
        self.saved = False
        self.input_active = True
        self.error_msg = ""

    def validate_name(self, name):
        """Validasi input nama. Raise ValueError jika tidak valid."""
        # 1. Cek Panjang Karakter (3 - 21)
        if not (3 <= len(name) <= 21):
            raise ValueError("Name must be 3-21 characters long!")
        
        # 2. Cek Alphanumeric (Huruf dan Angka saja)
        if not name.isalnum():
            raise ValueError("Only letters and numbers allowed!")

    def save_score(self):
        """Save the player's score to highscore.json with Exception Handling."""
        if self.saved:
            return  # Already saved

        # Reset pesan error sebelumnya
        self.error_msg = ""

        # --- IMPLEMENTASI EXCEPTION HANDLING BARU ---
        try:
            # Validasi input nama sebelum diproses
            self.validate_name(self.player_name.strip())
            
        except ValueError as e:
            # Menangkap error validasi (nama kependekan/simbol aneh)
            print(f"✗ Validation Error: {e}")
            self.error_msg = str(e)  # Tampilkan pesan error ke layar
            return  # Batalkan proses save
        # ---------------------------------------------

        # Prepare new entry
        new_entry = {
            "name": self.player_name.strip(),
            "turns": self.boss_turns
        }

        # Load existing scores
        json_path = os.path.join(os.path.dirname(__file__), "..", "..", "highscore.json")
        scores = []

        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        scores = data
        except json.JSONDecodeError as ex:
            print(f"✗ Error reading highscore.json, starting fresh: {ex}")
            scores = []
        except Exception as ex:
            print(f"✗ Error loading scores: {ex}")
            scores = []

        # Append new score
        scores.append(new_entry)

        # Sort by turns (ascending - lowest is best) and keep top 10
        scores.sort(key=lambda x: x.get('turns', 999))
        scores = scores[:10]

        # Save back to file
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(scores, f, indent=2, ensure_ascii=False)
            print(f"✓ Score saved: {self.player_name} - {self.boss_turns} turns")
            self.saved = True
            self.input_active = False
        except Exception as ex:
            print(f"✗ Error saving score: {ex}")

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.go_to("main_menu")

    def quit_game(self):
        """Exit the game."""
        pygame.quit()
        raise SystemExit

    def handle_event(self, event):
        """Handle keyboard input and button clicks."""
        # Handle buttons (save button only for victory)
        if not self.is_defeated and not self.saved:
            self.save_btn.handle_event(event)
        self.menu_btn.handle_event(event)
        self.quit_btn.handle_event(event)

        # Handle text input (only for victory, not defeated)
        if not self.is_defeated and not self.saved:
            if event.type == pygame.KEYDOWN and self.input_active:
                if event.key == pygame.K_RETURN:
                    # Enter key: save score
                    self.save_score()
                elif event.key == pygame.K_BACKSPACE:
                    # Remove last character
                    self.player_name = self.player_name[:-1]
                    self.error_msg = ""  # Clear error on input change
                else:
                    # Add character (limit to 20 characters)
                    if len(self.player_name) < 20:
                        char = event.unicode
                        if char.isprintable():
                            self.player_name += char
                            self.error_msg = ""  # Clear error on input change

    def update(self, dt):
        """No updates needed."""
        pass

    def draw(self, surface):
        """Draw victory or defeat screen with appropriate elements."""
        # Draw background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((20, 30, 20))

        if self.is_defeated:
            # DEFEATED state - show only title and navigation buttons
            # Draw background panel for readability
            panel_rect = pygame.Rect(0, 0, 400, 320)
            panel_rect.center = (self.screen_width // 2, 200)
            panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            panel_surface.fill((0, 0, 0, 200))  # Semi-transparent black
            surface.blit(panel_surface, panel_rect.topleft)
            pygame.draw.rect(surface, (80, 80, 80), panel_rect, 3)  # Border
            
            title = self.font_title.render("DEFEATED", True, (255, 50, 50))
            tw = title.get_width()
            surface.blit(title, ((self.screen_width - tw) // 2, 80))

            # Center the navigation buttons for defeated state
            cx = self.screen_width // 2
            
            # Draw Main Menu button (centered)
            menu_btn_rect = pygame.Rect(0, 0, 180, 48)
            menu_btn_rect.center = (cx, 250)
            self.menu_btn.rect = menu_btn_rect
            self.menu_btn.text_rect = self.menu_btn.text_surface.get_rect(center=menu_btn_rect.center)
            self.menu_btn.draw(surface)
            
            # Draw Quit Game button (centered)
            quit_btn_rect = pygame.Rect(0, 0, 180, 48)
            quit_btn_rect.center = (cx, 320)
            self.quit_btn.rect = quit_btn_rect
            self.quit_btn.text_rect = self.quit_btn.text_surface.get_rect(center=quit_btn_rect.center)
            self.quit_btn.draw(surface)
        else:
            # VICTORY state - show full UI with score input
            # Draw background panel for readability
            panel_rect = pygame.Rect(0, 0, 420, 450)
            panel_rect.center = (self.screen_width // 2, 280)
            panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            panel_surface.fill((0, 0, 0, 200))  # Semi-transparent black
            surface.blit(panel_surface, panel_rect.topleft)
            pygame.draw.rect(surface, (80, 80, 80), panel_rect, 3)  # Border
            
            title = self.font_title.render("VICTORY!", True, (255, 255, 100))
            tw = title.get_width()
            surface.blit(title, ((self.screen_width - tw) // 2, 80))

            # Draw turn count
            turns_text = self.font_text.render(f"Total Run Turns: {self.boss_turns}", True, (255, 255, 255))
            ttw = turns_text.get_width()
            surface.blit(turns_text, ((self.screen_width - ttw) // 2, 170))

            # Draw input prompt
            if not self.saved:
                prompt = self.font_text.render("Enter Your Name:", True, (255, 255, 255))
                pw = prompt.get_width()
                surface.blit(prompt, ((self.screen_width - pw) // 2, 230))

                # Draw input box - use error color if error message present
                if self.error_msg:
                    box_color = self.input_color_error
                else:
                    box_color = self.input_color_active if self.input_active else self.input_color_inactive
                pygame.draw.rect(surface, box_color, self.input_box, 2)
                pygame.draw.rect(surface, (30, 30, 30), self.input_box.inflate(-4, -4))

                # Draw input text
                input_surf = self.font_input.render(self.player_name, True, (255, 255, 255))
                surface.blit(input_surf, (self.input_box.x + 10, self.input_box.y + 8))

                # Draw cursor (blinking effect)
                if pygame.time.get_ticks() % 1000 < 500:
                    cursor_x = self.input_box.x + 10 + input_surf.get_width() + 2
                    cursor_y = self.input_box.y + 8
                    pygame.draw.line(surface, (255, 255, 255), 
                                   (cursor_x, cursor_y), 
                                   (cursor_x, cursor_y + 24), 2)

                # Draw error message below input box
                if self.error_msg:
                    error_surf = self.font_error.render(self.error_msg, True, self.input_color_error)
                    error_x = self.input_box.x + (self.input_box.width - error_surf.get_width()) // 2
                    error_y = self.input_box.y + self.input_box.height + 5
                    surface.blit(error_surf, (error_x, error_y))
            else:
                # Show saved message
                saved_msg = self.font_text.render("Score Saved!", True, (100, 255, 100))
                smw = saved_msg.get_width()
                surface.blit(saved_msg, ((self.screen_width - smw) // 2, 280))

            # Draw buttons - reposition based on state
            cx = self.screen_width // 2
            btn_width = 200
            btn_height = 48
            btn_spacing = 60
            start_y = 370  # Adjusted to make room for error message
            
            if not self.saved:
                # All three buttons vertically stacked
                self.save_btn.rect.center = (cx, start_y)
                self.save_btn.text_rect = self.save_btn.text_surface.get_rect(center=self.save_btn.rect.center)
                self.save_btn.draw(surface)
                
                self.menu_btn.rect.center = (cx, start_y + btn_spacing)
                self.menu_btn.text_rect = self.menu_btn.text_surface.get_rect(center=self.menu_btn.rect.center)
                self.menu_btn.draw(surface)
                
                self.quit_btn.rect.center = (cx, start_y + btn_spacing * 2)
                self.quit_btn.text_rect = self.quit_btn.text_surface.get_rect(center=self.quit_btn.rect.center)
                self.quit_btn.draw(surface)
            else:
                # Only menu and quit buttons, repositioned after save
                self.menu_btn.rect.center = (cx, start_y)
                self.menu_btn.text_rect = self.menu_btn.text_surface.get_rect(center=self.menu_btn.rect.center)
                self.menu_btn.draw(surface)
                
                self.quit_btn.rect.center = (cx, start_y + btn_spacing)
                self.quit_btn.text_rect = self.quit_btn.text_surface.get_rect(center=self.quit_btn.rect.center)
                self.quit_btn.draw(surface)
