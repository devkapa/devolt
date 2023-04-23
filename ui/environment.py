import sys
import os


class Environment:
    
    def __init__(self):
        self.unfrozen = getattr(sys, 'frozen', False)
        
    def get_this_path(self):
        return sys._MEIPASS if self.unfrozen else os.path.dirname(__file__)

    def get_main_path(self):
        return sys._MEIPASS if self.unfrozen else ''
    