"""Utility functions for the game."""
import pygame
from collections import deque


def scale_preserve(surface, target_size):
    """Scale a surface to fit within target_size while preserving aspect ratio.
    
    Args:
        surface: pygame.Surface to scale
        target_size: tuple (width, height) for target dimensions
        
    Returns:
        Scaled surface centered in target_size canvas
    """
    tw, th = target_size
    ow, oh = surface.get_size()
    if oh == 0:
        return pygame.Surface(target_size, pygame.SRCALPHA)
    scale = th / oh
    nw = max(1, int(ow * scale))
    nh = max(1, int(oh * scale))
    scaled = pygame.transform.smoothscale(surface, (nw, nh))
    out = pygame.Surface((tw, th), pygame.SRCALPHA)
    x = (tw - nw) // 2
    y = (th - nh) // 2
    out.blit(scaled, (x, y))
    return out


def bfs_reachable(start, max_dist, obstacles, grid_w=8, grid_h=6, blocked_tiles=None):
    """Find all grid positions reachable within max_dist steps using BFS.
    
    Args:
        start: tuple (x, y) starting position
        max_dist: maximum distance/steps allowed
        obstacles: set of (x, y) positions that block movement (e.g., other units)
        grid_w: grid width
        grid_h: grid height
        blocked_tiles: set of (x, y) map tiles that are impassable (fences, stones)
        
    Returns:
        set of (x, y) positions reachable from start
    """
    # Import here to avoid circular import
    from config import MAP_BLOCKED_TILES
    
    # Use provided blocked_tiles or default to config
    if blocked_tiles is None:
        blocked_tiles = MAP_BLOCKED_TILES
    
    q = deque()
    q.append((start, 0))
    visited = {start}
    results = set()
    while q:
        (x, y), d = q.popleft()
        if d > max_dist:
            continue
        results.add((x, y))
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                continue
            if (nx, ny) in visited:
                continue
            if (nx, ny) in obstacles:
                continue
            if (nx, ny) in blocked_tiles:
                continue
            visited.add((nx, ny))
            q.append(((nx, ny), d+1))
    return results
