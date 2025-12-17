"""Tactical grid-based battle scene with turn-based combat."""
import pygame
import os
from scenes.base import ScreenBase
from config import (
    PLAYER_HEAL_COST,
    PLAYER_HEAL_AMOUNT,
    ENEMY_HEAL_COST,
    ENEMY_HEAL_AMOUNT,
    GRID_W,
    GRID_H,
    ENDERMAN_ESCAPE_TURN
)
from entities.player import Player
from entities.enemies import Zombie, Skeleton, Enderman
from entities.boss import Boss
from ai import fuzzy_logic as fuzzy
from utils import bfs_reachable
from scenes.components.battle_assets import BattleAssetLoader
from scenes.components.battle_renderer import BattleRenderer
from scenes.components.battle_ui import BattleUIManager


class TurnBasedGrid(ScreenBase):
    """Turn-based grid with player and enemy units. Enemies use fuzzy logic for AI.
    Supports either `enemies` (list of dicts for simultaneous multi-enemy)
    or `stages` (list of enemy type names for sequential single-enemy stages).
    """
    def __init__(self, manager, screen_size, enemies: list[dict] = None, stages: list[str] = None, next_scene=None, forced_inference=None, reward_levels=0, is_miniboss=False):
        super().__init__(manager, screen_size)
        
        # RPG parameters
        self.reward_levels = reward_levels
        self.is_miniboss = is_miniboss

        self.grid_w = GRID_W
        self.grid_h = GRID_H
        usable_h = self.screen_height - 120
        self.tile = min(self.screen_width // self.grid_w, usable_h // self.grid_h)
        # align grid to top-left
        self.origin_x = 0
        self.origin_y = 0

        # player - use persistent stats from manager
        self.player = Player(1, self.grid_h // 2, stats=self.manager.player_stats)
        
        # boss damage boost
        if stages and 'Boss' in stages:
            self.player.atk += 5  # boost +5 ATK for boss fight

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
            if etype == 'Zombie':
                self.enemies.append(Zombie(ex, ey))
            elif etype == 'Skeleton':
                self.enemies.append(Skeleton(ex, ey))
            elif etype == 'Enderman':
                self.enemies.append(Enderman(ex, ey))
            elif etype == 'Boss':
                self.enemies.append(Boss(ex, ey))
            else:
                self.enemies.append(Zombie(ex, ey))  # default fallback
        else:
            enemies = enemies or []
            for e in enemies:
                etype = e.get('type')
                ex = e.get('x', self.grid_w-2)
                ey = e.get('y', self.grid_h//2)
                if etype == 'Zombie':
                    self.enemies.append(Zombie(ex, ey))
                elif etype == 'Skeleton':
                    self.enemies.append(Skeleton(ex, ey))
                elif etype == 'Enderman':
                    self.enemies.append(Enderman(ex, ey))
                elif etype == 'Boss':
                    self.enemies.append(Boss(ex, ey))
                else:
                    self.enemies.append(Zombie(ex, ey))  # default fallback

        # Initialize asset loader component and load all assets
        self.asset_loader = BattleAssetLoader(self.tile)
        self.assets = self.asset_loader.load_assets(self.enemies, self.grid_w, self.grid_h)

        self.cursor = [0,0]
        self.turn = 'PLAYER'
        self.move_range = 2
        self.turn_count = 0  # track turn number for current battle
        
        # Play spawn sound for initial enemies
        self._play_spawn_sounds()
        
        # Boss fight flag
        self.is_boss_fight = stages and 'Boss' in stages

        # Use fuzzy logic module (already imported at module level)
        self.fuzzy = fuzzy

        self.font = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 20)
        # gameplay state
        self.mode = 'IDLE'
        self.move_targets = set()
        self.message = 'Giliran PLAYER. Tekan M:move A:attack H:heal E:end.'
        self.units = [self.player] + self.enemies
        
        # Initialize renderer component
        self.renderer = BattleRenderer(
            self.tile, self.grid_w, self.grid_h,
            self.origin_x, self.origin_y, self.screen_width
        )
        
        # Initialize UI manager component
        self.ui_manager = BattleUIManager(
            self.grid_h, self.tile,
            callbacks={
                'move': self.btn_move,
                'attack': self.btn_attack,
                'heal': self.btn_heal,
                'end': self.btn_end
            }
        )
    
    def _play_spawn_sounds(self):
        """Play spawn sounds for all current enemies."""
        for e in self.enemies:
            if not e.alive:
                continue
            etype = type(e).__name__.lower()
            sound_key = f"{etype}_spawn"
            if sound_key in self.assets['sounds'] and self.assets['sounds'][sound_key]:
                self.assets['sounds'][sound_key].play()
    
    def _play_sound(self, key):
        """Play a sound effect by key if it exists."""
        if key in self.assets['sounds'] and self.assets['sounds'][key]:
            self.assets['sounds'][key].play()

    def on_enter(self):
        """Reset local turn counter when battle starts (global counter keeps accumulating)."""
        self.turn_count = 0
        
        # Play boss music if this is a boss fight
        if self.is_boss_fight:
            try:
                pygame.mixer.music.load(self.assets['boss_music_path'])
                pygame.mixer.music.play(loops=-1)
            except Exception as e:
                print(f"Warning: Could not load boss music: {e}")
    
    def on_exit(self):
        """Called when leaving the battle - stop boss music if playing."""
        if self.is_boss_fight:
            pygame.mixer.music.stop()

    # STEP 2: Button callback methods
    def btn_move(self):
        if self.turn != 'PLAYER':
            return
        self.mode = 'MOVE'
        self.move_targets = bfs_reachable((self.player.x, self.player.y), self.move_range, {(e.x, e.y) for e in self.enemies if e.alive})
        self.message = 'Mode MOVE. Pilih petak tujuan lalu tekan Enter.'
    
    def btn_attack(self):
        if self.turn != 'PLAYER':
            return
        self.mode = 'ATTACK'
        self.message = 'Mode ATTACK. Pilih petak musuh bersebelahan lalu Enter.'
    
    def btn_heal(self):
        if self.turn != 'PLAYER':
            return
        if self.player.mana >= PLAYER_HEAL_COST:
            self.mode = 'HEAL'
            self.message = f'Mode HEAL. Tekan Enter untuk heal (+{PLAYER_HEAL_AMOUNT} HP, costs {PLAYER_HEAL_COST} Mana).'
        else:
            self.message = f'Not enough Mana for Heal! Need {PLAYER_HEAL_COST} Mana.'
    
    def btn_end(self):
        if self.turn != 'PLAYER':
            return
        self.end_turn()

    def handle_event(self, event):
        # Delegate to UI manager for button events
        self.ui_manager.handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            # cursor keys
            if event.key in (pygame.K_RIGHT, pygame.K_d): self.cursor[0] = min(self.grid_w-1, self.cursor[0]+1)
            if event.key in (pygame.K_LEFT, pygame.K_a): self.cursor[0] = max(0, self.cursor[0]-1)
            if event.key in (pygame.K_DOWN, pygame.K_s): self.cursor[1] = min(self.grid_h-1, self.cursor[1]+1)
            if event.key in (pygame.K_UP, pygame.K_w): self.cursor[1] = max(0, self.cursor[1]-1)
            # mode keys
            if event.key == pygame.K_m and self.turn == 'PLAYER':
                self.mode = 'MOVE'
                self.move_targets = bfs_reachable((self.player.x, self.player.y), self.move_range, {(e.x, e.y) for e in self.enemies if e.alive})
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
            if u.alive and (u.x, u.y) == pos:
                return u
        return None

    def confirm_action(self):
        cx, cy = self.cursor
        if self.turn != 'PLAYER':
            return
        if self.mode == 'MOVE':
            if (cx, cy) in self.move_targets and self.unit_at((cx, cy)) is None:
                self.player.x, self.player.y = cx, cy
                self.mode = 'IDLE'
                self.move_targets = set()
                self.message = f'Player moved to {cx},{cy}.'
                self.end_turn()
            else:
                self.message = 'Lokasi tidak valid untuk MOVE.'
        elif self.mode == 'ATTACK':
            target = self.unit_at((cx, cy))
            if target and target.team != 'PLAYER' and abs(self.player.x-cx)+abs(self.player.y-cy) == 1:
                self._play_sound('player_attack')
                target.take_damage(self.player.atk)
                if target.hp <= 0:
                    target.alive = False
                    # increment player damage on enemy defeat
                    self.player.atk += 1
                    self.message = f'Enemy {type(target).__name__} defeated. ATK +1 (now {self.player.atk}).'
                else:
                    self.message = f'Attack! Enemy HP: {max(0,target.hp)}.'
                self.mode = 'IDLE'
                self.end_turn()
            else:
                self.message = 'Target tidak valid untuk ATTACK.'
        elif self.mode == 'HEAL':
            # STEP 3.1: Player Heal with Mana cost check
            old_hp = self.player.hp
            if self.player.heal(PLAYER_HEAL_AMOUNT, PLAYER_HEAL_COST):
                self._play_sound('heal')
                healed = self.player.hp - old_hp
                self.message = f'Player healed +{healed} HP. HP: {self.player.hp}/{self.player.max_hp}. Mana: {self.player.mana}.'
                self.mode = 'IDLE'
                self.end_turn()
            else:
                self.message = f'Not enough Mana! Need {PLAYER_HEAL_COST}, have {self.player.mana}.'
                self.mode = 'IDLE'
        else:
            self.message = 'Tidak ada aksi dipilih. Tekan M/A/H atau E untuk end turn.'

    def end_turn(self):
        if self.turn != 'PLAYER':
            return
        self.turn = 'ENEMY'
        self.mode = 'IDLE'
        self.move_targets = set()
        self.message = 'Giliran ENEMY.'
        self.turn_count += 1  # increment local turn counter
        self.manager.total_run_turns += 1  # increment global turn counter
        
        # auto-win for Enderman at escape turn threshold
        if self.turn_count >= ENDERMAN_ESCAPE_TURN and self.stages and any(type(e).__name__ == 'Enderman' for e in self.enemies if e.alive):
            for e in self.enemies:
                if type(e).__name__ == 'Enderman':
                    e.alive = False
            self.message = f'Turn {ENDERMAN_ESCAPE_TURN} reached! Enderman auto-defeated!'
            if self.next_scene:
                self.manager.go_to(self.next_scene)
            else:
                self.manager.go_to('main_menu')
            return
        # enemy actions sequentially
        for e in self.enemies:
            if not e.alive:
                continue
            self.enemy_action(e)
            if self.player.hp <= 0:
                break
        # check results
        if self.player.hp <= 0:
            # Sync the death state (HP <= 0) to the manager so EndMenu knows we died
            self.manager.update_player_state(self.player.hp, self.player.mana)
            self.manager.go_to('end_menu')
            return
        if all(not e.alive for e in self.enemies):
            # if sequential stages were provided, advance to next stage
            if self.stages:
                if self.stage_index < len(self.stages) - 1:
                    self.stage_index += 1
                    # spawn next single enemy
                    etype = self.stages[self.stage_index]
                    ex = self.grid_w - 2
                    ey = self.grid_h // 2
                    if etype == 'Zombie':
                        self.enemies = [Zombie(ex, ey)]
                    elif etype == 'Skeleton':
                        self.enemies = [Skeleton(ex, ey)]
                    elif etype == 'Enderman':
                        self.enemies = [Enderman(ex, ey)]
                    elif etype == 'Boss':
                        self.enemies = [Boss(ex, ey)]
                    else:
                        self.enemies = [Zombie(ex, ey)]  # default fallback
                    # update self.units to include new enemy (fix for unit_at check)
                    self.units = [self.player] + self.enemies
                    # reload enemy_frames using asset_loader
                    enemy_frames, enemy_anim_indexes, enemy_anim_timers = self.asset_loader.reload_enemy_frames(self.enemies)
                    self.assets['enemy_frames'] = enemy_frames
                    self.assets['enemy_anim_indexes'] = enemy_anim_indexes
                    self.assets['enemy_anim_timers'] = enemy_anim_timers
                    # Player HP persists between stages (no auto-heal)
                    self.turn = 'PLAYER'
                    self.mode = 'IDLE'
                    self.message = f'Stage {self.stage_index+1}: {type(self.enemies[0]).__name__}. ATK={self.player.atk}. M:move A:attack H:heal'
                    # Play spawn sound for the new enemy
                    self._play_spawn_sounds()
                    return
                else:
                    # All stages complete - victory!
                    self.manager.total_run_turns -= 1  # Refund the killing blow turn
                    self.manager.update_player_state(self.player.hp, self.player.mana)
                    self.manager.level_up(self.reward_levels)
                    if self.is_miniboss:
                        self.manager.miniboss_defeated = True
                    # Use next_scene if provided (e.g., boss -> end_menu), else crossroads
                    if self.next_scene:
                        self.manager.go_to(self.next_scene)
                    else:
                        self.manager.go_to('crossroads')
                    return
            else:
                # All enemies dead (non-staged battle) - victory!
                self.manager.total_run_turns -= 1  # Refund the killing blow turn
                self.manager.update_player_state(self.player.hp, self.player.mana)
                self.manager.level_up(self.reward_levels)
                if self.is_miniboss:
                    self.manager.miniboss_defeated = True
                # Use next_scene if provided (e.g., boss -> end_menu), else crossroads
                if self.next_scene:
                    self.manager.go_to(self.next_scene)
                else:
                    self.manager.go_to('crossroads')
                return
        # back to player
        self.turn = 'PLAYER'
        self.message = 'Giliran PLAYER. Tekan M untuk move, A untuk attack, E untuk end turn.'

    def enemy_action(self, e):
        # simple enemy action using fuzzy.get_final_action when available
        occupied = {(ee.x, ee.y) for ee in self.enemies if ee.alive}
        occupied.add((self.player.x, self.player.y))
        hp_p = int(100 * self.player.hp / max(1, self.player.max_hp))
        hp_b = int(100 * e.hp / max(1, e.max_hp))
        mana_p = int(self.player.mana)
        mana_b = int(e.mana)
        cd_p = 0
        if self.fuzzy:
            try:
                action, target = self.fuzzy.get_final_action(type(e).__name__, hp_p, hp_b, mana_p, mana_b, cd_p, (e.x, e.y), (self.player.x, self.player.y), occupied, self.grid_w, self.grid_h)
            except Exception:
                action, target = ('MOVE_CLOSE', None)
        else:
            action, target = ('MOVE_CLOSE', None)
        
        # Get enemy type for sound keys
        etype = type(e).__name__.lower()
        
        if action in ('ATTACK', 'RANGED_ATTACK'):
            if abs(e.x - self.player.x) + abs(e.y - self.player.y) <= 2:
                self._play_sound(f"{etype}_attack")
                self.player.hp -= e.atk
        elif action in ('MOVE_CLOSE', 'MOVE_RETREAT', 'TELEPORT'):
            if target and target not in occupied:
                # Play teleport sound for Enderman on move/teleport actions
                if etype == 'enderman' and action in ('MOVE_CLOSE', 'MOVE_RETREAT', 'TELEPORT'):
                    self._play_sound('enderman_teleport')
                e.x, e.y = target
        elif action == 'HEAL':
            # STEP 3.2: Enemy Heal with Mana cost check
            if e.mana >= ENEMY_HEAL_COST:
                self._play_sound('heal')
                e.hp = min(e.max_hp, e.hp + ENEMY_HEAL_AMOUNT)
                e.mana -= ENEMY_HEAL_COST
                print(f"{type(e).__name__} healed +{ENEMY_HEAL_AMOUNT} HP. Mana: {e.mana}")

    def update(self, dt):
        # advance animations using assets dictionary
        self.assets['player_anim_timer'] += 1
        if self.assets['player_anim_timer'] >= self.assets['player_anim_speed']:
            self.assets['player_anim_timer'] = 0
            self.assets['player_anim_index'] = (self.assets['player_anim_index'] + 1) % len(self.assets['player_frames'])
        for i, frames in enumerate(self.assets['enemy_frames']):
            self.assets['enemy_anim_timers'][i] += 1
            if self.assets['enemy_anim_timers'][i] >= 8:
                self.assets['enemy_anim_timers'][i] = 0
                self.assets['enemy_anim_indexes'][i] = (self.assets['enemy_anim_indexes'][i] + 1) % max(1, len(frames))

        if self.turn == 'ENEMY':
            occupied = {(e.x, e.y) for e in self.enemies if e.alive}
            occupied.add((self.player.x, self.player.y))
            for e in self.enemies:
                if not e.alive: continue
                hp_p = int(100 * self.player.hp / max(1, self.player.max_hp))
                hp_b = int(100 * e.hp / max(1, e.max_hp))
                mana_p = int(self.player.mana)
                mana_b = int(e.mana)
                cd_p = 0
                if self.fuzzy:
                    try:
                        action, target = self.fuzzy.get_final_action(type(e).__name__, hp_p, hp_b, mana_p, mana_b, cd_p, (e.x, e.y), (self.player.x, self.player.y), occupied, self.grid_w, self.grid_h)
                    except Exception:
                        action, target = ('MOVE_CLOSE', None)
                else:
                    action, target = ('MOVE_CLOSE', None)
                if action in ('ATTACK','RANGED_ATTACK'):
                    if abs(e.x-self.player.x)+abs(e.y-self.player.y) <= 2:
                        self.player.hp -= e.atk
                elif action in ('MOVE_CLOSE','MOVE_RETREAT','TELEPORT'):
                    if target and target not in occupied:
                        e.x, e.y = target
                elif action == 'HEAL':
                    # STEP 3.2: Enemy Heal with Mana cost check (update method)
                    if e.mana >= ENEMY_HEAL_COST:
                        e.hp = min(e.max_hp, e.hp + ENEMY_HEAL_AMOUNT)
                        e.mana -= ENEMY_HEAL_COST

            if self.player.hp <= 0:
                # Sync the death state (HP <= 0) to the manager so EndMenu knows we died
                self.manager.update_player_state(self.player.hp, self.player.mana)
                self.manager.go_to('end_menu')
                return
            if all(not e.alive for e in self.enemies):
                if self.next_scene:
                    self.manager.go_to(self.next_scene)
                else:
                    self.manager.go_to('main_menu')
                return
            self.turn = 'PLAYER'
            self.mode = 'IDLE'

    def draw(self, surface):
        # Build game state dictionary for renderer
        game_state = {
            'player': self.player,
            'enemies': self.enemies,
            'cursor': self.cursor,
            'mode': self.mode,
            'move_targets': self.move_targets,
            'message': self.message,
            'turn': self.turn,
            'total_run_turns': self.manager.total_run_turns
        }
        
        # Delegate rendering to the renderer component
        self.renderer.draw(surface, self.assets, game_state)
        
        # Delegate UI drawing to the UI manager component
        self.ui_manager.draw(surface)
