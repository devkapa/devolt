import math
import pickle
import time

import pygame
from operator import sub, mul
from pathlib import Path

from logic.vectormath import Vector
from ui.colours import *
from ui.text import TextHandler
from tkinter import Tk, StringVar, OptionMenu, Button


class SaveState:

    def __init__(self, boards, wires, name):
        self.boards = boards
        self.wires = wires
        self.name = name

    def get_attrs(self):
        return self.boards, self.wires, self.name


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
        self.point_hovered = None
        self.incomplete_wire = None
        self.handler = TextHandler(env, 'Play-Regular.ttf', 25)
        self.wire_colour_handler = TextHandler(env, 'Play-Regular.ttf', 18)
        self.drag_warning = self.handler.render("Drag above a breadboard hole", colour=COL_HOME_BKG)
        self.anode_warning = self.handler.render("Select anode (+)", colour=COL_BLACK)
        self.cathode_warning = self.handler.render("Select cathode (-)", colour=COL_BLACK)
        self.colour_text = self.wire_colour_handler.render("Select wire colour", colour=COL_BLACK)
        self.resist_text = self.wire_colour_handler.render("Change resistance", colour=COL_BLACK)
        self.saved = (True, None)
        self.cached = {}

    def shift(self, x, y):
        self.offset_x += x
        self.offset_y += y

    def save(self, file):
        self.change_made()
        self.display_name = Path(file.name).name
        self.saved = (True, file)
        return SaveState(self.boards, self.wires, self.display_name)

    def make_save_state(self):
        return pickle.dumps(SaveState(self.boards, self.wires, self.display_name))

    def load_save_state(self, save_data):
        self.boards, self.wires, self.display_name = pickle.loads(save_data).get_attrs()
        self.rejuvenate()

    def reset(self):
        self.boards = {}
        self.wires = []
        self.offset_x, self.offset_y = 0, 0
        self.zoom = 50
        self.panning = False
        self.last_surface = None
        self.last_mouse_pos = None
        self.pos = (0, 0)
        self.display_name = "Untitled.dev"
        self.in_hand = None
        self.point_hovered = None
        self.incomplete_wire = None
        self.saved = (True, None)
        self.cached.clear()
        self.env.reset()

    def change_made(self):
        self.saved = (False, self.saved[1])
        self.env.redo_states.clear()
        self.env.undo_states.append(self.make_save_state())
        pygame.event.post(pygame.event.Event(pygame.USEREVENT + 10))

    def rejuvenate(self):
        from logic.parts import PowerSupply, Breadboard
        for wire in self.wires:
            old_point_a_group = wire.point_a.discriminator.name
            group_1 = None
            if isinstance(wire.point_a.parent, PowerSupply):
                if wire.point_a.discriminator.row:
                    wire.point_a = wire.point_a.parent.points[0]
                else:
                    wire.point_a = wire.point_a.parent.points[1]
            elif isinstance(wire.point_a.parent, Breadboard):
                if old_point_a_group == "main":
                    group_1 = wire.point_a.parent.main_board_rects
                elif old_point_a_group == "power":
                    group_1 = wire.point_a.parent.pr_rects
                wire.point_a = group_1[wire.point_a.discriminator][2]

            old_point_b_group = wire.point_b.discriminator.name
            group_2 = None
            if isinstance(wire.point_b.parent, PowerSupply):
                if wire.point_b.discriminator.row:
                    wire.point_b = wire.point_b.parent.points[0]
                else:
                    wire.point_b = wire.point_b.parent.points[1]
            elif isinstance(wire.point_b.parent, Breadboard):
                if old_point_b_group == "main":
                    group_2 = wire.point_b.parent.main_board_rects
                elif old_point_b_group == "power":
                    group_2 = wire.point_b.parent.pr_rects
                wire.point_b = group_2[wire.point_b.discriminator][2]

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
        self.cached.clear()

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

    def delete(self, coordinate, remove_wires=True):
        self.change_made()
        self.env.undo_states.append(self.make_save_state())
        for coord in self.boards.copy():
            element = self.boards[coord]
            if isinstance(element, Occupier) and element.parent_coord == coordinate:
                del self.boards[coord]
        self.point_hovered = None
        self.incomplete_wire = None
        if remove_wires:
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

                mouse_pressed = pygame.mouse.get_pressed()
                keys_pressed = pygame.key.get_pressed()

                if self.last_mouse_pos is None:
                    self.last_mouse_pos = pygame.mouse.get_pos()

                not_occupied = self.in_hand is None and self.point_hovered is None and self.incomplete_wire is None and self.env.selected is None
                selected_not_occupied = self.in_hand is None and self.point_hovered is None and self.incomplete_wire is None
                case_1 = mouse_pressed[0] and keys_pressed[pygame.K_LCTRL] and not_occupied
                case_2 = mouse_pressed[1] and not keys_pressed[pygame.K_LCTRL] and not_occupied

                if case_1 or case_2:
                    self.panning = True
                    if self not in env.query_disable:
                        env.query_disable.append(self)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
                    mouse_change = tuple(map(sub, pygame.mouse.get_pos(), self.last_mouse_pos))
                    self.shift(mouse_change[0], mouse_change[1])
                    self.last_mouse_pos = pygame.mouse.get_pos()
                    return

                if mouse_pressed[0] and keys_pressed[pygame.K_LCTRL] and selected_not_occupied:
                    from logic.parts import Breadboard
                    relative_mouse = self.relative_mouse()
                    point = (math.floor(relative_mouse[0] / self.zoom), math.floor(relative_mouse[1] / self.zoom))
                    if point in self.boards:
                        if isinstance(self.boards[point], Breadboard):
                            self.in_hand = self.boards[point]
                            self.delete(point, remove_wires=False)
                            return
                        elif isinstance(self.boards[point], Occupier):
                            self.in_hand = self.boards[self.boards[point].parent_coord]
                            self.delete(self.boards[point].parent_coord, remove_wires=False)
                            return

                if mouse_pressed[0] and self.env.selected is not None and not len(self.env.query_disable):
                    relative_mouse = self.relative_mouse()
                    point = (math.floor(relative_mouse[0] / self.zoom), math.floor(relative_mouse[1] / self.zoom))
                    if point not in self.boards:
                        self.env.selected = None

                self.panning = False

                if self in env.query_disable:
                    env.query_disable.remove(self)

                self.last_mouse_pos = pygame.mouse.get_pos()

    def gridlines(self, win, axis):
        current_line = 0
        while abs(current_line-self.origin[axis]) % self.zoom != 0:
            current_line += 1
        while current_line <= (self.height if axis else self.width):
            start_coord = (0, current_line) if axis else (current_line, 0)
            end_coord = (self.width, current_line) if axis else (current_line, self.height)
            pygame.draw.line(win, COL_SIM_GRIDLINES, start_coord, end_coord)
            current_line += self.zoom

    def out_of_bounds(self, point):
        if point[0] < 0 or point[0] > self.width:
            return True
        if point[1] < 0 or point[1] > self.height:
            return True
        return False

    def draw_scaled_big(self, win, element, coord, draw, colour=(255, 255, 255, 255), led_only=False):
        size = (element.size[0] * self.zoom, element.size[1] * self.zoom)
        scale = (size[0] / element.texture.get_width(), size[1] / element.texture.get_height())
        real_element_pos = tuple(map(sum, zip(self.pos, self.convert_point(coord))))
        if led_only:
            element_surf, rect_hovered = element.surface_led(), None
        else:
            element_surf, rect_hovered = element.surface(real_element_pos, scale)
        if draw:
            surf = pygame.transform.scale(element_surf, size)
            surf.fill(colour, None, pygame.BLEND_RGBA_MULT)
            win.blit(surf, self.convert_point(coord))
        return scale, coord, rect_hovered, self.convert_point(coord)

    def surface(self):
        self.win.fill(COL_SIM_BKG)
        self.listen()
        self.origin = (10 + self.offset_x, 10 + self.offset_y)
        self.gridlines(self.win, 0)
        self.gridlines(self.win, 1)
        self.last_surface = self.win

        temp_positions = {}
        temp_hovered = None

        occupier_coord_parent = {}

        for coord in self.boards:
            element = self.boards[coord]
            if isinstance(element, Occupier):
                if not self.boards[element.parent_coord] in occupier_coord_parent:
                    occupier_coord_parent[self.boards[element.parent_coord]] = []
                occupier_coord_parent[self.boards[element.parent_coord]].append(coord)

        for coord in self.boards:
            element = self.boards[coord]
            if isinstance(element, Occupier):
                continue
            draw = True
            if self.out_of_bounds(self.convert_point(coord)):
                draw = False
                for occupier in occupier_coord_parent[element]:
                    if not self.out_of_bounds(self.convert_point(occupier)):
                        draw = True
            scale, coord, rect_hovered, real_element_pos = self.draw_scaled_big(self.win, element, coord, draw)
            temp_positions[element] = (scale, coord, real_element_pos)
            if rect_hovered is not None:
                temp_hovered = rect_hovered

        if self.last_surface is not None:
            if self.last_surface.get_rect(topleft=self.pos).collidepoint(pygame.mouse.get_pos()):
                self.point_hovered = temp_hovered

        if self.incomplete_wire is not None:
            a_scale, a_coord, _ = temp_positions[self.incomplete_wire.parent]
            a_rect = self.incomplete_wire.rect
            a_pos = self.convert_point(a_coord)
            a_scaled_center = tuple(map(mul, a_scale, a_rect.center))
            a_real_center = tuple(map(sum, zip(a_pos, a_scaled_center)))
            mouse_pos = pygame.mouse.get_pos()
            mouse_relative = tuple(map(lambda i, j: i - j, mouse_pos, self.pos))
            pygame.draw.aaline(self.win, COL_RED, a_real_center, mouse_relative)

        if self.in_hand is not None:
            from logic.parts import PluginPart, IntegratedCircuit, LED
            if isinstance(self.in_hand, PluginPart):
                mouse_pos = pygame.mouse.get_pos()
                mouse_relative = tuple(map(lambda i, j: i - j, mouse_pos, self.pos))
                if self.point_hovered is not None:
                    scale = temp_positions[self.point_hovered.parent][0]
                    surf = self.in_hand.surface(self.point_hovered.parent)[0]
                    size = tuple(map(mul, scale, surf.get_size()))
                    surf = pygame.transform.scale(surf, size)
                    mouse_relative = (mouse_relative[0] - self.point_hovered.parent.radius*scale[0], mouse_relative[1])
                    if isinstance(self.in_hand, IntegratedCircuit):
                        if self.point_hovered.parent.ic_allowed(self.in_hand, self.point_hovered):
                            colour = (255, 255, 255, 128)
                        else:
                            colour = (200, 0, 0, 128)
                        surf.fill(colour, None, pygame.BLEND_RGBA_MULT)
                    if isinstance(self.in_hand, LED):
                        if self.in_hand.cathode_connecting:
                            scale = temp_positions[self.point_hovered.parent][0]
                            parent_real = temp_positions[self.in_hand.anode_point.parent][2]
                            point = self.in_hand.anode_point.rect.center
                            point = tuple(map(lambda i, j, k: (i*j)+k, point, scale, parent_real))
                            pygame.draw.line(self.win, COL_IC_PIN, point, mouse_relative, width=4)
                            rect_size = self.cathode_warning.get_size()
                            pygame.draw.rect(self.win, COL_WHITE, pygame.Rect(mouse_relative, rect_size))
                            self.win.blit(self.cathode_warning, mouse_relative)
                        else:
                            self.win.blit(surf, mouse_relative)
                            label_coord = (mouse_relative[0]+surf.get_width(), mouse_relative[1])
                            rect_size = self.anode_warning.get_size()
                            pygame.draw.rect(self.win, COL_WHITE, pygame.Rect(label_coord, rect_size))
                            self.win.blit(self.anode_warning, label_coord)
                    else:
                        self.win.blit(surf, mouse_relative)
                else:
                    rect_size = self.drag_warning.get_size()
                    pygame.draw.rect(self.win, COL_WHITE, pygame.Rect(mouse_relative, rect_size))
                    self.win.blit(self.drag_warning, mouse_relative)
            else:
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
                scale, coord, _, real = self.draw_scaled_big(self.win, self.in_hand, point, True, colour=colour)
                temp_positions[self.in_hand] = (scale, coord, real)

        colour_selection = []
        colours = [COL_WIRE_RED, COL_WIRE_BLACK, COL_WIRE_YELLOW, COL_WIRE_WHITE, COL_WIRE_GREEN, COL_WIRE_BLUE]

        for wire in self.wires:
            a_scale, a_coord, _ = temp_positions[wire.point_a.parent]
            b_scale, b_coord, _ = temp_positions[wire.point_b.parent]
            a_rect = wire.point_a.rect
            b_rect = wire.point_b.rect
            a_pos = self.convert_point(a_coord)
            b_pos = self.convert_point(b_coord)
            a_scaled_center = tuple(map(mul, a_scale, a_rect.center))
            a_real_center = tuple(map(sum, zip(a_pos, a_scaled_center)))
            b_scaled_center = tuple(map(mul, b_scale, b_rect.center))
            b_real_center = tuple(map(sum, zip(b_pos, b_scaled_center)))
            wire_rect = pygame.draw.line(self.win, COL_BLACK, a_real_center, b_real_center, width=4)
            pygame.draw.line(self.win, wire.colour, a_real_center, b_real_center, width=2)
            if wire.resistance != 0:
                vec_a = Vector(*a_real_center)
                vec_b = Vector(*b_real_center)
                vec_ab = vec_b - vec_a
                vec_c = (vec_a + vec_b)*(1/2)
                vec_ac = (vec_a + vec_c)*(1/2)
                vec_cb = (vec_b + vec_c)*(1/2)
                if vec_a.y == vec_b.y:
                    vec_perpendicular = vec_ab.perptox().normalized()
                elif vec_a.x == vec_b.x:
                    vec_perpendicular = vec_ab.perptoy().normalized()
                else:
                    vec_perpendicular = vec_ab.perp().normalized()
                x = 0
                while x <= 10:
                    vec_p1_a = vec_ac + vec_perpendicular * x
                    vec_p2_a = vec_ac - vec_perpendicular * x
                    vec_p1_b = vec_cb + vec_perpendicular * x
                    vec_p2_b = vec_cb - vec_perpendicular * x
                    lines = [(vec_p1_a.x, vec_p1_a.y), (vec_p1_b.x, vec_p1_b.y),
                             (vec_p2_b.x, vec_p2_b.y), (vec_p2_a.x, vec_p2_a.y)]
                    pygame.draw.lines(self.win, COL_RESISTOR, True, lines, width=2)
                    x += 1
                vec_band_1 = (vec_c + vec_ac) * (1 / 2)
                vec_band_2 = (vec_c + vec_band_1) * (1 / 2)
                vec_band_3 = vec_c
                vec_band_5 = (vec_c + vec_cb) * (1 / 2)
                vec_band_4 = (vec_c + vec_band_5) * (1 / 2)
                band_vecs = [vec_band_1, vec_band_2, vec_band_3, vec_band_4, vec_band_5]
                x = 0
                while x <= 4:
                    band_colour = wire.convert(colours=True)[x]
                    vec = band_vecs[x]
                    vec_p1 = vec + vec_perpendicular * 10
                    vec_p2 = vec - vec_perpendicular * 10
                    pygame.draw.line(self.win, band_colour, (vec_p1.x, vec_p1.y), (vec_p2.x, vec_p2.y), width=2)
                    x += 1
            collide_checker = wire_rect.copy()
            collide_checker.topleft = tuple(map(sum, zip(wire_rect.topleft, self.pos)))
            keys_pressed = pygame.key.get_pressed()
            if collide_checker.collidepoint(pygame.mouse.get_pos()) and keys_pressed[pygame.K_LSHIFT]:
                if not len(self.env.query_disable) or wire in self.env.query_disable:
                    if wire not in self.env.query_disable:
                        self.env.query_disable.append(wire)
                    pygame.draw.line(self.win, COL_SELECTED, a_real_center, b_real_center, width=4)
                    if pygame.mouse.get_pressed()[0] and self.incomplete_wire is None:
                        self.env.selected = wire
            else:
                if wire in self.env.query_disable:
                    self.env.query_disable.remove(wire)
            if self.env.selected == wire:
                colour_selection.clear()
                colour_rect = pygame.Rect(wire_rect.bottomright, (370, 120))
                colour_selection.append(colour_rect)
                real_colour_rect = colour_rect.copy()
                real_colour_rect.topleft = tuple(map(sum, zip(colour_rect.topleft, self.pos)))
                pygame.draw.line(self.win, COL_SELECTED, a_real_center, b_real_center, width=4)
                accumulated = 10
                for colour in colours:
                    top_left = (colour_rect.x + accumulated, colour_rect.y + self.colour_text.get_height() + 10)
                    specific_colour = pygame.Rect(top_left, (40, 40))
                    colour_selection.append(specific_colour)
                    real = specific_colour.copy()
                    real.topleft = tuple(map(sum, zip(specific_colour.topleft, self.pos)))
                    if real.collidepoint(pygame.mouse.get_pos()):
                        if specific_colour not in self.env.query_disable:
                            self.env.query_disable.append(specific_colour)
                        if pygame.mouse.get_pressed()[0]:
                            wire.colour = colour
                    else:
                        if specific_colour in self.env.query_disable:
                            self.env.query_disable.remove(specific_colour)
                    accumulated += 50
                resistance_change = pygame.Rect(colour_rect.x + 10, colour_rect.y + self.colour_text.get_height() + 60,
                                                self.resist_text.get_width() + 20, 30)
                colour_selection.append(resistance_change)
                real = resistance_change.copy()
                real.topleft = tuple(map(sum, zip(resistance_change.topleft, self.pos)))
                if real.collidepoint(pygame.mouse.get_pos()):
                    if resistance_change not in self.env.query_disable:
                        self.env.query_disable.append(resistance_change)
                    if pygame.mouse.get_pressed()[0]:
                        quick = Tk()
                        quick.title("Choose resistance")
                        quick.geometry("200x70")
                        quick.eval('tk::PlaceWindow . center')
                        variable = StringVar(quick)
                        variable.set(wire.convert())
                        w = OptionMenu(quick, variable, *wire.resistances.keys())
                        w.pack()
                        Button(quick, text="Done", command=quick.destroy).pack()
                        quick.mainloop()
                        wire.resistance = wire.convert(x=variable.get())
                        self.change_made()
                else:
                    if resistance_change in self.env.query_disable:
                        self.env.query_disable.remove(resistance_change)
                colour_selection.append(wire)
                if wire.resistance != 0:
                    wire.colour = COL_IC_PIN
        for coord in self.boards:
            element = self.boards[coord]
            from logic.parts import Breadboard, LED
            if not isinstance(element, Breadboard):
                continue
            for plugin in element.plugins:
                plugin_obj = element.plugins[plugin]
                if isinstance(plugin_obj, LED) and not plugin_obj.cathode_connecting:
                    parent_scale = temp_positions[element][0]
                    parent_real = temp_positions[element][2]
                    anode_point = plugin_obj.anode_point.rect.center
                    anode_point = tuple(map(lambda i, j, k: (i * j) + k, anode_point, parent_scale, parent_real))
                    parent_scale = temp_positions[plugin_obj.cathode_point.parent][0]
                    parent_real = temp_positions[plugin_obj.cathode_point.parent][2]
                    cathode_point = plugin_obj.cathode_point.rect.center
                    cathode_point = tuple(map(lambda i, j, k: (i * j) + k, cathode_point, parent_scale, parent_real))
                    pygame.draw.line(self.win, COL_IC_PIN, anode_point, cathode_point, width=4)
            self.draw_scaled_big(self.win, element, coord, True, led_only=True)

        if len(colour_selection):
            for index, rect in enumerate(colour_selection):
                if index == 0:
                    pygame.draw.rect(self.win, COL_HOME_SHADOW, rect)
                    self.win.blit(self.colour_text, (rect.x + 10, rect.y + 5))
                    continue
                if index == len(colour_selection) - 1:
                    continue
                if index == len(colour_selection) - 2:
                    pygame.draw.rect(self.win, COL_HOME_TITLE, rect)
                    pos = self.win.blit(self.resist_text, (rect.x + 10, rect.y + 5))
                    current = f"Current: {colour_selection[-1].convert()} ohms"
                    current = self.wire_colour_handler.render(current, colour=COL_BLACK)
                    self.win.blit(current, (pos.right + 20, pos.y))
                    continue
                pygame.draw.rect(self.win, colours[index-1], rect)
                if colour_selection[-1].colour == colours[index-1]:
                    pygame.draw.line(self.win, COL_HOME_SHADOW, rect.topleft, rect.bottomright, width=4)
                    pygame.draw.line(self.win, COL_HOME_SHADOW, rect.topright, rect.bottomleft, width=4)

        return self.win


class Occupier:

    def __init__(self, parent_coord):
        self.parent_coord = parent_coord
