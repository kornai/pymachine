import sys

from machine import Machine
from monoid import Monoid
from control import PosControl as Control
from definition_parser import read
from constructions import read_constructions

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
        word, pos = pos.split("||", 1)
        m = Machine(Monoid(word), Control(pos))
        machines.append(m)
    return machines

def run(order, definitions, constructions):
    machines = create_machines(order)

    while True:
        something = False
        for con in constructions:
            l = len(con.rule_right)
            for i in xrange(len(machines) - l + 1):
                result = con.do(machines[i:i+l])
                if result is not None:
                    machines[i:i+l] = result
                    something = True

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


