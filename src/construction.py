import logging
import re
from collections import defaultdict
from itertools import permutations
from copy import deepcopy as copy

from fst import FSA
from matcher import PrintnameMatcher
from matcher import PosControlMatcher as PosMatcher
from machine import Machine
from monoid import Monoid
from control import PosControl, ElviraPluginControl
from constants import deep_cases

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

class VerbConstruction(Construction):
    """A default construction for verbs. It reads definitions, discovers
    cases, and builds a control from it. After that, the act() will do the
    linking process, eg. link the verb with other words, object, subject, etc.
    """
    def __init__(self, name, machine, supp_dict):
        self.name = name
        self.machine = machine
        self.supp_dict = supp_dict
        self.arg_locations = self.discover_arguments()
        self.phi = self.generate_phi()
        control = self.generate_control()
        self.case_pattern = re.compile("N(OUN|P)[^C]*CAS<([^>]*)>")
        Construction.__init__(self, name, control)
        self.activated = False

    def generate_phi(self):
        arguments = self.arg_locations.keys()
        # creating Matcher objects from arguments
        self.matchers = {}
        phi = {}

        # Verb transition will imply no change, we put it into phi
        # to implement act() easier
        vm = PosMatcher("^VERB.*")
        self.matchers["VERB"] = vm
        phi[vm] = None

        # normal arguments
        for arg in arguments:
            if arg.startswith("@"):
                pm = PosMatcher(
                    "({0})".format("|".join(self.supp_dict[arg[1:]])))
                self.matchers[arg] = pm
                phi[pm] = self.arg_locations[arg]

            # NOM case is implicit, that is why we need a distinction here
            elif arg == "NOM":
                pm = PosMatcher("NOUN(?!.*CAS)".format(arg))
                self.matchers[arg] = pm
                phi[pm] = self.arg_locations[arg]

            else:
                pm = PosMatcher("CAS<{0}>".format(arg))
                self.matchers[arg] = pm
                phi[pm] = self.arg_locations[arg]
        return phi

    def generate_control(self):
        arguments = self.matchers.keys()
        arguments.remove("VERB")
        
        # this will be a hypercube
        control = FSA()

        # zero state is for verb
        control.add_state("0", is_init=True, is_final=False)

        # inside states for the cube, except the last, accepting state
        for i in xrange(1, pow(2, len(arguments))):
            control.add_state(str(i), is_init=False, is_final=False)

        # last node of the hypercube
        control.add_state(str(int(pow(2, len(arguments)))),
                              is_init=False, is_final=True)

        # first transition
        control.add_transition(self.matchers["VERB"], "0", "1")

        # count every transition as an increase in number of state
        for path in permutations(arguments):
            actual_state = 1
            for arg in path:
                increase = pow(2, arguments.index(arg))
                new_state = actual_state + increase
                control.add_transition(self.matchers[arg],
                        str(actual_state), str(new_state))

                actual_state = new_state
        return control

    def discover_arguments(self, machine=None, d=None):
        if machine is None:
            machine = self.machine
        if d is None:
            d = defaultdict(list)

        for pi, p in enumerate(machine.base.partitions[1:]):
            pi += 1
            to_remove = None
            for mi, part_machine in enumerate(p):
                pn = part_machine.printname()
                # we are interested in deep cases and
                # supplementary regexps
                if pn in deep_cases or pn.startswith("@"):
                    d[pn].append((machine, pi))
                    to_remove = mi

                # recursive call
                d.update(self.discover_arguments(part_machine, d))

            if to_remove is not None:
                p = p[:to_remove] + p[to_remove+1:]
                machine.base.partitions[pi] = p

        return d

    def check(self, seq):
        if self.activated:
            return False
        else:
            return Construction.check(self, seq)

    def act(self, seq):
        result = []

        # put a clear machine into self.machine while verb_machine will be
        # the old self.machine, and the references in self.arg_locations
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

        for m in seq:
            for transition in self.phi:
                # skip None transitions (VERB)
                if self.phi[transition] is None:
                    continue

                if transition.match(m):
                    # possible multiple places for one machine
                    for m_to, m_p_i in self.phi[transition]:
                        m_to.append(m, m_p_i)
                    break

        self.activated = True
        return result

class AVMConstruction(Construction):
    """this class will fill the slots in the AVM"""
    def __init__(self, avm, name):
        self.avm = avm
        self.phi = self.generate_phi()
        control = self.generate_control()
        Construction.__init__(self, name, control, type_=Construction.AVM)

    def generate_phi(self):
        phi = {}
        for key in self.avm:
            matcher, _, _, _ = self.avm[key]
            phi[matcher] = key
        return phi

    def generate_control(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)

        state_num = 1
        for key in self.avm:
            state_name = str(state_num)
            matcher, _, _, _ = self.avm[key]
            control.add_state(state_name, is_init=False, is_final=True)
            control.add_transition(matcher, "0", state_name)
            state_num += 1
        return control

    def act(self, seq):
        for machine in seq:
            for matcher in self.phi:
                if matcher.match(machine):
                    self.avm[self.phi[matcher]] = machine
        return [self.avm]

class TheConstruction(Construction):
    """NOUN<DET> -> The NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=True)
        control.add_transition(PrintnameMatcher("^az?$"), "0", "1")
        control.add_transition(PosMatcher("^NOUN.*"), "1", "2")

        Construction.__init__(self, "TheConstruction", control,
                              type_=Construction.CHUNK)

    def act(self, seq):
        logging.debug("Construction matched, running last check")
        self.last_check(seq)
        logging.debug("TheConstruction matched, running action")
        seq[1].control.pos += "<DET>"
        return [seq[1]]

class DummyNPConstruction(Construction):
    """NP construction. NP -> Adj* NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=True)
        control.add_transition(PosMatcher("^ADJ.*"), "0", "0")
        control.add_transition(PosMatcher("^NOUN.*"), "0", "1")

        Construction.__init__(self, "DummyNPConstruction", control,
                              type_=Construction.CHUNK)

    def act(self, seq):
        logging.debug("Construction matched, running last check")
        self.last_check(seq)
        logging.debug("DummyNPConstruction matched, running action")
        noun = seq[-1]
        adjs = seq[:-1]
        for adj in adjs:
            noun.append(adj)
        return [noun]

class MaxNP_InBetweenPostP_Construction(Construction):
    """NP -> NOUN POSTP[ATTRIB]|ADJ NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=False)
        control.add_state("3", is_init=False, is_final=True)
        control.add_transition(PosMatcher("^NOUN.*"), "0", "1")
        control.add_transition(PosMatcher("POSTP\[ATTRIB\]\|ADJ", exact=True), "1", "2")
        control.add_transition(PosMatcher("^NOUN.*"), "2", "3")
        Construction.__init__(self, "MaxNP_InBetweenPostP_Construction", control,
                              type_=Construction.CHUNK)

    def act(self, seq):
        logging.debug("Construction matched, running last check")
        self.last_check(seq)
        logging.debug("MaxNP_InBetweenPostP_Construction matched, running action")
        noun1 = seq[0]
        postp = seq[1]
        noun2 = seq[2]
        postp.append(noun1, 2)
        postp.append(noun2, 1)
        return [noun2]

class PostPConstruction(Construction):
    """PP -> NOUN POSTP"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=True)
        control.add_transition(PosMatcher("^NOUN.*"), "0", "1")
        control.add_transition(PosMatcher("POSTP", exact=True), "1", "2")
        Construction.__init__(self, "PostPConstruction", control, type_=
                              Construction.CHUNK)

    def act(self, seq):
        logging.debug("Construction matched, running last check")
        self.last_check(seq)
        logging.debug("PostPConstruction matched, running action")
        noun1 = seq[0]
        postp = seq[1]
        noun2 = seq[2]
        postp.append(noun1, 2)
        postp.append(noun2, 1)
        return [noun2]

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

