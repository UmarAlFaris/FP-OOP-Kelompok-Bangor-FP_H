"""Base Entity class for all game units."""


class Entity:
    """Base class for all game entities with health, attack, and position."""
    
    def __init__(self, x, y, hp, atk, team):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.team = team
        self.alive = True

    def pos(self):
        """Return the current position as a tuple."""
        return (self.x, self.y)

    def take_damage(self, amount):
        """Apply damage to the entity and mark as dead if HP reaches 0."""
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False
