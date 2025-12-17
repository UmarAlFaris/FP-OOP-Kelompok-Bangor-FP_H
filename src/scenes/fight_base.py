"""Base classes for fight scenes with simple button-based combat and grid movement."""
import pygame
import os
from scenes.base import ScreenBase
from ui.button import Button
from config import *
from utils import scale_preserve


class FightBase(ScreenBase):
    """Simple button-based fight scene with animation frames."""
    FRAME_COUNTS = {
        'Zombie': 6,
        'Skeleton': 7,
        'Enderman': 14,
        'Boss': 8,
    }

    def __init__(self, manager, screen_size, stages, next_scene=None):
        super().__init__(manager, screen_size)
        self.stages = stages
        self.stage_index = 0
        self.next_scene = next_scene

        self.font = pygame.font.SysFont(None, 28)
        self.bigfont = pygame.font.SysFont(None, 36)

        cx = self.screen_width // 2
        cy = self.screen_height - 120

        self.attack_btn = Button('Attack', (cx - 120, cy), (160, 48), self.player_attack, self.font)
        self.next_btn = Button('NEXT', (cx + 120, cy), (160, 48), self.next_stage, self.font)

        self.player_hp = 30
        self.player_atk = 6

        self.enemies = []
        self.enemy_hps = []
        self.enemy_frames = []
        self.anim_indexes = []
        self.anim_timers = []

        self._load_enemy(self.stage_index)

    def _load_enemy(self, index):
        """Load enemy type and animation frames."""
        etype = self.stages[index]
        self.enemy_type = etype
        
        # default stats
        if etype == 'Zombie':
            hp = 20
        elif etype == 'Skeleton':
            hp = 14
        elif etype == 'Enderman':
            hp = 20
        elif etype == 'Boss':
            hp = 100
        else:
            hp = 20

        self.enemies = [etype]
        self.enemy_hps = [hp]

        # load animation frames
        name = etype.lower()
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        sheet_path = os.path.join(repo, 'assets', name, 'Idle.png')

        frames = []
        if os.path.isfile(sheet_path):
            try:
                sheet = pygame.image.load(sheet_path).convert_alpha()
                n = self.FRAME_COUNTS.get(etype, 6)
                fw = sheet.get_width() // max(1, n)
                fh = sheet.get_height()
                for i in range(n):
                    sub = sheet.subsurface((i*fw, 0, fw, fh))
                    frames.append(scale_preserve(sub, (120, 120)))
                print(f"✓ Loaded {etype} animation frames")
            except Exception as ex:
                print(f"✗ Failed loading {etype} frames: {ex}")

        if not frames:
            # fallback
            surf = pygame.Surface((100, 100))
            surf.fill((120, 0, 0))
            frames = [surf]

        self.enemy_frames = [frames]
        self.anim_indexes = [0]
        self.anim_timers = [0]

    def player_attack(self):
        """Player attacks current enemy."""
        if self.enemy_hps[0] > 0:
            self.enemy_hps[0] -= self.player_atk
            if self.enemy_hps[0] <= 0:
                self.enemy_hps[0] = 0

    def next_stage(self):
        """Progress to next stage or scene."""
        if self.enemy_hps[0] <= 0:
            if self.stage_index < len(self.stages) - 1:
                self.stage_index += 1
                self._load_enemy(self.stage_index)
            else:
                if self.next_scene:
                    self.manager.go_to(self.next_scene)
                else:
                    self.manager.go_to('main_menu')

    def update(self, dt):
        """Update animations."""
        for i in range(len(self.enemy_frames)):
            self.anim_timers[i] += 1
            if self.anim_timers[i] >= 8:
                self.anim_timers[i] = 0
                self.anim_indexes[i] = (self.anim_indexes[i] + 1) % len(self.enemy_frames[i])

    def handle_event(self, event):
        """Handle mouse clicks on buttons."""
        self.attack_btn.handle_event(event)
        self.next_btn.handle_event(event)

    def draw(self, surface):
        """Draw battle screen."""
        surface.fill((30,30,30))
        title = self.bigfont.render('Battle', True, (255,255,255))
        surface.blit(title, (20,20))

        # draw enemies spread horizontally
        n = len(self.enemies)
        spacing = self.screen_width // (n+1)
        for i in range(n):
            frame = self.enemy_frames[i][self.anim_indexes[i] % len(self.enemy_frames[i])]
            fx = spacing*(i+1) - frame.get_width()//2
            fy = 120
            surface.blit(frame, (fx, fy))
            hp = max(0, self.enemy_hps[i])
            hp_txt = self.font.render(f'{self.enemies[i]} HP: {hp}', True, (255,255,255))
            surface.blit(hp_txt, (fx, fy + frame.get_height() + 6))

        # player info and buttons
        ph_text = self.font.render(f'Player HP: {self.player_hp}', True, (255,255,255))
        surface.blit(ph_text, (20, self.screen_height - 160))
        self.attack_btn.draw(surface)
        self.next_btn.draw(surface)


class FightGrid(FightBase):
    """Grid-based scene where a single enemy can move on tiles (no player)."""
    def __init__(self, manager, screen_size, enemy_type: str, next_scene=None):
        super().__init__(manager, screen_size, stages=[enemy_type], next_scene=next_scene)
        self.grid_w = 8
        self.grid_h = 8
        # compute tile size to fit area with UI panel reserved
        usable_h = self.screen_height - 120
        self.tile = min(self.screen_width // self.grid_w, usable_h // self.grid_h)
        # center grid horizontally
        self.grid_origin_x = (self.screen_width - self.tile * self.grid_w) // 2
        self.grid_origin_y = 20

        # enemy
        self.enemy_type = enemy_type
        self.enemy_x = self.grid_w - 2
        self.enemy_y = self.grid_h // 2
        if enemy_type == 'Enderman':
            self.enemy_hp = 24
        elif enemy_type == 'Boss':
            self.enemy_hp = 40
        else:
            self.enemy_hp = 20

        self.move_timer = 0.0
        self.move_interval = 1.0

        # load a frame for enemy (reuse single frame if available)
        name = enemy_type.lower()
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        p = os.path.join(repo, 'assets', name, 'Idle.png')
        
        try:
            sheet = pygame.image.load(p).convert_alpha()
            n = self.FRAME_COUNTS.get(enemy_type, 6)
            fw = sheet.get_width() // max(1, n)
            fh = sheet.get_height()
            sub = sheet.subsurface((0,0,fw,fh))
            self.enemy_surf = scale_preserve(sub, (self.tile, self.tile))
        except Exception as ex:
            print(f"✗ Failed loading enemy sprite: {ex}")
            self.enemy_surf = pygame.Surface((self.tile, self.tile))
            self.enemy_surf.fill((120, 0, 0))

    def handle_event(self, event):
        """Handle input for grid scene."""
        if event.type == pygame.KEYDOWN:
            dx = dy = 0
            if event.key == pygame.K_RIGHT: dx = 1
            if event.key == pygame.K_LEFT: dx = -1
            if event.key == pygame.K_UP: dy = -1
            if event.key == pygame.K_DOWN: dy = 1
            nx = max(0, min(self.grid_w-1, self.enemy_x + dx))
            ny = max(0, min(self.grid_h-1, self.enemy_y + dy))
            self.enemy_x, self.enemy_y = nx, ny

    def update(self, dt):
        """Update grid enemy movement."""
        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            # simple random movement
            import random
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            nx = max(0, min(self.grid_w-1, self.enemy_x + dx))
            ny = max(0, min(self.grid_h-1, self.enemy_y + dy))
            self.enemy_x, self.enemy_y = nx, ny

    def draw(self, surface):
        """Draw grid with enemy."""
        surface.fill((30,30,30))
        # draw grid
        for x in range(self.grid_w):
            for y in range(self.grid_h):
                rx = self.grid_origin_x + x * self.tile
                ry = self.grid_origin_y + y * self.tile
                rect = pygame.Rect(rx, ry, self.tile, self.tile)
                pygame.draw.rect(surface, (80,80,80), rect, 1)
        # draw enemy
        ex = self.grid_origin_x + self.enemy_x * self.tile
        ey = self.grid_origin_y + self.enemy_y * self.tile
        surface.blit(self.enemy_surf, (ex, ey))
        hp_txt = self.font.render(f'{self.enemy_type} HP: {max(0,self.enemy_hp)}', True, (255,255,255))
        surface.blit(hp_txt, (20, self.screen_height - 160))


