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

    def __hash__(self):
        pass

    def __eq__(self, other):
        pass

    def __cmp__(self, other):
        pass

    def is_a(self, other):
        if not isinstance(other, Control):
            raise Exception("Control can be compared only with other Control")

class PosControl(Control):
    import re
    case_pattern = re.compile("N(OUN|P)[^C]*CAS<([^>]*)>")

    def __init__(self, pos):
        Control.__init__(self)
        self.pos = pos

    def __hash__(self):
        return hash(self.pos)

    def __eq__(self, other):
        return self.pos.__eq__(other.pos)

    def __cmp__(self, other):
        return self.pos < other.pos

    def is_a(self, other):
        import re
        Control.is_a(self, other)
        is_a_pattern = re.compile(other.pos)
        if is_a_pattern.search(self.pos) is not None:
            return True
        else:
            return False

    def get_case(self):
        s = PosControl.case_pattern.search(self.pos)
        if s is not None:
            return s.groups()[1]
        else:
            return None

