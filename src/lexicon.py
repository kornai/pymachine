import logging
from itertools import chain
from collections import Iterable
import copy

from machine import Machine
from monoid import Monoid
from control import ElviraPluginControl, ConceptControl
from construction import Construction, AVMConstruction

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        # static will store only one machine per printname (key),
        # while active can store more
        self.static = {}
        # TODO: map: {active_machine : is it expanded?}
        self.active = {}
        # Constructions
        self.constructions = []
        # AVM name -> construction. Not used by default, have to be added to
        # self.constructions first via activation
        self.avm_constructions = {}
#        self.create_elvira_machine()

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
            logging.error("Calling Lexicon.add_active() with an incompatible" +
                          " type")

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
        """
        Adds construction(s) to the lexicon.
        @param what a construction, or an iterable thereof.
        """
        if isinstance(what, Construction):
            self.constructions.append(what)
        elif isinstance(what, Iterable):
            for c in what:
                if isinstance(what, Construction):
                    self.constructions.append(c)

    def add_avm_construction(self, what):
        """
        Adds an AVM construction. Constructions added via this function are
        in a 'dormant' state, which can only be changed by the activation
        algorithm.
        @param what an AVM construction, or an iterable thereof.
        """
        if isinstance(what, AVMConstruction):
            self.avm_constructions[what.avm.name()] = what
        elif isinstance(what, Iterable):
            for c in what:
                if isinstance(what, AVMConstruction):
                    self.avm_constructions[c.avm.name()] = c

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
            logging.warning(("expanding a machine ({0}) that is not in " + 
                            "knowledge base ie. Lexicon.static").format(
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
            logging.debug("unify_recursively:\n"
                          + Machine.to_debug_str(static_machine))
            stop = set()

        # If we have already unified this machine: just return
        static_printname = static_machine.printname()
        if static_printname in stop:
#            logging.debug('ur stops')
            return self.active[static_printname].keys()[0]
        # If static_machine is a string, we don't have much to do
#        logging.debug('ur static_machine {0}, type: {1}'.format(str(static_machine), str(type(static_machine))))
        if isinstance(static_machine, str):
            if static_machine in self.active:
                # FIXME: [0] is a hack, fix it 
#                logging.debug('ur str in active')
                return self.active[static_machine].keys()[0]
            else:
                if static_machine.startswith('#'):
#                    logging.debug('ur waking up')
                    self.wake_avm_construction(static_machine)
                    return None
#                logging.debug('ur activating str')
                active_machine = Machine(Monoid(static_machine), ConceptControl())
                self.__add_active_machine(active_machine)
                return active_machine
        # If it's a machine, we create the corresponding active one
        elif isinstance(static_machine, Machine):
            static_name = static_machine.printname()
#            logging.debug('Does {0} start with #? {1}'.format(static_name, static_name.startswith('#')))

            if static_name in self.active:
#                logging.debug('ur machine in active')
                active_machine = self.active[static_name].keys()[0]
            else:
#                logging.debug('Not in active')
                if static_name.startswith('#'):
#                    logging.debug('ur waking up')
                    self.wake_avm_construction(static_name)
                    return None
#                logging.debug('ur activating machine')
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
                    if as_machine is not None:
                        active_machine.append(as_machine, part_index)
            return active_machine
        else:
            raise TypeError('static_machine must be a Machine or a str')

    def wake_avm_construction(self, avm_name):
        """
        Copies an AVM construction from @c avm_constructions to @c constructions
        (that is, "wakes" it up).
        """
        avm_construction = self.avm_constructions.get(avm_name[1:])
        # TODO
        if avm_construction is not None and avm_construction not in self.constructions:
            self.constructions.append(avm_construction)

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
                if (not unicode(machine).startswith(u'#') and
                    unicode(machine) not in self.active):
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
            logging.error("asking whether a machine is expanded about a " +
                          "non-active machine")
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

    def active_machines(self):
        return [v.keys()[0] for v in self.active.values()]

    def clear_active(self):
        self.active = {}

