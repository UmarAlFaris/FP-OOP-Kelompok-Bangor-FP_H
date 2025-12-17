"""Enemy classes for different monster types."""
from .base import Entity
from src.config import (
    ZOMBIE_HP,
    ZOMBIE_ATK,
    ZOMBIE_MANA,
    SKELETON_HP,
    SKELETON_ATK,
    SKELETON_MANA,
    ENDERMAN_HP,
    ENDERMAN_ATK,
    ENDERMAN_MANA
)


class Monster(Entity):
    """Base class for all enemy monsters."""
    
    def __init__(self, x, y, hp, atk, mana=0):
        super().__init__(x, y, hp, atk, team='ENEMY')
        self.mana = mana
        self.max_mana = mana


class Zombie(Monster):
    """Zombie enemy - high HP, moderate attack."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=ZOMBIE_HP, atk=ZOMBIE_ATK, mana=ZOMBIE_MANA)


class Skeleton(Monster):
    """Skeleton enemy - low HP, low attack."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=SKELETON_HP, atk=SKELETON_ATK, mana=SKELETON_MANA)


class Enderman(Monster):
    """Enderman enemy - high HP, high attack, has mana."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=ENDERMAN_HP, atk=ENDERMAN_ATK, mana=ENDERMAN_MANA)
