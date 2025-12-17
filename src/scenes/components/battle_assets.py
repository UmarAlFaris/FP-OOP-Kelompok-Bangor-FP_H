"""Asset loading component for battle scene."""
import pygame
import os
from utils import scale_preserve


class BattleAssetLoader:
    """Handles all asset loading for the battle scene including images and sounds."""
    
    # Frame counts for spritesheet extraction
    FRAME_COUNTS = {
        'Zombie': 6,
        'Skeleton': 7,
        'Enderman': 14,
        'Boss': 8,
    }
    
    def __init__(self, tile_size: int):
        """Initialize the asset loader.
        
        Args:
            tile_size: The tile size in pixels for scaling sprites.
        """
        self.tile = tile_size
        self.repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    def load_assets(self, enemies_list: list, grid_w: int, grid_h: int) -> dict:
        """Load all assets required for battle.
        
        Args:
            enemies_list: List of enemy entity objects.
            grid_w: Grid width in tiles.
            grid_h: Grid height in tiles.
            
        Returns:
            Dictionary containing all loaded assets:
            - player_frames: list of player animation surfaces
            - battlefield_bg: background surface for regular battles
            - boss_battle_bg: background surface for boss battles
            - enemy_frames: list of frame lists per enemy
            - enemy_anim_indexes: list of animation indexes per enemy
            - enemy_anim_timers: list of animation timers per enemy
            - sounds: dict of sound objects keyed by name
            - boss_music_path: path to boss music file
        """
        assets = {}
        
        # Load player frames
        assets['player_frames'] = self._load_player_frames()
        assets['player_anim_index'] = 0
        assets['player_anim_timer'] = 0
        assets['player_anim_speed'] = 8
        
        # Load backgrounds
        assets['battlefield_bg'], assets['boss_battle_bg'] = self._load_backgrounds(grid_w, grid_h)
        
        # Load enemy frames
        enemy_frames, enemy_anim_indexes, enemy_anim_timers = self._load_enemy_frames(enemies_list)
        assets['enemy_frames'] = enemy_frames
        assets['enemy_anim_indexes'] = enemy_anim_indexes
        assets['enemy_anim_timers'] = enemy_anim_timers
        
        # Load sounds
        assets['sounds'] = self._load_sounds()
        
        # Boss music path
        sounds_dir = os.path.join(self.repo, 'assets', 'sounds')
        assets['boss_music_path'] = os.path.join(sounds_dir, 'sound_boss.mp3')
        
        return assets
    
    def reload_enemy_frames(self, enemies_list: list) -> tuple:
        """Reload enemy frames for a new set of enemies (e.g., stage progression).
        
        Args:
            enemies_list: List of enemy entity objects.
            
        Returns:
            Tuple of (enemy_frames, enemy_anim_indexes, enemy_anim_timers)
        """
        return self._load_enemy_frames(enemies_list)
    
    def _load_player_frames(self) -> list:
        """Load animated player frames.
        
        Returns:
            List of player animation surfaces.
        """
        player_frames = []
        player_paths = [
            os.path.join(self.repo, 'assets', 'player')
        ]
        
        for player_dir in player_paths:
            if not os.path.isdir(player_dir):
                continue
            try:
                files = sorted([f for f in os.listdir(player_dir) if f.lower().startswith('idle') and f.lower().endswith('.png')])
                if files:
                    for f in files:
                        p = os.path.join(player_dir, f)
                        img = pygame.image.load(p).convert_alpha()
                        player_frames.append(scale_preserve(img, (self.tile + 30, self.tile + 30)))
                    print(f"✓ Loaded {len(player_frames)} player frames from {player_dir}")
                    break
            except Exception as ex:
                print(f"✗ Failed loading player from {player_dir}: {ex}")
                
        if not player_frames:
            # fallback single square
            print("WARNING: No player frames loaded, using fallback")
            surf = pygame.Surface((self.tile, self.tile))
            surf.fill((200, 200, 200))
            player_frames = [surf]
        
        return player_frames
    
    def _load_backgrounds(self, grid_w: int, grid_h: int) -> tuple:
        """Load battlefield background images.
        
        Args:
            grid_w: Grid width in tiles.
            grid_h: Grid height in tiles.
            
        Returns:
            Tuple of (battlefield_bg, boss_battle_bg) surfaces.
        """
        grid_width = grid_w * self.tile
        grid_height = grid_h * self.tile
        
        battlefield_bg = None
        boss_battle_bg = None
        
        # Load regular battlefield background
        try:
            battlefield_path = os.path.join(self.repo, 'assets', 'battlefield', 'battlefield_grid.png')
            if os.path.isfile(battlefield_path):
                bg_img = pygame.image.load(battlefield_path).convert()
                battlefield_bg = pygame.transform.scale(bg_img, (grid_width, grid_height))
                print(f"✓ Loaded battlefield background from {battlefield_path}")
            else:
                print(f"✗ Battlefield background not found at {battlefield_path}")
        except Exception as ex:
            print(f"✗ Failed loading battlefield background: {ex}")
        
        # Load boss battle background
        try:
            boss_path = os.path.join(self.repo, 'assets', 'battlefield', 'boss_battle.png')
            if os.path.isfile(boss_path):
                boss_img = pygame.image.load(boss_path).convert()
                boss_battle_bg = pygame.transform.scale(boss_img, (grid_width, grid_height))
                print(f"✓ Loaded boss battle background from {boss_path}")
            else:
                print(f"✗ Boss battle background not found at {boss_path}")
        except Exception as ex:
            print(f"✗ Failed loading boss battle background: {ex}")
        
        return battlefield_bg, boss_battle_bg
    
    def _load_enemy_frames(self, enemies_list: list) -> tuple:
        """Load animated frames for all enemies.
        
        Args:
            enemies_list: List of enemy entity objects.
            
        Returns:
            Tuple of (enemy_frames, enemy_anim_indexes, enemy_anim_timers).
        """
        enemy_frames = []
        enemy_anim_indexes = []
        enemy_anim_timers = []
        
        for e in enemies_list:
            et = type(e).__name__
            name = et.lower()
            frames = []
            loaded = False
            
            enemy_paths = [
                os.path.join(self.repo, 'assets', name)
            ]
            
            for enemy_dir in enemy_paths:
                if loaded:
                    break
                    
                # Try spritesheet first (Idle.png or idle.png - case insensitive)
                sheet_path = None
                for fname in ['Idle.png', 'idle.png']:
                    test_path = os.path.join(enemy_dir, fname)
                    if os.path.isfile(test_path):
                        sheet_path = test_path
                        break
                        
                if sheet_path:
                    try:
                        sheet = pygame.image.load(sheet_path).convert_alpha()
                        n = self.FRAME_COUNTS.get(et, 6)
                        fw = sheet.get_width() // max(1, n)
                        fh = sheet.get_height()
                        # Boss uses larger sprite size
                        sprite_size = (self.tile + 100, self.tile + 100) if et == 'Boss' else (self.tile + 30, self.tile + 30)
                        for i in range(n):
                            sub = sheet.subsurface((i*fw, 0, fw, fh))
                            frames.append(scale_preserve(sub, sprite_size))
                        print(f"✓ Loaded {et} spritesheet ({n} frames) from {sheet_path}")
                        loaded = True
                        break
                    except Exception as ex:
                        print(f"✗ Failed loading {et} sheet from {sheet_path}: {ex}")
                        
                # Try individual files
                if os.path.isdir(enemy_dir):
                    try:
                        files = sorted([f for f in os.listdir(enemy_dir) if f.lower().endswith('.png')])
                        if files:
                            sprite_size = (self.tile + 100, self.tile + 100) if et == 'Boss' else (self.tile + 30, self.tile + 30)
                            for f in files:
                                p = os.path.join(enemy_dir, f)
                                img = pygame.image.load(p).convert_alpha()
                                frames.append(scale_preserve(img, sprite_size))
                            print(f"✓ Loaded {et} from {enemy_dir} ({len(frames)} frames)")
                            loaded = True
                            break
                    except Exception as ex:
                        print(f"✗ Failed loading {et} from {enemy_dir}: {ex}")
                        
            if not frames:
                print(f"WARNING: No frames for {et}, using fallback")
                surf = pygame.Surface((self.tile, self.tile))
                surf.fill((120, 0, 0))
                frames = [surf]
                
            enemy_frames.append(frames)
            enemy_anim_indexes.append(0)
            enemy_anim_timers.append(0)
        
        return enemy_frames, enemy_anim_indexes, enemy_anim_timers
    
    def _load_sounds(self) -> dict:
        """Load all sound effects.
        
        Returns:
            Dictionary of sound objects keyed by name.
        """
        sounds_dir = os.path.join(self.repo, 'assets', 'sounds')
        sounds = {}
        sound_files = {
            'player_attack': 'Player_attack.mp3',
            'heal': 'Heal.mp3',
            'zombie_spawn': 'Zombie_spawn.mp3',
            'zombie_attack': 'Zombie_attack.mp3',
            'skeleton_spawn': 'Skeleton_spawn.mp3',
            'skeleton_attack': 'Skeleton_attack.mp3',
            'enderman_spawn': 'Enderman_spawn.mp3',
            'enderman_attack': 'Enderman_attack.mp3',
            'enderman_teleport': 'Enderman_teleport.mp3',
            'boss_spawn': 'Boss_spawn.mp3',
            'boss_attack': 'Boss_attack.mp3',
        }
        for key, filename in sound_files.items():
            try:
                sound_path = os.path.join(sounds_dir, filename)
                sounds[key] = pygame.mixer.Sound(sound_path)
            except FileNotFoundError:
                print(f"Warning: Sound file not found: {filename}")
                sounds[key] = None
            except Exception as e:
                print(f"Warning: Could not load sound {filename}: {e}")
                sounds[key] = None
        
        return sounds
