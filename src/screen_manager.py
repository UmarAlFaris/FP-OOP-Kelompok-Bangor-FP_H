import random
from scenes.main_menu import MainMenuScreen
from scenes.S1_Scene_Opening import Scene1
from scenes.S2_Scene_RuangRapat import Scene2
from scenes.S3_Game_Kroco_Fight import SceneKroco
from scenes.S4_Scene_StorageRoom_1 import Scene4
from scenes.S5_Scene_StorageRoom_2 import Scene5
from scenes.S6_Game_MiniBoss_Fight import Scene6
from scenes.S7_Scene_Adzan_Subuh import Scene7
from scenes.S8_Game_Boss_Fight import SceneBoss
from scenes.S_end_menu import EndMenuScreen
from scenes.high_score import HighScoreScreen
from scenes.crossroads import CrossroadsScreen

class ScreenManager:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.screens = {}
        self.current_screen = None
        self.total_run_turns = 0  # Global turn counter for entire run
        # RPG persistent player stats
        self.player_stats = {'level': 1, 'hp': 20, 'max_hp': 20, 'atk': 5, 'mana': 100, 'max_mana': 100}
        self.miniboss_defeated = False
        self._register_screens()

    def _register_screens(self):
        self.screens["main_menu"] = MainMenuScreen(self, self.screen_size)
        self.screens["scene_1"] = Scene1(self, self.screen_size)
        self.screens["scene_2"] = Scene2(self, self.screen_size)
        self.screens["scene_3"] = SceneKroco(self, self.screen_size, next_scene='scene_4')
        self.screens["scene_4"] = Scene4(self, self.screen_size)
        self.screens["scene_5"] = Scene5(self, self.screen_size)
        self.screens["scene_6"] = Scene6(self, self.screen_size)
        self.screens["scene_7"] = Scene7(self, self.screen_size)
        self.screens["scene_8"] = SceneBoss(self, self.screen_size)
        self.screens["end_menu"] = EndMenuScreen(self, self.screen_size)
        self.screens["high_score"] = HighScoreScreen(self, self.screen_size)
        self.screens["crossroads"] = CrossroadsScreen(self, self.screen_size)

        self.go_to("main_menu")

    def reset_score(self):
        """Reset the global turn counter and player stats for a new game run."""
        self.total_run_turns = 0
        self.player_stats = {'level': 1, 'hp': 20, 'max_hp': 20, 'atk': 5, 'mana': 100, 'max_mana': 100}
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
        from scenes.fight_tactical import TurnBasedGrid
        enemy_types = ['Zombie', 'Skeleton', 'Zombie']
        random.shuffle(enemy_types)
        battle = TurnBasedGrid(self, self.screen_size, stages=enemy_types, reward_levels=1)
        self.screens['battle'] = battle
        self.go_to('battle')

    def start_miniboss(self):
        """Battle Factory: Start miniboss fight, reward +3 levels, unlocks boss."""
        from scenes.fight_tactical import TurnBasedGrid
        battle = TurnBasedGrid(self, self.screen_size, stages=['Enderman'], reward_levels=3, is_miniboss=True)
        self.screens['battle'] = battle
        self.go_to('battle')

    def go_to(self, name):
        if name == "exit_game":
            import pygame
            pygame.quit()
            raise SystemExit

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
