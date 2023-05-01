import math
import os.path
import time

import pygame.image
import xml.etree.ElementTree as Et

from runtime.environment import Environment
from _elementtree import ParseError
from ui.interface import List, ListItem
from ui.colours import *


def parse(xml_path):
    try:

        parts_xml = Et.parse(xml_path)

        root = parts_xml.getroot()
        parts_tree = root.findall("part")
        boards, ics, electronics = {}, {}, {}

        for part in parts_tree:

            try:
                part_name = part.find("name").text
                part_desc = part.find("desc").text
                part_picture = part.find("picture").text
                part_texture = part.find("texture").text
                part_type = part.attrib.get("type")
                part_uid = part.attrib.get("uid")

                if part_type == "board":
                    board_config = part.find("boardConfig")
                    size = board_config.find("size").text
                    size = tuple(int(i) for i in size.split('x'))
                    rows = int(board_config.find("rows").text)
                    columns = board_config.find("columns")
                    points = board_config.find("points")
                    points_per_col = int(points.find("perColumn").text)
                    distance = int(points.find("distance").text)
                    radius = int(points.find("radius").text)
                    start = tuple(int(i) for i in points.find("start").text.split(","))
                    row_gap = int(points.find("rowGap").text)
                    points = (points_per_col, distance, radius, start, row_gap)
                    columns = int(columns.text)
                    board = (part_name, part_desc, part_texture, part_picture, size, rows, columns, points), \
                        Breadboard
                    boards[part_uid] = board

                # TODO: Other part types

            except TypeError:
                continue

        return boards, ics, electronics

    except (AttributeError, ParseError):
        return None, None, None


class PartManager:

    def __init__(self, title, desc, parts, project, small_title=None):
        self.title = title
        self.small_title = title if small_title is None else small_title
        self.desc = desc
        self.project = project
        self.parts = parts if parts is not None else {}

    def find(self, uid):
        if self.parts[uid] is not None:
            return self.parts[uid]
        return None

    def create_list(self, size, pos, real_pos):
        part_list = List(size, self.title, self.desc, pos, real_pos, small_title=self.small_title)
        for part in self.parts:
            conf = self.parts[part][0]
            list_item = ListItem(part_list.size, conf[0], conf[3], conf[1], part, self)
            part_list.list_items.append(list_item)
        return part_list


class Part:

    BOARD_DESC = "Breadboards are plastic holed boards in which electronic components can be inserted and connected " \
                 "with jumper wires for prototyping and experimenting with circuits. After testing, components " \
                 "can be easily re-wired."
    IC_DESC = "Integrated circuits (ICs) are small electronic devices that contain interconnected electronic " \
              "components on a single chip of semiconductor material, allowing for small, efficient devices that can " \
              "perform logic, such as mathematics."
    ELECTRONICS_DESC = "Electrical components, such as resistors, capacitors, diodes, and transistors, are basic " \
                       "building blocks used in electronic circuits to control the flow of electricity and create " \
                       "complex circuits that perform specific functions."

    def __init__(self, name, desc, texture, preview_texture):
        path = Environment().get_main_path()
        self.name = name
        self.desc = desc
        self.texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', texture))
        self.texture = self.texture.convert_alpha()
        self.preview_texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', preview_texture))
        self.preview_texture = self.preview_texture.convert_alpha()


class Breadboard(Part):

    def __init__(self, name, desc, texture, preview_texture, size, rows, columns, points):
        super().__init__(name, desc, texture, preview_texture)
        self.size = size
        self.rows = rows
        self.columns = columns
        self.points_per_col = points[0]
        self.distance = points[1]
        self.radius = points[2]
        self.start = points[3]
        self.row_gap = points[4]
        self.rects = {}
        for row in range(self.rows):
            row_y = row*(self.row_gap + (self.points_per_col-1)*self.distance)
            for column in range(self.columns):
                column_x = self.start[0] + self.distance*column
                for point in range(self.points_per_col):
                    point_y = row_y + self.start[1] + self.distance*point
                    square_sides = self.distance
                    rect = pygame.Rect(column_x-(square_sides/2), point_y-(square_sides/2), square_sides, square_sides)
                    self.rects[(row, column, point)] = rect

    def surface(self, real_pos, scale):
        surface = self.texture.copy()
        if not len(pygame.query_disable):
            surface_rect = self.texture.get_rect().copy()
            surface_rect.w *= scale[0]
            surface_rect.h *= scale[1]
            surface_rect.topleft = real_pos
            if surface_rect.collidepoint(pygame.mouse.get_pos()):
                for rect in self.rects:
                    r = self.rects[rect].copy()
                    real_r_pos = tuple(map(sum, zip(real_pos, (r.x*scale[0], r.y*scale[1]))))
                    r.w *= scale[0]
                    r.h *= scale[1]
                    r.topleft = real_r_pos
                    if r.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(surface, COL_BLACK, self.rects[rect])
        return surface









