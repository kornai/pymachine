import sys

from machine import Machine
from monoid import Monoid
from control import PosControl as Control
from definition_parser import read
from constructions import read_constructions, VerbCommand

def read_order_file(f):
    sentence = []
    for line in f:
        le = line.strip().split("\t")
        if len(le) == 0:
            break
        else:
            sentence.append(tuple(le))
    return sentence

def create_machines(sen):
    machines = []
    for _, pos in sen:
        word, _, pos = pos.split("|", 2)
        m = Machine(Monoid(word), Control(pos))
        machines.append(m)
    return machines

def run_constructions_over_machines(constructions, machines):
    something = False
    for con in constructions:
        l = len(con.rule_right)
        for i in xrange(len(machines) - l + 1):
            result = con.do(machines[i:i+l])
            if result is not None:
                machines[i:i+l] = result
                something = True
    return something

def run(order, definitions, constructions):
    machines = create_machines(order)

    while True:
        something = False
        non_verb_constructions = [con for con in constructions if not isinstance(con.command, VerbCommand)]
        verb_constructions = [con for con in constructions if isinstance(con.command, VerbCommand)]
        something |= run_constructions_over_machines(non_verb_constructions, machines)
        something |= run_constructions_over_machines(verb_constructions, machines)
        if not something:
            break
        else:
            pass
    # TODO why [0]?
    return machines[0]

if __name__ == "__main__":
    order = read_order_file(file(sys.argv[1]))
    definitions = read(file(sys.argv[3]))
    cons = read_constructions(file(sys.argv[2]), definitions)
    run(order, definitions, cons)


