class Conductor:

    def __init__(self, voltage=0):
        self.voltage = voltage
        self.nodes = []

    def set_voltage(self, voltage, finished_nodes=None):
        self.voltage = voltage
        finished_nodes = [] if finished_nodes is None else finished_nodes
        for node in self.nodes:
            if node in finished_nodes:
                continue
            finished_nodes.append(node)
            for conductor in node.conductors:
                if conductor != self:
                    conductor.set_voltage(voltage, finished_nodes)


class Node:

    def __init__(self, conductors):
        self.conductors = conductors
        for conductor in conductors:
            conductor.nodes.append(self)
