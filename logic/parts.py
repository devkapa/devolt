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


def get_common_conductor(discriminator, group):
    for conductor in group.conductors:
        valid_discriminators = []
        for i in range(4):
            digit = conductor.discriminator[i]
            valid_discriminators.append(discriminator[i] == digit or digit is None)
        if all(valid_discriminators):
            return conductor
    return None


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
        RectGroup = namedtuple('RectGroup', 'rects conductors')
        if board_config is None:
            return {}
        rects = {}
        discriminators = []

        for segment in range(2):
            segment_y = board_config.start_coord[1]+(segment*board_config.segment_gap)
            for rep in range(board_config.per_segment_rep_count):
                rep_x = board_config.start_coord[0]+(rep*board_config.per_segment_rep_gap)
                for column in range(board_config.per_segment_columns):
                    column_x = rep_x+(self.inch_tenth*column)
                    for row in range(board_config.per_column_rows):
                        discriminator = (segment if board_config.rule.segment else None,
                                         rep if board_config.rule.repetition else None,
                                         column if board_config.rule.column else None,
                                         row if board_config.rule.row else None)
                        if discriminator not in discriminators:
                            discriminators.append(discriminator)
                        row_y = segment_y+(self.inch_tenth*row)
                        rect_tl = (column_x-(self.inch_tenth/2), row_y-(self.inch_tenth/2))
                        rect_wh = (self.inch_tenth, self.inch_tenth)
                        rect = pygame.Rect(rect_tl, rect_wh)
                        rects[(segment, rep, column, row)] = rect

        conductors = [BreadboardUnifier(discriminator) for discriminator in discriminators]

        return RectGroup(rects, conductors)

    def surface(self, real_pos, scale):
        surface = self.texture
        if not len(self.env.query_disable):
            surface_rect = self.texture.get_rect().copy()
            surface_rect.w *= scale[0]
            surface_rect.h *= scale[1]
            surface_rect.topleft = real_pos
            if surface_rect.collidepoint(pygame.mouse.get_pos()):
                for rect_group in [self.main_board_rects, self.pr_rects]:
                    for rect in rect_group.rects:
                        r = rect_group.rects[rect].copy()
                        real_r_pos = tuple(map(sum, zip(real_pos, (r.x*scale[0], r.y*scale[1]))))
                        r.w *= scale[0]
                        r.h *= scale[1]
                        r.topleft = real_r_pos
                        if r.collidepoint(pygame.mouse.get_pos()):
                            surface = surface.copy()
                            pygame.draw.rect(surface, COL_BLACK, rect_group.rects[rect])
                            print(get_common_conductor(rect, rect_group).discriminator)
        return surface


class BreadboardUnifier(Conductor):

    def __init__(self, discriminator):
        super().__init__()
        self.discriminator = discriminator
