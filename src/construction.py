from fst import FSA

class Construction(object):
    def __init__(self, name, control):
        self.name = name

        if not isinstance(control, FSA):
            raise TypeError("control has to be an FSA instance")
        self.control = control

    def check(self, seq):
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

    def act(self, seq):
        # arbitrary python code, now every construction will have it
        # hardcoded into the code, later it will be done by Machine objects
        pass

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
    def __init__(self):
        control = FSA()
        control.set_input_alphabet(set(["the", "NOUN"]))
        control.add_state("0", is_init=True, is_final=False)
        control.add_state("1", is_init=False, is_final=False)
        control.add_state("2", is_init=False, is_final=True)
        control.add_transition(self, "the", "0", "1")
        control.add_transition(self, "NOUN", "1", "2")

        Construction.__init__(self, "TheConstruction", control)

    def act(self, seq):
        seq[1].control.append("<DET>")
        return [seq[1]]

