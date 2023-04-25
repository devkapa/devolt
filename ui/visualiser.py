import random
import pygame.draw
from ui.colours import COL_CIRCUIT_VISUALISER, COL_BACKGROUND


class Visualiser:
    INITIAL_ANGLES = ((2, 0), (0, 2), (-2, 0), (0, -2))
    TOP_ANGLES = [(1, -1), (2, 0), (1, 1)]
    BOTTOM_ANGLES = [(-1, 1), (-2, 0), (-1, -1)]
    LEFT_ANGLES = [(0, 2), (-1, 1), (1, 1)]
    RIGHT_ANGLES = [(-1, -1), (0, -2), (1, -1)]
    NUMBERED_ANGLES = [TOP_ANGLES, LEFT_ANGLES, BOTTOM_ANGLES, RIGHT_ANGLES]

    TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3
    
    strands: list

    def __init__(self):
        self.strands = []
        self.generate_initial_strands()
    
    def generate_edge(self, override=None):
        edge = random.randint(self.TOP, self.RIGHT) if override is None else override
        if edge == self.TOP:
            rand_coord = (random.randint(10, 990), 0)
        elif edge == self.BOTTOM:
            rand_coord = (random.randint(10, 990), 700)
        elif edge == self.RIGHT:
            rand_coord = (1000, random.randint(10, 690))
        elif edge == self.LEFT:
            rand_coord = (0, random.randint(10, 690))
        return edge, rand_coord
    
    def generate_initial_strands(self):
        self.strands.clear()
        for _ in range(1):
            edge, rand_coord = self.generate_edge()
            initial_strand = Strand(rand_coord, self.INITIAL_ANGLES[edge], self, self.NUMBERED_ANGLES[edge])
            self.strands.append(initial_strand)
    
    def add_strand(self, strand):
        self.strands.append(strand)
    
    def draw(self, win):
        if len(self.strands) > 100:
            self.generate_initial_strands()
        for strand in self.strands:
            strand.grow()
            strand.draw_line(win)
        for strand in self.strands:
            strand.draw_circle(win)
        

class Strand:

    enabled: bool
    TOP, LEFT, BOTTOM, RIGHT = 0, 1, 2, 3

    def __init__(self, starting_point, angle, parent, numbered):
        self.enabled = True
        self.angle = angle
        self.starting_point = starting_point
        self.new_point = starting_point
        self.numbered = numbered
        self.parent = parent
        
    def grow(self):
        if self.enabled:
            if self.new_point[0] + self.angle[1] < 0 or self.new_point[0] + self.angle[1] > 1000:
                self.restart()
                return
            if self.new_point[1] + self.angle[0] < 0 or self.new_point[1] + self.angle[0] > 700:
                self.restart()
                return
            distance_travelled = tuple(map(lambda i, j: abs(i - j), self.starting_point, self.new_point))
            enough_travelled = distance_travelled[0] + distance_travelled[1] > 60
            if random.random() < 0.02 and enough_travelled:
                self.end()
                return
            self.new_point = (self.new_point[0] + self.angle[1], self.new_point[1] + self.angle[0])
    
    def end(self, destroy=True):
        self.enabled = False if destroy else True
        complimentary_angle = (-self.angle[0], -self.angle[1])
        new_angle = random.choice([i for i in self.numbered if i != self.angle and i != complimentary_angle])
        self.parent.add_strand(Strand(self.new_point, new_angle, self.parent, self.numbered))

    def restart(self):
        self.enabled = False
        edge, rand_coord = self.parent.generate_edge()
        self.parent.add_strand(Strand(rand_coord, Visualiser.INITIAL_ANGLES[edge], self.parent, Visualiser.NUMBERED_ANGLES[edge]))

    def draw_line(self, win):
        pygame.draw.aaline(win, COL_CIRCUIT_VISUALISER, self.starting_point, self.new_point)
    
    def draw_circle(self, win):
        pygame.draw.circle(win, COL_CIRCUIT_VISUALISER, self.new_point, 10, width=4)
        pygame.draw.circle(win, COL_BACKGROUND, self.new_point, 6)
