import math
import pygame

from operator import sub
from ui.colours import *


class Project:

    def __init__(self, width, height):
        self.elements = {}  # {[x, y]: <Object>}, where x and y are the coordinates of the grid
        self.offset_x, self.offset_y = 0, 0
        self.zoom = 50
        self.origin = (10, 10)
        self.width, self.height = width, height
        self.panning = False
        self.last_surface = None
        self.last_mouse_pos = None
        self.pos = (0, 0)
        self.display_name = "Untitled.dev"

    def shift(self, x, y):
        self.offset_x += x
        self.offset_y += y

    def scale(self, x):
        if x > 0 and self.zoom + x > 100:
            self.zoom = 100
            return
        if x < 0 and self.zoom + x < 10:
            self.zoom = 10
            return
        self.zoom += x

    def set_size(self, width=None, height=None):
        self.width = width if width is not None else self.width
        self.height = height if height is not None else self.height

    def relative_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_relative_to_protosim = tuple(map(lambda i, j: i - j, mouse_pos, self.pos))
        return mouse_relative_to_protosim[0] - self.origin[0], mouse_relative_to_protosim[1] - self.origin[1]

    def convert_point(self, point):
        x = point[0] * self.zoom
        y = point[1] * self.zoom
        return self.origin[0] + x, self.origin[1] + y

    def listen(self, win):
        if self.last_surface is not None:
            if self.last_surface.get_rect(topleft=self.pos).collidepoint(pygame.mouse.get_pos()) or self.panning:

                if self.last_mouse_pos is None:
                    self.last_mouse_pos = pygame.mouse.get_pos()

                if pygame.mouse.get_pressed()[1]:
                    self.panning = True
                    if self not in pygame.query_disable:
                        pygame.query_disable.append(self)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                    mouse_change = tuple(map(sub, pygame.mouse.get_pos(), self.last_mouse_pos))
                    self.shift(mouse_change[0], mouse_change[1])
                    self.last_mouse_pos = pygame.mouse.get_pos()
                else:
                    self.panning = False
                    if self in pygame.query_disable:
                        pygame.query_disable.remove(self)
                    self.last_mouse_pos = pygame.mouse.get_pos()

                    if not len(pygame.query_disable):
                        relative_mouse = self.relative_mouse()
                        point = (math.floor(relative_mouse[0]/self.zoom), math.floor(relative_mouse[1]/self.zoom))
                        x, y = self.convert_point(point)
                        box = pygame.Rect(x, y, self.zoom, self.zoom)
                        pygame.draw.rect(win, COL_SIM_GRIDLINES, box)

    def gridlines(self, win, axis):
        current_line = 0
        while abs(current_line-self.origin[axis]) % self.zoom != 0:
            current_line += 1
        while current_line <= (self.height if axis else self.width):
            start_coord = (0, current_line) if axis else (current_line, 0)
            end_coord = (self.width, current_line) if axis else (current_line, self.height)
            pygame.draw.line(win, COL_SIM_GRIDLINES, start_coord, end_coord)
            current_line += self.zoom

    def surface(self):
        win = pygame.Surface((self.width, self.height))
        win.fill(COL_SIM_BKG)
        self.listen(win)
        self.origin = (10 + self.offset_x, 10 + self.offset_y)
        self.gridlines(win, 0)
        self.gridlines(win, 1)
        self.last_surface = win
        return win
