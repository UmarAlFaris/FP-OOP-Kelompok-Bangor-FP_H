
from .fight_base import TurnBasedGrid


class Scene6(TurnBasedGrid):
	def __init__(self, manager, screen_size):
		# Enderman turn-based grid, continue to scene_7 afterwards
		super().__init__(manager, screen_size, stages=['Enderman'], next_scene='scene_7')

