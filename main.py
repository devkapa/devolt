import pygame
import os
import sys

from pygame.locals import SCALED
from ui.environment import Environment


# Versioning
version = "0.0.1"

# Enable double buffer for speed
flags = SCALED

# Size constants
WIDTH, HEIGHT = 1200, 800

# Determine execution environment
ENV = Environment()

# Frames per second constant
FPS = 120

# Enum values for code readability
HOME, SIM = 0, 1


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
            pass
        
        if current_state == SIM:
            pass
        
        pygame.display.update()
    

if __name__ == '__main__':
    main()
    