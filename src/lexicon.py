import logging
from itertools import chain
from collections import Iterable
import copy

from constants import deep_cases
from machine import Machine
from monoid import Monoid
from control import ElviraPluginControl
from construction import Construction

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        self.deep_cases = set(deep_cases)  # Set of deep cases

        # static will store only one machine per printname (key),
        # while active can store more
        self.static = {}
        # TODO: map: {active_machine : is it expanded?}
        self.active = {}
        # Constructions
        self.constructions = []
        self.create_elvira_machine()

    def create_elvira_machine(self):
        logging.warning("Elvira machine is created right " +
                        "now at init of Lexicon, HACKHACKHACK")
        # HACK
        elvira_control = ElviraPluginControl()
        elvira_machine = Machine(Monoid("elvira"), elvira_control)
        elvira_machine.append("BEFORE_AT")
        elvira_machine.append("AFTER_AT")
        elvira_machine.append("vonat")
        elvira_machine.append("menetrend")
        self.static["elvira"] = elvira_machine

    def __add_active_machine(self, m, expanded=False):
        """Helper method for add_active()"""
        printname = m.printname()
        if printname in self.active:
            already_expanded = self.active[printname].get(m, False)
            self.active[printname][m] = expanded | already_expanded
        else:
            self.active[printname] = {m: expanded}

    def add_active(self, what):
        """adds machines to active collection
        typically called to add a sentence being worked with"""
        if isinstance(what, Iterable):
            for m in what:
                self.__add_active_machine(m)
        elif isinstance(what, Machine):
            self.__add_active_machine(what)
        else:
            logging.error("""Calling Lexicon.add_active() with an incompatible
                          type""")

    def add_static(self, what):
        """adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser"""
        if isinstance(what, Machine):
            self.static[what.printname()] = what
        elif isinstance(what, Iterable):
            for m in what:
                self.add_static(m)

    def add_construction(self, what):
        """Adds construction(s) to the lexicon."""
        if isinstance(what, Construction):
            self.constructions.append(what)
        elif isinstance(what, Iterable):
            for c in what:
                self.constructions.append(c)

    def expand(self, machine):
        """expanding a machine
        if machine is not active, we raise an exception
        if machine is active but not in knowledge base, we warn the user,
        and do nothing
        if everything is okay, everything from every partition of the
        static machine is copied to the active one"""
        printname = machine.printname()
        if (printname not in self.active or
                machine not in self.active[printname]):
            raise Exception("""only active machines can be expanded
                            right now, but {0} is not active""".format(
                            printname))
        if printname not in self.static:
            logging.warning("""expanding a machine ({0}) that is not in
                            knowledge base ie. Lexicon.static""".format(
                            repr(printname)))
            self.active[printname][machine] = True
            return
        
        machine = self.unify_recursively(self.static[printname])

        # change expand status in active store
        self.active[printname][machine] = True

    def unify_recursively(self, static_machine, stop=None):
        """Returns the active machine that corresponds to @p static_machine. It
        recursively unifies all machines in all partitions of @p static_machine
        with machines in the active set. @p static_machine may be either a
        machine or a string.
        @param stop the set of machines already unified."""
        if stop is None:
            logging.debug("unify_recursively: " + Machine.to_debug_str(static_machine))
            stop = set()

        # If we have already unified this machine: just return
        static_printname = static_machine.printname()
        if static_printname in stop:
            return self.active[static_printname].keys()[0]
        # If static_machine is a string, we don't have much to do
        if isinstance(static_machine, str):
            if static_machine in self.active:
                # FIXME: [0] is a hack, fix it 
                return self.active[static_machine].keys()[0]
            else:
                # Linkers are handled as strings.
                if self.is_deep_case(static_machine):
                    return static_machine
                else:
                    active_machine = Machine(Monoid(static_machine))
                    self.__add_active_machine(active_machine)
                    return active_machine
        # If it's a machine, we create the corresponding active one
        elif isinstance(static_machine, Machine):
            static_name = static_machine.printname()
            if self.is_deep_case(static_machine):
                return Machine(Monoid(static_name))

            if static_name in self.active:
                active_machine = self.active[static_name].keys()[0]
            else:
                active_machine = Machine(Monoid(static_name))
                active_control = copy.deepcopy(static_machine.control)
                active_machine.set_control(active_control)
                self.__add_active_machine(active_machine)

            stop.add(static_name)

            # Now we have to walk through the tree recursively
            for i, part in enumerate(static_machine.base.partitions[1:]):
                part_index = i + 1
                for ss_machine in part:
                    as_machine = self.unify_recursively(ss_machine, stop)
                    active_machine.append_if_not_there(as_machine, part_index)
            return active_machine
        else:
            raise TypeError('static_machine must be a Machine or a str')

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
        printname = m.printname()
        try:
            return self.active[printname][m]
        except KeyError:
            logging.error("""asking whether a machine is expanded about a
                          non-active machine""")
            logging.debug("This machine is: " + m.printname())
            return None

    def get_expanded(self, inverse=False):
        """Returns the list of expanded machines."""
        result = []
        for pn, machines in self.active.iteritems():
            for machine in machines:
                # if inverse: return unexpandeds
                if inverse ^ machines[machine]:
                    result.append(machine)
        return result

    def get_unexpanded(self):
        return self.get_expanded(True)

    def clear_active(self):
        self.active = {}

    def is_deep_case(self, machine):
        """Returns @c True, if @p machine (which can be a string as well) is
        a deep case."""
        return machine.printname() in self.deep_cases

