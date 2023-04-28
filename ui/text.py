import os.path
import pygame.font
from ui.colours import *


class TextHandler:
    
    def __init__(self, env, font, px):
        self.font = pygame.font.Font(os.path.join(env.get_main_path(), 'assets', 'fonts', font), px)
        self.px = px
        
    def render(self, text, colour=COL_WHITE, alpha=None):
        """Returns a pygame surface with the passed text in the app font."""
        text = self.font.render(text, True, colour)
        text.set_alpha(alpha) if alpha is not None else None
        return text

    def render_shadow(self, text, colour=COL_WHITE, shadow_colour=COL_BLACK, alpha=None):
        """Returns a pygame surface with the passed text and a shadow in the app font."""
        text_main = self.font.render(text, True, colour)
        text_shadow = self.font.render(text, True, shadow_colour)
        text_main.set_alpha(alpha) if alpha is not None else None
        text_shadow.set_alpha(alpha) if alpha is not None else None
        return text_main, text_shadow

    def render_multiline(self, text, width, colour=COL_WHITE):
        """Returns text surface(s) that are split based on the given length"""
        text_main = self.font.render(text, True, colour)
        if text_main.get_width() > width:
            finished_lines = []
            current_line = ""
            height = 0
            for word in text.split(" "):
                test_line = current_line + f"{word} "
                test_text = self.font.render(test_line, True, colour)
                if test_text.get_width() > width:
                    previous_line = self.font.render(current_line, True, colour)
                    finished_lines.append(previous_line)
                    height += previous_line.get_height() + 5
                    current_line = f"{word} "
                    continue
                current_line += f"{word} "
            previous_line = self.font.render(current_line, True, colour)
            finished_lines.append(previous_line)
            height += previous_line.get_height() + 5
            return finished_lines, height
        else:
            return [text_main], text_main.get_height()

    def render_coloured(self, text, colour=COL_WHITE):
        """Returns text surface(s) that are coloured separately."""
        dummy_text = self.render(text)
        master_surface = pygame.Surface(dummy_text.get_size())
        master_surface.set_colorkey((0, 0, 0))
        text: str = text.split("||")
        current_colour = colour
        x_accumulated = 0
        for split_section in text:
            if split_section.startswith("col."):
                current_colour = eval(split_section[4:])
                continue
            split_text = self.render(split_section, colour=current_colour)
            master_surface.blit(split_text, (x_accumulated, 0))
            x_accumulated += split_text.get_width()
        return master_surface
    