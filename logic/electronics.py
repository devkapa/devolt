import weakref
import uuid
from PySpice.Spice.Netlist import SubCircuit
from ui.colours import *


class Node:

    instances = weakref.WeakSet()

    def __init__(self):
        self.uuid = str(uuid.uuid4())
        self.temp = self.uuid
        Node.instances.add(self)

    @classmethod
    def get_instances(cls):
        return list(Node.instances)


class Source(Node):

    def __init__(self):
        super().__init__()


class Sink(Node):

    def __init__(self):
        super().__init__()
        self.uuid = "gnd"
        self.temp = "gnd"


class Wire:

    def __init__(self, point_a, point_b, colour=COL_WIRE_RED):
        self.point_a = point_a
        self.point_b = point_b
        self.colour = colour


class ICSpiceSubCircuit(SubCircuit):

    def __init__(self, name, raw, nodes):
        SubCircuit.__init__(self, name, *nodes)
        self.raw_spice += raw
