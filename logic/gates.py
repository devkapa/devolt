from PySpice.Spice.Netlist import SubCircuit


class NAND(SubCircuit):
    NODES = ('vcc', 'gnd', 'A', 'B', 'Y')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'Y', 'A', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(2, 'Y', 'B', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(3, 'Y', 'A', 'T', 'gnd', model='t-nmos')
        self.MOSFET(4, 'T', 'B', 'gnd', 'gnd', model='t-nmos')


class INVERTER(SubCircuit):
    NODES = ('vcc', 'gnd', 'A', 'Y')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'Y', 'A', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(2, 'Y', 'A', 'vcc', 'vcc', model='t-pmos')


class AND(SubCircuit):
    NODES = ('vcc', 'gnd', 'A', 'B', 'Y')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'R', 'A', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(2, 'R', 'B', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(3, 'R', 'A', 'T', 'gnd', model='t-nmos')
        self.MOSFET(4, 'T', 'B', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(5, 'Y', 'R', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(6, 'Y', 'R', 'vcc', 'vcc', model='t-pmos')


class NOR(SubCircuit):
    NODES = ('vcc', 'gnd', 'A', 'B', 'Y')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'T', 'A', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(2, 'Y', 'B', 'T', 'vcc', model='t-pmos')
        self.MOSFET(3, 'Y', 'A', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(4, 'Y', 'B', 'gnd', 'gnd', model='t-nmos')


class OR(SubCircuit):
    NODES = ('vcc', 'gnd', 'A', 'B', 'Y')

    def __init__(self, name):
        SubCircuit.__init__(self, name, *self.NODES)
        self.MOSFET(1, 'T', 'A', 'vcc', 'vcc', model='t-pmos')
        self.MOSFET(2, 'R', 'B', 'T', 'vcc', model='t-pmos')
        self.MOSFET(3, 'R', 'A', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(4, 'R', 'B', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(5, 'Y', 'R', 'gnd', 'gnd', model='t-nmos')
        self.MOSFET(6, 'Y', 'R', 'vcc', 'vcc', model='t-pmos')
