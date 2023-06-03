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

    resistances = {'0': [],
                   '100': [COL_RES_BAND_1_1, COL_RES_BAND_2_0, COL_RES_BAND_3_0, COL_RES_BAND_M_1, COL_TOLERANCE],
                   '220': [COL_RES_BAND_1_2, COL_RES_BAND_2_2, COL_RES_BAND_3_0, COL_RES_BAND_M_1, COL_TOLERANCE],
                   '560': [COL_RES_BAND_1_5, COL_RES_BAND_2_6, COL_RES_BAND_3_0, COL_RES_BAND_M_1, COL_TOLERANCE],
                   '1K': [COL_RES_BAND_1_1, COL_RES_BAND_2_0, COL_RES_BAND_3_0, COL_RES_BAND_M_10, COL_TOLERANCE],
                   '10K': [COL_RES_BAND_1_1, COL_RES_BAND_2_0, COL_RES_BAND_3_0, COL_RES_BAND_M_100, COL_TOLERANCE],
                   '100K': [COL_RES_BAND_1_1, COL_RES_BAND_2_0, COL_RES_BAND_3_0, COL_RES_BAND_M_1K, COL_TOLERANCE],
                   '1M': [COL_RES_BAND_1_1, COL_RES_BAND_2_0, COL_RES_BAND_3_0, COL_RES_BAND_M_10K, COL_TOLERANCE]}

    def __init__(self, point_a, point_b, colour=COL_WIRE_RED):
        self.point_a = point_a
        self.point_b = point_b
        self.colour = colour
        self.resistance = 0

    def convert(self, x=None, colours=False):
        if x is not None:
            if 'K' in x:
                if len(x) > 1:
                    return float(x.replace('K', '')) * 1000
                return 1000.0
            if 'M' in x:
                if len(x) > 1:
                    return float(x.replace('M', '')) * 1000000
                return 1000000.0
            return float(x)
        else:
            num = float('{:.3g}'.format(self.resistance))
            magnitude = 0
            while abs(num) >= 1000:
                magnitude += 1
                num /= 1000.0
            k_m = '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M'][magnitude])
            return self.resistances[k_m] if colours else k_m


class ICSpiceSubCircuit(SubCircuit):

    def __init__(self, name, raw, nodes):
        SubCircuit.__init__(self, name, *nodes)
        self.raw_spice += raw
