import weakref
import uuid
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
