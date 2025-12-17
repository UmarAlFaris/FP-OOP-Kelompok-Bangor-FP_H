"""Crossroads Hub Screen - Central menu for the RPG overhaul."""
import pygame
import os
from scenes.base import ScreenBase
from ui.button import Button


class CrossroadsScreen(ScreenBase):
    """Hub screen where the player can choose their next action."""
    
    def __init__(self, manager, screen_size):
        super().__init__(manager, screen_size)
        
        # Load background
        base_path = os.path.dirname(__file__)
        img_path = os.path.join(base_path, "..", "..", "assets", "battlefield", "basecamp.png")
        try:
            self.bg = pygame.image.load(img_path).convert()
            self.bg = pygame.transform.scale(self.bg, screen_size)
        except Exception:
            self.bg = None
        
        # Fonts
        self.font_title = pygame.font.SysFont(None, 56)
        self.font_stats = pygame.font.SysFont(None, 32)
        self.font_button = pygame.font.SysFont(None, 28)
        self.font_tooltip = pygame.font.SysFont(None, 22)
        
        # Button layout
        cx = screen_size[0] // 2
        cy = screen_size[1] // 2 + 50
        
        self.buttons = [
            Button("Hunt Monsters", (cx, cy), (220, 45), self.start_hunt, self.font_button),
            Button("Challenge Miniboss", (cx, cy + 60), (220, 45), self.start_miniboss, self.font_button),
            Button("Enter Boss Lair", (cx, cy + 120), (220, 45), self.start_boss, self.font_button,
                   bg_color=(100, 50, 50)),
            Button("Retire / Main Menu", (cx, cy + 180), (220, 45), self.go_main_menu, self.font_button,
                   bg_color=(80, 80, 80)),
        ]
        
        # Assign tooltips
        self.buttons[0].tooltip = "3 Stages. Reward: +1 Lv"
        self.buttons[1].tooltip = "Hard! Reward: +3 Lv, Unlocks Boss"
        self.buttons[2].tooltip = "Final Battle! Requires Miniboss Defeated"
        self.buttons[3].tooltip = "Return to Main Menu"
    
    def start_hunt(self):
        self.manager.start_hunt()
    
    def start_miniboss(self):
        self.manager.start_miniboss()
    
    def start_boss(self):
        # Only allow if miniboss is defeated
        if self.manager.miniboss_defeated:
            self.manager.start_boss()
    
    def go_main_menu(self):
        self.manager.go_to('main_menu')
    
    def handle_event(self, event):
        for b in self.buttons:
            # Skip boss button if miniboss not defeated
            if b.text == "Enter Boss Lair" and not self.manager.miniboss_defeated:
                continue
            # Skip miniboss button if already defeated
            if b.text == "Challenge Miniboss" and self.manager.miniboss_defeated:
                continue
            b.handle_event(event)
    
    def update(self, dt):
        pass
    
    def draw(self, surface):
        # Draw background
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((30, 30, 50))
        
        # Draw semi-transparent overlay for readability
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        
        # Draw title
        title = self.font_title.render("CROSSROADS", True, (255, 215, 0))
        tw = title.get_width()
        surface.blit(title, ((self.screen_width - tw) // 2, 50))
        
        # Draw stats panel
        stats = self.manager.player_stats
        panel_x = self.screen_width // 2 - 150
        panel_y = 120
        panel_w = 300
        panel_h = 140
        
        # Panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(surface, (40, 40, 60), panel_rect, border_radius=10)
        pygame.draw.rect(surface, (100, 100, 150), panel_rect, 2, border_radius=10)
        
        # Stats text
        stat_lines = [
            f"Level: {stats['level']}",
            f"HP: {stats['hp']} / {stats['max_hp']}",
            f"ATK: {stats['atk']}",
            f"Mana: {stats['mana']} / {stats['max_mana']}",
        ]
        
        for i, line in enumerate(stat_lines):
            stat_surf = self.font_stats.render(line, True, (200, 255, 200))
            surface.blit(stat_surf, (panel_x + 20, panel_y + 15 + i * 30))
        
        # Draw turn counter
        turn_text = f"Total Turns: {self.manager.total_run_turns}"
        turn_surf = self.font_stats.render(turn_text, True, (150, 200, 255))
        surface.blit(turn_surf, (self.screen_width - 220, 20))
        
        # Draw miniboss status
        if self.manager.miniboss_defeated:
            status_text = "✓ Miniboss Defeated"
            status_color = (100, 255, 100)
        else:
            status_text = "✗ Miniboss Not Defeated"
            status_color = (255, 100, 100)
        status_surf = self.font_stats.render(status_text, True, status_color)
        surface.blit(status_surf, (panel_x + 20, panel_y + panel_h + 10))
        
        # Draw buttons
        for b in self.buttons:
            # Grey out boss button if miniboss not defeated
            if b.text == "Enter Boss Lair" and not self.manager.miniboss_defeated:
                # Draw greyed out button
                grey_rect = b.rect.copy()
                pygame.draw.rect(surface, (60, 60, 60), grey_rect, border_radius=8)
                pygame.draw.rect(surface, (100, 100, 100), grey_rect, 2, border_radius=8)
                grey_text = self.font_button.render(b.text, True, (100, 100, 100))
                text_rect = grey_text.get_rect(center=grey_rect.center)
                surface.blit(grey_text, text_rect)
            # Grey out miniboss button if already defeated
            elif b.text == "Challenge Miniboss" and self.manager.miniboss_defeated:
                # Draw greyed out button
                grey_rect = b.rect.copy()
                pygame.draw.rect(surface, (60, 60, 60), grey_rect, border_radius=8)
                pygame.draw.rect(surface, (100, 100, 100), grey_rect, 2, border_radius=8)
                grey_text = self.font_button.render(b.text, True, (100, 100, 100))
                text_rect = grey_text.get_rect(center=grey_rect.center)
                surface.blit(grey_text, text_rect)
            else:
                b.draw(surface)
        
        # Draw tooltips on hover
        mx, my = pygame.mouse.get_pos()
        for b in self.buttons:
            if hasattr(b, 'tooltip') and b.rect.collidepoint((mx, my)):
                # Custom tooltip for disabled boss button
                if b.text == "Enter Boss Lair" and not self.manager.miniboss_defeated:
                    tooltip_text = "Defeat the Miniboss first!"
                # Custom tooltip for defeated miniboss
                elif b.text == "Challenge Miniboss" and self.manager.miniboss_defeated:
                    tooltip_text = "Already Defeated"
                else:
                    tooltip_text = b.tooltip
                
                tooltip_surf = self.font_tooltip.render(tooltip_text, True, (255, 255, 200))
                tooltip_rect = tooltip_surf.get_rect()
                tooltip_rect.midbottom = (b.rect.centerx, b.rect.top - 5)
                
                # Draw tooltip background
                bg_rect = tooltip_rect.inflate(10, 6)
                pygame.draw.rect(surface, (50, 50, 50), bg_rect, border_radius=4)
                pygame.draw.rect(surface, (200, 200, 150), bg_rect, 1, border_radius=4)
                surface.blit(tooltip_surf, tooltip_rect)
                break
