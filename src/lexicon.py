import logging
from itertools import chain
import copy

from constants import deep_cases
from machine import Machine
from monoid import Monoid
from control import ElviraPluginControl

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        self.deep_cases = set(deep_cases)  # Set of deep cases

        # static will store only one machine per printname (key),
        # while active can store more
        self.static = {}
        # TODO: map: {active_machine : is it expanded?}
        self.active = {}
        self.create_elvira_machine()

    def create_elvira_machine(self):
        logging.warning("""Elvira machine is created right
                        now at init of Lexicon, HACKHACKHACK""")
        # HACK
        elvira_control = ElviraPluginControl()
        elvira_machine = Machine(Monoid("elvira"), elvira_control)
        elvira_machine.append_if_not_there("BEFORE_AT")
        elvira_machine.append_if_not_there("AFTER_AT")
        elvira_machine.append_if_not_there("vonat")
        elvira_machine.append_if_not_there("menetrend")
        self.static["elvira"] = elvira_machine

    def __add_active_machine(self, m, expanded=False):
        """Helper method for add_active()"""
        printname = str(m)
        if printname in self.active:
            self.active[printname][m] = expanded
        else:
            self.active[printname] = {m: expanded}

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
                            right now, but {0} is not active""".format(
                            printname))
        if printname not in self.static:
            logging.warning("""expanding a machine ({0}) that is not in
                            knowledge base ie. Lexicon.static""".format(
                            printname))
            self.active[printname][machine] = True
            return
        
        logging.debug("Expanding machine: " + str(machine))
        for i, part in enumerate(self.static[printname].base.partitions[1:]):
            logging.debug(part)
            # we skipped 0th partition so index has to be corrected
            part_index = i + 1

            # FIXME: copy to active
            for anything in part:
                #logging.debug(anything)
                #logging.debug(type(anything))
                machine_to_append = None

                if str(anything) in self.active:
                    # FIXME: [0] is a hack, fix it
                    machine_to_append = self.active[anything].keys()[0]
                else:
                    if isinstance(anything, Machine):
                        # FIXME: The deep copy must be a manual, recursive one,
                        # creating a new machine only if self.active + the set
                        # of machines created during the recursion itself do
                        # not contain the (name) of the new machine -- in other
                        # words, proper unification.
                        machine_to_append = copy.deepcopy(anything)
                    else:
                        machine_to_append = Machine(Monoid(anything))
                
                machine.append_if_not_there(machine_to_append, part_index)
                
                pn = str(machine_to_append)
                if pn not in self.active:
                    self.active[pn] = {}
                    self.active[pn][machine_to_append] = False

        logging.debug(repr(self.active[printname].keys()[0].base.partitions))
        # change expand status in active store
        self.active[printname][machine] = True

    def activate(self):
        """Finds and returns the machines that should be activated by the
        machines already active. These machines are automatically added
        to self.active as well
        
        When exactly a machine should be activated is still up for
        consideration; however, currently this method returns a machine if
        all non-primitive machines on its partitions are active."""
        activated = []
        
        for printname, static_machine in self.static.iteritems():
            if printname in self.active:
                continue
            has_machine = False
            for machine in chain(*static_machine.base.partitions[1:]):
                has_machine = True
                if str(machine) not in self.active:
                    break
            else:
                if has_machine:
                    m = Machine(Monoid(printname), copy.copy(static_machine.control))
                    self.add_active(m)
                    activated.append(m)
        return activated

    def is_expanded(self, m):
        """Returns whether m is expanded or not"""
        printname = str(m)
        try:
            return self.active[printname][m]
        except KeyError:
            logging.error("""asking whether a machine is expanded about a
                          non-active machine""")
            logging.debug("This machine is: " + str(m))
            return None

    def get_expanded(self, inverse=False):
        """Returns the list of expanded machines."""
        logging.debug('get_expanded(' + str(inverse) + ')')
        result = []
        for pn, machines in self.active.iteritems():
            for machine in machines:
                # if inverse: return unexpandeds
                if inverse ^ machines[machine]:
                    result.append(machine)
        logging.debug("RESULT: " + ','.join(str(m) for m in result))
        return result

    def get_unexpanded(self):
        return self.get_expanded(True)

    def clear_active(self):
        self.active = {}

