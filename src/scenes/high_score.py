"""High score leaderboard screen displaying top 10 lowest turn counts."""
import pygame
import os
import json
from scenes.base import ScreenBase
from ui.button import Button


class HighScoreScreen(ScreenBase):
    """Display leaderboard of top players with lowest turn counts."""
    
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size)

        # Load background
        base_path = os.path.dirname(__file__)
        bg_path = os.path.join(base_path, "..", "..", "assets", "ui", "MainMenu.jpg")
        try:
            bg = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.scale(bg, screen_size)
        except Exception as ex:
            print(f"✗ Failed loading high score background: {ex}")
            self.bg = None

        # Fonts
        self.font_title = pygame.font.SysFont(None, 48)
        self.font_score = pygame.font.SysFont(None, 32)
        self.font_button = pygame.font.SysFont(None, 28)

        # Back button
        cx = screen_size[0] // 2
        cy = screen_size[1] - 80
        self.back_btn = Button("Back to Menu", (cx, cy), (200, 48), self.back_to_menu, self.font_button)

        # Score list (loaded on_enter)
        self.scores = []

    def on_enter(self):
        """Load scores when screen becomes active."""
        self.load_scores()

    def load_scores(self):
        """Load high scores from highscore.json."""
        json_path = os.path.join(os.path.dirname(__file__), "..", "..", "highscore.json")
        
        try:
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure it's a list
                    if isinstance(data, list):
                        self.scores = data[:10]  # Top 10 only
                    else:
                        self.scores = []
            else:
                self.scores = []
                print("✓ No highscore.json found, starting with empty leaderboard")
        except json.JSONDecodeError as ex:
            print(f"✗ Error parsing highscore.json: {ex}")
            self.scores = []
        except Exception as ex:
            print(f"✗ Error loading high scores: {ex}")
            self.scores = []

    def back_to_menu(self):
        """Return to main menu."""
        self.manager.go_to("main_menu")

    def handle_event(self, event):
        """Handle button clicks."""
        self.back_btn.handle_event(event)

    def update(self, dt):
        """No updates needed."""
        pass

    def draw(self, surface):
        """Draw leaderboard with scores."""
        # Draw background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((20, 20, 40))

        # Draw title
        title = self.font_title.render("Hall of Fame (Lowest Turns)", True, (255, 255, 255))
        tw = title.get_width()
        surface.blit(title, ((self.screen_width - tw) // 2, 50))

        # Draw scores
        start_y = 130
        spacing = 45

        if not self.scores:
            no_scores = self.font_score.render("No scores yet. Be the first!", True, (200, 200, 200))
            surface.blit(no_scores, ((self.screen_width - no_scores.get_width()) // 2, start_y + 100))
        else:
            for i, entry in enumerate(self.scores[:10]):
                rank = i + 1
                name = entry.get('name', 'Unknown')
                turns = entry.get('turns', '???')

                # Color coding for top 3
                if rank == 1:
                    color = (255, 215, 0)  # Gold
                elif rank == 2:
                    color = (192, 192, 192)  # Silver
                elif rank == 3:
                    color = (205, 127, 50)  # Bronze
                else:
                    color = (220, 220, 220)  # White

                # Format: "1. PlayerName - 12 Turns"
                score_text = f"{rank}. {name} - {turns} Turns"
                text_surf = self.font_score.render(score_text, True, color)
                
                # Center horizontally
                x = (self.screen_width - text_surf.get_width()) // 2
                y = start_y + (i * spacing)
                
                surface.blit(text_surf, (x, y))

        # Draw back button
        self.back_btn.draw(surface)
