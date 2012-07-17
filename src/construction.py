from fst import FSA

class Construction(object):
    def __init__(self, name, control):
        
        self.name = name

        if not isinstance(control, FSA):
            raise TypeError("control has to be an FSA instance")
        self.control = control

    def check(self, seq):
        # read the sequence first, and give it to the control
        pass

        # if control got into acceptor state, do something
        if self.control.in_final():
            self.act()
        else:
            return None

    def act(self):
        # arbitrary python code, now every construction will have it
        # hardcoded into the code, later it will be done by Machine objects
        pass
