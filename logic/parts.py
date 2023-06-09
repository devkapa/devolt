import math
import os.path
import textwrap

import pygame.image
import xml.etree.ElementTree as Et

from logic.electronics import Node, Sink
from collections import namedtuple
from _elementtree import ParseError
from ui.interface import List, ListItem
from ui.colours import *
from ui.text import TextHandler


# Named tuples for readable code
BoardConfig = namedtuple("BoardConfig", "start_coord segment_gap per_segment_columns per_column_rows "
                                        "per_segment_rep_count per_segment_rep_gap rule")
Rule = namedtuple("Rule", "segment repetition column row")
SupplyInfo = namedtuple("SupplyInfo", "pos_rail neg_rail radius")
Discriminator = namedtuple("Discriminator", "segment rep column row name")


# Input an XML element and return a named tuple with extracted information about a breadboard
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


# Parse the part XML file and create Part objects for each entry
def parse(xml_path):
    try:

        # Create an object tree of the XML
        parts_xml = Et.parse(xml_path)

        # Get the parent root
        root = parts_xml.getroot()
        parts_tree = root.findall("part")
        boards, ics, electronics = {}, {}, {}

        for part in parts_tree:

            try:
                # Get the name, description, name of textures, type and identifier of each element
                part_name = part.find("name").text
                part_desc = part.find("desc").text
                part_picture = part.find("picture").text
                part_texture = part.find("texture").text
                part_type = part.attrib.get("type")
                part_uid = part.attrib.get("uid")

                # If the part is a board, add it to the boards list
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

                # If the part is a power supply, add it to the electronics list
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

                    pos_info = SupplyInfo(pos_node, neg_node, radius)

                    supply = (part_name, part_desc, part_texture, part_picture, size, voltage, pos_info, inch_tenth), \
                        PowerSupply
                    electronics[part_uid] = supply

                # If the part is an IC, add it to the IC list
                if part_type == "ic":
                    ic_config = part.find("icConfig")
                    dip_count = int(ic_config.find("dipCount").text)
                    raw_spice = textwrap.dedent(ic_config.find("rawSpice").text)
                    spice_nodes = tuple(ic_config.find("spiceNodes").text.split(" "))
                    datasheet = ic_config.find("datasheet").text

                    ic = (part_name, part_desc, part_texture, part_picture, dip_count, raw_spice, spice_nodes,
                          datasheet), IntegratedCircuit
                    ics[part_uid] = ic

                # If the part is an LED, add it to the electronics list
                if part_type == "led":
                    led_config = part.find("ledConfig")
                    on_colour = tuple(int(i) for i in led_config.find("onColour").text.split(','))
                    off_colour = tuple(int(i) for i in led_config.find("offColour").text.split(','))

                    led = (part_name, part_desc, part_texture, part_picture, on_colour, off_colour), \
                        LED
                    electronics[part_uid] = led

                # If the part is a switch, add it to the electronics list
                if part_type == "switch":
                    switch_config = part.find("switchConfig")
                    dip_count = int(switch_config.find("dipCount").text)
                    spice_nodes = tuple(switch_config.find("spiceNodes").text.split(" "))
                    datasheet = switch_config.find("datasheet").text
                    latch = int(switch_config.attrib.get("latch"))

                    ele = (part_name, part_desc, part_texture, part_picture, dip_count, "", spice_nodes,
                           latch, datasheet), Switch
                    electronics[part_uid] = ele

            except TypeError:
                continue

        return boards, ics, electronics

    except (AttributeError, ParseError):
        return None, None, None


class PartManager:
    """The PartManager structure holds every part in a category, to be used in creating UI Lists"""

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
    """A base class for any part that can be placed in the editor space"""

    BOARD_DESC = "Breadboards are plastic holed boards in which electronic components can be inserted and connected " \
                 "with jumper wires for experimenting with circuits. To connect jumper wires, simply click on a " \
                 "breadboard or power supply hole and drag the new wire to your desired point."
    IC_DESC = "Integrated circuits (ICs) are small devices that contain interconnected electronic components on a " \
              f"single chip allowing for small, efficient chips that can perform logic. {' '*170}" \
              "NOTE: You must tie unused inputs on ICs to ground or 5V for de:volt simulation to function. This " \
              "practice encourages you to maintain healthy chip temperature and avoid high-impedance floating " \
              "inputs, which may cause confusing, unexpected logic errors in real life circuitry."
    ELECTRONICS_DESC = "Electrical components, such as resistors and diodes, are basic " \
                       "building blocks used in electronic circuits to control the flow of electricity and create " \
                       f"complex circuits that perform specific functions. {' '*120}NOTE: To make a resistor, draw a " \
                       "wire normally, then select it to choose a resistance."

    # Initialising the class with any necessary attributes for any part type
    def __init__(self, name, desc, texture, preview_texture, env):
        path = env.get_main_path()
        self.name = name
        self.desc = desc
        self.texture_name, self.preview_texture_name = texture, preview_texture
        self.texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', texture))
        self.texture = self.texture.convert_alpha()
        self.preview_texture = pygame.image.load(os.path.join(path, 'assets', 'textures', 'parts', preview_texture))
        self.preview_texture = self.preview_texture.convert_alpha()
        self.env = env


class PowerSupply(Part):
    """The Power Supply contains two breadboard-type nodes that represent a positive and negative electrical terminal"""

    def __init__(self, name, desc, texture, preview_texture, size, voltage, pos_info, inch_tenth, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.size = size
        self.inch_tenth = inch_tenth
        self.voltage = voltage
        self.pos_info = pos_info
        neg_rail_coord = pos_info.neg_rail
        pos_rail_coord = pos_info.pos_rail
        radius = pos_info.radius
        pos_rect_tl = (pos_rail_coord[0] - radius, pos_rail_coord[1] - radius)
        neg_rect_tl = (neg_rail_coord[0] - radius, neg_rail_coord[1] - radius)
        rect_wh = (radius*2, radius*2)
        self.rects = [pygame.Rect(pos_rect_tl, rect_wh), pygame.Rect(neg_rect_tl, rect_wh)]
        self.points = [BreadboardPoint(self, Discriminator(0, 0, 0, 1, "main"), Node(), self.rects[0]),
                       BreadboardPoint(self, Discriminator(0, 0, 0, 0, "main"), Sink(), self.rects[1])]

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.name, self.desc, self.texture_name, self.preview_texture_name, self.size, self.voltage, \
            self.pos_info, self.inch_tenth

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__init__(*state, pygame.env)

    # Return a surface containing the power supply texture
    def surface(self, real_pos, scale):
        rect_hovered = None
        surface = self.texture.copy()
        incomplete_wire = any(isinstance(x, BreadboardPoint) for x in self.env.query_disable)
        if not len(self.env.query_disable) or incomplete_wire:
            surface_rect = surface.get_rect().copy()
            surface_rect.w *= scale[0]
            surface_rect.h *= scale[1]
            surface_rect.topleft = real_pos
            if surface_rect.collidepoint(pygame.mouse.get_pos()):
                for i, rect in enumerate(self.rects):
                    r = rect.copy()
                    real_r_pos = tuple(map(sum, zip(real_pos, (r.x * scale[0], r.y * scale[1]))))
                    r.w *= scale[0]
                    r.h *= scale[1]
                    r.topleft = real_r_pos
                    if r.collidepoint(pygame.mouse.get_pos()):
                        rect_hovered = self.points[i]
                        pygame.draw.rect(surface, COL_BLACK, rect)
                pygame.draw.rect(surface, COL_SELECTED, self.texture.get_rect(), width=math.floor(2 / scale[0]))
                if pygame.mouse.get_pressed()[0] and rect_hovered is None and not incomplete_wire:
                    self.env.selected = self
        if self.env.selected == self:
            pygame.draw.rect(surface, COL_SELECTED, self.texture.get_rect(), width=math.floor(4 / scale[0]))
        return surface, rect_hovered


class Breadboard(Part):
    """A breadboard structure contains a large array of breadboard points that can be interfaced with to connect
    electronics together, and place wires onto for prototypical simulation"""

    def __init__(self, name, desc, texture, preview_texture, size, inch_tenth, radius, main, power_rail, env, plugins=None):
        super().__init__(name, desc, texture, preview_texture, env)
        self.size = size
        self.inch_tenth = inch_tenth
        self.radius = radius
        self.env = env
        self.main_board_config = main
        self.pr_config = power_rail
        self.plugins = {} if plugins is None else plugins
        self.main_board_rects, self.main_rails = self.create_rects(main, "main")
        self.pr_rects, self.pr_rails = self.create_rects(power_rail, "power")
        self.plain_surface = pygame.Surface(self.texture.get_size())
        self.drawing_surface = self.texture.copy()

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.name, self.desc, self.texture_name, self.preview_texture_name, self.size, self.inch_tenth, \
            self.radius, self.main_board_config, self.pr_config, self.plugins

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__init__(*state[:-1], pygame.env, plugins=state[-1])
        self.rejuvenate()

    # For every plugin in the breadboard, update the references such that when loaded from a save state,
    # the plugin correctly simulates a connection between regenerated breadboard points
    def rejuvenate(self):
        for plugin in self.plugins:
            plugin_obj = self.plugins[plugin]
            if isinstance(plugin_obj, IntegratedCircuit):
                new_reqs = self.ic_requirements(plugin.discriminator, plugin_obj.dip_count)
                plugin_obj.pins_to_nodes = new_reqs
            if isinstance(plugin_obj, LED):
                old_anode_group = plugin_obj.anode_point.discriminator.name
                group_1 = None
                if old_anode_group == "main":
                    group_1 = self.main_board_rects
                elif old_anode_group == "power":
                    group_1 = self.pr_rects
                old_cathode_group = plugin_obj.cathode_point.discriminator.name
                group_2 = None
                if old_cathode_group == "main":
                    group_2 = self.main_board_rects
                elif old_cathode_group == "power":
                    group_2 = self.pr_rects
                plugin_obj.anode_point = group_1[plugin_obj.anode_point.discriminator][2]
                plugin_obj.cathode_point = group_2[plugin_obj.cathode_point.discriminator][2]

    # Given a config, generate the correct number of breadboard points which the breadboard should contain
    def create_rects(self, board_config, name):
        if board_config is None:
            return {}, ""
        rects = {}
        rails = []

        # Two segments of a breadboard, separated by DIP support
        for segment in range(2):

            segment_y = board_config.start_coord[1] + (segment * board_config.segment_gap)

            # Inline repetitions of a segment
            for rep in range(board_config.per_segment_rep_count):

                rep_x = board_config.start_coord[0] + (rep * board_config.per_segment_rep_gap)

                # Vertical columns of breadboard points
                for column in range(board_config.per_segment_columns):

                    column_x = rep_x + (self.inch_tenth * column)

                    # Horizontal rows of breadboard points
                    for row in range(board_config.per_column_rows):

                        # Calculate the relation rule of the breadboard rail (how are they connected)
                        rail_discrim = (segment if board_config.rule.segment else None,
                                        rep if board_config.rule.repetition else None,
                                        column if board_config.rule.column else None,
                                        row if board_config.rule.row else None)

                        # Check if the rail already exists
                        found = None
                        for rail in rails:
                            if rail.rail_discriminator == rail_discrim:
                                found = rail
                        if found is None:
                            found = BreadboardRail(rail_discrim)
                            rails.append(found)

                        # Create a rect and a breadboard point
                        row_y = segment_y + (self.inch_tenth * row)
                        rect_tl = (column_x - (self.inch_tenth / 2), row_y - (self.inch_tenth / 2))
                        rect_wh = (self.inch_tenth, self.inch_tenth)
                        rect = pygame.Rect(rect_tl, rect_wh)
                        discriminator = Discriminator(segment, rep, column, row, name)
                        point = BreadboardPoint(self, discriminator, found, rect)

                        # Store
                        rects[discriminator] = rect, found, point

        return rects, rails

    # Calculate the amount of points required by an IC to fit on the breadboard
    def ic_requirements(self, ic_discrim, ic_dips):
        pins_to_nodes = {}
        for i in range(ic_dips):
            if i < ic_dips/2:
                discriminator = (ic_discrim.segment + 1, ic_discrim.rep, ic_discrim.column + i, ic_discrim.row, ic_discrim.name)
            else:
                f_x = i + (ic_dips - 1) - (2 * i)
                discriminator = (ic_discrim.segment, ic_discrim.rep, ic_discrim.column + f_x, ic_discrim.row, ic_discrim.name)
            pins_to_nodes[i] = self.main_board_rects[discriminator][1]
        return pins_to_nodes

    # Check if an IC will collide with other elements on a breadboard given the coordinate
    def ic_collision(self, ic_discrim, ic_dips):
        requirements = [i.uuid for i in self.ic_requirements(ic_discrim, ic_dips).values()]
        for plugin in self.plugins.values():
            if isinstance(plugin, IntegratedCircuit):
                for node in plugin.pins_to_nodes.values():
                    if node.uuid in requirements:
                        return True
        return False

    # Check if an IC is allowed to sit on a row of breadboard points given the coordinate
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

    # Convert from a position to a coordinate and scale
    def point_to_coord(self, real_pos, point, scale):
        for rect_group in [self.main_board_rects, self.pr_rects]:
            for coord in rect_group:
                p = rect_group[coord][2]
                if p == point:
                    r = rect_group[coord][0].copy()
                    real_r_pos = tuple(map(sum, zip(real_pos, (r.centerx * scale[0], r.centery * scale[1]))))
                    return real_r_pos
        return 0, 0

    # Return a surface that only contains the LED bulb heads
    def surface_led(self):
        surface = self.plain_surface.copy()
        surface.set_colorkey((0, 0, 0))
        for plugin in self.plugins:
            plugin_obj = self.plugins[plugin]
            if isinstance(plugin_obj, LED):
                plugin_rect = plugin.rect
                plugin_surf = plugin_obj.surface(self)[0]
                plugin_size = plugin_surf.get_width(), plugin_surf.get_height()
                plugin_pos = (plugin_rect.centerx - plugin_size[0] / 2, plugin_rect.centery - plugin_size[1] / 2)
                surface.blit(plugin_surf, plugin_pos)
        return surface

    # Return a surface that contains all plugin parts on the part texture
    def surface(self, real_pos, scale):

        rect_hovered = None

        # Prepare the surface
        self.texture.blit(self.drawing_surface, (0, 0))
        surface = self.texture

        # Draw plugins
        incomplete_wire = any(isinstance(x, BreadboardPoint) or isinstance(x, PluginPart) for x in self.env.query_disable)
        for plugin in self.plugins:

            # Prepare plugin surface
            plugin_obj = self.plugins[plugin]
            plugin_rect = plugin.rect
            plugin_surf = plugin_obj.surface(self)[0]
            plugin_size = plugin_surf.get_width(), plugin_surf.get_height()

            # Snap plugin to center if it is an Integrated Circuit
            if isinstance(plugin_obj, IntegratedCircuit):
                plugin_pos = (plugin_rect.left, plugin_rect.centery)
            else:
                plugin_pos = (plugin_rect.centerx - plugin_size[0]/2, plugin_rect.centery - plugin_size[1]/2)

            # Draw plugin
            surface.blit(plugin_surf, plugin_pos)

            # Check if the plugin is hovered with the mouse
            if not len(self.env.query_disable) or self.env.query_disable == [plugin_rect]:
                scaled_topleft = tuple(map(lambda i, j, k: (i*j)+k, plugin_pos, scale, real_pos))
                plugin_surf_rect = plugin_surf.get_rect(topleft=scaled_topleft)
                plugin_surf_rect.w *= scale[0]
                plugin_surf_rect.h *= scale[1]
                if plugin_surf_rect.collidepoint(pygame.mouse.get_pos()):
                    if plugin_rect not in self.env.query_disable:
                        self.env.query_disable.append(plugin_rect)
                    pygame.draw.rect(surface, COL_SELECTED, plugin_surf.get_rect(topleft=plugin_pos), width=math.floor(2 / scale[0]))
                    if pygame.mouse.get_pressed()[0]:
                        if incomplete_wire is False:
                            plugin_obj.deletion_key = self, plugin
                            self.env.selected = plugin_obj
                else:
                    if plugin_rect in self.env.query_disable:
                        self.env.query_disable.remove(plugin_rect)

            # If there is a volatile switch that is not pressed, make sure it is off
            if not pygame.mouse.get_pressed()[0]:
                if isinstance(plugin_obj, Switch):
                    if not plugin_obj.latch:
                        plugin_obj.state = 0

            # Draw an outline if the plugin is selected
            if self.env.selected == plugin_obj:
                pygame.draw.rect(surface, COL_SELECTED, plugin_surf.get_rect(topleft=plugin_pos), width=math.floor(4 / scale[0]))

        # Check if the breadboard is hovered
        if not len(self.env.query_disable) or incomplete_wire:

            surface_rect = self.texture.get_rect().copy()
            surface_rect.w *= scale[0]
            surface_rect.h *= scale[1]
            surface_rect.topleft = real_pos

            # Find a hovered point
            for rect_group in [self.main_board_rects, self.pr_rects]:
                for coord in rect_group:
                    pygame.draw.circle(surface, COL_BREADBOARD_HOLE, rect_group[coord][0].center, self.radius)
                    if surface_rect.collidepoint(pygame.mouse.get_pos()):
                        r = rect_group[coord][0].copy()
                        real_r_pos = tuple(map(sum, zip(real_pos, (r.x * scale[0], r.y * scale[1]))))
                        r.w *= scale[0]
                        r.h *= scale[1]
                        r.topleft = real_r_pos
                        if r.collidepoint(pygame.mouse.get_pos()):
                            rect_hovered = rect_group[coord][2]
                            pygame.draw.rect(surface, COL_BLACK, rect_group[coord][0])

            # Draw an outline around breadboard if hovered
            if surface_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, COL_SELECTED, self.texture.get_rect(), width=2)
                if pygame.mouse.get_pressed()[0] and rect_hovered is None and not incomplete_wire:
                    self.env.selected = self

        # Draw an outline around breadboard if selected
        if self.env.selected == self:
            pygame.draw.rect(surface, COL_SELECTED, self.texture.get_rect(), width=4)

        return surface, rect_hovered


class BreadboardPoint:
    """A structure denoting an individual point on a breadboard, which may be common to a rail"""

    def __init__(self, parent, discriminator, common, rect):
        self.parent = parent
        self.discriminator = discriminator
        self.common = common
        self.rect = rect


class BreadboardRail(Node):
    """A structure denoting a set of points on a breadboard that are electrically connected"""

    def __init__(self, rail_discriminator):
        super().__init__()
        self.rail_discriminator = rail_discriminator


class PluginPart(Part):
    """A type of part which must be plugged into a breadboard"""

    def __init__(self, name, desc, texture, preview_texture, env):
        super().__init__(name, desc, texture, preview_texture, env)
        self.deletion_key = None

    def surface(self, hovered_board):
        pass


class LED(PluginPart):
    """The LED is a structure containing details about where the positive and negative terminals are connected, the
    colour of the light, if the light is functioning and its state"""

    def __init__(self, name, desc, texture, preview_texture, on_colour, off_colour, env, anode_point=None, cathode_point=None):
        super().__init__(name, desc, texture, preview_texture, env)
        self.state = 0
        self.on_colour = on_colour
        self.off_colour = off_colour
        self.cathode_connecting = False
        self.anode_point = anode_point
        self.cathode_point = cathode_point
        self.alive = True

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.name, self.desc, self.texture_name, self.preview_texture_name, self.on_colour, self.off_colour, self.anode_point, self.cathode_point

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__init__(*state[:-2], pygame.env, anode_point=state[-2], cathode_point=state[-1])

    # Draw the LED
    def surface(self, hovered_board):

        inch_tenth = hovered_board.inch_tenth

        # Prepare the surface
        surface = pygame.Surface((inch_tenth*2, inch_tenth*2))
        surface.set_colorkey((0, 0, 0))

        # Draw the bulb
        pygame.draw.circle(surface, self.off_colour, surface.get_rect().center, inch_tenth)

        # If it is dead, draw an X on it
        if not self.alive:
            pygame.draw.line(surface, COL_FAKE_BLACK, (0, 0), (inch_tenth*2, inch_tenth*2), width=10)
            pygame.draw.line(surface, COL_FAKE_BLACK, (inch_tenth*2, 0), (0, inch_tenth*2), width=10)

        # Otherwise if it is on, draw the light
        elif self.state:
            pygame.draw.circle(surface, self.on_colour, surface.get_rect().center, math.floor(3*(inch_tenth/4)))

        return surface, None


class IntegratedCircuit(PluginPart):
    """The integrated circuit is a structure containing the number of points it occupies, the related subcircuit
    raw SPICE data and any relevant documentation."""

    def __init__(self, name, desc, texture, preview_texture, dip_count, raw_spice, spice_nodes, datasheet_img, env, pin_map=None):
        super().__init__(name, desc, texture, preview_texture, env)
        path = env.get_main_path()
        self.dip_count = dip_count
        self.raw_spice = raw_spice
        self.spice_nodes = spice_nodes
        self.datasheet_file = datasheet_img
        self.datasheet_image = pygame.image.load(os.path.join(path, 'assets', 'textures', 'datasheets', datasheet_img))
        self.pins_to_nodes = {} if pin_map is None else pin_map

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.name, self.desc, self.texture_name, self.preview_texture_name, self.dip_count, self.raw_spice, self.spice_nodes, self.datasheet_file, self.pins_to_nodes

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__init__(*state[:-1], pygame.env, pin_map=state[-1])

    # Return a surface containing the integrated circuit and its labels
    def draw(self, inch_tenth, radius, gap):

        # Prepare the surface and text handlers
        win = pygame.Surface(((self.dip_count/2)*inch_tenth, gap+inch_tenth))
        handler = TextHandler(self.env, 'Play-Regular.ttf', radius*4)
        pin_handler = TextHandler(self.env, 'Play-Regular.ttf', math.floor(radius*1.5))

        # Render the label
        label = handler.render(self.name)
        win.set_colorkey((0, 0, 0))

        # Draw the DIP chassis
        rect = pygame.Rect(0, radius, win.get_width(), win.get_height()-(2*radius))
        pygame.draw.rect(win, COL_IC_LID, rect)

        # For each pin, draw a smaller rectangle corresponding to the breadboard point
        # Also draw a label showing the purpose of the pin
        for i in range(self.dip_count):
            if i < self.dip_count/2:
                r = pygame.Rect((inch_tenth/2) - (radius/2) + (inch_tenth*i), win.get_height()-radius, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)
                r_label = pin_handler.render(self.spice_nodes[i])
                win.blit(r_label, (r.centerx - (r_label.get_width()/2), r.y - r_label.get_height()))
            else:
                r = pygame.Rect((win.get_width() - (inch_tenth / 2)) - (radius/2) - (inch_tenth * (i-(self.dip_count/2))), 0, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)
                r_label = pin_handler.render(self.spice_nodes[i])
                win.blit(r_label, (r.centerx - (r_label.get_width()/2), r.bottom))

        # Draw the label
        win.blit(label, (win.get_width()/2 - label.get_width()/2, win.get_height()/2 - label.get_height()/2))

        return win

    # Return a surface containing the integrated circuit and its labels
    def surface(self, hovered_board):
        main_board_config = hovered_board.main_board_config
        inch_tenth, radius = hovered_board.inch_tenth, hovered_board.radius
        gap = main_board_config.segment_gap - (main_board_config.per_column_rows*inch_tenth)
        surface = self.draw(inch_tenth, radius, gap)
        return surface, None


class Switch(IntegratedCircuit):
    """The switch structure contains the type of switch and acts as an integrated circuit so that it uses the
    same rules when connecting to a breadboard"""

    def __init__(self, name, desc, texture, preview_texture, dip_count, raw_spice, spice_nodes, latch, datasheet_img, env, pin_map=None):
        super().__init__(name, desc, texture, preview_texture, dip_count, raw_spice, spice_nodes, datasheet_img, env, pin_map=pin_map)
        self.state = 0
        self.latch = latch
        self.raw_spice = ""

    def __getstate__(self):
        """Return state values to be pickled."""
        return self.name, self.desc, self.texture_name, self.preview_texture_name, self.dip_count, self.raw_spice, \
            self.spice_nodes, self.latch, self.datasheet_file, self.pins_to_nodes

    def __setstate__(self, state):
        """Restore state from the unpickled state values."""
        self.__init__(*state[:-1], pygame.env, pin_map=state[-1])

    # Return a surface containing the switch
    def draw(self, inch_tenth, radius, gap):

        # Prepare the surface
        win = pygame.Surface(((self.dip_count/2)*inch_tenth, gap+inch_tenth))
        win.set_colorkey((0, 0, 0))

        # Draw the switch body
        rect = pygame.Rect(0, radius, win.get_width(), win.get_height()-(2*radius))
        pygame.draw.rect(win, COL_SWITCH, rect)

        # Draw the switch shaft
        switch_shaft = pygame.Rect(rect.centerx - rect.w*3/8, rect.centery - rect.h*1/5, rect.w*3/4, rect.h*2/5)
        pygame.draw.rect(win, COL_SWITCH_SHAFT, switch_shaft)

        # Draw the switch
        switch = pygame.Rect((rect.centerx - rect.w*3/8) + (self.state*rect.w*3/8), rect.centery - rect.h*1/5, rect.w*3/8, rect.h*2/5)
        pygame.draw.rect(win, (1, 1, 1), switch)

        # Draw the switch indicator
        pygame.draw.circle(win, COL_WHITE, switch.center, switch.w/4)

        # Draw the pins without labels
        for i in range(self.dip_count):
            if i < self.dip_count/2:
                r = pygame.Rect((inch_tenth/2) - (radius/2) + (inch_tenth*i), win.get_height()-radius, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)
            else:
                r = pygame.Rect((win.get_width() - (inch_tenth / 2)) - (radius/2) - (inch_tenth * (i-(self.dip_count/2))), 0, radius, radius)
                pygame.draw.rect(win, COL_IC_PIN, r)

        return win
