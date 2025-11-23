from .Scenes.main_menu import MainMenuScreen
from .Scenes.S1_Scene_Opening import Scene1
from .Scenes.S4_Scene_StorageRoom_1 import Scene2
from .Scenes.S7_Scene_Adzan_Subuh import Scene3

class ScreenManager:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.screens = {}
        self.current_screen = None
        self._register_screens()

    def _register_screens(self):
        self.screens["main_menu"] = MainMenuScreen(self, self.screen_size)
        self.screens["scene_1"] = Scene1(self, self.screen_size)
        self.screens["scene_2"] = Scene2(self, self.screen_size)
        self.screens["scene_3"] = Scene3(self, self.screen_size)

        self.go_to("main_menu")

    def go_to(self, name):
        if name == "exit_game":
            import pygame
            pygame.quit()
            raise SystemExit

        self.current_screen = self.screens[name]

    def handle_event(self, event):
        self.current_screen.handle_event(event)

    def update(self, dt):
        self.current_screen.update(dt)

    def draw(self, surface):
        self.current_screen.draw(surface)
