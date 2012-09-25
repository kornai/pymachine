import re
import logging

from control import PosControl, ConceptControl

class Matcher(object):
    def __init__(self, string, exact=False):
        if exact:
            self.input_ = re.compile("^{0}$".format(string))
        else:
            self.input_ = re.compile("{0}".format(string))

    def match(self, machine):
        """@return a boolean."""
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
        logging.debug("matching of {0} in {1} is {2}".format(
            str_, self.input_.pattern,
            self.input_.search(str_) is not None))
        return self.input_.search(str_) is not None

class ConceptMatcher(PrintnameMatcher):
    def match(self, machine):
        if PrintnameMatcher.match(self, machine):
            return isinstance(machine.control, ConceptControl)
        else:
            return False

class EnumMatcher(Matcher):
    def __init__(self, enum_name, lexicon):
        self.name = enum_name
        self.machine_names = self.collect_machines(lexicon)

    def collect_machines(self, lexicon):
        cm = lexicon.static[self.name]
        return set([str(m.base.partitions[1][0]) for m in cm.base.partitions[1]
                if m.printname() == "IS_A"])

    def match(self, machine):
        return str(machine) in self.machine_names

class NotMatcher(Matcher):
    """The boolean NOT operator."""
    def __init__(self, matcher):
        self.matcher = matcher

    def match(self, machine):
        return not self.matcher.match(machine)

class AndMatcher(Matcher):
    """The boolean AND operator."""
    def __init__(self, *matchers):
        self.matchers = matchers

    def match(self, machine):
        for m in self.matchers:
            if not m.match(machine):
                return False
        return True

