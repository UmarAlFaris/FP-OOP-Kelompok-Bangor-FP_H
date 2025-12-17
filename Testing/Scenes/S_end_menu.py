import pygame
import os
from .base import ScreenBase
from ui.button import Button


class EndMenuScreen(ScreenBase):
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size)

        # background (optional reuse from main menu if exists)
        base_path = os.path.dirname(__file__)
        bg_path = os.path.join(base_path, "..", "..", "Imagesthingy", "MainMenu.jpg")
        try:
            bg = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.scale(bg, screen_size)
        except Exception:
            self.bg = None

        # Fonts
        self.font_title = pygame.font.SysFont(None, 40)
        self.font_button = pygame.font.SysFont(None, 28)

        cx = screen_size[0] // 2
        cy = screen_size[1] // 2 - 20

        self.buttons = [
            Button("Kembali ke Menu", (cx, cy), (220, 48), self.back_to_menu, self.font_button),
            Button("Quit Game", (cx, cy + 80), (220, 48), self.quit_game, self.font_button),
        ]

    def back_to_menu(self):
        self.manager.go_to("main_menu")

    def quit_game(self):
        import pygame
        pygame.quit()
        raise SystemExit

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surface):
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((20, 20, 20))

        title = self.font_title.render("Pilih Aksi", True, (255, 255, 255))
        tw = title.get_width()
        surface.blit(title, ((self.screen_width - tw) // 2, 70))

        for b in self.buttons:
            b.draw(surface)
