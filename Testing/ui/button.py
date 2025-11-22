import pygame

class Button:
    def __init__(self, text, center_pos, size, callback, font,
                 bg_color=(70,70,70), hover_color=(100,100,100), text_color=(255,255,255)):
        
        self.text = text
        self.callback = callback
        self.font = font

        self.rect = pygame.Rect(0, 0, *size)
        self.rect.center = center_pos

        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color

        self._is_hovered = False
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._is_hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface):
        color = self.hover_color if self._is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (200,200,200), self.rect, 2, border_radius=8)
        surface.blit(self.text_surface, self.text_rect)