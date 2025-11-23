import pygame
import cv2
import os
from .base import ScreenBase

class VideoScene(ScreenBase):
    def __init__(self, manager, screen_size, video_name, next_scene=None):
        super().__init__(manager, screen_size)
        self.video_name = video_name
        self.next_scene = next_scene

        base_path = os.path.dirname(__file__)
        self.video_path = os.path.join(base_path, "scene-video", video_name)

        self.cap = cv2.VideoCapture(self.video_path)
        self.finished = False
        self.current_frame = None

        self.font = pygame.font.SysFont(None, 32)
        self.show_next_button = False
        self.button_rect = pygame.Rect(
            self.screen_width//2 - 80,
            self.screen_height - 100,
            160,
            50
        )

    def handle_event(self, event):
        if self.show_next_button and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                if self.next_scene:
                    self.manager.go_to(self.next_scene)

    def update(self, dt):
        if not self.finished:
            ret, frame = self.cap.read()
            if not ret:
                self.finished = True
                self.show_next_button = True
            else:
                frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.current_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def draw(self, surface):
        if not self.finished:
            if self.current_frame is not None:
                surface.blit(self.current_frame, (0, 0))
        else:
            txt = self.font.render("Video Selesai", True, (255,255,255))
            surface.blit(txt, (self.screen_width//2 - 80, 40))

        if self.show_next_button:
            pygame.draw.rect(surface, (50,50,50), self.button_rect)
            pygame.draw.rect(surface, (255,255,255), self.button_rect, 2)
            t = self.font.render("NEXT", True, (255,255,255))
            surface.blit(t, (self.button_rect.x + 40, self.button_rect.y + 12))
