
from scenes.fight_tactical import TurnBasedGrid


class SceneBoss(TurnBasedGrid):
	def __init__(self, manager, screen_size):
		# Boss turn-based grid, proceed to end_menu afterwards
		super().__init__(manager, screen_size, stages=['Boss'], next_scene='end_menu')

