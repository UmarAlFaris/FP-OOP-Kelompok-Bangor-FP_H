"""Game configuration constants."""
import pygame
import os

# Grid & Window
GRID_W, GRID_H = 8, 6
TILE = 80
WIDTH, HEIGHT = 1200, 800
FPS = 60

# Gameplay Constants
MOVE_RANGE = 1
PLAYER_MAX_HP = 20
PLAYER_ATK = 5
PLAYER_MANA = 100
PLAYER_MANA_REGEN = 5
PLAYER_HEAL_AMOUNT = 10
PLAYER_HEAL_COST = 50
RANGED_COST = 20

ENEMY_MAX_HP = 20
ENEMY_ATK = 1

# Sprite Offsets
ZOMBIE_Y_OFFSET = 27
SKELETON_Y_OFFSET = 27
ENDERMAN_Y_OFFSET = 22
ENDERMAN_X_OFFSET = 20
BOSS_Y_OFFSET = 1

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK = (40, 40, 40)
GREEN = (50, 180, 50)
RED = (200, 60, 60)
BLUE = (60, 120, 200)
YELLOW = (230, 200, 60)
PURPLE = (160, 80, 200)
LIGHT_BLUE = (140, 200, 255)


def asset_path(rel_path):
    """Get the absolute path to an asset file.
    
    Args:
        rel_path: Relative path like 'player/idle1.png'
        
    Returns:
        Absolute path to the asset file
    """
    # Get the repository root (two levels up from config.py)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    assets_path = os.path.join(repo_root, 'assets', rel_path)
    
    if os.path.isfile(assets_path):
        return assets_path
    
    # Try case-insensitive fallback
    parent = os.path.dirname(assets_path)
    if os.path.isdir(parent):
        for f in os.listdir(parent):
            if f.lower() == os.path.basename(rel_path).lower():
                return os.path.join(parent, f)
    
    return assets_path  # Return the path even if file doesn't exist

