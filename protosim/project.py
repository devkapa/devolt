import math
import pygame

from operator import sub, mul
from ui.colours import *


class Project:

    def __init__(self, width, height, env):
        self.boards = {}
        self.wires = []
        self.offset_x, self.offset_y = 0, 0
        self.zoom = 50
        self.origin = (10, 10)
        self.env = env
        self.width, self.height = width, height
        self.panning = False
        self.last_surface = None
        self.last_mouse_pos = None
        self.pos = (0, 0)
        self.display_name = "Untitled.dev"
        self.in_hand = None
        self.win = pygame.Surface((self.width, self.height))
        self.rect_hovered = None
        self.incomplete_wire = None

    def shift(self, x, y):
        self.offset_x += x
        self.offset_y += y

    def grab(self, part):
        self.in_hand = part

    def drop(self):
        self.in_hand = None

    def scale(self, x):
        if x > 0 and self.zoom + x > 400:
            self.zoom = 400
            return
        if x < 0 and self.zoom + x < 10:
            self.zoom = 10
            return
        mouse = self.relative_mouse()
        point_before_zoom = (mouse[0]/self.zoom, mouse[1]/self.zoom)
        self.zoom += x
        point_after_zoom = (mouse[0]/self.zoom, mouse[1]/self.zoom)
        delta = tuple(map(lambda i, j: math.floor((i - j)*self.zoom), point_after_zoom, point_before_zoom))
        self.shift(*delta)

    def set_size(self, width=None, height=None):
        self.width = width if width is not None else self.width
        self.height = height if height is not None else self.height
        self.win = pygame.Surface((self.width, self.height))

    def relative_mouse(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_relative_to_protosim = tuple(map(lambda i, j: i - j, mouse_pos, self.pos))
        return mouse_relative_to_protosim[0] - self.origin[0], mouse_relative_to_protosim[1] - self.origin[1]

    def convert_point(self, point):
        x = point[0] * self.zoom
        y = point[1] * self.zoom
        return self.origin[0] + x, self.origin[1] + y

    def delete(self, coordinate):
        for coord in self.boards.copy():
            element = self.boards[coord]
            if isinstance(element, Occupier) and element.parent_coord == coordinate:
                del self.boards[coord]
        self.rect_hovered = None
        self.incomplete_wire = None
        for wire in self.wires.copy():
            if wire.point_a.parent == self.boards[coordinate] or wire.point_b.parent == self.boards[coordinate]:
                self.wires.remove(wire)
        del self.boards[coordinate]

    def listen(self):
        env = self.env
        if self.in_hand is not None:
            if self.in_hand not in env.query_disable:
                env.query_disable.append(self.in_hand)
        if self.incomplete_wire is not None:
            if self.incomplete_wire not in env.query_disable:
                env.query_disable.append(self.incomplete_wire)
        if self.last_surface is not None:
            if self.last_surface.get_rect(topleft=self.pos).collidepoint(pygame.mouse.get_pos()) or self.panning:

                keys_pressed = pygame.key.get_pressed()
                mouse_pressed = pygame.mouse.get_pressed()

                if self.last_mouse_pos is None:
                    self.last_mouse_pos = pygame.mouse.get_pos()

                if mouse_pressed[1] or (keys_pressed[pygame.K_LCTRL] and mouse_pressed[0]):
                    self.panning = True
                    if self not in env.query_disable:
                        env.query_disable.append(self)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                    mouse_change = tuple(map(sub, pygame.mouse.get_pos(), self.last_mouse_pos))
                    self.shift(mouse_change[0], mouse_change[1])
                    self.last_mouse_pos = pygame.mouse.get_pos()
                    return

                self.panning = False

                if self in env.query_disable:
                    env.query_disable.remove(self)

                self.last_mouse_pos = pygame.mouse.get_pos()

                if self.incomplete_wire is not None:

                    if keys_pressed[pygame.K_ESCAPE]:

                        if self.incomplete_wire in env.query_disable:
                            env.query_disable.remove(self.incomplete_wire)
                        self.incomplete_wire = None

                if self.in_hand is not None:

                    if keys_pressed[pygame.K_ESCAPE]:

                        if self.in_hand in env.query_disable:
                            env.query_disable.remove(self.in_hand)
                        self.in_hand = None

                    if mouse_pressed[0]:
                        relative_mouse = self.relative_mouse()
                        point = (math.floor(relative_mouse[0]/self.zoom), math.floor(relative_mouse[1]/self.zoom))
                        occupying_points = []
                        allowed = True
                        for row in range(self.in_hand.size[0]):
                            for column in range(self.in_hand.size[1]):
                                occupying_point = tuple(map(sum, zip(point, (row, column))))
                                if occupying_point in self.boards:
                                    allowed = False
                                    break
                                occupying_points.append(occupying_point)
                        if allowed:
                            self.boards[point] = self.in_hand
                            occupier = Occupier(point)
                            for occupying_point in occupying_points:
                                if occupying_point == point:
                                    continue
                                self.boards[occupying_point] = occupier
                            if self.in_hand in env.query_disable:
                                env.query_disable.remove(self.in_hand)
                            self.in_hand = None

                    return

                if self.incomplete_wire is None and mouse_pressed[2]:
                    relative_mouse = self.relative_mouse()
                    point = (math.floor(relative_mouse[0] / self.zoom), math.floor(relative_mouse[1] / self.zoom))
                    if point in self.boards:
                        if isinstance(self.boards[point], Occupier):
                            self.delete(self.boards[point].parent_coord)

    def gridlines(self, win, axis):
        current_line = 0
        while abs(current_line-self.origin[axis]) % self.zoom != 0:
            current_line += 1
        while current_line <= (self.height if axis else self.width):
            start_coord = (0, current_line) if axis else (current_line, 0)
            end_coord = (self.width, current_line) if axis else (current_line, self.height)
            pygame.draw.line(win, COL_SIM_GRIDLINES, start_coord, end_coord)
            current_line += self.zoom

    def draw_scaled(self, win, element, coord, colour=(255, 255, 255, 255)):
        real_element_pos = tuple(map(sum, zip(self.pos, self.convert_point(coord))))
        size = (element.size[0] * self.zoom, element.size[1] * self.zoom)
        scale = (size[0] / element.texture.get_width(), size[1] / element.texture.get_height())
        element_surf, rect_hovered = element.surface(real_element_pos, scale)
        surf = pygame.transform.scale(element_surf, size)
        surf.fill(colour, None, pygame.BLEND_RGBA_MULT)
        win.blit(surf, self.convert_point(coord))
        return scale, coord, rect_hovered

    def surface(self):
        self.win.fill(COL_SIM_BKG)
        self.listen()
        self.origin = (10 + self.offset_x, 10 + self.offset_y)
        self.gridlines(self.win, 0)
        self.gridlines(self.win, 1)
        self.last_surface = self.win

        temp_positions = {}
        temp_hovered = None

        for coord in self.boards:
            element = self.boards[coord]
            if isinstance(element, Occupier):
                continue
            scale, coord, rect_hovered = self.draw_scaled(self.win, element, coord)
            temp_positions[element] = (scale, coord)
            if rect_hovered is not None:
                temp_hovered = rect_hovered

        self.rect_hovered = temp_hovered

        if self.incomplete_wire is not None:
            a_scale, a_coord = temp_positions[self.incomplete_wire.parent]
            a_rect = self.incomplete_wire.rect
            a_pos = self.convert_point(a_coord)
            a_scaled_center = tuple(map(mul, a_scale, a_rect.center))
            a_real_center = tuple(map(sum, zip(a_pos, a_scaled_center)))
            mouse_pos = pygame.mouse.get_pos()
            mouse_relative = tuple(map(lambda i, j: i - j, mouse_pos, self.pos))
            pygame.draw.aaline(self.win, COL_RED, a_real_center, mouse_relative)

        for wire in self.wires:
            a_scale, a_coord = temp_positions[wire.point_a.parent]
            b_scale, b_coord = temp_positions[wire.point_b.parent]
            a_rect = wire.point_a.rect
            b_rect = wire.point_b.rect
            a_pos = self.convert_point(a_coord)
            b_pos = self.convert_point(b_coord)
            a_scaled_center = tuple(map(mul, a_scale, a_rect.center))
            a_real_center = tuple(map(sum, zip(a_pos, a_scaled_center)))
            b_scaled_center = tuple(map(mul, b_scale, b_rect.center))
            b_real_center = tuple(map(sum, zip(b_pos, b_scaled_center)))
            pygame.draw.line(self.win, COL_BLACK, a_real_center, b_real_center, width=4)
            pygame.draw.line(self.win, wire.colour, a_real_center, b_real_center, width=2)

        if self.in_hand is not None:
            relative_mouse = self.relative_mouse()
            point = (math.floor(relative_mouse[0] / self.zoom), math.floor(relative_mouse[1] / self.zoom))
            allowed = True
            for row in range(self.in_hand.size[0]):
                for column in range(self.in_hand.size[1]):
                    occupying_point = tuple(map(sum, zip(point, (row, column))))
                    if occupying_point in self.boards:
                        allowed = False
                        break
            if point in self.boards or not allowed:
                colour = (200, 0, 0, 128)
            else:
                colour = (255, 255, 255, 128)
            self.draw_scaled(self.win, self.in_hand, point, colour=colour)

        return self.win


class Occupier:

    def __init__(self, parent_coord):
        self.parent_coord = parent_coord
