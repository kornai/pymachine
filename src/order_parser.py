import sys
import logging
from collections import defaultdict

from machine import Machine
from monoid import Monoid
from control import PosControl as Control
from definition_parser import read
from constructions import read_constructions, FinalCommand
from machine_exceptions import UnknownWordException, UnknownSentenceException, TooManySameCasesException, TooManyLocationsException
from constants import locative_cases

class OrderParser:
    def __init__(self, constructions, definitions):
        """
        TODO rename to CommandParser? english expert needed

        constructions are used for transformations
        definitions are used to raise exception when unknown
          word in command
        """
        self._constructions = constructions
        self._definitions = definitions

        # index has to be changed if other language
        self._vocab = set(fourlang[0] for fourlang in self._definitions.keys())

    def read_order_file(self, f):
        sentence = []
        for line in f:
            le = line.strip().split("\t")
            if len(le) == 0:
                break
            else:
                sentence.append(tuple(le))
        return sentence

    def create_machines(self, sen):
        """
        creates machines from a tagged sentence
        returns a list of machines, one machine per word
        """
        machines = []
        for word, pos in sen:
            stem, _, pos = pos.split("|", 2)
            if stem not in self._vocab:
                if stem == 'unknown':
                    raise UnknownWordException(word)
                raise UnknownWordException(stem)

            m = Machine(Monoid(stem), Control(pos))
            machines.append(m)
        return machines

    def run_constructions_over_machines(self, constructions, machines):
        """
        runs some construction over a list of machines
        constructions is an arg (instead of using self.constructions)
          because this way one can run only some of the constructions
        """

        # has something happened?
        something = False

        # iterate over all the constructions
        for con in constructions:
            len_of_rule = len(con.rule_right)

            # iterate over machine n-tuples
            for i in xrange(len(machines) - len_of_rule + 1):

                # run the construction over the machine tuple
                # of construction is not applicable, no change will be made
                result = con.do(machines[i:i+len_of_rule])
                if result is not None:
                    # possible shortening of machines list
                    machines[i:i+len_of_rule] = result
                    something = True
        return something

    def check_ambiguity(self, machines):
        known_cases = defaultdict(list)
        known_locatives = []
        for m in machines:
            case = m.control.get_case()
            if case is not None:
                known_cases[case].append(m)
                if case in locative_cases:
                    known_locatives.append(m)
            else:
                if m.control.is_a(Control("PP")):
                    known_locatives.append(m)

        if len(known_locatives) > 1:
            raise TooManyLocationsException(known_locatives)

        for case in known_cases:
            if len(known_cases[case]) > 1:
                raise TooManySameCasesException(known_cases[case], case)

    def run(self, order):
        """
        main function
        - creates machines from order
        - transform machines by using constructions
        """

        # creating machines
        machines = self.create_machines(order)

        #First: all non-final commands
        while True:
            something = False
            non_final_constructions = [con for con in self._constructions if not isinstance(con.command, FinalCommand)]
            something |= self.run_constructions_over_machines(non_final_constructions, machines)
            if not something:
                break
            else:
                pass

        self.check_ambiguity(machines)

        #Second: verb commands
        #TODO fucking copy-paste, should be put in a function
        while True:
            something = False
            final_constructions = [con for con in self._constructions if isinstance(con.command, FinalCommand)]
            something |= self.run_constructions_over_machines(final_constructions, machines)
            # only one verb command can be run right now
            # no need to be in a while
            break

        # TODO why [0]?
        # this is a temporary solution, the only valuable result is a list, that has only one element

        if len(machines) > 1:
            logging.debug(u"Sentence cannot be completely understood")
            raise UnknownSentenceException() 
        else:
            return machines[0]

if __name__ == "__main__":
    definitions = read(file(sys.argv[3]))
    cons = read_constructions(file(sys.argv[2]), definitions)
    op = OrderParser(cons, definitions)
    order = op.read_order_file(file(sys.argv[1]))
    op.run(order)


