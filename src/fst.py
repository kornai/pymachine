from collections import defaultdict, Iterable
import logging

from machine import Machine
from matcher import Matcher
from avm import AVM

class FSA(object):
    def __init__(self):
        self.states = set()
        self.input_alphabet = set()
        self.init_states = set()
        self.final_states = set()
        self.transitions = defaultdict(dict)
        self.active_states = None

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

    def add_transition(self, matcher, input_state, output_state):
        if input_state not in self.states or output_state not in self.states:
            raise ValueError("transition states has to be in states already")
        if not isinstance(matcher, Matcher):
            raise TypeError("transition's matcher has to be of type Matcher")
        self.transitions[input_state][matcher] = output_state

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
        if isinstance(what, Machine) or isinstance(what, AVM):
            self.read_machine(what)
        elif isinstance(what, Iterable):
            for what_ in what:
                self.read(what_)

class FST(FSA):
    def __init__(self):
        FSA.__init__(self)

    def add_transition(self, matcher, operators, input_state, output_state):
        if input_state not in self.states or output_state not in self.states:
            raise ValueError("transition states has to be in states already")
        if not isinstance(matcher, Matcher):
            raise TypeError("transition's matcher has to be of type Matcher")
        self.transitions[input_state][matcher] = (output_state, operators)

    def read_machine(self, machine):
        self.check_states()
        if self.active_states is None:
            self.init_active_states()
        new_active_states = set() 
        for active_state in self.active_states:
            for transition, (out_state, operators) in (
                self.transitions[active_state].iteritems()):

                if transition.match(machine):
                    for op in operators:
                        op.act()
                    new_active_states.add(out_state)
        self.active_states = new_active_states

