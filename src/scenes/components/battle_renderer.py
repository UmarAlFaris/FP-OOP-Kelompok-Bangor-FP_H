"""Rendering component for battle scene."""
import pygame


class BattleRenderer:
    """Handles all rendering for the battle scene."""
    
    def __init__(self, tile_size: int, grid_w: int, grid_h: int, origin_x: int, origin_y: int, screen_width: int):
        """Initialize the renderer.
        
        Args:
            tile_size: The tile size in pixels.
            grid_w: Grid width in tiles.
            grid_h: Grid height in tiles.
            origin_x: Grid origin x position.
            origin_y: Grid origin y position.
            screen_width: Screen width in pixels.
        """
        self.tile = tile_size
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.screen_width = screen_width
        
        self.font = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 20)
    
    def draw(self, surface, assets: dict, game_state: dict):
        """Draw the complete battle scene.
        
        Args:
            surface: The pygame surface to draw on.
            assets: Dictionary containing loaded assets from BattleAssetLoader.
            game_state: Dictionary containing current game state:
                - player: Player entity
                - enemies: List of enemy entities
                - cursor: [x, y] cursor position
                - mode: Current mode ('IDLE', 'MOVE', 'ATTACK', 'HEAL')
                - move_targets: Set of reachable positions
                - message: Current message string
                - turn: Current turn ('PLAYER' or 'ENEMY')
                - total_run_turns: Total turn count from manager
        """
        # Clear screen
        surface.fill((20, 20, 20))
        
        # Draw background
        self._draw_background(surface, assets, game_state['enemies'])
        
        # Draw move target highlights
        if game_state['mode'] == 'MOVE' and game_state['move_targets']:
            self._draw_move_targets(surface, game_state['move_targets'])
        
        # Draw player
        self._draw_player(surface, assets, game_state['player'])
        
        # Draw enemies
        self._draw_enemies(surface, assets, game_state['enemies'])
        
        # Draw cursor
        self._draw_cursor(surface, game_state['cursor'])
        
        # Draw UI panel
        self._draw_ui_panel(surface, game_state)
    
    def _draw_background(self, surface, assets: dict, enemies: list):
        """Draw the battlefield background.
        
        Args:
            surface: The pygame surface to draw on.
            assets: Dictionary containing loaded assets.
            enemies: List of enemy entities.
        """
        is_boss_fight = any(type(e).__name__ == 'Boss' and e.alive for e in enemies)
        
        if is_boss_fight and assets['boss_battle_bg']:
            surface.blit(assets['boss_battle_bg'], (self.origin_x, self.origin_y))
        elif assets['battlefield_bg']:
            surface.blit(assets['battlefield_bg'], (self.origin_x, self.origin_y))
        else:
            # Fallback to grid drawing if images not loaded
            for x in range(self.grid_w):
                for y in range(self.grid_h):
                    rx = self.origin_x + x * self.tile
                    ry = self.origin_y + y * self.tile
                    rect = pygame.Rect(rx, ry, self.tile, self.tile)
                    pygame.draw.rect(surface, (80, 80, 80), rect, 1)
    
    def _draw_move_targets(self, surface, move_targets: set):
        """Draw move target highlights.
        
        Args:
            surface: The pygame surface to draw on.
            move_targets: Set of reachable (x, y) positions.
        """
        for (mx, my) in move_targets:
            r = pygame.Rect(mx * self.tile + 6, my * self.tile + 6, self.tile - 12, self.tile - 12)
            pygame.draw.rect(surface, (180, 240, 180), r, 2)
    
    def _draw_player(self, surface, assets: dict, player):
        """Draw the player sprite and HP bar.
        
        Args:
            surface: The pygame surface to draw on.
            assets: Dictionary containing loaded assets.
            player: Player entity.
        """
        px = self.origin_x + player.x * self.tile
        py = self.origin_y + player.y * self.tile
        
        # Get current animation frame
        player_frames = assets['player_frames']
        anim_index = assets['player_anim_index']
        pframe = player_frames[anim_index]
        
        # Position sprite to sit on bottom center of tile
        rect = pframe.get_rect(midbottom=(px + self.tile // 2, py + self.tile - 8))
        surface.blit(pframe, rect)
        
        # Draw player HP bar
        ph_ratio = max(0, player.hp) / player.max_hp
        bar_w = int(self.tile * 0.8)
        bx = player.x * self.tile + (self.tile - bar_w) // 2
        by = player.y * self.tile + self.tile - 12
        pygame.draw.rect(surface, (40, 40, 40), (bx, by, bar_w, 6))
        pygame.draw.rect(surface, (50, 180, 50), (bx, by, int(bar_w * ph_ratio), 6))
        
        # Draw level indicator above player sprite
        level_text = f"Lv.{player.level}"
        level_surf = self.font_small.render(level_text, True, (255, 215, 0))
        level_rect = level_surf.get_rect(midbottom=(px + self.tile // 2, py - 40))
        surface.blit(level_surf, level_rect)
    
    def _draw_enemies(self, surface, assets: dict, enemies: list):
        """Draw all enemy sprites and HP bars.
        
        Args:
            surface: The pygame surface to draw on.
            assets: Dictionary containing loaded assets.
            enemies: List of enemy entities.
        """
        enemy_frames = assets['enemy_frames']
        enemy_anim_indexes = assets['enemy_anim_indexes']
        
        for i, e in enumerate(enemies):
            if not e.alive:
                continue
            
            ex = self.origin_x + e.x * self.tile
            ey = self.origin_y + e.y * self.tile
            
            frames = enemy_frames[i]
            idx = enemy_anim_indexes[i] % max(1, len(frames))
            ef = frames[idx]
            
            # Position sprite to sit on bottom center of tile
            erect = ef.get_rect(midbottom=(ex + self.tile // 2, ey + self.tile - 8))
            surface.blit(ef, erect)
            
            # Draw HP bar
            ehr = max(0, e.hp) / e.max_hp
            bar_w = int(self.tile * 0.8)
            bx = e.x * self.tile + (self.tile - bar_w) // 2
            by = e.y * self.tile + self.tile - 12
            pygame.draw.rect(surface, (40, 40, 40), (bx, by, bar_w, 6))
            pygame.draw.rect(surface, (50, 180, 50), (bx, by, int(bar_w * ehr), 6))
    
    def _draw_cursor(self, surface, cursor: list):
        """Draw the cursor highlight.
        
        Args:
            surface: The pygame surface to draw on.
            cursor: [x, y] cursor position.
        """
        crx = self.origin_x + cursor[0] * self.tile
        cry = self.origin_y + cursor[1] * self.tile
        pygame.draw.rect(surface, (255, 200, 0), (crx, cry, self.tile, self.tile), 3)
    
    def _draw_ui_panel(self, surface, game_state: dict):
        """Draw the UI panel at the bottom of the screen.
        
        Args:
            surface: The pygame surface to draw on.
            game_state: Dictionary containing current game state.
        """
        player = game_state['player']
        cursor = game_state['cursor']
        mode = game_state['mode']
        message = game_state['message']
        turn = game_state['turn']
        total_run_turns = game_state['total_run_turns']
        
        # Draw panel background
        panel = pygame.Rect(0, self.grid_h * self.tile, self.screen_width, 120)
        pygame.draw.rect(surface, (30, 30, 30), panel)
        
        # Draw info text
        info = f'Turn: {turn} | Mode: {mode} | Cursor: {cursor[0]},{cursor[1]}'
        surface.blit(self.font.render(info, True, (255, 255, 255)), (8, self.grid_h * self.tile + 6))
        
        # Draw message
        surface.blit(self.font.render(message, True, (230, 200, 60)), (8, self.grid_h * self.tile + 30))
        
        # Draw turn counter in bottom right
        turn_text = f'Total Turns: {total_run_turns}'
        turn_surf = self.font.render(turn_text, True, (100, 255, 255))
        surface.blit(turn_surf, (self.screen_width - 200, self.grid_h * self.tile + 6))
        
        # Draw player stats
        stats_text = f"Lv. {player.level} | HP: {player.hp}/{player.max_hp} | ATK: {player.atk} | Mana: {player.mana}"
        stats_surf = self.font.render(stats_text, True, (100, 255, 100))
        surface.blit(stats_surf, (8, self.grid_h * self.tile + 90))
