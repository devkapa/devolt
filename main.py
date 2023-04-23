import random

import pygame
import os
import sys

from pygame.locals import SCALED
from runtime.environment import Environment
from ui.text import TextHandler
from ui.colours import *
from ui.visualiser import Visualiser


# Versioning
version = "0.0.1"

# Enable smart scaling
flags = SCALED

# Size constants
WIDTH, HEIGHT = 1000, 700

# Determine execution environment
ENV = Environment()

# Frames per second constant
FPS = 60

# Enum values for code readability
HOME, SIM = 0, 1
TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3


def draw_homepage(win, homepage_title, homepage_version, visualiser):
    draw_circuit_graphic(win, visualiser)
    title_surface, title_shadow = homepage_title
    win.blit(title_shadow, ((WIDTH/2) - title_shadow.get_width()/2 + 2, HEIGHT/2 - 140 + 2))
    win.blit(title_surface, ((WIDTH/2) - title_surface.get_width()/2, HEIGHT/2 - 140))
    version_surface, version_shadow = homepage_version
    win.blit(version_shadow, ((WIDTH/2) + (title_surface.get_width()/2) - version_surface.get_width() + 1, HEIGHT/2 - 150 + title_shadow.get_height() + 1))
    win.blit(version_surface, ((WIDTH/2) + (title_surface.get_width()/2) - version_surface.get_width(), HEIGHT/2 - 150 + title_surface.get_height()))


def draw_circuit_graphic(win, visualiser):
    win.fill(COL_BACKGROUND)
    visualiser.draw(win)


def main():

    # Initialise pygame modules
    pygame.font.init()
    pygame.display.init()
    pygame.mixer.init()
    
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

    # Set the initial state to the title screen
    current_state = HOME
    
    # Create text handlers
    title_handler = TextHandler(ENV, 'Play-Bold.ttf', 75)
    version_text_handler = TextHandler(ENV, 'Play-Regular.ttf', 15)

    # Pre-rendered text
    homepage_title = title_handler.render_shadow("de:volt", shadow_colour=COL_TITLE, colour=COL_TITLE_SHADOW)
    homepage_version = version_text_handler.render_shadow(f"v{version}", shadow_colour=COL_TITLE, colour=COL_TITLE_SHADOW)

    visualiser = None

    while running:

        # Limit the loop to run only 60 times per second
        clock.tick(FPS)
        
        # Check for new events 
        for event in pygame.event.get():

            # Exit the program if the user quit
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
        # Display the page corresponding to the program state
        if current_state == HOME:
            if visualiser is None:
                visualiser = Visualiser()
            draw_homepage(win, homepage_title, homepage_version, visualiser)
        
        if current_state == SIM:
            pass
        
        pygame.display.update()
    

if __name__ == '__main__':
    main()
    