import os.path

import pygame.image
import xml.etree.ElementTree as Et

from logic.electronics import Conductor
from collections import namedtuple
from _elementtree import ParseError
from ui.interface import List, ListItem
from ui.colours import *

BoardConfig = namedtuple("BoardConfig", "start_coord segment_gap per_segment_columns per_column_rows "
                                        "per_segment_rep_count per_segment_rep_gap rule")
Rule = namedtuple("Rule", "segment repetition column row")


def get_board_config(element):
    start_coord = tuple(int(i) for i in element.find("startCoord").text.split(","))
    segment_gap = int(element.find("segmentGap").text)
    per_segment_columns = int(element.find("perSegmentColumns").text)
    per_column_rows = int(element.find("perColumnRows").text)
    per_segment_rep = element.find("perSegmentRepetition")
    per_segment_rep_count = int(per_segment_rep.text)
    per_segment_rep_gap = int(per_segment_rep.attrib.get("gap"))
    rule = element.attrib.get("rule").split(",")
    rule = Rule("SEGMENT" in rule, "REPETITION" in rule, "COLUMN" in rule, "ROW" in rule)
    return BoardConfig(start_coord, segment_gap, per_segment_columns, per_column_rows, per_segment_rep_count,
                       per_segment_rep_gap, rule)


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
                    inch_tenth = int(board_config.find("inchTenth").text)
                    radius = int(board_config.find("radius").text)

                    main_board = board_config.find("mainBoard")
                    main_board_config = get_board_config(main_board)

                    power_rails = board_config.find("powerRails")
                    if power_rails is not None:
                        rail_config = get_board_config(power_rails)
                    else:
                        rail_config = None

                    board = (part_name, part_desc, part_texture, part_picture, size, inch_tenth, radius,
                             main_board_config, rail_config), Breadboard

                    boards[part_uid] = board

                if part_type == "supply":
                    power_config = part.find("powerConfig")
                    size = power_config.find("size").text
                    size = tuple(int(i) for i in size.split('x'))
                    radius = int(power_config.find("nodeRadius").text)
                    inch_tenth = int(power_config.find("inchTenth").text)
                    voltage = int(power_config.find("voltage").text)
                    pos_node = power_config.find("posNodeCoord").text
                    pos_node = tuple(int(i) for i in pos_node.split(','))
                    neg_node = power_config.find("negNodeCoord").text
                    neg_node = tuple(int(i) for i in neg_node.split(','))

                    SupplyInfo = namedtuple("SupplyInfo", "pos_rail neg_rail radius")
                    pos_info = SupplyInfo(pos_node, neg_node, radius)

                    supply = (part_name, part_desc, part_texture, part_picture, size, voltage, pos_info, inch_tenth), \
                        PowerSupply
                    electronics[part_uid] = supply

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

    def create_list(self, size, pos, real_pos, env):
        part_list = List(size, self.title, self.desc, pos, real_pos, env, small_title=self.small_title)
        for part in self.parts:
            conf = self.parts[part][0]
            list_item = ListItem(part_list.size, conf[0], conf[3], conf[1], part, self, env)
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

    def __init__(self, name, desc, texture, preview_texture, env):
        path = env.get_main_path()
        self.name = name
        self.desc = desc
        self.texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', texture))
        self.texture = self.texture.convert_alpha()
        self.preview_texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', preview_texture))
        self.preview_texture = self.preview_texture.convert_alpha()
        self.env = env


class PowerSupply(Part):

    def __init__(self, name, desc, texture, preview_texture, size, voltage, pos_info, inch_tenth, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.size = size
        self.inch_tenth = inch_tenth
        voltage = voltage
        neg_rail_coord = pos_info.neg_rail
        pos_rail_coord = pos_info.pos_rail
        radius = pos_info.radius
        pos_rect_tl = (pos_rail_coord[0] - radius, pos_rail_coord[1] - radius)
        neg_rect_tl = (neg_rail_coord[0] - radius, neg_rail_coord[1] - radius)
        rect_wh = (radius*2, radius*2)
        self.rects = [pygame.Rect(pos_rect_tl, rect_wh), pygame.Rect(neg_rect_tl, rect_wh)]
        self.points = [BreadboardPoint(self, None, Conductor(voltage=voltage), self.rects[0]),
                       BreadboardPoint(self, None, Conductor(), self.rects[1])]

    def surface(self, real_pos, scale):
        rect_hovered = None
        surface = self.texture
        incomplete_wire = any(isinstance(x, BreadboardPoint) for x in self.env.query_disable)
        if not len(self.env.query_disable) or incomplete_wire:
            for i, rect in enumerate(self.rects):
                r = rect.copy()
                real_r_pos = tuple(map(sum, zip(real_pos, (r.x * scale[0], r.y * scale[1]))))
                r.w *= scale[0]
                r.h *= scale[1]
                r.topleft = real_r_pos
                if r.collidepoint(pygame.mouse.get_pos()):
                    rect_hovered = self.points[i]
                    surface = surface.copy()
                    pygame.draw.rect(surface, COL_BLACK, rect)
        return surface, rect_hovered


class Breadboard(Part):

    def __init__(self, name, desc, texture, preview_texture, size, inch_tenth, radius, main, power_rail, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.size = size
        self.inch_tenth = inch_tenth
        self.radius = radius
        self.env = env
        self.main_board_rects = self.create_rects(main)
        self.pr_rects = self.create_rects(power_rail)

    def create_rects(self, board_config):
        if board_config is None:
            return {}
        rects = {}
        rails = []

        for segment in range(2):
            segment_y = board_config.start_coord[1] + (segment * board_config.segment_gap)
            for rep in range(board_config.per_segment_rep_count):
                rep_x = board_config.start_coord[0] + (rep * board_config.per_segment_rep_gap)
                for column in range(board_config.per_segment_columns):
                    column_x = rep_x + (self.inch_tenth * column)
                    for row in range(board_config.per_column_rows):
                        rail_discrim = (segment if board_config.rule.segment else None,
                                        rep if board_config.rule.repetition else None,
                                        column if board_config.rule.column else None,
                                        row if board_config.rule.row else None)
                        if rail_discrim in rails:
                            common_conductor = [rail for rail in rails if rail == rail_discrim][0]
                        else:
                            common_conductor = BreadboardRail(rail_discrim)
                        row_y = segment_y + (self.inch_tenth * row)
                        rect_tl = (column_x - (self.inch_tenth / 2), row_y - (self.inch_tenth / 2))
                        rect_wh = (self.inch_tenth, self.inch_tenth)
                        rect = pygame.Rect(rect_tl, rect_wh)
                        discriminator = (segment, rep, column, row)
                        point = BreadboardPoint(self, discriminator, common_conductor, rect)
                        rects[discriminator] = rect, common_conductor, point

        return rects

    def surface(self, real_pos, scale):
        rect_hovered = None
        surface = self.texture
        incomplete_wire = any(isinstance(x, BreadboardPoint) for x in self.env.query_disable)
        if not len(self.env.query_disable) or incomplete_wire:
            surface_rect = self.texture.get_rect().copy()
            surface_rect.w *= scale[0]
            surface_rect.h *= scale[1]
            surface_rect.topleft = real_pos
            if surface_rect.collidepoint(pygame.mouse.get_pos()):
                for rect_group in [self.main_board_rects, self.pr_rects]:
                    for coord in rect_group:
                        r = rect_group[coord][0].copy()
                        real_r_pos = tuple(map(sum, zip(real_pos, (r.x * scale[0], r.y * scale[1]))))
                        r.w *= scale[0]
                        r.h *= scale[1]
                        r.topleft = real_r_pos
                        if r.collidepoint(pygame.mouse.get_pos()):
                            rect_hovered = rect_group[coord][2]
                            surface = surface.copy()
                            pygame.draw.rect(surface, COL_BLACK, rect_group[coord][0])
        return surface, rect_hovered


class BreadboardPoint:

    def __init__(self, parent, discriminator, common, rect):
        self.parent = parent
        self.discriminator = discriminator
        self.common = common
        self.rect = rect


class BreadboardRail(Conductor):

    def __init__(self, rail_discriminator):
        super().__init__()
        self.rail_discriminator = rail_discriminator

    def __eq__(self, other):
        return self.rail_discriminator == other
