import logging
from itertools import chain
from collections import Iterable
import copy

from machine import Machine
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
        self.clear_active()

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
        """
        adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser

        @note We assume that a machine is added to the static graph only once.
        """
        if isinstance(what, Machine):
            whats_already_seen = self.static.get(what.printname(), [])
            if len(whats_already_seen) == 0:
                self.static[what.printname()] = [what]
                placeholder = what
            else:
                # Update placeholder with the definition
                placeholder = whats_already_seen[0]
                placeholder.partitions = what.partitions
                for part_i, part in enumerate(placeholder.partitions):
                    for child in part:
                        child.add_parent_link(placeholder, part_i)
                        child.del_parent_link(what,        part_i)
                placeholder.control    = what.control
                placeholder.parents.union(what.parents)
                self.__recursive_replace(placeholder, what, placeholder)

            unique_machines = placeholder.unique_machines_in_tree()
            for um in unique_machines:
                um_already_seen = self.static.get(um.printname(), [])
                if len(um_already_seen) == 0:
                    # There is no entry for the machine: add it (+ a placeholder
                    # for the canonical slot, if the machine is modified)
                    if len(um.children()) == 0:
                        um_already_seen = [um]
                    else:
                        # TODO: what to do with the modified words?
                        um_already_seen = [Machine(um.printname()), um]
                    self.static[um.printname()] = um_already_seen
                else:
                    # Add to the entry list, if modified
                    if len(um.children()) > 0:
                        um_already_seen.append(um)

                # Unify with the canonical entry if unmodified 
                if len(um.children()) == 0:
                    self.__recursive_replace(placeholder, um, um_already_seen[0])

        # Add to graph
        elif isinstance(what, Iterable):
            for m in what:
                self.add_static(m)

    def __recursive_replace(self, root, from_m, to_m, visited=None):
        """
        Replaces all instances of @p from_m with @p to_m in the tree under
        @p root. @p to_m inherits all properties (content of partitions, etc.)
        of @p from_m. This method cannot replace the root of the tree.

        @param visited the set of already visited roots.
        """
        if visited is None:
            visited = set()
        if root in visited:
            return

        # TODO: make person1[drunk], person2 DRINKS, person1 == person2?
        visited.add(root)
        to_visit = set()
        for part_i, part in enumerate(root.partitions):
            for m_i, m in enumerate(part):
                if not (m == to_m):
                    num_children = len(m.children())
                    if m.printname() == from_m.printname() and m is not to_m:
                        if num_children == 0:
                            # TODO Machine.replace()?
                            part[m_i] = to_m
                            #root.remove(m, part_i)
                            #root.append(m, to_m, part_i)
                            to_m.parents.union(m.parents)
                            m.del_parent_link(root, part_i)
                        else:
                            # No replacement if from_m is modified
                            # TODO: w = 0 link from m to to_m
                            # TODO: test direct recursion
                            m.append(to_m, 0)
                    if num_children > 0:
                        to_visit.add(m)
        for m in to_visit:
            self.__recursive_replace(m, from_m, to_m, visited)

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
            self.avm_constructions[what.avm.name] = what
        elif isinstance(what, Iterable):
            for c in what:
                if isinstance(what, AVMConstruction):
                    self.avm_constructions[c.avm.name] = c

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
            stop = set()

        if unicode(static_machine) == u'IS_A':
            return None
        # If we have already unified this machine: just return
        if not isinstance(static_machine, str) and not isinstance(static_machine, unicode):
            static_printname = static_machine.printname()
        else:
            static_printname = static_machine
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
                active_machine = Machine(static_machine, ConceptControl())
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
                active_machine = Machine(static_name)
                active_control = copy.deepcopy(static_machine.control)
                active_machine.set_control(active_control)
                self.__add_active_machine(active_machine)

            stop.add(static_name)

            # Now we have to walk through the tree recursively
            for i, part in enumerate(static_machine.partitions):
                for ss_machine in part:
                    as_machine = self.unify_recursively(ss_machine, stop)
                    if as_machine is not None:
                        active_machine.append(as_machine, i)
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
            for machine in chain(*static_machine.partitions):
                has_machine = True
                if (not unicode(machine).startswith(u'#') and
                    unicode(machine) not in self.active):
                    break
            else:
                if has_machine:
                    m = Machine(printname, copy.copy(static_machine.control))
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
        """
        Resets the lexicon to the default (inactive) state. Must be called
        between activation phases.
        """
        self.active = {}
        # HACK
        self.unify_recursively('train')

        # Resets the AVM constructions.
        avm_constructions = [c for c in self.constructions
                             if c.type_ == Construction.AVM]
        for c in avm_constructions:
            c.avm.clear()
            if c in self.avm_constructions.values():
                self.constructions.remove(c)

    def test_static_graph_building():
        """Tests the static graph building procedure."""
        pass

