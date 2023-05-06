class Conductor:

    def __init__(self, voltage=0):
        self.voltage = voltage
        self.nodes = []

    def set_voltage(self, voltage):
        for node in self.nodes:
            for conductor in node.conductors:
                conductor.voltage = voltage


class Node:

    def __init__(self, conductors):
        self.conductors = conductors
        for conductor in conductors:
            conductor.nodes.append(self)
