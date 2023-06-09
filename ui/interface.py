import os.path
import pygame

from ui.button import Button
from ui.text import TextHandler
from ui.colours import *


class TabbedMenu:
    """A structure which holds categorised tabs, each representing a different page"""

    # Initialise an empty menu
    def __init__(self, size, lists, tab_height, real_pos, env):
        self.size = size
        self.selected = 0
        self.tab_height = tab_height
        self.real_pos = real_pos
        self.handler = TextHandler(env, 'Play-Regular.ttf', 15)
        self.rects = []
        self.clicked = False
        self.env = env
        self.hovering = False
        self.lists = []
        self.list_pos = (0, 10 + self.tab_height)
        list_real_pos = tuple(map(sum, zip(self.real_pos, self.list_pos)))

        # Create the individual tabs for each list category and store for later use
        accumulated = 10
        for i in lists:
            i = i.create_list((self.size[0], self.size[1] - 10 - tab_height), self.list_pos, list_real_pos, env)
            text = self.handler.render(i.small_title)
            rect = pygame.Rect(accumulated, 10, text.get_width() + 20, self.tab_height)
            self.rects.append([rect, False])
            self.lists.append(i)
            accumulated += rect.w + 5

    # Returns a surface containing the tabbed menu and any recurring children
    def surface(self):

        # Prepare the surface to be drawn on
        surface = pygame.Surface(self.size)
        surface.fill(COL_SIM_GRIDLINES)

        # Draw the category tabs and their labels
        accumulated = 10
        for index, part_list in enumerate(self.lists):
            text_colour = COL_HOME_BKG if self.selected == index or self.rects[index][1] else COL_WHITE
            text = self.handler.render(part_list.small_title, colour=text_colour)
            rect = self.rects[index][0]
            rect_colour = COL_TABBED_BAR if self.selected == index or self.rects[index][1] else COL_HOME_BKG
            pygame.draw.rect(surface, rect_colour, rect, border_top_left_radius=8, border_top_right_radius=8)
            surface.blit(text, (rect.center[0] - text.get_width()/2, 10 + self.tab_height/2 - text.get_height()/2))
            accumulated += rect.w + 5

        # Draw the space in which a list will be placed
        drawing_space = pygame.Rect(0, 10 + self.tab_height, self.size[0], self.size[1] - 10 + self.tab_height)
        pygame.draw.rect(surface, COL_TABBED_BAR, drawing_space)

        # Draw the currently selected list
        if self.lists[self.selected] is not None:
            surface.blit(self.lists[self.selected].surface(), self.list_pos)

        return surface

    # Wait for a tab to be pressed, and change the selected list if so
    def listen(self):
        found = False
        if not len(self.env.query_disable):
            mouse_pos = pygame.mouse.get_pos()
            for i, rect in enumerate(self.rects):
                rect_copy = rect[0].copy()
                rect_copy.y += 60
                if rect_copy.collidepoint(mouse_pos):
                    rect[1] = True
                    found = True
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                    if pygame.mouse.get_pressed()[0]:
                        if not self.clicked:
                            self.clicked = True
                            self.selected = i
                    else:
                        self.clicked = False
                else:
                    rect[1] = False
            for i in self.lists:
                for j in i.list_items:
                    if j.add_button.hovering:
                        found = True
        self.hovering = found


class List:
    """The List structure is a visual, scrollable tile filled with elements. The list contains a title and description
    to outline what the elements within may contain"""

    # Initialise an empty list
    def __init__(self, size, title, desc, pos, real_pos, env, small_title=None):
        self.scroll_offset = 0
        self.size = size
        self.title = title
        self.small_title = title if small_title is None else small_title
        self.real_pos = real_pos
        self.clicked = False
        self.pos = pos
        self.list_items = []
        self.env = env
        self.title_handler = TextHandler(env, 'Play-Regular.ttf', 25)
        desc_handler = TextHandler(env, 'Play-Regular.ttf', 15)
        self.desc = desc_handler.render_multiline(desc, self.size[0] - 30, colour=COL_BLACK)
        self.scroll_up = pygame.Rect(self.size[0] - 20, 0, 20, 20)
        self.scroll_down = pygame.Rect(self.size[0] - 20, self.size[1] - 20, 20, 20)
        self.scroll_bar = pygame.Rect(self.size[0] - 20, 20, 20, self.size[1] - 40)
        self.scroller = pygame.Rect(self.size[0] - 16, 24, 12, 1)
        scroll_arrow = pygame.image.load(os.path.join(env.get_main_path(), 'assets', 'textures', 'icons', 'arrow.png'))
        self.scroll_up_img = pygame.transform.scale(scroll_arrow, (16, 16))
        self.scroll_down_img = pygame.transform.flip(self.scroll_up_img, False, True)
        self.overflow = 0

    # Increase or decrease the offset based on how much has been scrolled
    def scroll(self, x):
        if self.overflow:
            if self.scroll_offset + x < 0:
                self.scroll_offset = 0
                return
            if self.scroll_offset + x > self.overflow:
                self.scroll_offset = self.overflow
                return
            self.scroll_offset += x

    # Wait for the scroll bar to be pressed. If it is pressed, activate the scroller
    # and translate the vertical mouse movements to scroll up/downs.
    def listen(self):
        env = self.env
        scroller_real_pos = tuple(map(sum, zip(self.real_pos, self.scroller.topleft)))
        mouse_pos = pygame.mouse.get_pos()
        scroller_relative = self.scroller.copy()
        scroller_relative.topleft = scroller_real_pos
        if len(env.query_disable) == 0 or self.clicked:
            if scroller_relative.collidepoint(mouse_pos) or self.clicked:
                if pygame.mouse.get_pressed()[0]:
                    self.clicked = True
                    if self not in env.query_disable:
                        env.query_disable.append(self)
                    y_change = pygame.mouse.get_rel()[1]
                    self.scroll(y_change)
                else:
                    if self in env.query_disable:
                        env.query_disable.remove(self)
                    self.clicked = False
                    pygame.mouse.get_rel()

    # Returns the surface containing the list background, title, description, scrolling instruments
    # and all elements based on the relative scrolling position.
    def surface(self):

        # Prepare a surface to be drawn on
        surface = pygame.Surface(self.size)
        surface.fill(COL_TABBED_BAR)

        # Render the title
        title = self.title_handler.render_shadow(self.title, colour=COL_WHITE, shadow_colour=COL_HOME_BKG)
        title_surface, title_shadow = title
        title_coords = (10, 10)
        surface.blit(title_shadow, tuple(x + 1 for x in title_coords))
        surface.blit(title_surface, title_coords)

        # Get the position of the description
        desc_coords = (10, 15 + title_surface.get_height())

        # For each line in the description, render with a small padding
        multi_line = 0
        for line in self.desc[0]:
            surface.blit(line, (desc_coords[0], desc_coords[1] + multi_line))
            multi_line += line.get_height() + 5

        # Draw the scrolling instruments
        pygame.draw.rect(surface, COL_HOME_BKG, self.scroll_up)
        pygame.draw.rect(surface, COL_HOME_BKG, self.scroll_down)
        pygame.draw.rect(surface, COL_SIM_GRIDLINES, self.scroll_bar)
        surface.blit(self.scroll_up_img, (self.size[0] - 18, 2))
        surface.blit(self.scroll_down_img, (self.size[0] - 18, self.size[1] - 18))

        # Draw all the list items
        accumulated = 10 + title_surface.get_height() + self.desc[1] + 10
        for item in self.list_items:
            item_pos = (0, accumulated - self.scroll_offset)
            item_real_pos = tuple(map(sum, zip(self.real_pos, item_pos)))
            item.set_real_pos(item_real_pos)
            item.set_pos(item_pos)
            surface.blit(item.surface(), item_pos)
            rect = (0, accumulated - self.scroll_offset + item.size[1])
            pygame.draw.rect(surface, COL_TABBED_BAR, pygame.Rect(rect, (item.size[0], 10)))
            accumulated += item.size[1] + 10

        # If there are too many elements in the list, make the scroll bar appear
        if accumulated > self.size[1]:
            self.overflow = abs(accumulated - self.size[1])
            scrolling_space = self.scroll_bar.height - 8
            items_per_page = (self.size[1]/accumulated)*scrolling_space
            self.scroller.y = 24 + (self.scroll_offset/accumulated)*scrolling_space
            self.scroller.height = items_per_page
            pygame.draw.rect(surface, COL_HOME_BKG, self.scroller)

        # Listen for scroll events
        self.listen()

        return surface


class ListItem:
    """A specific type of element that is shown on the list which is used to add different de:volt parts
    The parent List structure contains the project to which the item will be added to"""

    # Initialise the list element
    def __init__(self, list_size, title, image, desc, part, manager, env):
        self.size = (list_size[0] - 20, 150)
        unscaled = pygame.image.load(os.path.join(env.get_main_path(), 'assets', 'textures', 'parts', image))
        self.image = pygame.transform.scale(unscaled, (self.size[0]/3, self.size[0]/3))
        self.title_handler = TextHandler(env, 'Play-Regular.ttf', 15)
        desc_handler = TextHandler(env, 'Play-Regular.ttf', 12)
        self.title = self.title_handler.render(title, colour=COL_BLACK)
        self.desc = desc_handler.render_multiline(desc, self.size[0] - self.image.get_width() - 25, colour=COL_BLACK)
        self.part = manager.parts[part]
        self.manager = manager
        self.env = env
        button_size = ((2/3)*self.size[0] - 30, 40)
        self.size = (self.size[0], 15 + self.title.get_height() + 25 + self.desc[1] + button_size[1])
        self.button_pos = (self.size[0]/3 + 20, self.size[1] - button_size[1] - 15)
        self.add_button = Button(button_size, self.button_pos, 'plus.png', f'Add {title}', self.event, env)
        self.real_pos = (0, 0)
        self.pos = (0, 0)
        self.temp_part = None

    # Change the position relative to global (0, 0)
    def set_real_pos(self, real_pos):
        self.real_pos = real_pos

    # Set the position of the button relative to the parent List
    def set_pos(self, pos):
        self.pos = pos

    # When the button of the item is clicked, send the part to be added
    def event(self):
        new_part = self.part[1](*self.part[0], self.env)
        self.manager.project.change_made()
        self.manager.project.in_hand = new_part

    # Return a surface containing the item, title, photo, description and the add button
    def surface(self):

        # Prepare the surface
        surface = pygame.Surface(self.size)
        surface.fill(COL_TABBED_BAR)

        # Draw the rectangle
        rect = pygame.Rect((5, 5), (self.size[0] - 10, self.size[1] - 10))
        pygame.draw.rect(surface, COL_SIM_BKG, rect, border_radius=15)

        # Draw the image and title
        surface.blit(self.image, (10, self.size[1]/2 - self.image.get_height()/2))
        surface.blit(self.title, (self.image.get_width() + 20, 15))

        # Draw the description
        accumulated = 0
        for line in self.desc[0]:
            surface.blit(line, (self.image.get_width() + 20, 20 + self.title.get_height() + accumulated))
            accumulated += line.get_height() + 5

        # Draw the button
        button_pos_y = tuple(map(sum, zip(self.pos, self.button_pos)))[1]
        self.add_button.draw(surface, self.title_handler)
        button_real_pos = tuple(map(sum, zip(self.real_pos, self.button_pos)))

        # If the button is in view, allow it to be pressed
        if button_pos_y > 0:
            self.add_button.listen(top_left=button_real_pos)

        return surface
