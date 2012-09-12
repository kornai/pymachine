import re

from control import PosControl, ConceptControl

class Matcher(object):
    def __init__(self, string, exact=False):
        if exact:
            self.input_ = re.compile("^{0}$".format(string))
        else:
            self.input_ = re.compile("{0}".format(string))

    def match(self, machine):
        raise NotImplementedError()

class PrintnameMatcher(Matcher):
    def match(self, machine):
        str_ = machine.printname()
        return self.input_.search(str_) is not None

class PosControlMatcher(Matcher):
    def match(self, machine):
        if not isinstance(machine.control, PosControl):
            return False
        str_ = machine.control.pos
        return self.input_.search(str_) is not None

class ConceptMatcher(PrintnameMatcher):
    def match(self, machine):
        if PrintnameMatcher.match(self, machine):
            return isinstance(machine.control, ConceptControl)
        else:
            return False

