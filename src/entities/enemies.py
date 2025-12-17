"""Enemy classes for different monster types."""
from .base import Entity


class Monster(Entity):
    """Base class for all enemy monsters."""
    
    def __init__(self, x, y, hp, atk, mana=0):
        super().__init__(x, y, hp, atk, team='ENEMY')
        self.mana = mana
        self.max_mana = mana


class Zombie(Monster):
    """Zombie enemy - high HP, moderate attack."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=20, atk=5, mana=20)


class Skeleton(Monster):
    """Skeleton enemy - low HP, low attack."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=15, atk=3, mana=20)


class Enderman(Monster):
    """Enderman enemy - high HP, high attack, has mana."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=64, atk=25, mana=100)
