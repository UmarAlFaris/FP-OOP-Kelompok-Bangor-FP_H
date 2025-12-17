"""Player class for the player-controlled character."""
from .base import Entity
from src.config import (
    PLAYER_MAX_HP,
    PLAYER_ATK,
    PLAYER_MANA,
    PLAYER_MANA_REGEN
)


class Player(Entity):
    """Player character with mana and healing abilities."""
    
    @staticmethod
    def get_default_stats():
        """Return default player stats from config constants."""
        return {
            'level': 1,
            'hp': PLAYER_MAX_HP,
            'max_hp': PLAYER_MAX_HP,
            'atk': PLAYER_ATK,
            'mana': PLAYER_MANA,
            'max_mana': PLAYER_MANA
        }
    
    def __init__(self, x, y, stats: dict = None):
        # Use persistent stats from manager if provided, otherwise use defaults
        if stats is None:
            stats = Player.get_default_stats()
        
        level = stats.get('level', 1)
        hp = stats.get('hp', PLAYER_MAX_HP)
        max_hp = stats.get('max_hp', PLAYER_MAX_HP)
        atk = stats.get('atk', PLAYER_ATK)
        mana = stats.get('mana', PLAYER_MANA)
        max_mana = stats.get('max_mana', PLAYER_MANA)
        
        super().__init__(x, y, hp=hp, atk=atk, team='PLAYER')
        self.max_hp = max_hp  # Override max_hp from stats
        self.level = level
        self.mana = mana
        self.max_mana = max_mana
        self.mana_regen = PLAYER_MANA_REGEN

    def heal(self, amount, cost):
        """Heal the player if there's enough mana."""
        if self.mana >= cost:
            self.hp = min(self.max_hp, self.hp + amount)
            self.mana -= cost
            return True
        return False
