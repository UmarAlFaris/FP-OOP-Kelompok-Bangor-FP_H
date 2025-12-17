"""Boss class for the final boss enemy."""
from .base import Entity


class Boss(Entity):
    """Boss enemy with high HP, attack, and mana."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=120, atk=40, team='ENEMY')
        self.mana = 100
        self.max_mana = 100
