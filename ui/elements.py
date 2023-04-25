import os
import pygame
from runtime.environment import Environment
from ui.colours import *


# Fill all pixels of the surface with color, preserve transparency.
def fill(surface, color):
    copy = surface.copy()
    width, height = surface.get_size()
    r, g, b = color
    for x in range(width):
        for y in range(height):
            a = surface.get_at((x, y))[3]
            copy.set_at((x, y), pygame.Color(r, g, b, a))
    return copy


class Button:
    
    def __init__(self, size, pos, icon, label, event):
        self.size = size
        self.pos = pos
        self.hovering = False
        environment_path = Environment().get_main_path()
        icon_path = os.path.join(environment_path, 'assets', 'textures', icon)
        self.icon = pygame.image.load(icon_path).convert_alpha()
        self.hovered_icon = fill(self.icon, COL_TITLE)
        self.label = label
        self.event = event
        self.rect = pygame.Rect(pos, size)
        self.clicked = False
        
    def listen(self):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            self.hovering = True
            if pygame.mouse.get_pressed()[0]:
                if not self.clicked:
                    self.clicked = True
                    pygame.event.post(pygame.event.Event(self.event))
            else:
                self.clicked = False
        else:
            self.hovering = False
        
    def draw(self, win, text_handler):
        pygame.draw.rect(win, COL_TITLE if self.hovering else COL_TITLE_SHADOW, self.rect.move(2, 2), border_radius=16)
        pygame.draw.rect(win, COL_TITLE_SHADOW if self.hovering else COL_TITLE, self.rect, border_radius=16)
        label_surface, label_shadow = text_handler.render_shadow(self.label, shadow_colour=COL_TITLE if self.hovering else COL_TITLE_SHADOW, colour=COL_WHITE)
        combined_width = (label_surface.get_width() + self.icon.get_width() + 10)/2
        starting_x = self.pos[0] + (self.size[0]/2) - combined_width
        starting_y = self.pos[1] + (self.size[1]/2)
        win.blit(self.hovered_icon if self.hovering else self.icon, (starting_x, starting_y - (self.icon.get_height()/2)))
        win.blit(label_shadow, (starting_x + self.icon.get_width() + 10 + 1, starting_y - (label_surface.get_height()/2) + 1))
        win.blit(label_surface, (starting_x + self.icon.get_width() + 10, starting_y - (label_surface.get_height()/2)))
        
        