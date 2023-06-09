import random
import pygame.draw
from ui.colours import COL_VISUALISER_STRAND, COL_HOME_BKG


class Visualiser:
    """The Visualiser structure generates a randomly moving item in any of the given directions."""

    INITIAL_ANGLES = ((2, 0), (0, 2), (-2, 0), (0, -2))
    TOP_ANGLES = [(1, -1), (2, 0), (1, 1)]
    BOTTOM_ANGLES = [(-1, 1), (-2, 0), (-1, -1)]
    LEFT_ANGLES = [(0, 2), (-1, 1), (1, 1)]
    RIGHT_ANGLES = [(-1, -1), (0, -2), (1, -1)]
    NUMBERED_ANGLES = [TOP_ANGLES, LEFT_ANGLES, BOTTOM_ANGLES, RIGHT_ANGLES]

    TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3
    
    strands: list

    # Initialise an empty visualiser and generate the first strand
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.strands = []
        self.generate_initial_strands()

    # When a previous strand has ended, find a new edge to generate from
    def generate_edge(self, override=None):
        edge = random.randint(self.TOP, self.RIGHT) if override is None else override
        if edge == self.TOP:
            rand_coord = (random.randint(10, self.width - 10), 0)
        elif edge == self.BOTTOM:
            rand_coord = (random.randint(10, self.width - 10), self.height)
        elif edge == self.RIGHT:
            rand_coord = (self.width, random.randint(10, self.height - 10))
        else:
            rand_coord = (0, random.randint(10, self.height - 10))
        return edge, rand_coord

    # Create a strand and add it to the agenda
    def generate_initial_strands(self):
        self.strands.clear()
        edge, rand_coord = self.generate_edge()
        initial_strand = Strand(rand_coord, self.INITIAL_ANGLES[edge], self, self.NUMBERED_ANGLES[edge])
        self.strands.append(initial_strand)

    # Add a strand to the agenda
    def add_strand(self, strand):
        self.strands.append(strand)

    # Draw the visualiser, incrementing the life of the active strands
    def draw(self, win):
        for strand in self.strands:
            strand.grow()
            strand.draw_line(win)
        for strand in self.strands:
            strand.draw_circle(win)
        

class Strand:
    """The Strand structure is used by the visualiser as a vector of movement that remembers its path."""

    enabled: bool
    TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3

    # Initialise a dead strand
    def __init__(self, starting_point, angle, parent, numbered):
        self.enabled = True
        self.angle = angle
        self.starting_point = starting_point
        self.new_point = starting_point
        self.numbered = numbered
        self.parent = parent

    # Increase the size of the strand. On a 2% chance, change the direction of the strand if it has travelled enough
    def grow(self):
        if self.enabled:
            if self.new_point[0] + self.angle[1] < 0 or self.new_point[0] + self.angle[1] > self.parent.width:
                self.restart()
                return
            if self.new_point[1] + self.angle[0] < 0 or self.new_point[1] + self.angle[0] > self.parent.height:
                self.restart()
                return
            distance_travelled = tuple(map(lambda i, j: abs(i - j), self.starting_point, self.new_point))
            enough_travelled = distance_travelled[0] + distance_travelled[1] > 60
            if random.random() < 0.02 and enough_travelled:
                self.end()
                return
            self.new_point = (self.new_point[0] + self.angle[1], self.new_point[1] + self.angle[0])

    # Kill the strand and generate a new one
    def end(self, destroy=True):
        self.enabled = False if destroy else True
        complimentary_angle = (-self.angle[0], -self.angle[1])
        new_angle = random.choice([i for i in self.numbered if i != self.angle and i != complimentary_angle])
        self.parent.add_strand(Strand(self.new_point, new_angle, self.parent, self.numbered))

    # If the visualiser has too many strands, start over
    def restart(self):
        self.enabled = False
        if len(self.parent.strands) > 100:
            self.parent.generate_initial_strands()
            return
        edge, rand_coord = self.parent.generate_edge()
        new_strand = Strand(rand_coord, Visualiser.INITIAL_ANGLES[edge], self.parent, Visualiser.NUMBERED_ANGLES[edge])
        self.parent.add_strand(new_strand)

    def draw_line(self, win):
        pygame.draw.aaline(win, COL_VISUALISER_STRAND, self.starting_point, self.new_point)
    
    def draw_circle(self, win):
        pygame.draw.circle(win, COL_VISUALISER_STRAND, self.new_point, 10, width=4)
        pygame.draw.circle(win, COL_HOME_BKG, self.new_point, 6)
