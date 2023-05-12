import os.path

import pygame.image
import xml.etree.ElementTree as Et

from logic.electronics import Node, Source, Sink
from collections import namedtuple
from _elementtree import ParseError
from ui.interface import List, ListItem
from ui.colours import *
from ui.text import TextHandler

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

                if part_type == "ic":
                    ic_config = part.find("icConfig")
                    dip_count = int(ic_config.find("dipCount").text)

                    ic = (part_name, part_desc, part_texture, part_picture, dip_count), \
                        IntegratedCircuit
                    ics[part_uid] = ic

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
    IC_DESC = "Integrated circuits (ICs) are small devices that contain interconnected electronic components on a " \
              f"single chip allowing for small, efficient chips that can perform logic. {' '*170}" \
              "NOTE: You must tie unused inputs on ICs to ground or 5V for the chip to function. In real life, this " \
              "is good practice as to maintain a healthy chip temperature and avoid high-impedance floating inputs, " \
              "which may cause confusing, unexpected logic errors."
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
        self.voltage = voltage
        neg_rail_coord = pos_info.neg_rail
        pos_rail_coord = pos_info.pos_rail
        radius = pos_info.radius
        pos_rect_tl = (pos_rail_coord[0] - radius, pos_rail_coord[1] - radius)
        neg_rect_tl = (neg_rail_coord[0] - radius, neg_rail_coord[1] - radius)
        rect_wh = (radius*2, radius*2)
        self.rects = [pygame.Rect(pos_rect_tl, rect_wh), pygame.Rect(neg_rect_tl, rect_wh)]
        self.points = [BreadboardPoint(self, None, Source(), self.rects[0]),
                       BreadboardPoint(self, None, Sink(), self.rects[1])]

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

    DISCRIMINATOR = namedtuple("Discriminator", "segment rep column row")

    def __init__(self, name, desc, texture, preview_texture, size, inch_tenth, radius, main, power_rail, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.size = size
        self.inch_tenth = inch_tenth
        self.radius = radius
        self.env = env
        self.main_board_config = main
        self.pr_config = power_rail
        self.plugins = {}
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
                        found = None
                        for rail in rails:
                            if rail.rail_discriminator == rail_discrim:
                                found = rail
                        if found is None:
                            found = BreadboardRail(rail_discrim)
                        rails.append(found)
                        row_y = segment_y + (self.inch_tenth * row)
                        rect_tl = (column_x - (self.inch_tenth / 2), row_y - (self.inch_tenth / 2))
                        rect_wh = (self.inch_tenth, self.inch_tenth)
                        rect = pygame.Rect(rect_tl, rect_wh)
                        discriminator = self.DISCRIMINATOR(segment, rep, column, row)
                        point = BreadboardPoint(self, discriminator, found, rect)
                        rects[discriminator] = rect, found, point

        return rects

    def ic_requirements(self, ic_discrim, ic_dips):
        pins_to_nodes = {}
        for i in range(ic_dips):
            if i < ic_dips/2:
                discriminator = (ic_discrim.segment + 1, ic_discrim.rep, ic_discrim.column + i, ic_discrim.row)
            else:
                f_x = i + (ic_dips - 1) - (2 * i)
                discriminator = (ic_discrim.segment, ic_discrim.rep, ic_discrim.column + f_x, ic_discrim.row)
            pins_to_nodes[i] = self.main_board_rects[discriminator][1].uuid
        return pins_to_nodes

    def ic_collision(self, ic_discrim, ic_dips):
        requirements = list(self.ic_requirements(ic_discrim, ic_dips).values())
        for plugin in self.plugins.values():
            if isinstance(plugin, IntegratedCircuit):
                for node_uuid in plugin.pins_to_nodes.values():
                    if node_uuid in requirements:
                        return True
        return False

    def ic_allowed(self, ic, point_hovered):
        discriminator = point_hovered.discriminator
        if discriminator.segment == 0:
            rows = self.main_board_config.per_column_rows
            if discriminator.row == (rows - 1):
                columns = self.main_board_config.per_segment_columns
                if discriminator.column + (ic.dip_count / 2) <= columns:
                    col = self.ic_collision(discriminator, ic.dip_count)
                    return not col
        return False

    def surface(self, real_pos, scale):
        rect_hovered = None
        surface = self.texture.copy()
        for plugin in self.plugins:
            plugin_rect = self.main_board_rects[plugin][0]
            plugin_pos = (plugin_rect.left, plugin_rect.centery)
            surface.blit(self.plugins[plugin].surface(self)[0], plugin_pos)
        incomplete_wire = any(isinstance(x, BreadboardPoint) or isinstance(x, IntegratedCircuit) for x in self.env.query_disable)
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
                            pygame.draw.rect(surface, COL_BLACK, rect_group[coord][0])
        return surface, rect_hovered


class BreadboardPoint:

    def __init__(self, parent, discriminator, common, rect):
        self.parent = parent
        self.discriminator = discriminator
        self.common = common
        self.rect = rect


class BreadboardRail(Node):

    def __init__(self, rail_discriminator):
        super().__init__()
        self.rail_discriminator = rail_discriminator


class PluginPart(Part):

    def __init__(self, name, desc, texture, preview_texture, env):
        super().__init__(name, desc, texture, preview_texture, env)

    def surface(self, hovered_board):
        pass


class IntegratedCircuit(PluginPart):

    def __init__(self, name, desc, texture, preview_texture, dip_count, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.dip_count = dip_count
        self.pins_to_nodes = {}

    def draw(self, inch_tenth, radius, gap):
        win = pygame.Surface(((self.dip_count/2)*inch_tenth, gap+inch_tenth))
        handler = TextHandler(self.env, 'Play-Regular.ttf', radius*4)
        label = handler.render(self.name)
        win.set_colorkey((0, 0, 0))
        rect = pygame.Rect(0, radius, win.get_width(), win.get_height()-(2*radius))
        pygame.draw.rect(win, COL_IC_LID, rect)
        for i in range(self.dip_count):
            if i < self.dip_count/2:
                r = pygame.Rect((inch_tenth/2) - (radius/2) + (inch_tenth*i), win.get_height()-radius, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)
            else:
                r = pygame.Rect((win.get_width() - (inch_tenth / 2)) - (radius/2) - (inch_tenth * (i-(self.dip_count/2))), 0, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)
        win.blit(label, (win.get_width()/2 - label.get_width()/2, win.get_height()/2 - label.get_height()/2))
        return win

    def surface(self, hovered_board):
        if hovered_board is None:
            inch_tenth, radius, gap = 25, 25, 60
        else:
            main_board_config = hovered_board.main_board_config
            inch_tenth, radius = hovered_board.inch_tenth, hovered_board.radius
            gap = main_board_config.segment_gap - (main_board_config.per_column_rows*inch_tenth)
        surface = self.draw(inch_tenth, radius, gap)
        rect_hovered = None
        if hovered_board is not None:
            pass
        return surface, rect_hovered
