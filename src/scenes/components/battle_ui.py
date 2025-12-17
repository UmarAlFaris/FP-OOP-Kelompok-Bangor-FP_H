"""UI management component for battle scene."""
import pygame
from ui.button import Button


class BattleUIManager:
    """Manages the battle scene UI including buttons and tooltips."""
    
    def __init__(self, grid_h: int, tile_size: int, callbacks: dict):
        """Initialize the UI manager.
        
        Args:
            grid_h: Grid height in tiles.
            tile_size: The tile size in pixels.
            callbacks: Dictionary of callback functions:
                - move: Callback for move button
                - attack: Callback for attack button
                - heal: Callback for heal button
                - end: Callback for end turn button
        """
        self.grid_h = grid_h
        self.tile = tile_size
        
        self.font = pygame.font.SysFont(None, 24)
        self.font_small = pygame.font.SysFont(None, 20)
        
        # Create action buttons with tooltips
        button_y = self.grid_h * self.tile + 80
        button_spacing = 150
        button_start_x = 500
        
        self.buttons = [
            Button("Move (M)", (button_start_x, button_y), (130, 40), callbacks['move'], self.font),
            Button("Attack (A)", (button_start_x + button_spacing, button_y), (130, 40), callbacks['attack'], self.font),
            Button("Heal (H)", (button_start_x + button_spacing * 2, button_y), (130, 40), callbacks['heal'], self.font),
            Button("End Turn (E)", (button_start_x + button_spacing * 3, button_y), (130, 40), callbacks['end'], self.font),
        ]
        
        # Assign tooltips to each button
        self.buttons[0].tooltip = "Move your character to an adjacent tile."
        self.buttons[1].tooltip = "Attack an enemy in range."
        self.buttons[2].tooltip = "Heal yourself (costs 20 Mana)."
        self.buttons[3].tooltip = "End your turn."
    
    def handle_event(self, event) -> str:
        """Handle input events for UI elements.
        
        Args:
            event: Pygame event.
            
        Returns:
            String indicating which action was triggered, or None if no action.
        """
        for button in self.buttons:
            button.handle_event(event)
        
        # The buttons call their callbacks directly, so we don't need to return action here
        return None
    
    def draw(self, surface):
        """Draw all UI elements.
        
        Args:
            surface: The pygame surface to draw on.
        """
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)
        
        # Draw tooltips on hover
        self._draw_tooltips(surface)
    
    def _draw_tooltips(self, surface):
        """Draw tooltips for hovered buttons.
        
        Args:
            surface: The pygame surface to draw on.
        """
        mx, my = pygame.mouse.get_pos()
        for button in self.buttons:
            if button.rect.collidepoint((mx, my)):
                # Render tooltip above the button
                tooltip_text = getattr(button, 'tooltip', '')
                if tooltip_text:
                    tooltip_surf = self.font_small.render(tooltip_text, True, (255, 255, 200))
                    tooltip_rect = tooltip_surf.get_rect()
                    tooltip_rect.midbottom = (button.rect.centerx, button.rect.top - 5)
                    
                    # Draw tooltip background
                    bg_rect = tooltip_rect.inflate(10, 6)
                    pygame.draw.rect(surface, (50, 50, 50), bg_rect, border_radius=4)
                    pygame.draw.rect(surface, (200, 200, 150), bg_rect, 1, border_radius=4)
                    
                    # Draw tooltip text
                    surface.blit(tooltip_surf, tooltip_rect)
                break  # Only show one tooltip at a time
