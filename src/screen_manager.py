import random
from scenes.main_menu import MainMenuScreen
from scenes.end_menu import EndMenuScreen
from scenes.high_score import HighScoreScreen
from scenes.campfire import CampfireScreen
from entities.player import Player

class ScreenManager:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.screens = {}
        self.current_screen = None
        self.total_run_turns = 0  # Global turn counter for entire run
        # RPG persistent player stats - uses centralized defaults from Player
        self.player_stats = Player.get_default_stats()
        self.miniboss_defeated = False
        self._register_screens()

    def _register_screens(self):
        self.screens["main_menu"] = MainMenuScreen(self, self.screen_size)
        self.screens["campfire"] = CampfireScreen(self, self.screen_size)
        self.screens["high_score"] = HighScoreScreen(self, self.screen_size)
        self.screens["end_menu"] = EndMenuScreen(self, self.screen_size)

        self.go_to("main_menu")

    def reset_score(self):
        """Reset the global turn counter and player stats for a new game run."""
        self.total_run_turns = 0
        self.player_stats = Player.get_default_stats()
        self.miniboss_defeated = False

    def level_up(self, amount):
        """Level up the player, increasing stats and full heal."""
        self.player_stats['level'] += amount
        self.player_stats['atk'] += 5 * amount
        self.player_stats['max_hp'] += 10 * amount
        # Full heal on level up
        self.player_stats['hp'] = self.player_stats['max_hp']
        self.player_stats['mana'] = self.player_stats['max_mana']
        print(f"Leveled Up to {self.player_stats['level']}!")

    def update_player_state(self, hp, mana):
        """Update player stats with current battle values (damage persists)."""
        self.player_stats['hp'] = hp
        self.player_stats['mana'] = mana

    def start_hunt(self):
        """Battle Factory: Start a random hunt with 3 stages, reward +1 level."""
        from scenes.battle_scene import TurnBasedGrid
        enemy_types = ['Zombie', 'Skeleton', 'Zombie']
        random.shuffle(enemy_types)
        battle = TurnBasedGrid(self, self.screen_size, stages=enemy_types, reward_levels=1)
        self.screens['battle'] = battle
        self.go_to('battle')

    def start_miniboss(self):
        """Battle Factory: Start miniboss fight, reward +3 levels, unlocks boss."""
        from scenes.battle_scene import TurnBasedGrid
        battle = TurnBasedGrid(self, self.screen_size, stages=['Enderman'], reward_levels=3, is_miniboss=True)
        self.screens['battle'] = battle
        self.go_to('battle')

    def start_boss(self):
        """Battle Factory: Start boss fight, next scene is end_menu."""
        from scenes.battle_scene import TurnBasedGrid
        battle = TurnBasedGrid(self, self.screen_size, stages=['Boss'], is_miniboss=False, next_scene='end_menu')
        self.screens['battle'] = battle
        self.go_to('battle')

    def go_to(self, name):
        if name == "exit_game":
            import pygame
            pygame.quit()
            raise SystemExit
        
        # Call on_exit on the current screen before switching
        if self.current_screen and hasattr(self.current_screen, 'on_exit'):
            self.current_screen.on_exit()

        self.current_screen = self.screens[name]
        
        # Call on_enter if the screen has this method
        if hasattr(self.current_screen, 'on_enter'):
            self.current_screen.on_enter()

    def handle_event(self, event):
        self.current_screen.handle_event(event)

    def update(self, dt):
        self.current_screen.update(dt)

    def draw(self, surface):
        self.current_screen.draw(surface)
