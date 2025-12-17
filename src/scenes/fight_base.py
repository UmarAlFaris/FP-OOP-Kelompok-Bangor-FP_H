import pygame
import os
import sys
from scenes.base import ScreenBase
from ui.button import Button
from config import *
from entities.unit import Unit
from ai import fuzzy_logic as fuzzy


def scale_preserve(surface, target_size):
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


def bfs_reachable(start, max_dist, obstacles, grid_w=8, grid_h=6):
    from collections import deque
    q = deque()
    q.append((start, 0))
    visited = {start}
    results = set()
    while q:
        (x, y), d = q.popleft()
        if d > max_dist:
            continue
        results.add((x, y))
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < grid_w and 0 <= ny < grid_h):
                continue
            if (nx, ny) in visited:
                continue
            if (nx, ny) in obstacles:
                continue
            visited.add((nx, ny))
            q.append(((nx, ny), d+1))
    return results


class FightBase(ScreenBase):
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

        self._load_enemy(self.stage_index)

    def _load_enemy(self, index):
        etype = self.stages[index]
        self.enemy_type = etype
        # default stats
        if etype == 'Zombie':
            self.enemy_hp = 20
        elif etype == 'Skeleton':
            self.enemy_hp = 14
        elif etype == 'Enderman':
            self.enemy_hp = 24
        elif etype == 'Boss':
            self.enemy_hp = 40
        else:
            self.enemy_hp = 20

        # load animation frames
        name = etype.lower()
        sheet_path = os.path.join(os.path.dirname(__file__), '..', 'Code', 'assets', name, 'Idle.png')
        # also try project assets path
        sheet_path_alt = os.path.join(os.path.dirname(__file__), '..', '..', 'Code', 'assets', name, 'Idle.png')
        if os.path.isfile(sheet_path):
            p = sheet_path
        elif os.path.isfile(sheet_path_alt):
            p = sheet_path_alt
        else:
            # fallback to assets folder
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', name, 'Idle.png')

        self.frames = []
        class TurnBasedGrid(ScreenBase):
            """Port of Code/main.py in-scene: grid-based, turn-based, staged enemies.
            Accepts `stages` (list of enemy type names) and `forced_inference`.
            This mirrors the gameplay logic in `Code/main.py` so S3 behaves identically.
            """
            def __init__(self, manager, screen_size, stages: list[str], next_scene=None, forced_inference=None):
                super().__init__(manager, screen_size)
                
                # Configuration from config.py
                self.GRID_W = GRID_W
                self.GRID_H = GRID_H
                self.TILE = min(self.screen_width // self.GRID_W, (self.screen_height - 120) // self.GRID_H)
                self.origin_x = 0
                self.origin_y = 0

                # store stages
                self.stages = stages[:] if stages else ['Zombie']
                self.stage_index = 0
                self.next_scene = next_scene
                self.forced_inference = forced_inference

                # player unit
                self.player = Unit(1, self.GRID_H//2, PLAYER_MAX_HP, PLAYER_ATK, 'PLAYER', 
                                  mana=PLAYER_MANA, mana_regen=PLAYER_MANA_REGEN)
                
                # animation assets
                self.player_idle_anim = None
                self.zombie_frames = []
                self.skeleton_frames = []
                self.enderman_frames = []
                self.boss_frames = []
                
                # Load player idle frames
                try:
                    idle_frames = []
                    for i in range(1, 9):
                        p = asset_path(f'player/idle{i}.png')
                        if os.path.isfile(p):
                            idle_frames.append(p)
                    if idle_frames:
                        print(f"Loaded {len(idle_frames)} player frames")
                    else:
                        print("WARNING: No player frames loaded, using fallback")
                except Exception as e:
                    print(f"Error loading player frames: {e}")
                
                # Load zombie frames
                try:
                    sheet = pygame.image.load(asset_path('zombie/Idle.png')).convert_alpha()
                    n_frames = 6
                    fw = sheet.get_width() // n_frames
                    fh = sheet.get_height()
                    for i in range(n_frames):
                        sub = sheet.subsurface((i*fw, 0, fw, fh))
                        self.zombie_frames.append(scale_preserve(sub, (self.TILE+30, self.TILE+30)))
                except Exception as e:
                    print(f"WARNING: No frames for Zombie, using fallback")
                    self.zombie_frames = []
                
                # Load skeleton frames
                try:
                    skel_sheet = pygame.image.load(asset_path('skeleton/Idle.png')).convert_alpha()
                    n_skel = 7
                    skel_fw = skel_sheet.get_width() // n_skel
                    for i in range(n_skel):
                        sub = skel_sheet.subsurface((i*skel_fw, 0, skel_fw, skel_sheet.get_height()))
                        self.skeleton_frames.append(scale_preserve(sub, (self.TILE+30, self.TILE+30)))
                except Exception as e:
                    print(f"WARNING: No frames for Skeleton")
                    self.skeleton_frames = []
                
                # Load enderman frames
                try:
                    end_sheet = pygame.image.load(asset_path('enderman/Idle.png')).convert_alpha()
                    n_end = 14
                    end_fw = end_sheet.get_width() // n_end
                    for i in range(n_end):
                        sub = end_sheet.subsurface((i*end_fw, 0, end_fw, end_sheet.get_height()))
                        self.enderman_frames.append(scale_preserve(sub, (self.TILE+30, self.TILE+30)))
                except Exception as e:
                    print(f"WARNING: No frames for Enderman")
                    self.enderman_frames = []
                
                # Load boss frames
                try:
                    boss_sheet = pygame.image.load(asset_path('boss/Idle.png')).convert_alpha()
                    n_boss = 8
                    boss_fw = boss_sheet.get_width() // n_boss
                    for i in range(n_boss):
                        sub = boss_sheet.subsurface((i*boss_fw, 0, boss_fw, boss_sheet.get_height()))
                        self.boss_frames.append(scale_preserve(sub, (self.TILE+100, self.TILE+100)))
                except Exception as e:
                    print(f"WARNING: No frames for Boss")
                    self.boss_frames = []

                # gameplay state
                self.units = [self.player]
                self.enemy = None
                self.enemy_type = None
                self.turn = 'PLAYER'
                self.cursor = [0,0]
                self.mode = 'IDLE'
                self.move_targets = set()
                self.selected_target = None
                self.message = ''
                # anim timers
                self.zombie_anim_index = 0; self.zombie_anim_timer = 0; self.zombie_anim_speed = 8
                self.skeleton_anim_index = 0; self.skeleton_anim_timer = 0; self.skeleton_anim_speed = 8
                self.enderman_anim_index = 0; self.enderman_anim_timer = 0; self.enderman_anim_speed = 6
                self.boss_anim_index = 0; self.boss_anim_timer = 0; self.boss_anim_speed = 7

                # spawn first enemy
                self.victory = False
                self.spawn_enemy(self.stage_index)

            def unit_at(self, pos):
                for u in self.units:
                    if getattr(u, 'alive', True) and u.pos() == pos:
                        return u
                return None

            def spawn_enemy(self, index):
                etype = self.stages[index]
                self.enemy_type = etype
                ex, ey = self.GRID_W-2, self.GRID_H//2
                if etype == 'Zombie': ehp, eatk, emana, erange = 20, 3, 0, 1
                elif etype == 'Skeleton': ehp, eatk, emana, erange = 10, 1, 0, 3
                elif etype == 'Enderman': ehp, eatk, emana, erange = 15, 4, 80, 3
                elif etype == 'Boss': ehp, eatk, emana, erange = 30, 4, 100, 2
                else: ehp, eatk, emana, erange = 20, 1, 50, 1
                
                # Create enemy using Unit class
                self.enemy = Unit(ex, ey, ehp, eatk, 'ENEMY', mana=emana, 
                                 mana_regen=5 if etype in ('Enderman', 'Boss') else 0)
                self.enemy.max_hp = ehp
                self.enemy.mana = emana
                self.enemy.range = erange
                if etype == 'Boss':
                    self.enemy.ranged_atk = 2
                    self.enemy.heal_amount = 10
                    self.enemy.heal_cost = 50
                
                # update units
                self.units = [self.player, self.enemy]
                self.turn = 'PLAYER'
                self.mode = 'IDLE'
                self.move_targets = set()
                self.message = f'Starting Stage {self.stage_index+1}: {self.enemy_type}. Giliran PLAYER. Tekan M untuk move, A untuk attack, E untuk end turn.'

            def handle_event(self, event):
                # similar mapping to Code/main.py
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # go back to manager main menu
                        self.manager.go_to('main_menu')
                        return
                    if event.key in (pygame.K_SPACE, pygame.K_e):
                        self.end_turn()
                    if event.key == pygame.K_m and self.turn == 'PLAYER':
                        self.mode = 'MOVE'
                        # compute move targets using bfs reachable
                        self.move_targets = bfs_reachable(self.player.pos(), MOVE_RANGE, {self.enemy.pos()}, 
                                                          self.GRID_W, self.GRID_H)
                        self.message = 'Mode MOVE. Tekan Enter untuk konfirmasi.'
                    if event.key == pygame.K_a and self.turn == 'PLAYER':
                        self.mode = 'ATTACK'
                        self.message = 'Mode ATTACK. Pilih petak bersebelahan dan tekan Enter.'
                    if event.key == pygame.K_f and self.turn == 'PLAYER':
                        self.mode = 'RANGED'
                        self.message = f'Mode RANGED. Pilih tile untuk menyerang.'
                    if event.key == pygame.K_h and self.turn == 'PLAYER':
                        # heal
                        if getattr(self.player, 'mana', 0) >= PLAYER_HEAL_COST:
                            self.player.mana -= PLAYER_HEAL_COST
                            self.player.hp = min(self.player.max_hp, self.player.hp + PLAYER_HEAL_AMOUNT)
                            self.message = f'Player heal +{PLAYER_HEAL_AMOUNT}.'
                            self.end_turn()
                        else:
                            self.message = 'Mana tidak cukup.'
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.confirm_action()
                    # cursor movement
                    dx = dy = 0
                    if event.key in (pygame.K_RIGHT, pygame.K_d): dx = 1
                    if event.key in (pygame.K_LEFT, pygame.K_a) and not pygame.key.get_mods() & pygame.KMOD_CTRL: dx = -1
                    if event.key in (pygame.K_UP, pygame.K_w): dy = -1
                    if event.key in (pygame.K_DOWN, pygame.K_s): dy = 1
                    if dx or dy:
                        nx = max(0, min(self.GRID_W-1, self.cursor[0]+dx))
                        ny = max(0, min(self.GRID_H-1, self.cursor[1]+dy))
                        self.cursor = [nx, ny]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx,my = event.pos
                    if event.button == 1:
                        if my < self.GRID_H * self.TILE:
                            gx = mx // self.TILE
                            gy = my // self.TILE
                            self.cursor = [gx, gy]
                            if self.turn == 'PLAYER' and self.mode in ('MOVE','ATTACK','RANGED'):
                                self.confirm_action()
                    elif event.button == 3:
                        if self.turn == 'PLAYER' and my < self.GRID_H * self.TILE:
                            gx = mx // self.TILE
                            gy = my // self.TILE
                            self.cursor = [gx, gy]
                            # right-click immediate action
                            if (abs(self.player.x - gx) + abs(self.player.y - gy)) == 1:
                                target = self.unit_at((gx,gy))
                                if target and target.team == 'ENEMY':
                                    target.take_damage(self.player.atk)
                                    if not target.alive:
                                        self.message = 'Serang berhasil! Musuh dikalahkan.'
                                    else:
                                        self.message = f'Serang! Musuh HP: {max(0,target.hp)}.'
                                    self.end_turn()
                                else:
                                    self.message = 'Tidak ada musuh di petak bersebelahan.'
                            elif abs(self.player.x - gx) + abs(self.player.y - gy) <= MOVE_RANGE and self.unit_at((gx, gy)) is None:
                                self.player.x, self.player.y = gx, gy
                                self.message = f'Player moved to {gx},{gy}.'
                                self.end_turn()
                            else:
                                self.message = 'Aksi tidak valid.'

            def confirm_action(self):
                cx,cy = self.cursor
                if self.turn != 'PLAYER': return
                if self.mode == 'MOVE':
                    if (cx,cy) in self.move_targets and self.unit_at((cx,cy)) is None:
                        self.player.x, self.player.y = cx, cy
                        self.mode = 'IDLE'
                        self.move_targets = set()
                        self.message = f'Player moved to {cx},{cy}.'
                        self.end_turn()
                    else:
                        self.message = 'Lokasi tidak valid untuk MOVE.'
                elif self.mode == 'ATTACK':
                    target = self.unit_at((cx,cy))
                    if target and target.team == 'ENEMY' and (abs(self.player.x - target.x) + abs(self.player.y - target.y)) == 1:
                        target.take_damage(self.player.atk)
                        if not target.alive:
                            self.message = 'Serang! Musuh kalah!'
                        else:
                            self.message = f'Serang! Musuh HP tersisa {max(0,target.hp)}.'
                        self.mode = 'IDLE'
                        self.end_turn()
                    else:
                        self.message = 'Target tidak valid untuk ATTACK.'
                elif self.mode == 'RANGED':
                    if getattr(self.player,'mana',0) < getattr(self.player,'max_mana',0):
                        self.message = 'Mana tidak cukup untuk RANGED.'
                        return
                    px,py = self.player.pos()
                    dx = cx - px
                    dy = cy - py
                    if abs(dx) > abs(dy): step = (1 if dx>0 else -1, 0)
                    else: step = (0, 1 if dy>0 else -1)
                    self.player.mana -= getattr(self.player, 'max_mana', 0)
                    dmg = self.player.atk
                    hits = []
                    nx, ny = px + step[0], py + step[1]
                    for i in range(2):
                        if not (0 <= nx < self.GRID_W and 0 <= ny < self.GRID_H): break
                        u = self.unit_at((nx,ny))
                        if u and u.team == 'ENEMY':
                            u.take_damage(dmg)
                            hits.append((nx,ny))
                        nx += step[0]; ny += step[1]
                    if hits:
                        self.message = f'Ranged hit at {hits}.'
                    else:
                        self.message = 'Ranged tidak mengenai musuh.'
                    self.mode = 'IDLE'
                    self.end_turn()
                else:
                    self.message = 'Tidak ada aksi dipilih.'

            def end_turn(self):
                if self.turn == 'PLAYER':
                    self.turn = 'ENEMY'
                    self.mode = 'IDLE'
                    self.move_targets = set()
                    self.message = 'Giliran ENEMY.'
                    self.enemy_action()
                    # check results
                    if not getattr(self.player, 'alive', True) or not getattr(self.enemy, 'alive', True):
                        # stage progression
                        if not getattr(self.enemy, 'alive', True):
                            if self.stage_index < len(self.stages) - 1:
                                self.stage_index += 1
                                # restore player HP
                                self.player.hp = self.player.max_hp
                                self.spawn_enemy(self.stage_index)
                            else:
                                self.victory = True
                                self.message = 'SEMUA MUSUH DIKALAHKAN!'
                                if self.next_scene:
                                    self.manager.go_to(self.next_scene)
                        else:
                            # player died
                            self.manager.go_to('end_menu')
                    else:
                        # regen mana
                        if hasattr(self.player, 'mana_regen'):
                            self.player.mana = min(getattr(self.player,'max_mana',0), getattr(self.player,'mana',0) + getattr(self.player,'mana_regen',0))
                        if hasattr(self.enemy, 'mana_regen') and getattr(self.enemy,'mana_regen',0) > 0:
                            self.enemy.mana = min(getattr(self.enemy,'max_mana',0), getattr(self.enemy,'mana',0) + getattr(self.enemy,'mana_regen',0))
                        self.turn = 'PLAYER'
                        self.message = 'Giliran PLAYER.'

            def enemy_action(self):
                # Enemy AI action using fuzzy logic
                if not self.enemy or not getattr(self.enemy, 'alive', True) or not getattr(self.player, 'alive', True):
                    return
                
                # Use fuzzy logic from ai module (already imported at top)
                occupied = {u.pos() for u in self.units if u.alive}
                occupied.discard(self.enemy.pos())
                etype = getattr(self, 'enemy_type', 'Zombie')

                heal_act, do_heal = fuzzy.heal_priority_check(etype, self.enemy.hp, getattr(self.enemy, 'mana', 0))
                if do_heal:
                    tgt = fuzzy.pick_adjacent_for_farther(self.enemy.pos(), self.player.pos(), occupied, self.GRID_W, self.GRID_H)
                    if tgt and self.unit_at(tgt) is None:
                        self.enemy.x, self.enemy.y = tgt
                    heal_amt = getattr(self.enemy, 'heal_amount', max(1, int(self.enemy.max_hp * 0.25)))
                    mana_cost = getattr(self.enemy, 'heal_cost', 20)
                    self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + heal_amt)
                    if hasattr(self.enemy, 'mana'):
                        self.enemy.mana = max(0, getattr(self.enemy, 'mana', 0) - mana_cost)
                    self.message = f'{etype} melakukan HEAL (+{heal_amt}).'
                    return

                if abs(self.enemy.x - self.player.x) + abs(self.enemy.y - self.player.y) == 1:
                    self.player.take_damage(self.enemy.atk)
                    self.message = f'{etype} menyerang! Player HP: {max(0, self.player.hp)}.'
                    return

                scores = fuzzy.get_all_scores(etype, self.player.hp, self.enemy.hp, 0, getattr(self.enemy, 'mana', 0), 5)
                infer_choice = self.forced_inference or 'mamdani'
                infer_choice = infer_choice if infer_choice in scores else 'mamdani'
                score = scores[infer_choice]
                behavior = fuzzy.map_fuzzy_score_to_behavior(score, etype)

                if behavior == 'RANGED_ATTACK':
                    rng = getattr(self.enemy, 'range', 2)
                    dist = abs(self.enemy.x - self.player.x) + abs(self.enemy.y - self.player.y)
                    if dist <= rng:
                        if etype == 'Skeleton':
                            if dist == 1: dmg = 1
                            elif dist == 2: dmg = 3
                            else: dmg = 5
                        elif etype == 'Boss': dmg = getattr(self.enemy, 'ranged_atk', 2)
                        else: dmg = getattr(self.enemy, 'atk', 1)
                        self.player.take_damage(dmg)
                        self.message = f'{etype} melakukan serangan jarak jauh!'
                    else:
                        tgt = getattr(fuzzy, 'pick_adjacent_for_closer')(self.enemy.pos(), self.player.pos(), occupied, self.GRID_W, self.GRID_H)
                        if tgt:
                            self.enemy.x, self.enemy.y = tgt
                            self.message = f'{etype} bergerak mendekat.'
                    return

                if behavior in ('MOVE_CLOSE','MOVE_TOWARDS','APPROACH','ATTACK_MELEE','MELEE'):
                    tgt = getattr(fuzzy, 'pick_adjacent_for_closer')(self.enemy.pos(), self.player.pos(), occupied, self.GRID_W, self.GRID_H)
                    if tgt:
                        self.enemy.x, self.enemy.y = tgt
                        self.message = f'{etype} bergerak mendekat.'
                    return
                if behavior in ('MOVE_RETREAT','MOVE_AWAY','RETREAT'):
                    tgt = getattr(fuzzy, 'pick_adjacent_for_farther')(self.enemy.pos(), self.player.pos(), occupied, self.GRID_W, self.GRID_H)
                    if tgt:
                        self.enemy.x, self.enemy.y = tgt
                        self.message = f'{etype} mundur.'
                    return

                tgt = getattr(fuzzy, 'pick_adjacent_for_closer')(self.enemy.pos(), self.player.pos(), occupied, self.GRID_W, self.GRID_H)
                if tgt:
                    self.enemy.x, self.enemy.y = tgt
                    self.message = f'{etype} bergerak (fallback).'

            def update(self, dt):
                # animations update similar to Code/main
                if self.player_idle_anim:
                    self.player_idle_anim.update()
                if self.zombie_frames and self.enemy_type == 'Zombie' and getattr(self.enemy, 'alive', True):
                    self.zombie_anim_timer += 1
                    if self.zombie_anim_timer >= self.zombie_anim_speed:
                        self.zombie_anim_timer = 0
                        self.zombie_anim_index = (self.zombie_anim_index + 1) % len(self.zombie_frames)
                if self.skeleton_frames and self.enemy_type == 'Skeleton' and getattr(self.enemy, 'alive', True):
                    self.skeleton_anim_timer += 1
                    if self.skeleton_anim_timer >= self.skeleton_anim_speed:
                        self.skeleton_anim_timer = 0
                        self.skeleton_anim_index = (self.skeleton_anim_index + 1) % len(self.skeleton_frames)

            def draw(self, surface):
                surface.fill((40,40,40))
                # draw grid
                for x in range(self.GRID_W):
                    for y in range(self.GRID_H):
                        rect = pygame.Rect(x*self.TILE, y*self.TILE, self.TILE, self.TILE)
                        pygame.draw.rect(surface, (200,200,200), rect, 1)

                # draw units
                for u in self.units:
                    if not getattr(u, 'alive', True):
                        continue
                    cx = u.x * self.TILE + self.TILE//2
                    cy = u.y * self.TILE + self.TILE//2
                    if getattr(u, 'team', None) == 'PLAYER' and self.player_idle_anim:
                        img = self.player_idle_anim.get_frame()
                        rect = img.get_rect(center=(cx, cy))
                        surface.blit(img, rect)
                    else:
                        etype = self.enemy_type
                        if etype == 'Zombie' and self.zombie_frames:
                            frame = self.zombie_frames[self.zombie_anim_index % len(self.zombie_frames)]
                            rect = frame.get_rect(center=(cx, cy - ZOMBIE_Y_OFFSET))
                            surface.blit(frame, rect)
                        elif etype == 'Skeleton' and self.skeleton_frames:
                            frame = self.skeleton_frames[self.skeleton_anim_index % len(self.skeleton_frames)]
                            rect = frame.get_rect(center=(cx, cy - SKELETON_Y_OFFSET))
                            surface.blit(frame, rect)
                        elif etype == 'Enderman' and self.enderman_frames:
                            frame = self.enderman_frames[self.enderman_anim_index % len(self.enderman_frames)]
                            rect = frame.get_rect(center=(cx + ENDERMAN_X_OFFSET, cy - ENDERMAN_Y_OFFSET))
                            surface.blit(frame, rect)
                        elif etype == 'Boss' and self.boss_frames:
                            frame = self.boss_frames[self.boss_anim_index % len(self.boss_frames)]
                            rect = frame.get_rect(center=(cx, cy - BOSS_Y_OFFSET))
                            surface.blit(frame, rect)
                        else:
                            pygame.draw.rect(surface, (180,50,50), (u.x*self.TILE+12, u.y*self.TILE+12, self.TILE-24, self.TILE-24))
                    # HP bar
                    hp_ratio = max(0, u.hp) / u.max_hp
                    bar_w = int(self.TILE * 0.8)
                    bx = u.x*self.TILE + (self.TILE-bar_w)//2
                    by = u.y*self.TILE + self.TILE - 12
                    pygame.draw.rect(surface, (30,30,30), (bx,by,bar_w,6))
                    pygame.draw.rect(surface, (50,180,50), (bx,by,int(bar_w*hp_ratio),6))

                # cursor
                cx,cy = self.cursor
                rect = pygame.Rect(cx*self.TILE, cy*self.TILE, self.TILE, self.TILE)
                pygame.draw.rect(surface, (230,200,60), rect, 3)
                if self.mode == 'MOVE':
                    for (mx,my) in self.move_targets:
                        r = pygame.Rect(mx*self.TILE+6, my*self.TILE+6, self.TILE-12, self.TILE-12)
                        pygame.draw.rect(surface, (180,240,180), r, 2)
                if self.mode == 'ATTACK':
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx,ny = self.player.x+dx, self.player.y+dy
                        if 0 <= nx < self.GRID_W and 0 <= ny < self.GRID_H and self.unit_at((nx,ny)) and self.unit_at((nx,ny)).team == 'ENEMY':
                            r = pygame.Rect(nx*self.TILE+6, ny*self.TILE+6, self.TILE-12, self.TILE-12)
                            pygame.draw.rect(surface, (255,180,180), r, 2)

                # UI panel
                panel = pygame.Rect(0, self.GRID_H*self.TILE, self.screen_width, 120)
                pygame.draw.rect(surface, (40,40,40), panel)
                font = pygame.font.SysFont(None, 22)
                bigfont = pygame.font.SysFont(None, 28)
                info = f'Turn: {self.turn} | Mode: {self.mode} | Cursor: {self.cursor[0]},{self.cursor[1]}'
                txt = font.render(info, True, (255,255,255))
                surface.blit(txt, (8, self.GRID_H*self.TILE+6))
                msg = bigfont.render(self.message, True, (230,200,60))
                surface.blit(msg, (8, self.GRID_H*self.TILE+30))
                self.manager.go_to(self.next_scene)

    def draw(self, surface):
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
        p = os.path.join(os.path.dirname(__file__), '..', 'Code', 'assets', name, 'Idle.png')
        if not os.path.isfile(p):
            p = os.path.join(os.path.dirname(__file__), '..', '..', 'Code', 'assets', name, 'Idle.png')
        try:
            sheet = pygame.image.load(p).convert_alpha()
            n = self.FRAME_COUNTS.get(enemy_type, 6)
            fw = sheet.get_width() // max(1, n)
            fh = sheet.get_height()
            sub = sheet.subsurface((0,0,fw,fh))
            self.enemy_surf = scale_preserve(sub, (self.tile, self.tile))
        except Exception:
            self.enemy_surf = pygame.Surface((self.tile, self.tile))
            self.enemy_surf.fill((120,0,120))

    def handle_event(self, event):
        # allow clicking to damage enemy
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx,my = event.pos
            # damage if click on enemy
            ex = self.grid_origin_x + self.enemy_x * self.tile
            ey = self.grid_origin_y + self.enemy_y * self.tile
            rect = pygame.Rect(ex, ey, self.tile, self.tile)
            if rect.collidepoint((mx,my)):
                self.enemy_hp -= 5
                if self.enemy_hp <= 0:
                    if self.next_scene:
                        self.manager.go_to(self.next_scene)

    def update(self, dt):
        # auto-move enemy randomly every interval
        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.move_timer = 0.0
            import random
            choices = []
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx,ny = self.enemy_x+dx, self.enemy_y+dy
                if 0 <= nx < self.grid_w and 0 <= ny < self.grid_h:
                    choices.append((nx,ny))
            if choices:
                self.enemy_x, self.enemy_y = random.choice(choices)

    def draw(self, surface):
        surface.fill((20,20,20))
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


class TurnBasedGrid(ScreenBase):
    """Turn-based grid with player and enemy units. Enemies use Code.fuzzy for AI.
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
        # align grid to top-left like Code.main
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

        # load animated player frames (prefer Testing/Assets then Code/assets)
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.player_frames = []
        
        # Try Testing/Assets first, then Code/assets
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
            
            # Try Testing/Assets first, then Code/assets
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
                        
                        # Try Testing/Assets first, then Code/assets
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


