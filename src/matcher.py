import re
import logging

from langtools.utils.readkr import kr_to_dictionary as kr_to_dict

from control import PosControl, ConceptControl

class Matcher(object):
    def __init__(self, string, exact=False):
        if exact:
            self.input_ = re.compile("^{0}$".format(string))
        else:
            self.input_ = re.compile("{0}".format(string))

    def match(self, machine):
        try:
            return self._match(machine)
        except Exception, e:
            logging.debug('Exception in matcher {0}: {1}'.format(
                str(type(self)), e))
            return False

    def _match(self, machine):
        """@return a boolean."""
        raise NotImplementedError()

class PrintnameMatcher(Matcher):
    def _match(self, machine):
        str_ = machine.printname()
        return self.input_.search(str_) is not None

class PosControlMatcher(Matcher):
    def _match(self, machine):
        if not isinstance(machine.control, PosControl):
            return False
        str_ = machine.control.pos
        logging.debug("matching of {0} in {1} is {2}".format(
            str_, self.input_.pattern,
            self.input_.search(str_) is not None))
        return self.input_.search(str_) is not None

class ConceptMatcher(Matcher):
    """Matches concepts (words not in the sentence)."""
    def __init__(self):
        pass
    def _match(self, machine):
        return isinstance(machine.control, ConceptControl)

class EnumMatcher(Matcher):
    def __init__(self, enum_name, lexicon):
        self.name = enum_name
        self.machine_names = self.collect_machines(lexicon)
        logging.debug(u"EnumMatcher({0}) created with {1} machines".format(
            self.name, u" ".join(self.machine_names)))

    def collect_machines(self, lexicon):
        cm = lexicon.static[self.name]
        machines_on_type =  set([str(m.base.partitions[1][0])
            for m in cm.base.partitions[1] if m.printname() == "IS_A"])

        all_machines = machines_on_type
        for pn, m in lexicon.static.iteritems():
            for child in m.base.partitions[1]:
                if (child.printname() == "IS_A" and
                    child.base.partitions[2][0] == self.name):
                    all_machines.add(pn)
                    break
        return all_machines

    def _match(self, machine):
        res = unicode(machine) in self.machine_names
        logging.debug(u"matching of {0} in enum {1} is {2}".format(
            unicode(machine), self.name, res))
        return res

class FileContainsMatcher(Matcher):
    def __init__(self, file_name):
        self.fn = file_name
        self.strs = set([s.strip().lower() for s in
            open(file_name).read().decode("utf-8").split("\n")])

    def match(self, machine):
        res = unicode(machine).lower() in self.strs
        logging.debug(u"matching of {0} in file {1} is {2}".format(
            unicode(machine), self.fn, res))
        return res

class NotMatcher(Matcher):
    """The boolean NOT operator."""
    def __init__(self, matcher):
        self.matcher = matcher

    def _match(self, machine):
        return not self.matcher.match(machine)

class AndMatcher(Matcher):
    """The boolean AND operator."""
    def __init__(self, *matchers):
        self.matchers = matchers

    def _match(self, machine):
        for m in self.matchers:
            if not m.match(machine):
                return False
        return True

class OrMatcher(Matcher):
    """The boolean OR operator."""
    def __init__(self, *matchers):
        self.matchers = matchers

    def _match(self, machine):
        for m in self.matchers:
            if m.match(machine):
                return True
        return False

class SatisfiedAVMMatcher(Matcher):
    """
    Matches a satisfied (or unsatisfied, depending on the ctor's argument) AVM.
    """
    def __init__(self, satisfied=True):
        self.satisfied = satisfied

    def _match(self, avm):
        try:
            return avm.satisfied() == self.satisfied
        except AttributeError:
            # Not an avm
            return False

class PatternMatcher(Matcher):
    """ Matches a rule. """
    def __init__(self, pattern):
        if isinstance(pattern, str) or isinstance(pattern, unicode):
            self.pattern = kr_to_dict("stem/" + pattern)
        elif isinstance(pattern, dict):
            self.pattern = pattern
        else:
            raise Exception("No allowed type for pattern")

    def _subset(self, small, large):
        for key in small:
            if key not in large:
                return False    
            else:
                if type(small[key]) == dict:
                    return self._subset(small[key], large[key])
                else:  
                    if small[key] != large[key]:
                        #@ denotes a Greek character (matching everything). 
                        if len(small[key]) == 0 or small[key][0] != '@':
                            return False
        return True             
 
    def _match(self, machine):
        logging.debug("PatternMatcher[{0}]._match({1})".format(self.pattern, machine.control.kr))
        res = self._subset(self.pattern, machine.control.kr)
        logging.debug(res)
        return res

