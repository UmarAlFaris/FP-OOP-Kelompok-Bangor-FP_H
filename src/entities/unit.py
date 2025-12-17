"""Unit class for game entities."""


class Unit:
    """Represents a game unit (player or enemy) with health, attack, and mana."""
    
    def __init__(self, x, y, hp, atk, team, mana=0, mana_regen=0):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.team = team
        self.alive = True
        self.mana = mana
        self.max_mana = mana
        self.mana_regen = mana_regen

    def pos(self):
        """Return the current position as a tuple."""
        return (self.x, self.y)

    def take_damage(self, amount):
        """Apply damage to the unit and mark as dead if HP reaches 0."""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
