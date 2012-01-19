import logging

from constants import deep_cases
from machine import Machine
from monoid import Monoid

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        self.deep_cases = set(deep_cases)  # Set of deep cases

        # static will store only one machine per printname (key),
        # while active can store more
        self.static = {}
        # TODO: map: {active_machine : is it expanded?}
        self.active = {}

    def __add_active_machine(self, m):
        """Helper method for add_active()"""
        printname = str(m)
        if printname in self.active:
            self.active[printname].add(m)
        else:
            self.active[printname] = set([m])

    def add_active(self, what):
        """
        adds machines to active collection
        typically called to add a sentence being worked with
        """
        if isinstance(what, list):
            for m in what:
                self.__add_active_machine(m)
        elif isinstance(what, Machine):
            self.__add_active_machine(what)
        else:
            logging.error("""Calling Lexicon.add_active() with an incompatible
                          type""")

    def add_static(self, machines):
        """
        adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser
        """
        for m in machines:
            printname = str(m)
            self.static[printname] = m

    def expand(self, machine):
        """
        expanding a machine
        if machine is not active, we raise an exception
        if machine is active but not in knowledge base, we warn the user,
        and do nothing
        if everything is okay, everything from every partition of the
        static machine is copied to the active one
        """
        printname = str(machine)
        if (printname not in self.active or
                machine not in self.active[printname]):
            raise Exception("""only active machines can be expanded
                            right now""")
        if printname not in self.static:
            logging.warning("""expanding a machine that is not in knowledge
                            base ie. Lexicon.static""")
            return
        
        for i, partition in self.static[printname].base.partitions[1:]:
            # we skipped 0th partition so index has to be corrected
            part_index = i + 1

            # FIXME: copy to active
            for anything in partition:
                machine.append_if_not_there(anything, part_index)

    def activate(self):
        """Finds and returns the machines that should be activated by the
        machines already active. These machines are automatically added
        to self.active as well
        
        When exactly a machine should be activated is still up for
        consideration; however, currently this method returns a machine if
        all non-primitive machines on its partitions are active."""
        activated = []
        
        for printname, static_machine in self.static.iteritems():
            to_activate = True
            for partition in static_machine.base.partitions[1:]:
                for machine in partition:
                    if str(machine) not in self.active:
                        to_activate = False
                        break
                if not to_activate:
                    break
            if to_activate:
                m = Machine(Monoid(printname))
                self.add_active(m)
                self.expand(m)
                activated.append(m)
        return activated

    def expanded(self):
        """Returns the list of expanded machines."""
        # TODO: implement
        pass

    def unexpanded(self):
        """Returns the list of unexpanded machines."""
        # TODO: implement
        pass

