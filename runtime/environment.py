import sys
import os


class Environment:
    
    def __init__(self):
        self.unfrozen = getattr(sys, 'frozen', False)
        self.query_disable = []
        self.selected = None
        self.undo_states = []
        self.redo_states = []
        self.datasheet = None

    def reset(self):
        self.query_disable.clear()
        self.selected = None
        self.undo_states.clear()
        self.redo_states.clear()
        self.datasheet = None
        
    def get_this_path(self):
        return sys._MEIPASS if self.unfrozen else os.path.dirname(__file__)

    def get_main_path(self):
        return sys._MEIPASS if self.unfrozen else ''
    