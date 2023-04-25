import math

import pygame
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
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                    self.shift(pygame.mouse.get_pos()[0] - self.last_mouse_pos[0], pygame.mouse.get_pos()[1] - self.last_mouse_pos[1])
                    self.last_mouse_pos = pygame.mouse.get_pos()
                else:
                    self.panning = False
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    self.last_mouse_pos = pygame.mouse.get_pos()

                    relative_mouse = self.relative_mouse()
                    point = (math.floor(relative_mouse[0]/self.zoom), math.floor(relative_mouse[1]/self.zoom))
                    x, y = self.convert_point(point)
                    box = pygame.Rect(x, y, self.zoom, self.zoom)
                    pygame.draw.rect(win, COL_SIMULATOR_GRIDLINES, box)


            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def gridlines(self, win):
        accumulated = 0
        sign = 0
        while True:
            accumulated += self.zoom if not sign else -self.zoom
            new_x = self.origin[0] + accumulated
            if (new_x > self.width and not sign) or (new_x < 0 and sign):
                if not sign:
                    sign = ~sign
                    continue
                break
            pygame.draw.aaline(win, COL_SIMULATOR_GRIDLINES, (new_x, 0), (new_x, self.height))
        accumulated = 0
        sign = 0
        while True:
            accumulated += self.zoom if not sign else -self.zoom
            new_y = self.origin[1] + accumulated
            if (new_y > self.height and not sign) or (new_y < 0 and sign):
                if not sign:
                    sign = ~sign
                    continue
                break
            pygame.draw.aaline(win, COL_SIMULATOR_GRIDLINES, (0, new_y), (self.width, new_y))

    def surface(self):
        win = pygame.Surface((self.width, self.height))
        win.fill(COL_SIMULATOR)
        self.listen(win)
        self.origin = (10 + self.offset_x, 10 + self.offset_y)
        pygame.draw.line(win, COL_SIMULATOR_GRIDLINES, (self.origin[0], 0), (self.origin[0], self.height), width=2)
        pygame.draw.line(win, COL_SIMULATOR_GRIDLINES, (0, self.origin[1]), (self.width, self.origin[1]), width=2)
        self.gridlines(win)
        self.last_surface = win
        return win





