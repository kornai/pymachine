from collections import defaultdict, Iterable
import logging
assert logging  # silence pyflakes

from avm import AVM
from machine import Machine
from matcher import Matcher

class FSA(object):
    def __init__(self):
        self.states = set()
        self.input_alphabet = set()
        self.init_states = set()
        self.final_states = set()
        self.transitions = defaultdict(dict)
        self.active_states = None

    def __str__(self):
        return "{0}\nstates: {1}\ntransitions: {2}\ninitial states: {3}\
            final states: {4}".format(
            type(self), self.states, self.transitions,
            self.init_states, self.final_states)

    def to_dot(self):
        lines = ['digraph finite_state_machine {\n\tdpi=80;']
        #lines.append('\tordering=out;')
        for state in self.states:
            if state in self.final_states:
                shape = 'doublecircle'
            else:
                shape = 'circle'
            lines.append('\tnode [shape = {0}]; {1};'.format(shape, state))
        for state1, edges in self.transitions.iteritems():
            for transition, state2 in edges.iteritems():
                if isinstance(state2, tuple):

                    #TODO this should work nicely too
                    #transition = "{0}:{1}".format(transition, state2[1])

                    state2 = state2[0]

                lines.append('\t{0} -> {1} [ label = "{2}" ];'.format(
                    state1, state2, transition))
        lines.append('}')
        return '\n'.join(lines)

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

    def read_machine(self, machine, dry_run=False):
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

    def read(self, what, dry_run=False):
        if isinstance(what, Machine) or isinstance(what, AVM):
            self.read_machine(what, dry_run=dry_run)
        elif isinstance(what, Iterable):
            for what_ in what:
                self.read(what_, dry_run=dry_run)

class FST(FSA):
    def __init__(self):
        FSA.__init__(self)

    def add_transition(self, matcher, operators, input_state, output_state):
        if input_state not in self.states or output_state not in self.states:
            raise ValueError("transition states has to be in states already")
        if not isinstance(matcher, Matcher):
            raise TypeError("transition's matcher has to be of type Matcher")
        self.transitions[input_state][matcher] = (output_state, operators)

    def read_machine(self, machine, dry_run=False):
        #This is called so often, it should not create debug messages
        if not dry_run:
            logging.debug('FST reading machine: {}'.format(machine))
        #logging.debug("FST.read_machine() called with {0}".format(machine))
        self.check_states()
        if self.active_states is None:
            self.init_active_states()
        new_active_states = set()
        #logging.debug("Old active: {0}".format(self.active_states))
        for active_state in self.active_states:
            for transition, (out_state, operators) in (
                    self.transitions[active_state].iteritems()):

                if transition.match(machine):
                    #logging.info('FST: matching transitions: {}'.format(
                    #    transition))
                    if not dry_run:
                        for op in operators:
                            logging.debug('running operator: {}'.format(op))
                            op.act(machine)
                    new_active_states.add(out_state)

                    """TODO we now assume that there's only one edge from each
                    state matching any given machine"""

                    break

        # HACK no sink right now
        if len(new_active_states) > 0:
            self.active_states = new_active_states
        #logging.debug("New active: {0}".format(self.active_states))
