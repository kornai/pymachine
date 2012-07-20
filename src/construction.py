import logging

from fst import FSA
from machine import Machine
from monoid import Monoid
from control import PosControl

class Construction(object):
    def __init__(self, name, control):
        self.name = name

        if not isinstance(control, FSA):
            raise TypeError("control has to be an FSA instance")
        self.control = control

    def check(self, seq):
        logging.debug("""Checking {0} construction for matching with
                      {1} machines""".format(self.name, seq))
        for machine in seq:
            self.control.read_symbol(machine.control)

    def run(self, seq):
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

class TheConstruction(Construction):
    """NOUN<DET> -> The NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=True)
        control.add_transition(self, "^the$", "0", "1")
        control.add_transition(self, "^NOUN.*", "1", "2")

        Construction.__init__(self, "TheConstruction", control)

    def act(self, seq):
        logging.debug("""Construction matched, running last check""")
        self.last_check(seq)
        logging.debug("""TheConstruction matched, running action""")
        seq[1].control += "<DET>"
        return [seq[1]]

class DummyNPConstruction(Construction):
    """NP construction. NP -> Adj* NOUN"""
    def __init__(self):
        control = FSA()
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=True)
        control.add_transition(self, "^ADJ.*", "0", "0")
        control.add_transition(self, "^NOUN.*", "0", "1")

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

def test():
    a = Machine(Monoid("a"))
    a.control = PosControl("DET")
    kek = Machine(Monoid("kek"))
    kek.control = PosControl("ADJ")
    kockat = Machine(Monoid("kockat"))
    kockat.control = PosControl("NOUN<CAS<ACC>>")

    npc = DummyNPConstruction()
    thec = TheConstruction()

    res = npc.run([kek, kockat])
    print res
    res = thec.run([a, res])
    print res


if __name__ == "__main__":
    test()

