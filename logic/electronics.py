import weakref
import uuid
from PySpice.Spice.Netlist import SubCircuit
from ui.colours import *


class Node:

    instances = weakref.WeakSet()

    def __init__(self):
        self.uuid = uuid.uuid4()
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


class Wire:

    def __init__(self, point_a, point_b, colour=COL_RED):
        self.point_a = point_a
        self.point_b = point_b
        self.colour = colour


class SN74HC00(SubCircuit):
    NODES = ('vcc', 'A0', 'B0', 'Y0', 'A1', 'B1', 'Y1', 'A2', 'B2', 'Y2', 'A3', 'B3', 'Y3', 'gnd')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'Y0', 'A0', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(2, 'Y0', 'B0', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(3, 'Y0', 'A0', 'T0', 'gnd', model='t-nmos')
        self.MOSFET(4, 'T0', 'B0', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(5, 'Y1', 'A1', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(6, 'Y1', 'B1', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(7, 'Y1', 'A1', 'T1', 'gnd', model='t-nmos')
        self.MOSFET(8, 'T1', 'B1', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(9, 'Y2', 'A2', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(10, 'Y2', 'B2', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(11, 'Y2', 'A2', 'T2', 'gnd', model='t-nmos')
        self.MOSFET(12, 'T2', 'B2', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(13, 'Y3', 'A3', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(14, 'Y3', 'B3', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(15, 'Y3', 'A3', 'T3', 'gnd', model='t-nmos')
        self.MOSFET(16, 'T3', 'B3', 'gnd', 'gnd', model='t-nmos')
