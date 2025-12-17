"""Boss class for the final boss enemy."""
from .base import Entity
from src.config import BOSS_HP, BOSS_ATK, BOSS_MANA


class Boss(Entity):
    """Boss enemy with high HP, attack, and mana."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=BOSS_HP, atk=BOSS_ATK, team='ENEMY')
        self.mana = BOSS_MANA
        self.max_mana = BOSS_MANA
