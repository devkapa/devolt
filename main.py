import PySpice.Spice.NgSpice.Shared
import pygame
import os
import uuid

from tkinter import filedialog as fd
from pygame.locals import SCALED
from PySpice.Unit import *
from PySpice.Spice.Netlist import Circuit
from PySpice.Logging.Logging import setup_logging

from runtime.environment import Environment

from ui.text import TextHandler
from ui.colours import *
from ui.visualiser import Visualiser
from ui.button import Button, ElementManager
from ui.interface import TabbedMenu

from protosim.project import Project
from logic.electronics import Wire, ICSpiceSubCircuit, Sink
from logic.parts import PartManager, Part, parse, PowerSupply, Breadboard, IntegratedCircuit, LED

# Versioning
version = "0.0.1"

# PySpice Logger
# setup_logging(logging_level='INFO')

# Enable smart scaling
flags = SCALED

# Size constants
WIDTH, HEIGHT = 1300, 800
SIDEBAR_WIDTH = 320
ACTION_BAR_HEIGHT = 60

# Determine execution environment
ENV = Environment()

# Frames per second constant
HOME_FPS = 60
PROTOSIM_FPS = 120

# Enum values for code readability
HOME, PROTOSIM = 0, 1
TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3

# Pygame custom events
NEW_PROJECT_EVENT = pygame.USEREVENT + 1
OPEN_PROJECT_EVENT = pygame.USEREVENT + 2
EXIT_EVENT = pygame.USEREVENT + 3
UNDO_EVENT = pygame.USEREVENT + 4
REDO_EVENT = pygame.USEREVENT + 5
SAVE_EVENT = pygame.USEREVENT + 6
HOME_EVENT = pygame.USEREVENT + 7
MENU_EVENT = pygame.USEREVENT + 8
EDIT_EVENT = pygame.USEREVENT + 9


def draw_homepage(win, homepage_title, homepage_version, visualiser, buttons):
    draw_circuit_graphic(win, visualiser)
    title_text, title_shadow = homepage_title
    title_coords = ((WIDTH/2) - title_text.get_width()/2, HEIGHT/2 - 140)
    win.blit(title_shadow, tuple(x + 2 for x in title_coords))
    win.blit(title_text, title_coords)
    version_text, version_shadow = homepage_version
    version_x = WIDTH/2 + title_text.get_width()/2 - version_text.get_width()
    version_y = HEIGHT/2 + title_text.get_height() - 150
    win.blit(version_shadow, tuple(x + 1 for x in (version_x, version_y)))
    win.blit(version_text, (version_x, version_y))
    buttons.draw(win)


def draw_circuit_graphic(win, visualiser):
    win.fill(COL_HOME_BKG)
    visualiser.draw(win)


def draw_sim(win, sidebar_width, project, buttons, title, sidebar):
    win.fill(COL_HOME_BKG)
    if project.width != WIDTH-sidebar_width:
        project.set_size(width=WIDTH-sidebar_width)
    action_text, action_shadow = title
    action_coords = (WIDTH/2 - action_text.get_width()/2, ACTION_BAR_HEIGHT/2 - action_text.get_height()/2)
    win.blit(action_shadow, tuple(x + 1 for x in action_coords))
    win.blit(action_text, action_coords)
    project.pos = (sidebar_width, ACTION_BAR_HEIGHT)
    win.blit(project.surface(), project.pos)
    buttons.draw(win)
    if sidebar_width > 0:
        win.blit(sidebar.surface(), (0, ACTION_BAR_HEIGHT))
        sidebar.listen()


def open_dev():
    filetypes = (("de:volt Project", "*.dev"),)
    file = fd.askopenfile(title="Open de:volt Project", initialdir=ENV.get_main_path(), filetypes=filetypes)
    return file


def unionise_nodes(nodes):
    out = []
    while len(nodes) > 0:
        first, *rest = nodes
        first = set(first)

        lf = -1
        while len(first) > lf:
            lf = len(first)

            rest2 = []
            for r in rest:
                if len(first.intersection(set(r))) > 0:
                    first |= set(r)
                else:
                    rest2.append(r)
            rest = rest2

        out.append(first)
        nodes = rest
    return out


def main():

    # Initialise pygame modules
    pygame.font.init()
    pygame.display.init()

    # Create an opaque window surface with defined width and height, and set a title
    win = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    win.set_alpha(None)
    pygame.display.set_caption("de:volt")

    # Set the icon of the window
    icon = pygame.image.load(os.path.join(ENV.get_main_path(), 'assets', 'textures', 'logo.png'))
    pygame.display.set_icon(icon)

    # Initialise pygame's clock and start the game loop
    clock = pygame.time.Clock()
    running = True
    fps = HOME_FPS

    # Set the initial state to the title screen
    current_state = HOME

    # Create text handlers
    title_handler = TextHandler(ENV, 'Play-Bold.ttf', 75)
    version_handler = TextHandler(ENV, 'Play-Regular.ttf', 15)
    button_text_handler = TextHandler(ENV, 'Play-Regular.ttf', 25)
    action_text_handler = TextHandler(ENV, 'Play-Regular.ttf', 30)

    # HOMEPAGE ELEMENTS
    # Buttons
    new_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2)-20), 'plus.png', "New Project", NEW_PROJECT_EVENT, ENV)
    open_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2)+60), 'open.png', "Open Project", OPEN_PROJECT_EVENT, ENV)
    exit_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2)+140), 'exit.png', "Exit", EXIT_EVENT, ENV)
    home_buttons = [new_button, open_button, exit_button]
    home_button_manager = ElementManager(home_buttons, button_text_handler)

    # Pre-rendered text
    home_title = title_handler.render_shadow("de:volt", shadow_colour=COL_HOME_TITLE, colour=COL_HOME_SHADOW)
    home_version = version_handler.render_shadow(version, shadow_colour=COL_HOME_TITLE, colour=COL_HOME_SHADOW)

    # Circuit visualiser for homepage
    visualiser = Visualiser(WIDTH, HEIGHT)

    # SIMULATOR ELEMENTS
    # Project
    sidebar_width = SIDEBAR_WIDTH

    # TEMPORARY, TODO: Project serialisation
    project = Project(WIDTH - sidebar_width, HEIGHT - ACTION_BAR_HEIGHT, ENV)

    # Parts
    default_parts = parse(os.path.join(ENV.get_main_path(), 'logic', 'parts.xml'))
    boards = PartManager("Boards", Part.BOARD_DESC, default_parts[0], project)
    ics = PartManager("Integrated Circuits", Part.IC_DESC, default_parts[1], project, small_title="ICs")
    electronics = PartManager("Electronics", Part.ELECTRONICS_DESC, default_parts[2], project)

    # Sidebar
    sidebar_tabs = [boards, ics, electronics]
    sidebar = TabbedMenu((sidebar_width, HEIGHT - ACTION_BAR_HEIGHT), sidebar_tabs, 30, (0, ACTION_BAR_HEIGHT), ENV)

    # Pre-rendered text
    action_bar_title = action_text_handler.render_shadow(project.display_name)
    edit_title = WIDTH/2 + action_bar_title[0].get_width()/2 + 10

    # Buttons
    button_dimensions = ACTION_BAR_HEIGHT - 16
    button_size = (button_dimensions, button_dimensions)
    button_y = 8
    home_button = Button(button_size, (20 + button_dimensions, button_y), 'home.png', 'Home', HOME_EVENT, ENV)
    menu_button = Button(button_size, (10, button_y), 'menu.png', 'Menu', MENU_EVENT, ENV)
    edit_button = Button(tuple(x - 6 for x in button_size), (edit_title + 5, 10), 'edit.png', 'Edit', EDIT_EVENT, ENV)
    redo_button = Button(button_size, (WIDTH - 20 - 2*button_dimensions, button_y), 'redo.png', 'Redo', REDO_EVENT, ENV)
    undo_button = Button(button_size, (WIDTH - 30 - 3*button_dimensions, button_y), 'undo.png', 'Undo', UNDO_EVENT, ENV)
    save_button = Button(button_size, (WIDTH - 10 - button_dimensions, button_y), 'save.png', 'Save', SAVE_EVENT, ENV)
    sim_elements = [project, sidebar, undo_button, redo_button, save_button, home_button, menu_button, edit_button]
    sim_manager = ElementManager(sim_elements, version_handler)

    while running:

        # Limit the loop to run at the frame tick rate
        clock.tick(fps)

        # Create a virtual SPICE circuit
        circuit = Circuit("dev", ground="gnd")

        # IS = Saturated Current, RS = Ohmic Parasitic Resistance, N = Emission Coefficient
        circuit.model('LED', 'D', IS=3e-18, RS=17, N=2)

        # Find all power supplies and breadboards in the project
        supplies = [supply for supply in project.boards.values() if isinstance(supply, PowerSupply)]
        boards = [board for board in project.boards.values() if isinstance(board, Breadboard)]

        # Unionise wire sets to create common nodes in virtual circuit
        connected = []
        for wire in project.wires:
            a = wire.point_a.common
            b = wire.point_b.common
            a.temp = a.uuid
            b.temp = b.uuid
            connected.append([a, b])

        connected = unionise_nodes(connected)

        for common_node in connected:
            new_uuid = str(uuid.uuid4()) if not len([i for i in common_node if isinstance(i, Sink)]) else "gnd"
            for child_node in common_node:
                child_node.temp = new_uuid

        displays = []

        # Create voltage sources in virtual circuit
        for index, supply in enumerate(supplies):
            circuit.V(index, supply.points[0].common.temp, supply.points[1].common.temp, supply.voltage)

        # Create ICs and Electronics in virtual circuit
        for index, board in enumerate(boards):
            for jndex, plugin in enumerate(board.plugins):
                plugin_object = board.plugins[plugin]
                if isinstance(plugin_object, IntegratedCircuit):
                    name, raw, nodes = plugin_object.name, plugin_object.raw_spice, plugin_object.spice_nodes
                    pins_to_nodes = [i.temp for i in plugin_object.pins_to_nodes.values()]
                    circuit.subcircuit(ICSpiceSubCircuit(f'{plugin_object.name}-{index}{jndex}', raw, nodes))
                    circuit.X(f'{index}{jndex}', f'{plugin_object.name}-{index}{jndex}', *pins_to_nodes)
                if isinstance(plugin_object, LED):
                    if not plugin_object.cathode_connecting:
                        point_a, point_b = plugin_object.anode_point.common.temp, plugin_object.cathode_point.common.temp
                        circuit.Diode(f'{index}{jndex}', point_a, point_b, model='LED')
                        displays.append(plugin_object)

        # If there are elements present in the circuit, evaluate their logic state
        try:
            if len(circuit.elements):
                simulator = circuit.simulator().operating_point()
                node_analysis = simulator.nodes
            else:
                node_analysis = {}
        except PySpice.Spice.NgSpice.Shared.NgSpiceCommandError:
            node_analysis = {}

        for display in displays:
            point_a, point_b = display.anode_point.common.temp, display.cathode_point.common.temp
            if point_a in node_analysis:
                if float(node_analysis[point_a]) > 1 and point_b == circuit.gnd:
                    display.state = 1
                else:
                    display.state = 0
            else:
                display.state = 0

        # Check for new events 
        for event in pygame.event.get():

            # Exit the program if the user quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if current_state == HOME:

                if event.type == NEW_PROJECT_EVENT:
                    fps = PROTOSIM_FPS
                    current_state = PROTOSIM

                if event.type == OPEN_PROJECT_EVENT:
                    selected_file = open_dev()
                    if selected_file is not None:
                        print(selected_file.readlines())

                if event.type == EXIT_EVENT:
                    pygame.quit()
                    sys.exit()

            if current_state == PROTOSIM:

                if event.type == pygame.MOUSEWHEEL:
                    if event.y:
                        mouse_pos = pygame.mouse.get_pos()
                        if project.last_surface.get_rect(topleft=project.pos).collidepoint(mouse_pos):
                            project.scale(event.y*2)
                        element_list = sidebar.lists[sidebar.selected]
                        if element_list.surface().get_rect(topleft=element_list.real_pos).collidepoint(mouse_pos):
                            element_list.scroll(-event.y*20)

                if event.type == MENU_EVENT:
                    if sidebar_width > 0:
                        sidebar_width = 0
                    else:
                        sidebar_width = SIDEBAR_WIDTH

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if pygame.mouse.get_pressed()[0]:
                        if project.in_hand is None:
                            if project.point_hovered is not None:
                                if project.incomplete_wire is None:
                                    project.incomplete_wire = project.point_hovered
                                else:
                                    project.wires.append(Wire(project.incomplete_wire, project.point_hovered))
                                    if project.incomplete_wire in ENV.query_disable:
                                        ENV.query_disable.remove(project.incomplete_wire)
                                    project.incomplete_wire = None
                                    project.point_hovered = None
                        else:
                            if isinstance(project.in_hand, LED):
                                if project.point_hovered is not None:
                                    if not project.in_hand.cathode_connecting:
                                        project.in_hand.anode_point = project.point_hovered
                                        project.in_hand.cathode_connecting = True
                                        project.point_hovered.parent.plugins[project.point_hovered] = project.in_hand
                                    else:
                                        project.in_hand.cathode_point = project.point_hovered
                                        project.in_hand.cathode_connecting = False
                                        if project.in_hand in ENV.query_disable:
                                            ENV.query_disable.remove(project.in_hand)
                                        project.in_hand = None

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if project.in_hand is not None:
                            if project.in_hand in ENV.query_disable:
                                ENV.query_disable.remove(project.in_hand)
                            project.in_hand = None
                        if project.incomplete_wire is not None:
                            if project.incomplete_wire in ENV.query_disable:
                                ENV.query_disable.remove(project.incomplete_wire)
                            project.incomplete_wire = None

        # Display the page corresponding to the program state
        if current_state == HOME:

            pygame.display.set_caption(f"Home • de:volt")
            draw_homepage(win, home_title, home_version, visualiser, home_button_manager)

            if not home_button_manager.hovered:
                if pygame.mouse.get_cursor() != pygame.SYSTEM_CURSOR_ARROW:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        if current_state == PROTOSIM:

            pygame.display.set_caption(f"{project.display_name} • de:volt")
            draw_sim(win, sidebar_width, project, sim_manager, action_bar_title, sidebar)

            if not sim_manager.hovered:
                if pygame.mouse.get_cursor() != pygame.SYSTEM_CURSOR_ARROW:
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        pygame.display.update()


if __name__ == '__main__':
    main()
