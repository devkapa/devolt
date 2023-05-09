from ui.colours import *


class Conductor:

    def __init__(self, voltage=0):
        self.voltage = voltage
        self.nodes = []

    def set_voltage(self, voltage):
        self.voltage = voltage

    def update(self, finished_nodes):
        finished_nodes = [] if finished_nodes is None else finished_nodes
        for node in self.nodes:
            if node in finished_nodes:
                continue
            finished_nodes.append(node)
            for conductor in node.conductors:
                if conductor != self:
                    conductor.set_voltage(self)


class Node:

    def __init__(self, *conductors):
        self.conductors = conductors
        for conductor in conductors:
            conductor.nodes.append(self)


class Wire(Conductor):

    def __init__(self, point_a, point_b, colour=COL_RED):
        super().__init__()
        self.point_a = point_a
        self.point_b = point_b
        self.colour = colour
        self.node = Node(point_a.common, point_b.common)
