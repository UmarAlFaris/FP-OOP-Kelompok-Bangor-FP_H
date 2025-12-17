from .fight_base import TurnBasedGrid


class SceneKroco(TurnBasedGrid):
    def __init__(self, manager, screen_size, next_scene='scene_4'):
        stages = ['Zombie', 'Zombie', 'Skeleton']
        super().__init__(manager, screen_size, stages=stages, next_scene=next_scene, forced_inference='tsukamoto')

