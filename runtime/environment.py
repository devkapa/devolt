import sys


class Environment:
    """The environment serves as a global structure in which any item in the application can interact with other
    items which are in the same environment. It also tracks whether the app is run in a development environment or
    executable, and stores the program state."""
    
    def __init__(self):
        self.unfrozen = getattr(sys, 'frozen', False)
        self.query_disable = []
        self.selected = None
        self.undo_states = []
        self.redo_states = []
        self.datasheet = None

    # Clear the environment for a new project
    def reset(self):
        self.query_disable.clear()
        self.selected = None
        self.undo_states.clear()
        self.redo_states.clear()
        self.datasheet = None

    # Get the execution path at runtime
    def get_main_path(self):
        return sys._MEIPASS if self.unfrozen else ''
    