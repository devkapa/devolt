import pygame
import os
import sys

from tkinter import filedialog as fd
from pygame.locals import SCALED

from runtime.environment import Environment

from ui.text import TextHandler
from ui.colours import *
from ui.visualiser import Visualiser
from ui.elements import Button, ElementManager
from ui.interface import TabbedMenu

from protosim.project import Project


# Versioning
version = "0.0.1"

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
    pygame.query_disable = []

    # Set the initial state to the title screen
    current_state = HOME
    
    # Create text handlers
    title_handler = TextHandler(ENV, 'Play-Bold.ttf', 75)
    version_handler = TextHandler(ENV, 'Play-Regular.ttf', 15)
    button_text_handler = TextHandler(ENV, 'Play-Regular.ttf', 25)
    action_text_handler = TextHandler(ENV, 'Play-Regular.ttf', 30)

    # HOMEPAGE ELEMENTS
    # Buttons
    new_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2) - 20), 'plus.png', "New Project", NEW_PROJECT_EVENT)
    open_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2) + 60), 'open.png', "Open Project", OPEN_PROJECT_EVENT)
    exit_button = Button((220, 60), ((WIDTH/2)-110, (HEIGHT/2) + 140), 'exit.png', "Exit", EXIT_EVENT)
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
    project = Project(WIDTH - sidebar_width, HEIGHT - ACTION_BAR_HEIGHT)

    # Sidebar
    sidebar_tabs = {'Boards': [], 'ICs': [], 'Electronics': []}
    sidebar = TabbedMenu((sidebar_width, HEIGHT - ACTION_BAR_HEIGHT), 30, sidebar_tabs, (0, ACTION_BAR_HEIGHT))

    # Pre-rendered text
    action_bar_title = action_text_handler.render_shadow(project.display_name)
    edit_title = WIDTH/2 + action_bar_title[0].get_width()/2 + 10

    # Buttons
    button_dimensions = ACTION_BAR_HEIGHT - 16
    button_size = (button_dimensions, button_dimensions)
    button_y = 8
    home_button = Button(button_size, (20 + button_dimensions, button_y), 'home.png', 'Home', HOME_EVENT)
    menu_button = Button(button_size, (10, button_y), 'menu.png', 'Menu', MENU_EVENT)
    edit_button = Button(tuple(x - 6 for x in button_size), (edit_title + 5, 10), 'edit.png', 'Edit', EDIT_EVENT)
    redo_button = Button(button_size, (WIDTH - 20 - 2*button_dimensions, button_y), 'redo.png', 'Redo', REDO_EVENT)
    undo_button = Button(button_size, (WIDTH - 30 - 3*button_dimensions, button_y), 'undo.png', 'Undo', UNDO_EVENT)
    save_button = Button(button_size, (WIDTH - 10 - button_dimensions, button_y), 'save.png', 'Save', SAVE_EVENT)
    sim_elements = [project, sidebar, undo_button, redo_button, save_button, home_button, menu_button, edit_button]
    sim_manager = ElementManager(sim_elements, version_handler)

    while running:

        # Limit the loop to run at the frame tick rate
        clock.tick(fps)

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
                        for element_list in sidebar.lists:
                            if element_list.surface().get_rect(topleft=element_list.real_pos).collidepoint(mouse_pos):
                                element_list.scroll(-event.y*20)

                if event.type == MENU_EVENT:
                    if sidebar_width > 0:
                        sidebar_width = 0
                    else:
                        sidebar_width = SIDEBAR_WIDTH

        # Display the page corresponding to the program state
        if current_state == HOME:

            pygame.display.set_caption(f"Home • de:volt")
            draw_homepage(win, home_title, home_version, visualiser, home_button_manager)

            if not home_button_manager.hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        if current_state == PROTOSIM:

            pygame.display.set_caption(f"{project.display_name} • de:volt")
            draw_sim(win, sidebar_width, project, sim_manager, action_bar_title, sidebar)

            if not sim_manager.hovered:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        pygame.display.update()
    

if __name__ == '__main__':
    main()
    