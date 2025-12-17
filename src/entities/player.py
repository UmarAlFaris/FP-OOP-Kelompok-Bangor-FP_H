"""Player class for the player-controlled character."""
from .base import Entity


class Player(Entity):
    """Player character with mana and healing abilities."""
    
    def __init__(self, x, y):
        super().__init__(x, y, hp=40, atk=8, team='PLAYER')
        self.mana = 100
        self.max_mana = 100
        self.mana_regen = 5

    def heal(self, amount, cost):
        """Heal the player if there's enough mana."""
        if self.mana >= cost:
            self.hp = min(self.max_hp, self.hp + amount)
            self.mana -= cost
            return True
        return False
