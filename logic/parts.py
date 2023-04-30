import os.path
import pygame.image
import xml.etree.ElementTree as Et

from runtime.environment import Environment
from _elementtree import ParseError
from ui.interface import List, ListItem


def parse(xml_path):
    try:

        parts_xml = Et.parse(xml_path)

        root = parts_xml.getroot()
        parts_tree = root.findall("part")
        boards, ics, electronics = {}, {}, {}

        for part in parts_tree:

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
                points_per_col = int(columns.attrib.get("points"))
                columns = int(columns.text)
                board = (part_name, part_desc, part_texture, part_picture, size, rows, columns, points_per_col), \
                    Breadboard
                boards[part_uid] = board

            # TODO: Other part types

        return boards, ics, electronics

    except (AttributeError, ParseError):
        return None


class PartManager:

    def __init__(self, title, desc, parts, small_title=None):
        self.title = title
        self.small_title = title if small_title is None else small_title
        self.desc = desc
        self.parts = parts

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
        self.preview_texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', preview_texture))


class Breadboard(Part):

    def __init__(self, name, desc, texture, preview_texture, size, rows, columns, points_per_col):
        super().__init__(name, desc, texture, preview_texture)
        self.size = size
        self.rows = rows
        self.columns = columns
        self.points_per_col = points_per_col
