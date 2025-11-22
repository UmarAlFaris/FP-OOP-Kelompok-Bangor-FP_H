import pygame
from .screen_manager import ScreenManager

def main():
    pygame.init()

    screen_size = (800, 600)
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Screen Manager – PyGame OOP")

    clock = pygame.time.Clock()
    manager = ScreenManager(screen_size)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                manager.handle_event(event)

        manager.update(dt)
        manager.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()