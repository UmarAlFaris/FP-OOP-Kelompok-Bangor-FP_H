import pygame

class ScreenBase:
    def __init__(self, manager, screen_size: tuple[int, int]):
        self.manager = manager
        self.screen_width, self.screen_height = screen_size

    def on_enter(self):
        """Called when this screen becomes active. Override to refresh data."""
        pass
    
    def on_exit(self):
        """Called when leaving this screen. Override to cleanup resources."""
        pass

    def handle_event(self, event):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def draw(self, surface):
        raise NotImplementedError