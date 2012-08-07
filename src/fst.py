from collections import defaultdict, Iterable
import logging
import re

from control import PosControl, ConceptControl
from machine import Machine

class Transition(object):
    def __init__(self, string, exact=False):
        if exact:
            self.input_ = re.compile("^{0}$".format(string))
        else:
            self.input_ = re.compile("{0}".format(string))

    def match(self, machine):
        raise NotImplementedError()

class PrintnameTransition(Transition):
    def match(self, machine):
        str_ = machine.printname()
        return self.input_.search(str_) is not None

class PosControlTransition(Transition):
    def match(self, machine):
        if not isinstance(machine.control, PosControl):
            return False
        str_ = machine.control.pos
        return self.input_.search(str_) is not None

class ConceptTransition(PrintnameTransition):
    def match(self, machine):
        if PrintnameTransition.match(self, machine):
            return isinstance(machine.control, ConceptControl)
        else:
            return False


class FSA(object):
    def __init__(self, regex_transitions=True):
        self.states = set()
        self.input_alphabet = set()
        self.init_states = set()
        self.final_states = set()
        self.transitions = defaultdict(dict)
        self.active_states = None
        self.regex_transitions = regex_transitions

    def add_state(self, state, is_init=False, is_final=False):
        self.states.add(state)
        if is_init:
            self.set_init(state)
        if is_final:
            self.set_final(state)

    def add_states(self, states):
        for state in states:
            if isinstance(state, tuple) and len(state) == 3:
                self.add_state(*state)
            else:
                raise TypeError("states for FSA.add_states() has to be tuples")

    def set_init(self, state):
        if state not in self.states:
            raise ValueError("state to be init has to be in states already")
        else:
            self.init_states.add(state)

    def set_final(self, state):
        if state not in self.states:
            raise ValueError("state to be final has to be in states already")
        else:
            self.final_states.add(state)

    def add_transition(self, transition, input_state, output_state):
        if input_state not in self.states or output_state not in self.states:
            raise ValueError("transition states has to be in states already")
        if not isinstance(transition, Transition):
            raise TypeError("transition has to be of type Transition")
        self.transitions[input_state][transition] = output_state

    def check_states(self):
        if len(self.states) == 0:
            raise Exception("FSA has no states")
        if len(self.init_states) == 0:
            raise Exception("No init states in the FSA")
        if len(self.final_states) == 0:
            raise Exception("No final/acceptor states in the FSA")

    def init_active_states(self):
        self.active_states = set(self.init_states)

    def reset(self):
        self.init_active_states()

    def in_final(self):
        return len(self.active_states & self.final_states) > 0

    def read_machine(self, machine):
        self.check_states()
        if self.active_states is None:
            self.init_active_states()
        new_active_states = set() 
        for active_state in self.active_states:
            for transition, out_state in (
                self.transitions[active_state].iteritems()):

                if transition.match(machine):
                    new_active_states.add(out_state)
        self.active_states = new_active_states

    def read(self, what):
        if isinstance(what, Machine):
            self.read_machine(what)
        elif isinstance(what, Iterable):
            for what_ in what:
                self.read(what_)

class FST(FSA):
    def __init__(self, output_alphabet=None):
        FSA.__init__(self)
        if output_alphabet is None:
            self.output_alphabet = set()
        else:
            self.set_output_aplhabet(output_alphabet)

    def set_output_alphabet(self, a):
        if isinstance(a, set):
            self.output_alphabet = a
        else:
            raise TypeError("output alphabet has to be type of set")

    def add_transition(self, input_string, output_string, input_state,
                       output_state):
        # TODO
        # outputs are strings? what if input was regexp?
        raise Exception("FST.add_transition() has to be implemented.")

    def read_symbol(self, string):
        # TODO
        # deterministic or non-deterministic?
        # output is a print, a function call or what?
        raise Exception("FST.read_symbol() has to be implemented.")

