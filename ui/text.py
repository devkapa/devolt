import os.path
import pygame.font
from colours import WHITE


class TextHandler:
    
    def __init__(self, env, font, px):
        self.font = pygame.font.Font(os.path.join(env.get_main_path(), 'assets', 'fonts', font), px)
        self.px = px
        
    def render_text(self, text, color=WHITE, alpha=None):
        """Returns a pygame surface with the passed text in the app font."""
        text = self.font.render(text, True, color)
        text.set_alpha(alpha) if alpha is not None else None
        return text

    def render_coloured_text(self, text, color=WHITE):
        """Returns text surface(s) that are coloured separately."""
        dummy_text = self.render_text(text)
        master_surface = pygame.Surface(dummy_text.get_size())
        master_surface.set_colorkey((0, 0, 0))
        text: str = text.split("||")
        current_colour = color
        x_accumulated = 0
        for split_section in text:
            if split_section.startswith("col."):
                current_colour = eval(split_section[4:])
                continue
            split_text = self.render_text(split_section, color=current_colour)
            master_surface.blit(split_text, (x_accumulated, 0))
            x_accumulated += split_text.get_width()
        return master_surface
    