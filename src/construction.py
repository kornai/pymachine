import logging
import re
from collections import defaultdict
from itertools import permutations
from copy import deepcopy as copy

from fst import FSA, PrintnameTransition
from fst import PosControlTransition as PosTransition
from machine import Machine
from monoid import Monoid
from control import PosControl, ElviraPluginControl
from constants import deep_cases

class Construction(object):
    def __init__(self, name, control):
        self.name = name

        if not isinstance(control, FSA):
            raise TypeError("control has to be an FSA instance")
        self.control = control

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
        """
        @return a sequence of machines, or @c None, if last_check() failed.
        """
        logging.debug("""Construction matched, running action""")
        # arbitrary python code, now every construction will have it
        # hardcoded into the code, later it will be done by Machine objects

class AppendConstruction(Construction):
    def __init__(self, name, control, act_from_left=True, append_to_left=True):
        Construction.__init__(self)
        # when check is done, and an action is needed,
        # order of actions on machines is left to right or reverse
        self.act_from_left = act_from_left

        # when check is done, and an action is needed,
        # and we already have two machines chosen by the self.act_from_left
        # order traverse, on which machine do we want to append the other one
        self.append_to_left = append_to_left

class VerbConstruction(Construction):
    """A default construction for verbs. It reads definitions, discovers
    cases, and builds a control from it. After that, the act() will do the
    linking process, eg. link the verb with other words, object, subject, etc.
    """
    def __init__(self, name, machine):
        self.name = name
        self.machine = machine
        self.case_locations = self.discover_cases()
        control = self.generate_control()
        self.case_pattern = re.compile("N(OUN|P)[^C]*CAS<([^>]*)>")
        Construction.__init__(self, name, control)

    def generate_control(self):
        cases = self.case_locations.keys()
        
        # this will be a hypercube
        control = FSA()

        # zero state is for verb
        control.add_state("0", is_init=True, is_final=False)

        # inside states for the cube, except the last, accepting state
        for i in xrange(1, pow(2, len(cases))):
            control.add_state(str(i), is_init=False, is_final=False)

        # last node of the hypercube
        control.add_state(str(int(pow(2, len(cases)))),
                              is_init=False, is_final=True)

        # first transition
        control.add_transition(PosTransition("^VERB.*"), "0", "1")

        # count every transition as an increase in number of state
        for path in permutations(cases):
            actual_state = 1
            for case in path:
                increase = pow(2, cases.index(case))
                new_state = actual_state + increase
                if case == "NOM":
                    control.add_transition(PosTransition(
                        "NOUN(?!.*CAS)".format(case)),
                        str(actual_state), str(new_state))
                else:
                    control.add_transition(
                        PosTransition("CAS<{0}>".format(case)),
                        str(actual_state), str(new_state))
                actual_state = new_state
        return control

    def discover_cases(self, machine=None, d=None):
        if machine is None:
            machine = self.machine
        if d is None:
            d = defaultdict(list)

        for pi, p in enumerate(machine.base.partitions[1:]):
            pi += 1
            to_remove = None
            for mi, part_machine in enumerate(p):
                pn = part_machine.printname()
                if pn in deep_cases:
                    d[pn].append((machine, pi))
                    to_remove = mi

                # recursive call
                d.update(self.discover_cases(part_machine))

            if to_remove is not None:
                p = p[:to_remove] + p[to_remove+1:]
                machine.base.partitions[pi] = p

        return d

    def act(self, seq):
        # get case for every machine, and put them to right places

        result = []

        # put a clear machine into self.machine while verb_machine will be
        # the old self.machine, and the references in self.case_locations
        # will point at good locations in verb_machine
        clear_machine = copy(self.machine)
        verb_machine = self.machine
        self.machine = clear_machine
        result.append(verb_machine)

        for m in seq:
            if m.printname() == self.machine.printname():
                # this is the verb machine
                # copy the (referenceof) PosControl of the verb in the sentence
                # to the control of the new machine
                verb_machine.control = m.control
            else:
                matcher = self.case_pattern.match(m.control.pos)
                if matcher is not None or re.match("^NOUN", m.control.pos):
                    case = (matcher.group(2) if matcher is not None else "NOM")
                    if case not in self.case_locations:
                        raise Exception("""Got a NOUN with a useless case""")

                    for m_to, m_p_i in self.case_locations[case]:
                        m_to.append(m, m_p_i)
                else:
                    raise Exception("""Every machine at this point of the code
                                    has to match a case pattern""")

        return result


class TheConstruction(Construction):
    """NOUN<DET> -> The NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=True)
        control.add_transition(PrintnameTransition("the", exact=True), "0", "1")
        control.add_transition(PosTransition("^NOUN.*"), "1", "2")

        Construction.__init__(self, "TheConstruction", control)

    def act(self, seq):
        logging.debug("""Construction matched, running last check""")
        self.last_check(seq)
        logging.debug("""TheConstruction matched, running action""")
        seq[1].control.pos += "<DET>"
        return [seq[1]]

class DummyNPConstruction(Construction):
    """NP construction. NP -> Adj* NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=True)
        control.add_transition(PosTransition("^ADJ.*"), "0", "0")
        control.add_transition(PosTransition("^NOUN.*"), "0", "1")

        Construction.__init__(self, "DummyNPConstruction", control)

    def act(self, seq):
        logging.debug("""Construction matched, running last check""")
        self.last_check(seq)
        logging.debug("""DummyNPConstruction matched, running action""")
        noun = seq[-1]
        adjs = seq[:-1]
        for adj in adjs:
            noun.append(adj)
        return [noun]

class ElviraConstruction(Construction):
    def __init__(self):
        control = FSA()
        # TODO: to hypercube
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=False)
        control.add_state("3", is_init=False, is_final=False)
        control.add_state("4", is_init=False, is_final=True)
        control.add_transition(PrintnameTransition("vonat"), "0", "1")
        control.add_transition(PrintnameTransition("menetrend"), "1", "2")
        control.add_transition(PrintnameTransition("BEFORE_AT"), "2", "3")
        control.add_transition(PrintnameTransition("AFTER_AT"), "3", "4")

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

        return elvira_machine
        
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

