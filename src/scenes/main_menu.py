import pygame
import os
from scenes.base import ScreenBase
from ui.button import Button

class MainMenuScreen(ScreenBase):
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size)

        # Load background
        base_path = os.path.dirname(__file__)
        img_path = os.path.join(base_path, "..", "..", "assets", "ui", "MainMenu.jpg")
        self.bg = pygame.image.load(img_path).convert()
        self.bg = pygame.transform.scale(self.bg, screen_size)

        # Fonts
        self.font_title = pygame.font.SysFont(None, 48)
        self.font_button = pygame.font.SysFont(None, 28)

        # Buttons
        cx = screen_size[0] // 2
        cy = screen_size[1] // 2 - 40

        self.buttons = [
            Button("Start Game", (cx, cy), (180, 40), self.start_game, self.font_button),
            Button("High Score", (cx, cy + 60), (180, 40), self.go_high_score, self.font_button),
            Button("Exit", (cx, cy + 120), (180, 40), self.exit_game, self.font_button),
        ]

        # Load main menu music
        music_path = os.path.join(base_path, "..", "..", "assets", "sounds", "mainmenu_sound.mp3")
        self.music_path = music_path if os.path.exists(music_path) else None
        if not self.music_path:
            print("✗ Warning: mainmenu_sound.mp3 not found")

    def on_enter(self):
        """Play main menu music when entering the screen."""
        if self.music_path:
            try:
                pygame.mixer.music.load(self.music_path)
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except Exception as ex:
                print(f"✗ Error playing main menu music: {ex}")

    def on_exit(self):
        """Stop music when leaving main menu."""
        pygame.mixer.music.stop()

    def start_game(self):
        self.manager.reset_score()  # Reset global turn counter for new run
        self.manager.go_to("campfire")


    def go_high_score(self):
        self.manager.go_to("high_score")

    def exit_game(self):
        pygame.quit()
        raise SystemExit

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt): pass

    def draw(self, surface):
        # Draw background
        surface.blit(self.bg, (0, 0))

        # Draw title
        title = self.font_title.render(
            "VIVA FANTASY: Calvin Origin - Pygame Edition", True, (255,255,255)
        )
        tw, th = title.get_width(), title.get_height()
        x = (self.screen_width - tw) // 2
        surface.blit(title, (x, 70))

        # Draw buttons
        for b in self.buttons:
            b.draw(surface)