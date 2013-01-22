import logging
import re
from collections import defaultdict
from itertools import permutations
from copy import deepcopy as copy

from fst import FSA, FST
from matcher import PrintnameMatcher
from matcher import KRPosMatcher
from machine import Machine
from monoid import Monoid
from control import PosControl, ElviraPluginControl, KRPosControl
from constants import deep_cases
from avm import AVM
from operators import ExpandOperator, FillArgumentOperator
from np_parser import parse_rule

class Construction(object):
    SEMANTIC, CHUNK, AVM = xrange(3)  # types
    def __init__(self, name, control, type_=SEMANTIC):
        """
        @param type_ the type of the construction -- SEMANTIC, CHUNK or AVM.
        """
        self.name = name

        if not isinstance(control, FSA):
            raise TypeError("control has to be an FSA instance")
        self.control = control

        self.type_ = type_

    def check(self, seq):
        logging.debug((u"Checking {0} construction for matching with " +
                      u"{1} machines").format(self.name,
                      u" ".join(unicode(m) for m in seq)).encode("utf-8"))
        self.control.reset()
        for machine in seq:
            self.control.read(machine)
        return self.control.in_final()

    def run(self, seq):
        """Shorthand for if check: act."""
        # read the sequence first, and give it to the control
        self.check(seq)

        # if control got into acceptor state, do something
        if self.control.in_final():
            return self.act(seq)
        else:
            return None

    def last_check(self, seq):
        """last_check() is called after construction is activated by the
        spreading activation. Can be used for order checking for example"""
        return True

    def act(self, seq):
        """@return a sequence of machines, or @c None, if last_check() failed.
        """
        logging.debug("Construction matched, running action")
        # arbitrary python code, now every construction will have it
        # hardcoded into the code, later it will be done by Machine objects

class NPConstruction(Construction):
    def __init__(self, name, rule, operators):
        self.rule = rule  # TODO: create control
        self.matchers = parse_rule(self.rule)
        self.operators = operators
        Construction.__init__(self, name, self._create_control(),
                              Construction.CHUNK)

    def _create_control(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        for state in xrange(1, len(self.matchers) + 1):
            control.add_state(str(state), is_init=False,
                    is_final=(state == len(self.matchers)))
            control.add_transition(self.matchers[state - 1],
                                   str(state - 1), str(state))
        return control

    def last_check(self, seq):
        """
        Checks if the greek letters (e.g. bound variables) are consistent.
        @todo Implement it similarly VerbConstruction, e.g. as an argument
              filling problem.
        """
        patterns = [m.pattern for m in self.matchers]
        assert len(seq) == len(patterns)

        greeks = defaultdict(set)
        for i in xrange(len(seq)):
            if not self._collect_variable_values(
                    patterns[i], seq[i].control.kr, greeks):
                return False
        for v in greeks.values():
            if len(v) > 1:
                return False
        return True

    def _collect_variable_values(self, tmpl, data, greeks):
        """
        Collects the values of the variables in @p tmpl from @p cata and adds
        them to the multimap @p greeks.
        """
        for key in tmpl:
            if key not in data:
                # Should be; it's already checked in check()
                return False
            else:
                if isinstance(tmpl[key], dict):
                    return self._collect_variable_values(
                            tmpl[key], data[key], greeks)
                else:
                    if tmpl[key][0] == '@':
                        greeks[tmpl[key]].add(data[key])
        return True    

    def act(self, seq):
        for operator in self.operators:
            seq = operator.act(seq)
        return seq

class VerbConstruction(Construction):
    """A default construction for verbs. It reads definitions, discovers
    cases, and builds a control from it. After that, the act() will do the
    linking process, eg. link the verb with other words, object, subject, etc.

    Defines a single Machine as the "working area": the element in X that we
    follow. An operator represents a relation in phi; however, typically we
    only care about one element among the potentially infinite number of x's.
    Hence, it is enough to maintain a single Machine as a placeholder for
    this element.
    """
    def __init__(self, name, lexicon, supp_dict):
        self.name = name
        self.lexicon = lexicon
        self.supp_dict = supp_dict
        self.matchers = {}
        self.working_area = [Machine(Monoid(None), KRPosControl('stem/VERB'))]
        self.discover_arguments(lexicon.static[name])
        control = self.generate_control()
        self.case_pattern = re.compile("N(OUN|P)[^C]*CAS<([^>]*)>")
        Construction.__init__(self, name, control)
        self.activated = False

    def generate_control(self):
        arguments = self.matchers.keys()
        
        # this will be a hypercube
        control = FST()

        # zero state is for verb
        control.add_state("0", is_init=True, is_final=False)

        # inside states for the cube, except the last, accepting state
        for i in xrange(1, pow(2, len(arguments))):
            control.add_state(str(i), is_init=False, is_final=False)

        # last node of the hypercube
        control.add_state(str(int(pow(2, len(arguments)))),
                              is_init=False, is_final=True)

        # first transition
        control.add_transition(KRPosMatcher("VERB"), [ExpandOperator(
            self.lexicon, self.working_area)], "0", "1")

        # count every transition as an increase in number of state
        for path in permutations(arguments):
            actual_state = 1
            for arg in path:
                increase = pow(2, arguments.index(arg))
                new_state = actual_state + increase
                control.add_transition(self.matchers[arg], 
                    [FillArgumentOperator(arg, self.working_area)],                                      str(actual_state), str(new_state))

                actual_state = new_state
        return control

    def discover_arguments(self, machine):
        for pi, p in enumerate(machine.base.partitions[1:]):
            pi += 1
            for mi, part_machine in enumerate(p):
                pn = part_machine.printname()
                # we are interested in deep cases and
                # supplementary regexps
                if pn in deep_cases or pn.startswith("$"):
                    if pn.startswith("$"):
                        self.matchers[pn] = self.supp_dict[pn]
                    else:
                        self.matchers[pn] = KRPosMatcher("CAS<{0}>".format(pn))

                # recursive call
                self.discover_arguments(part_machine)

    def check(self, seq):
        if self.activated:
            return False
        else:
            res = Construction.check(self, seq)
            logging.debug("Result of check is {0} and working area is:\n{1}".format(res, Machine.to_debug_str(self.working_area[0])))
            return res

class AVMConstruction(Construction):
    """this class will fill the slots in the AVM"""
    def __init__(self, avm):
        self.avm = avm
        self.phi = self.generate_phi()
        control = self.generate_control()
        Construction.__init__(self, avm.name + 'Construction', control, type_=Construction.AVM)

    def generate_phi(self):
        phi = {}
        for key in self.avm:
            matcher = self.avm.get_field(key, AVM.TYPE)
            phi[matcher] = key
        return phi

    def generate_control(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)

        state_num = 1
        for key in self.avm:
            state_name = str(state_num)
            matcher = self.avm.get_field(key, AVM.TYPE)
            control.add_state(state_name, is_init=False, is_final=True)
            control.add_transition(matcher, "0", state_name)
            state_num += 1
        return control

    def check(self, seq):
        return True

    def act(self, seq):
        for machine in seq:
            for matcher in self.phi:
                if matcher.match(machine):
                    self.avm[self.phi[matcher]] = machine
                else:
                    if self.avm[self.phi[matcher]] == machine:
                        dv = self.avm.get_field(self.phi[matcher], AVM.DEFAULT)
                        self.avm[self.phi[matcher]] = dv

        return [self.avm]

class ElviraConstruction(Construction):
    def __init__(self):
        control = FSA()
        # TODO: to hypercube
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=False)
        control.add_state("3", is_init=False, is_final=False)
        control.add_state("4", is_init=False, is_final=True)
        control.add_transition(PrintnameMatcher("vonat"), "0", "1")
        control.add_transition(PrintnameMatcher("menetrend"), "1", "2")
        control.add_transition(PrintnameMatcher("BEFORE_AT"), "2", "3")
        control.add_transition(PrintnameMatcher("AFTER_AT"), "3", "4")

        Construction.__init__(self, self.__class__.__name__, control)

    def last_check(self, seq):
        try:
            if len(seq[2].base.partitions[2]) > 0 and len(seq[3].base.partitions[2]) > 0:
                return True
        except:
            pass
        return False

    def act(self, seq):
        #TODO: implement
        if not self.last_check(seq):
            return None

        elvira_machine = Machine(Monoid("elvira"), ElviraPluginControl())
        for m in seq:
            elvira_machine.append(m)

        return [elvira_machine]
        
def test():
    a = Machine(Monoid("the"), PosControl("DET"))
    kek = Machine(Monoid("kek"), PosControl("ADJ"))
    kockat = Machine(Monoid("kockat"), PosControl("NOUN<CAS<ACC>>"))
    m = Machine(Monoid("vonat"))
    m2 = Machine(Monoid("tb"))
    m.append(m2)
    m2.append(m)
    m3 = copy(m)

    npc = DummyNPConstruction()
    thec = TheConstruction()

    res = npc.run([kek, kockat])
    res = thec.run([a] + res)
    print res[0]
    print res[0].control
    print res[0].base.partitions[1][0]

if __name__ == "__main__":
    test()

