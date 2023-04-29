import os
import pygame

from runtime.environment import Environment
from ui.colours import *
from protosim.project import Project


def fill(surface, color):
    """Fill all pixels of the surface with color, preserve transparency."""
    copy = surface.copy()
    width, height = surface.get_size()
    r, g, b = color
    for x in range(width):
        for y in range(height):
            a = surface.get_at((x, y))[3]
            copy.set_at((x, y), pygame.Color(r, g, b, a))
    return copy


class ElementManager:

    def __init__(self, buttons, text_manager):
        self.elements = buttons
        self.text_manager = text_manager
        self.hovered = False

    def draw(self, win, draw=True):
        hovered = False
        for element in self.elements:
            if isinstance(element, Button):
                element.draw(win, self.text_manager) if draw else None
                element.listen()
                if element.hovering:
                    hovered = True
                continue
            if isinstance(element, Project):
                if element.panning:
                    hovered = True
                continue
            if element.hovering:
                hovered = True
        self.hovered = hovered


class Button:
    
    def __init__(self, size, pos, icon, label, event):
        self.size = size
        self.pos = pos
        self.hovering = False
        environment_path = Environment().get_main_path()
        icon_path = os.path.join(environment_path, 'assets', 'textures', icon)
        self.icon = pygame.image.load(icon_path).convert_alpha()
        self.hovered_icon = fill(self.icon, COL_HOME_TITLE)
        self.label = label
        self.event = event
        self.rect = pygame.Rect(pos, size)
        self.clicked = False
        
    def listen(self, top_left=None):
        mouse_pos = pygame.mouse.get_pos()
        if not len(pygame.query_disable):
            if top_left is not None:
                rect = self.rect.copy()
                rect.topleft = top_left
            else:
                rect = self.rect
            if rect.collidepoint(mouse_pos):
                self.hovering = True
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                if pygame.mouse.get_pressed()[0]:
                    if not self.clicked:
                        self.clicked = True
                        pygame.event.post(pygame.event.Event(self.event))
                else:
                    self.clicked = False
            else:
                self.hovering = False
        
    def draw(self, win, text_handler):
        colour = COL_HOME_TITLE if self.hovering else COL_HOME_SHADOW
        pygame.draw.rect(win, colour, self.rect.move(2, 2), border_radius=16)
        pygame.draw.rect(win, COL_HOME_SHADOW if self.hovering else COL_HOME_TITLE, self.rect, border_radius=16)
        label_surface, label_shadow = text_handler.render_shadow(self.label, shadow_colour=colour, colour=COL_WHITE)
        if label_surface.get_width() == 0:
            combined_width = self.icon.get_width()/2
        else:
            combined_width = (label_surface.get_width() + self.icon.get_width() + 10) / 2
        hover_label = combined_width*2 > self.size[0]
        starting_x = self.pos[0] + (self.size[0]/2) - combined_width
        starting_y = self.pos[1] + (self.size[1]/2)
        icon_coords = (starting_x, starting_y - (self.icon.get_height() / 2))
        label_coords = (starting_x + self.icon.get_width() + 10, starting_y - (label_surface.get_height() / 2))
        if hover_label:
            if self.hovering:
                label_coords = (self.pos[0] + (self.size[0]/2) - label_surface.get_width()/2, label_coords[1])
                win.blit(label_shadow, tuple(x + 1 for x in label_coords))
                win.blit(label_surface, label_coords)
            else:
                icon_coords = (self.pos[0] + (self.size[0]/2) - self.icon.get_width()/2, icon_coords[1])
                win.blit(self.hovered_icon if self.hovering else self.icon, icon_coords)
        else:
            win.blit(self.hovered_icon if self.hovering else self.icon, icon_coords)
            win.blit(label_shadow, tuple(x + 1 for x in label_coords))
            win.blit(label_surface, label_coords)
        
        