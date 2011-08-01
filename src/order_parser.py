import sys

from machine import Machine
from monoid import Monoid
from control import PosControl as Control
from definition_parser import read
from constructions import read_constructions, VerbCommand


class OrderParser:
    def __init__(self, constructions, definitions):
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
        machines = []
        for _, pos in sen:
            word, _, pos = pos.split("|", 2)
            if word not in self._vocab:
                from exceptions import UnknownWordException
                raise UnknownWordException(word)

            m = Machine(Monoid(word), Control(pos))
            machines.append(m)
        return machines

    def run_constructions_over_machines(self, constructions, machines):
        something = False
        for con in constructions:
            l = len(con.rule_right)
            for i in xrange(len(machines) - l + 1):
                result = con.do(machines[i:i+l])
                if result is not None:
                    machines[i:i+l] = result
                    something = True
        return something

    def run(self, order):
        machines = self.create_machines(order)

        #First: all non-verb commands
        while True:
            something = False
            non_verb_constructions = [con for con in self._constructions if not isinstance(con.command, VerbCommand)]
            something |= self.run_constructions_over_machines(non_verb_constructions, machines)
            if not something:
                break
            else:
                pass

        #Second: verb commands
        #TODO fucking copy-paste, should be put in a function
        while True:
            something = False
            verb_constructions = [con for con in self._constructions if isinstance(con.command, VerbCommand)]
            something |= self.run_constructions_over_machines(verb_constructions, machines)
            if not something:
                break
            else:
                pass
        # TODO why [0]?
        return machines[0]

if __name__ == "__main__":
    definitions = read(file(sys.argv[3]))
    cons = read_constructions(file(sys.argv[2]), definitions)
    op = OrderParser(cons, definitions)
    order = op.read_order_file(file(sys.argv[1]))
    op.run(order)


