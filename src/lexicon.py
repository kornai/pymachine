import logging
from itertools import chain
from collections import Iterable, defaultdict
import copy

from pymachine.src.machine import Machine
from pymachine.src.control import ConceptControl
from pymachine.src.construction import Construction, AVMConstruction
from pymachine.src.constants import id_sep
import sys

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        # static will store only one machine per printname (key),
        # while active can store more
        self.static = {}
        # e.g. {'in': {'in_2758', 'in_13'}}, where in_XXXs are keys in static
        self.static_disambig = defaultdict(set)
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
        Add lexical definition to the static collection 
        while keeping prior links (parent links).
        @note We assume that a machine is added to the static graph only once.
        """
        if isinstance(what, Machine):
            self.__add_static_recursive(what)
        # Call for each item in an iterable
        elif isinstance(what, Iterable):
            for m in what:
                self.add_static(m)

    # TODO: dog canonical == dog[faithful]!
    def __add_static_recursive(self, curr_from, replacement=None):
        if replacement == None:
            replacement = {}
        #print "Processing word ", curr_from
        #sys.stdout.flush()

        if curr_from not in replacement:
            # Deep cases are not canonized
            if curr_from.deep_case():
                replacement[curr_from] = curr_from
            else:
                if curr_from.printname().isupper():
                    curr_from.printname_ = curr_from.printname().lower()
                #print "Not in replacement"
                # Does this machine appear in the static tree?
                from_already_seen = self.__get_disambig_incomplete(curr_from.printname())
#                print "from already seen", curr_from.printname(), from_already_seen
                # If not: simply adding the new machine/definition...
                if len(from_already_seen) == 0:
                    #print "from already seen = 0"
                    # This is the definition word, or no children: accept as
                    # canonical / placeholder
                    if len(curr_from.children()) == 0 or len(replacement) == 0:
                        #print "adding as canoncical"
                        from_already_seen = [curr_from]
                    # Otherwise add a placeholder + itself to static
                    else:
                        #print "adding as placeholder"
                        from_already_seen = [Machine(curr_from.printname()), curr_from]

                    self.static[curr_from.printname()] = from_already_seen
                    self.__add_to_disambig(curr_from.printname())
                    replacement[curr_from] = curr_from

#                    print self.static, self.static_disambig

                else:
                    #print "in static"
                    # Definitions: the word is the canonical one, regardless of
                    # the number of children
                    if len(replacement) == 0:
                        #print "definition"
                        canonical = from_already_seen[0]
                        canonical.printname_ = curr_from.printname()
                        canonical.control = curr_from.control
                        replacement[curr_from] = canonical
                    # Handling non-definition words
                    else:
                        #print "not definition"
                        canonical = from_already_seen[0]
                        # No children: replace with the canonical
                        if len(curr_from.children()) == 0:
                            #print "no children"
                            replacement[curr_from] = canonical
                        # Otherwise: add the new machine to static, and keep it
                        else:
                            #print "children"
                            replacement[curr_from] = curr_from
                            from_already_seen.append(curr_from)

            # Copying the children...
            curr_to = replacement[curr_from]
            from_partitions = [[m for m in p] for p in curr_from.partitions]
            for part_i, part in enumerate(from_partitions):
                for child in part:
            #        print "found child", child
                    # Remove to delete any parent links
            #        print "part before", part, curr_from.partitions[part_i]
                    curr_from.remove(child, part_i)
            #        print "part after", part, curr_from.partitions[part_i]
                    curr_to.append(self.__add_static_recursive(child, replacement),
                                   part_i)

        return replacement[curr_from]

    def __add_to_disambig(self, print_name):
        """Adds @p print_name to the static_disambig."""
        self.static_disambig[print_name.split(id_sep)[0]].add(print_name)

    def __get_disambig_incomplete(self, print_name):
        """
        Returns the machine by its unique name. If the name is not in static,
        but static_disambig contains the ambiguous name, which points to itself,
        (and only itself,) then we replace the value in the mapping with the
        unique name.

        The above is needed because it is possible to encounter a word in the
        definition of another before we get to the word in the lexicon. If our
        word is referred to with its ambiguous name in the definition, we don't
        know the id yet, so we have to insert the ambiguous name to static as
        a placeholder. Once we see the definition of the word in question,
        however, we can replace ambiguous name with the fully qualified one.
        """
        if print_name in self.static:
#            print "XXX: printname", print_name, "in static"
            # in static: everything's OK, just return
            return self.static[print_name]
        else:
            ambig_name = print_name.split(id_sep)[0]
            names = self.static_disambig.get(ambig_name, set())
#            print "XXX: len(names:", ambig_name, ") ==", len(names), names
            if len(names) == 0:
#                print "len names == 0"
                # Not in static_disambig: we haven't heard of this word at all
                return []
            else:
                # The ambiguous word is in static_disambig, but is it mapped to
                # fully qualified names, or is there an ambiguous placeholder?
                if ambig_name in names:
#                    print "ambig_name in names"
                    # Ambiguous name -- we have not yet seen the definition.
                    assert len(names) == 1
#                    print "XXX: ambiguous name alert!"
                    # We see a fully specified form: replace the ambiguous one
                    if ambig_name != print_name:
                        names.remove(ambig_name)
                        names.add(print_name)
                        already_seen = self.static[ambig_name]
                        del self.static[ambig_name]
                        self.static[print_name] = already_seen
                        return already_seen
                    else:
                        return self.static[ambig_name]
                # Only fully qualified names. Our ambig is a valid reference, if
                # there is only one.
                else:
#                    print "else"
#                    print ambig_name, print_name, len(names), names
                    if ambig_name == print_name and len(names) == 1:
                        for name in names:      # why no peek()?
                            return self.static[name]
                    else:
#                        print "returning empty-handed"
                        return []

    def finalize_static(self):
        """
        Must be called after all words have been added to the static graph.
        Links the modified nodes to the canonical one.
        """
        for print_name, nodes in self.static.iteritems():
            # We don't care about deep cases here
            if not nodes[0].fancy():
                for node in nodes[1:]:
                    # HACK don't insert for binaries
                    if node.unary():
                        node.append(nodes[0])
        # defaultdict is not safe, so convert it to a regular dict
        self.static_disambig = dict(self.static_disambig)
        # TODO: remove the id from the print name of unambiguous machines

    def extract_definition_graph(self):
        """
        Extracts the definition graph from the static graph. The former is a
        "flattened" version of the latter: all canonical words in the definition
        are connected to the definiendum, as well as the canonical version of
        non-canonical terms. The structure of the definition is not preserved.
        """
        def_graph = {}
        for name in self.static.keys():
            def_graph[name] = Machine(name)
        for name, static_machine in self.static.iteritems():
            def_machine = def_graph[name]
            self.__build_definition_graph(def_machine, static_machine,
                    def_graph, set([def_machine]))

        return def_graph

    def __build_definition_graph(self, def_m, static_m, def_graph, stop):
        for child in static_m.children():
#            is_canonical = self.static[child.printname()] ==
            def_child = def_graph[child.printname()]
            if def_child not in stop:
                def_m.append(def_child)
                stop.add(def_child)


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
        if (not isinstance(static_machine, str) and
            not isinstance(static_machine, unicode)):
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
                active_machine = Machine(static_machine,
                                                 ConceptControl())
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
        if (avm_construction is not None and
            avm_construction not in self.constructions):
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
                    m = machine.Machine(printname,
                                        copy.copy(static_machine.control))
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

