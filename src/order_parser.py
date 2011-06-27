import sys

from machine import Machine
from monoid import Monoid
from control import PosControl as Control
from constructions import Construction, read_constructions

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
        word, pos = pos.split("/", 1)
        m = Machine(Monoid(word), Control(pos))
        machines.append(m)
    return machines

if __name__ == "__main__":
    order = read_order_file(file(sys.argv[1]))
    cons = read_constructions(file(sys.argv[2]))

    machines = create_machines(order)

    while True:
        something = False
        for con in cons:
            for i in xrange(len(machines) - 1):
                result = con.do(machines[i:i+2])
                if result is not None:
                    machines[i:i+2] = result
                    something = True

        if not something:
            break
        else:
            pass
    print " ".join([str(m) for m in machines])

