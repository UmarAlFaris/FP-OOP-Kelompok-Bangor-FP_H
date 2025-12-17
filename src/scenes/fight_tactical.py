"""Tactical grid-based battle scene with turn-based combat."""
import pygame
import os
from scenes.base import ScreenBase
from config import *
from entities.unit import Unit
from ai import fuzzy_logic as fuzzy
from utils import scale_preserve, bfs_reachable


class TurnBasedGrid(ScreenBase):
    """Turn-based grid with player and enemy units. Enemies use fuzzy logic for AI.
    Supports either `enemies` (list of dicts for simultaneous multi-enemy)
    or `stages` (list of enemy type names for sequential single-enemy stages).
    """
    def __init__(self, manager, screen_size, enemies: list[dict] = None, stages: list[str] = None, next_scene=None, forced_inference=None):
        super().__init__(manager, screen_size)

        self.FRAME_COUNTS = {
            'Zombie': 6,
            'Skeleton': 7,
            'Enderman': 14,
            'Boss': 8,
        }
        self.grid_w = 8
        self.grid_h = 6
        usable_h = self.screen_height - 120
        self.tile = min(self.screen_width // self.grid_w, usable_h // self.grid_h)
        # align grid to top-left
        self.origin_x = 0
        self.origin_y = 0

        # player
        self.player = {'type':'Player','x':1,'y':self.grid_h//2,'hp':40,'max_hp':40,'atk':8,'mana':100,'alive':True}
        
        # boss damage boost
        if stages and 'Boss' in stages:
            self.player['atk'] += 5  # boost +5 ATK for boss fight

        # support either simultaneous enemies or sequential stages
        self.stages = stages
        self.stage_index = 0
        self.forced_inference = forced_inference
        self.next_scene = next_scene

        # build initial enemies list
        self.enemies = []
        if stages and len(stages) > 0:
            # start with first stage as a single enemy
            etype = stages[0]
            ex = self.grid_w - 2
            ey = self.grid_h // 2
            if etype == 'Zombie': hp, atk, mana = 20, 3, 0
            elif etype == 'Skeleton': hp, atk, mana = 14, 1, 0
            elif etype == 'Enderman': hp, atk, mana = 24, 4, 80
            elif etype == 'Boss': hp, atk, mana = 40, 4, 100
            else: hp, atk, mana = 20, 2, 0
            self.enemies.append({'type':etype,'x':ex,'y':ey,'hp':hp,'max_hp':hp,'atk':atk,'mana':mana,'alive':True})
        else:
            enemies = enemies or []
            for e in enemies:
                etype = e.get('type')
                ex = e.get('x', self.grid_w-2)
                ey = e.get('y', self.grid_h//2)
                if etype == 'Zombie': hp, atk, mana = 20, 3, 0
                elif etype == 'Skeleton': hp, atk, mana = 14, 1, 0
                elif etype == 'Enderman': hp, atk, mana = 24, 4, 80
                elif etype == 'Boss': hp, atk, mana = 40, 4, 100
                else: hp, atk, mana = 20, 2, 0
                self.enemies.append({'type':etype,'x':ex,'y':ey,'hp':hp,'max_hp':hp,'atk':atk,'mana':mana,'alive':True})

        # load animated player frames
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.player_frames = []
        
        player_paths = [
            os.path.join(repo, 'assets', 'player')
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
                        self.player_frames.append(scale_preserve(img, (self.tile + 30, self.tile + 30)))
                    print(f"✓ Loaded {len(self.player_frames)} player frames from {player_dir}")
                    break
            except Exception as ex:
                print(f"✗ Failed loading player from {player_dir}: {ex}")
                
        if not self.player_frames:
            # fallback single square
            print("WARNING: No player frames loaded, using fallback")
            surf = pygame.Surface((self.tile, self.tile))
            surf.fill((200,200,200))
            self.player_frames = [surf]
        self.player_anim_index = 0
        self.player_anim_timer = 0
        self.player_anim_speed = 8

        # Load battlefield background images
        self.battlefield_bg = None
        self.boss_battle_bg = None
        try:
            battlefield_path = os.path.join(repo, 'assets', 'battlefield', 'battlefield_grid.png')
            if os.path.isfile(battlefield_path):
                bg_img = pygame.image.load(battlefield_path).convert()
                # Scale to fit grid area
                grid_width = self.grid_w * self.tile
                grid_height = self.grid_h * self.tile
                self.battlefield_bg = pygame.transform.scale(bg_img, (grid_width, grid_height))
                print(f"✓ Loaded battlefield background from {battlefield_path}")
            else:
                print(f"✗ Battlefield background not found at {battlefield_path}")
        except Exception as ex:
            print(f"✗ Failed loading battlefield background: {ex}")
        
        try:
            boss_path = os.path.join(repo, 'assets', 'battlefield', 'boss_battle.png')
            if os.path.isfile(boss_path):
                boss_img = pygame.image.load(boss_path).convert()
                # Scale to fit grid area
                grid_width = self.grid_w * self.tile
                grid_height = self.grid_h * self.tile
                self.boss_battle_bg = pygame.transform.scale(boss_img, (grid_width, grid_height))
                print(f"✓ Loaded boss battle background from {boss_path}")
            else:
                print(f"✗ Boss battle background not found at {boss_path}")
        except Exception as ex:
            print(f"✗ Failed loading boss battle background: {ex}")

        # load enemy animated frames per enemy
        self.enemy_frames = []
        self.enemy_anim_indexes = []
        self.enemy_anim_timers = []
        for e in self.enemies:
            et = e['type']
            name = et.lower()
            frames = []
            loaded = False
            
            enemy_paths = [
                os.path.join(repo, 'assets', name)
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
                
            self.enemy_frames.append(frames)
            self.enemy_anim_indexes.append(0)
            self.enemy_anim_timers.append(0)

        self.cursor = [0,0]
        self.turn = 'PLAYER'
        self.move_range = 2
        self.turn_count = 0  # track turn number

        # Use fuzzy logic module (already imported at module level)
        self.fuzzy = fuzzy

        self.font = pygame.font.SysFont(None, 24)
        # gameplay state
        self.mode = 'IDLE'
        self.move_targets = set()
        self.message = 'Giliran PLAYER. Tekan M:move A:attack H:heal E:end.'
        self.units = [self.player] + self.enemies

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # cursor keys
            if event.key in (pygame.K_RIGHT, pygame.K_d): self.cursor[0] = min(self.grid_w-1, self.cursor[0]+1)
            if event.key in (pygame.K_LEFT, pygame.K_a): self.cursor[0] = max(0, self.cursor[0]-1)
            if event.key in (pygame.K_DOWN, pygame.K_s): self.cursor[1] = min(self.grid_h-1, self.cursor[1]+1)
            if event.key in (pygame.K_UP, pygame.K_w): self.cursor[1] = max(0, self.cursor[1]-1)
            # mode keys
            if event.key == pygame.K_m and self.turn == 'PLAYER':
                self.mode = 'MOVE'
                self.move_targets = bfs_reachable((self.player['x'], self.player['y']), self.move_range, {(e['x'],e['y']) for e in self.enemies if e['alive']})
                self.message = 'Mode MOVE. Pilih petak tujuan lalu tekan Enter.'
            if event.key in (pygame.K_a, pygame.K_SPACE) and self.turn == 'PLAYER':
                self.mode = 'ATTACK'
                self.message = 'Mode ATTACK. Pilih petak musuh bersebelahan lalu Enter.'
            if event.key == pygame.K_h and self.turn == 'PLAYER':
                self.mode = 'HEAL'
                self.message = 'Mode HEAL. Tekan Enter untuk heal (+10 HP).'
            if event.key in (pygame.K_e, pygame.K_RETURN):
                if self.turn == 'PLAYER' and self.mode == 'IDLE':
                    self.end_turn()
                else:
                    self.confirm_action()

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx,my = event.pos
            if event.button == 1 and my < self.grid_h * self.tile:
                gx = mx // self.tile
                gy = my // self.tile
                self.cursor = [gx, gy]
                if self.turn == 'PLAYER' and self.mode in ('MOVE','ATTACK'):
                    self.confirm_action()

    def unit_at(self, pos):
        for u in self.units:
            if u.get('alive', True) and (u.get('x'), u.get('y')) == pos:
                return u
        return None

    def confirm_action(self):
        cx, cy = self.cursor
        if self.turn != 'PLAYER':
            return
        if self.mode == 'MOVE':
            if (cx, cy) in self.move_targets and self.unit_at((cx, cy)) is None:
                self.player['x'], self.player['y'] = cx, cy
                self.mode = 'IDLE'
                self.move_targets = set()
                self.message = f'Player moved to {cx},{cy}.'
                self.end_turn()
            else:
                self.message = 'Lokasi tidak valid untuk MOVE.'
        elif self.mode == 'ATTACK':
            target = self.unit_at((cx, cy))
            if target and target.get('type') != 'Player' and abs(self.player['x']-cx)+abs(self.player['y']-cy) == 1:
                target['hp'] -= self.player['atk']
                if target['hp'] <= 0:
                    target['alive'] = False
                    # increment player damage on enemy defeat
                    self.player['atk'] += 1
                    self.message = f'Enemy {target["type"]} defeated. ATK +1 (now {self.player["atk"]}).'
                else:
                    self.message = f'Attack! Enemy HP: {max(0,target["hp"])}.'
                self.mode = 'IDLE'
                self.end_turn()
            else:
                self.message = 'Target tidak valid untuk ATTACK.'
        elif self.mode == 'HEAL':
            heal_amount = 10
            old_hp = self.player['hp']
            self.player['hp'] = min(self.player['max_hp'], self.player['hp'] + heal_amount)
            healed = self.player['hp'] - old_hp
            self.message = f'Player healed +{healed} HP. HP: {self.player["hp"]}/{self.player["max_hp"]}.'
            self.mode = 'IDLE'
            self.end_turn()
        else:
            self.message = 'Tidak ada aksi dipilih. Tekan M/A/H atau E untuk end turn.'

    def end_turn(self):
        if self.turn != 'PLAYER':
            return
        self.turn = 'ENEMY'
        self.mode = 'IDLE'
        self.move_targets = set()
        self.message = 'Giliran ENEMY.'
        self.turn_count += 1  # increment turn counter
        
        # auto-win for Enderman at turn 20
        if self.turn_count >= 20 and self.stages and any(e.get('type') == 'Enderman' for e in self.enemies if e.get('alive')):
            for e in self.enemies:
                if e.get('type') == 'Enderman':
                    e['alive'] = False
            self.message = 'Turn 20 reached! Enderman auto-defeated!'
            if self.next_scene:
                self.manager.go_to(self.next_scene)
            else:
                self.manager.go_to('main_menu')
            return
        # enemy actions sequentially
        for e in self.enemies:
            if not e['alive']:
                continue
            self.enemy_action(e)
            if self.player['hp'] <= 0:
                break
        # check results
        if self.player['hp'] <= 0:
            self.manager.go_to('end_menu')
            return
        if all(not e['alive'] for e in self.enemies):
            # if sequential stages were provided, advance to next stage
            if self.stages:
                if self.stage_index < len(self.stages) - 1:
                    self.stage_index += 1
                    # spawn next single enemy
                    etype = self.stages[self.stage_index]
                    ex = self.grid_w - 2
                    ey = self.grid_h // 2
                    if etype == 'Zombie': hp, atk, mana = 20, 3, 0
                    elif etype == 'Skeleton': hp, atk, mana = 14, 1, 0
                    elif etype == 'Enderman': hp, atk, mana = 24, 4, 80
                    elif etype == 'Boss': hp, atk, mana = 40, 4, 100
                    else: hp, atk, mana = 20, 2, 0
                    self.enemies = [{'type':etype,'x':ex,'y':ey,'hp':hp,'max_hp':hp,'atk':atk,'mana':mana,'alive':True}]
                    # update self.units to include new enemy (fix for unit_at check)
                    self.units = [self.player] + self.enemies
                    # rebuild enemy_frames arrays
                    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                    self.enemy_frames = []
                    self.enemy_anim_indexes = []
                    self.enemy_anim_timers = []
                    for e in self.enemies:
                        et = e['type']
                        name = et.lower()
                        frames = []
                        loaded = False
                        
                        enemy_paths = [
                            os.path.join(repo, 'assets', name)
                        ]
                        
                        for enemy_dir in enemy_paths:
                            if loaded:
                                break
                                
                            # Try spritesheet first (Idle.png or idle.png)
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
                                    sprite_size = (self.tile + 100, self.tile + 100) if et == 'Boss' else (self.tile + 30, self.tile + 30)
                                    for i in range(n):
                                        sub = sheet.subsurface((i*fw, 0, fw, fh))
                                        frames.append(scale_preserve(sub, sprite_size))
                                    print(f"✓ Stage progression: Loaded {et} spritesheet ({n} frames)")
                                    loaded = True
                                    break
                                except Exception as ex:
                                    print(f"✗ Failed loading {et} sheet: {ex}")
                                    
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
                                        print(f"✓ Stage progression: Loaded {et} ({len(frames)} frames)")
                                        loaded = True
                                        break
                                except Exception as ex:
                                    print(f"✗ Failed loading {et}: {ex}")
                                    
                        if not frames:
                            print(f"WARNING: Stage progression - No frames for {et}, using fallback")
                            surf = pygame.Surface((self.tile, self.tile))
                            surf.fill((120, 0, 0))
                            frames = [surf]
                            
                        self.enemy_frames.append(frames)
                        self.enemy_anim_indexes.append(0)
                        self.enemy_anim_timers.append(0)
                    # restore player HP
                    self.player['hp'] = self.player['max_hp']
                    self.turn = 'PLAYER'
                    self.mode = 'IDLE'
                    self.message = f'Stage {self.stage_index+1}: {self.enemies[0]["type"]}. ATK={self.player["atk"]}. M:move A:attack H:heal'
                    return
                else:
                    if self.next_scene:
                        self.manager.go_to(self.next_scene)
                    else:
                        self.manager.go_to('main_menu')
                    return
            else:
                if self.next_scene:
                    self.manager.go_to(self.next_scene)
                else:
                    self.manager.go_to('main_menu')
                return
        # back to player
        self.turn = 'PLAYER'
        self.message = 'Giliran PLAYER. Tekan M untuk move, A untuk attack, E untuk end turn.'

    def enemy_action(self, e):
        # simple enemy action using fuzzy.get_final_action when available
        occupied = {(ee['x'], ee['y']) for ee in self.enemies if ee['alive']}
        occupied.add((self.player['x'], self.player['y']))
        hp_p = int(100 * self.player['hp'] / max(1, self.player['max_hp']))
        hp_b = int(100 * e['hp'] / max(1, e['max_hp']))
        mana_p = int(getattr(self.player, 'mana', 0))
        mana_b = int(e.get('mana', 0))
        cd_p = 0
        if self.fuzzy:
            try:
                action, target = self.fuzzy.get_final_action(e['type'], hp_p, hp_b, mana_p, mana_b, cd_p, (e['x'], e['y']), (self.player['x'], self.player['y']), occupied, self.grid_w, self.grid_h)
            except Exception:
                action, target = ('MOVE_CLOSE', None)
        else:
            action, target = ('MOVE_CLOSE', None)
        if action in ('ATTACK', 'RANGED_ATTACK'):
            if abs(e['x'] - self.player['x']) + abs(e['y'] - self.player['y']) <= 2:
                self.player['hp'] -= e['atk']
        elif action in ('MOVE_CLOSE', 'MOVE_RETREAT', 'TELEPORT'):
            if target and target not in occupied:
                e['x'], e['y'] = target
        elif action == 'HEAL':
            e['hp'] = min(e['max_hp'], e['hp'] + e.get('heal_amount', 10))

    def update(self, dt):
        # advance animations
        self.player_anim_timer += 1
        if self.player_anim_timer >= self.player_anim_speed:
            self.player_anim_timer = 0
            self.player_anim_index = (self.player_anim_index + 1) % len(self.player_frames)
        for i, frames in enumerate(self.enemy_frames):
            self.enemy_anim_timers[i] += 1
            if self.enemy_anim_timers[i] >= 8:
                self.enemy_anim_timers[i] = 0
                self.enemy_anim_indexes[i] = (self.enemy_anim_indexes[i] + 1) % max(1, len(frames))

        if self.turn == 'ENEMY':
            occupied = {(e['x'],e['y']) for e in self.enemies if e['alive']}
            occupied.add((self.player['x'], self.player['y']))
            for e in self.enemies:
                if not e['alive']: continue
                hp_p = int(100 * self.player['hp'] / max(1, self.player['max_hp']))
                hp_b = int(100 * e['hp'] / max(1, e['max_hp']))
                mana_p = int(getattr(self.player,'mana',0))
                mana_b = int(getattr(e,'mana',0))
                cd_p = 0
                if self.fuzzy:
                    try:
                        action, target = self.fuzzy.get_final_action(e['type'], hp_p, hp_b, mana_p, mana_b, cd_p, (e['x'],e['y']), (self.player['x'],self.player['y']), occupied, self.grid_w, self.grid_h)
                    except Exception:
                        action, target = ('MOVE_CLOSE', None)
                else:
                    action, target = ('MOVE_CLOSE', None)
                if action in ('ATTACK','RANGED_ATTACK'):
                    if abs(e['x']-self.player['x'])+abs(e['y']-self.player['y']) <= 2:
                        self.player['hp'] -= e['atk']
                elif action in ('MOVE_CLOSE','MOVE_RETREAT','TELEPORT'):
                    if target and target not in occupied:
                        e['x'], e['y'] = target
                elif action == 'HEAL':
                    e['hp'] = min(e['max_hp'], e['hp'] + getattr(e,'heal_amount',10))

            if self.player['hp'] <= 0:
                self.manager.go_to('end_menu')
                return
            if all(not e['alive'] for e in self.enemies):
                if self.next_scene:
                    self.manager.go_to(self.next_scene)
                else:
                    self.manager.go_to('main_menu')
                return
            self.turn = 'PLAYER'
            self.mode = 'IDLE'

    def draw(self, surface):
        surface.fill((20,20,20))
        # Draw battlefield background based on enemy type
        is_boss_fight = any(e.get('type') == 'Boss' and e.get('alive') for e in self.enemies)
        if is_boss_fight and self.boss_battle_bg:
            surface.blit(self.boss_battle_bg, (self.origin_x, self.origin_y))
        elif self.battlefield_bg:
            surface.blit(self.battlefield_bg, (self.origin_x, self.origin_y))
        else:
            # Fallback to grid drawing if images not loaded
            for x in range(self.grid_w):
                for y in range(self.grid_h):
                    rx = self.origin_x + x * self.tile
                    ry = self.origin_y + y * self.tile
                    rect = pygame.Rect(rx, ry, self.tile, self.tile)
                    pygame.draw.rect(surface, (80,80,80), rect, 1)

        # move target highlights
        if self.mode == 'MOVE' and self.move_targets:
            for (mx,my) in self.move_targets:
                r = pygame.Rect(mx*self.tile+6, my*self.tile+6, self.tile-12, self.tile-12)
                pygame.draw.rect(surface, (180,240,180), r, 2)

        # draw player (animated)
        px = self.origin_x + self.player['x'] * self.tile
        py = self.origin_y + self.player['y'] * self.tile
        pframe = self.player_frames[self.player_anim_index]
        # position sprite to sit on bottom center of tile
        rect = pframe.get_rect(midbottom=(px + self.tile//2, py + self.tile - 8))
        surface.blit(pframe, rect)
        # draw player HP bar
        ph_ratio = max(0, self.player['hp']) / self.player['max_hp']
        bar_w = int(self.tile * 0.8)
        bx = self.player['x']*self.tile + (self.tile-bar_w)//2
        by = self.player['y']*self.tile + self.tile - 12
        pygame.draw.rect(surface, (40,40,40), (bx,by,bar_w,6))
        pygame.draw.rect(surface, (50,180,50), (bx,by,int(bar_w*ph_ratio),6))

        # draw enemies
        for i, e in enumerate(self.enemies):
            if not e['alive']: continue
            ex = self.origin_x + e['x'] * self.tile
            ey = self.origin_y + e['y'] * self.tile
            frames = self.enemy_frames[i]
            idx = self.enemy_anim_indexes[i] % max(1, len(frames))
            ef = frames[idx]
            # position sprite to sit on bottom center of tile
            erect = ef.get_rect(midbottom=(ex + self.tile//2, ey + self.tile - 8))
            surface.blit(ef, erect)
            # hp bar
            ehr = max(0, e['hp']) / e['max_hp']
            bar_w = int(self.tile * 0.8)
            bx = e['x']*self.tile + (self.tile-bar_w)//2
            by = e['y']*self.tile + self.tile - 12
            pygame.draw.rect(surface, (40,40,40), (bx,by,bar_w,6))
            pygame.draw.rect(surface, (50,180,50), (bx,by,int(bar_w*ehr),6))

        # cursor
        crx = self.origin_x + self.cursor[0] * self.tile
        cry = self.origin_y + self.cursor[1] * self.tile
        pygame.draw.rect(surface, (255,200,0), (crx, cry, self.tile, self.tile), 3)

        # UI panel bottom
        panel = pygame.Rect(0, self.grid_h * self.tile, self.screen_width, 120)
        pygame.draw.rect(surface, (30,30,30), panel)
        info = f'Turn: {self.turn} | Mode: {self.mode} | Cursor: {self.cursor[0]},{self.cursor[1]}'
        surface.blit(self.font.render(info, True, (255,255,255)), (8, self.grid_h*self.tile + 6))
        surface.blit(self.font.render(self.message, True, (230,200,60)), (8, self.grid_h*self.tile + 30))
        # turn counter in bottom right
        turn_text = f'Turn Count: {self.turn_count}'
        turn_surf = self.font.render(turn_text, True, (100, 255, 255))
        surface.blit(turn_surf, (self.screen_width - 200, self.grid_h*self.tile + 6))
