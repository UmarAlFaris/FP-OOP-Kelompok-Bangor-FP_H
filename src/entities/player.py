"""Player class for the player-controlled character."""
from .base import Entity


class Player(Entity):
    """Player character with mana and healing abilities."""
    
    def __init__(self, x, y, stats: dict = None):
        # Use persistent stats from manager if provided, otherwise use defaults
        if stats is not None:
            level = stats.get('level', 1)
            hp = stats.get('hp', 20)
            max_hp = stats.get('max_hp', 20)
            atk = stats.get('atk', 5)
            mana = stats.get('mana', 100)
            max_mana = stats.get('max_mana', 100)
        else:
            # Default fallback values
            level = 1
            hp = 20
            max_hp = 20
            atk = 5
            mana = 100
            max_mana = 100
        
        super().__init__(x, y, hp=hp, atk=atk, team='PLAYER')
        self.max_hp = max_hp  # Override max_hp from stats
        self.level = level
        self.mana = mana
        self.max_mana = max_mana
        self.mana_regen = 5

    def heal(self, amount, cost):
        """Heal the player if there's enough mana."""
        if self.mana >= cost:
            self.hp = min(self.max_hp, self.hp + amount)
            self.mana -= cost
            return True
        return False
