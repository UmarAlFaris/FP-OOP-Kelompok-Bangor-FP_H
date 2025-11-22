from .screens.main_menu import MainMenuScreen
from .screens.game_screen import GameScreen
from .screens.high_score_screen import HighScoreScreen

class ScreenManager:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.screens = {}
        self.current_screen = None

        self._register_screens()

    def _register_screens(self):
        self.screens["main_menu"] = MainMenuScreen(self, self.screen_size)
        self.screens["game"] = GameScreen(self, self.screen_size)
        self.screens["high_score"] = HighScoreScreen(self, self.screen_size)

        # Screen awal
        self.go_to("main_menu")

    def go_to(self, name):
        self.current_screen = self.screens[name]

    def handle_event(self, event):
        self.current_screen.handle_event(event)

    def update(self, dt):
        self.current_screen.update(dt)

    def draw(self, surface):
        self.current_screen.draw(surface)