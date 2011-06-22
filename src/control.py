"""
Control class works as the control part of the machine
control does syntax-related things

TODO
now it's implemented to use only strings as pos tags
later control should be an FST
"""

class Control:
    def __init__(self):
        pass

    def is_a(self, other):
        if not isinstance(other, Control):
            raise Exception("Control can be compared only with other Control")

class PosControl(Control):
    def __init__(self, pos):
        Control.__init__(self)
        self.pos = pos

    def is_a(self, other):
        Control.is_a(other)
        if self.pos.find(other.pos) >- 1:
            return True
        else:
            return False

