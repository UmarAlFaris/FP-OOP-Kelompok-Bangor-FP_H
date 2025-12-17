import pygame
import cv2
import os
from scenes.base import ScreenBase

class VideoScene(ScreenBase):
    def __init__(self, manager, screen_size, video_name, next_scene=None):
        super().__init__(manager, screen_size)
        self.video_name = video_name
        self.next_scene = next_scene
        base_path = os.path.dirname(__file__)
        # try multiple candidate locations for the resource
        candidates = [
            os.path.join(base_path, "scene-video", video_name),
            os.path.join(base_path, "scene", video_name),
            os.path.join(base_path, video_name),
            video_name,
        ]

        self.video_path = None
        for p in candidates:
            if os.path.isfile(p):
                self.video_path = p
                break

        # fallback to first candidate if none found (will fail later and show message)
        if self.video_path is None:
            self.video_path = candidates[0]

        # determine whether the provided file is an image or a video
        _, ext = os.path.splitext(self.video_path)
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        self.is_video = ext.lower() not in image_exts

        self.cap = None
        self.finished = False
        self.current_frame = None
        self.image_surface = None

        # font and UI
        self.font = pygame.font.SysFont(None, 32)
        self.show_next_button = False
        self.button_rect = pygame.Rect(
            self.screen_width//2 - 80,
            self.screen_height - 100,
            160,
            50
        )

        # load resource depending on type
        if self.is_video:
            self.cap = cv2.VideoCapture(self.video_path)
            # if capture failed, mark finished so user can continue
            if not self.cap.isOpened():
                self.finished = True
                self.show_next_button = True
        else:
            try:
                img = pygame.image.load(self.video_path)
                if img.get_alpha() is not None:
                    img = img.convert_alpha()
                else:
                    img = img.convert()
                img = pygame.transform.scale(img, (self.screen_width, self.screen_height))
                self.image_surface = img
                # for images show NEXT immediately (acts like a static cutscene)
                self.finished = True
                self.show_next_button = True
            except Exception:
                # failed to load image: allow user to continue
                self.image_surface = None
                self.finished = True
                self.show_next_button = True

    def handle_event(self, event):
        if self.show_next_button and event.type == pygame.MOUSEBUTTONDOWN:
            if self.button_rect.collidepoint(event.pos):
                if self.next_scene:
                    self.manager.go_to(self.next_scene)

    def update(self, dt):
        # only update when playing video
        if self.is_video and not self.finished:
            if self.cap is None:
                self.finished = True
                self.show_next_button = True
                return

            ret, frame = self.cap.read()
            if not ret:
                self.finished = True
                self.show_next_button = True
                try:
                    self.cap.release()
                except Exception:
                    pass
            else:
                frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.current_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def draw(self, surface):
        if self.is_video:
            if not self.finished:
                if self.current_frame is not None:
                    surface.blit(self.current_frame, (0, 0))
            else:
                txt = self.font.render("Video Selesai", True, (255,255,255))
                surface.blit(txt, (self.screen_width//2 - 80, 40))
        else:
            # image mode
            if self.image_surface is not None:
                surface.blit(self.image_surface, (0, 0))
            else:
                txt = self.font.render("Gagal memuat gambar", True, (255,255,255))
                surface.blit(txt, (self.screen_width//2 - 120, 40))

        if self.show_next_button:
            pygame.draw.rect(surface, (50,50,50), self.button_rect)
            pygame.draw.rect(surface, (255,255,255), self.button_rect, 2)
            t = self.font.render("NEXT", True, (255,255,255))
            surface.blit(t, (self.button_rect.x + 40, self.button_rect.y + 12))
