import logging
from itertools import chain
from collections import Iterable, defaultdict
import copy

from pymachine.src.machine import Machine
from pymachine.src.control import ConceptControl
from pymachine.src.construction import Construction, AVMConstruction
from pymachine.src.constants import id_sep, deep_pre
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
        adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser

        @note We assume that a machine is added to the static graph only once.
        """
        """
        Add lexical definition to the static collection 
        while keeping prior links (parent links).
        """
        if isinstance(what, Machine):
#            if len(self.static) % 10 == 0:
#                print "STATIC"
#                for pn, machines in self.static.iteritems():
#                    print pn
#                    for m in machines:
#                        print m.to_debug_str()
#                    print
#                print "STATIC_DISAMBIG"
#                for a, u in self.static_disambig.iteritems():
#                    print a, u
#                print
            if what.printname().split('/')[0] == 'good':
                print "WHAT\n", what.to_debug_str() + "\n"
            # Does this machine appear in the static tree?
            #whats_already_seen = self.static.get(what.printname(), [])
            whats_already_seen = self.__get_disambig_incomplete(what.printname())
            if what.printname().split('/')[0] == 'good':
                print "already seen:"
                for m in whats_already_seen:
                    print m.to_debug_str(max_depth=1)

            # Simply adding the new machine/definition
            if len(whats_already_seen) == 0:
                self.static[what.printname()] = [what]
                canonical = what
            # Adding the canonical definition while keeping parent links
            else:
                # Updating canonical with the definition
                canonical = whats_already_seen[0]
                if what.printname().split('/')[0] == 'good':
                    print "canonical before"
                    print canonical.to_debug_str()
                canonical.printname_ = what.printname()
                canonical.partitions = what.partitions
                for part_i, part in enumerate(canonical.partitions):
                    for child in part:
                        # Keeping parent links
                        child.del_parent_link(what, part_i)
                        child.add_parent_link(canonical, part_i)
                canonical.control = what.control
                canonical.parents.union(what.parents)  # Do we even need this?
                if what.printname().split('/')[0] == 'good':
                    print "canonical after"
                    print canonical.to_debug_str()

                print
                print
                self.__recursive_replace(canonical, what, canonical, always=True)

            self.__add_to_disambig(what.printname())

            # Add every unique machine in the canonical's tree to static
            unique_machines = canonical.unique_machines_in_tree()
            for um in unique_machines:
                # Deep cases are not canonized
                if not um.deep_case():
                    if um.printname().isupper():
                        um.printname_ = um.printname().lower()
                    if um is canonical:
                        continue
                    um_already_seen = self.__get_disambig(um.printname())
# XXX                    um_already_seen = self.static.get(um.printname(), [])
                    if len(um_already_seen) == 0:
                        # There is no entry for the machine: add it (+ a
                        # placeholder for the canonical slot, if the machine
                        # is modified)
                        if len(um.children()) == 0:
                            um_already_seen = [um]
                        else:
                            # Modified words are linked to the canonical entry
                            # in finalize_static
                            um_already_seen = [Machine(um.printname()), um]
                        self.static[um.printname()] = um_already_seen
                        self.__add_to_disambig(um.printname())
                    else:
                        # Add to the entry list, if modified
                        if len(um.children()) > 0:
                            um_already_seen.append(um)

                    # Unify with the canonical entry if unmodified 
                    if len(um.children()) == 0 and um is not um_already_seen[0]:
                        self.__recursive_replace(canonical, um, um_already_seen[0])

        # Add to graph
        elif isinstance(what, Iterable):
            for m in what:
                self.add_static(m)

    # TODO: dog canonical == dog[faithfule]!
    def __replacement_map(self, uniques):
        """
        Creates the replacement map for use in add_static(). The mapping is
        as follows:
        - machines that have a canonical form are replaced with it
        """
        pass

    def __add_static_recursive(self, curr_from, replacement=None):
        if replacement == None:
            replacement = {}
        #print "Processing word ", curr_from
        sys.stdout.flush()

        if curr_from not in replacement:
            # Deep cases are not canonized
            if curr_from.deep_case():
                replacement[curr_from] = curr_from
            else:
                if curr_from.printname().isupper():
                    curr_from.printname_ = curr_from.printname().lower()
                #print "Not in replacement"
                # Does this machine appear in the static tree?
                from_already_seen = self.__get_disambig(curr_from.printname())
                print "from already seen", curr_from.printname(), from_already_seen
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

    def add_static2(self, what):
        """
        adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser

        @note We assume that a machine is added to the static graph only once.
        """
        """
        Add lexical definition to the static collection 
        while keeping prior links (parent links).
        """
        if isinstance(what, Machine):
            self.__add_static_recursive(what)
        # Add to graph
        elif isinstance(what, Iterable):
            for m in what:
                self.add_static2(m)

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
            names = self.static_disambig.get(ambig_name, [])
#            print "XXX: len(names:", ambig_name, ") ==", len(names), names
            if len(names) == 0:
                # Not in static_disambig: we haven't heard of this word at all
                return []
            else:
                # The ambiguous word is in static_disambig, but is mapped to
                # fully qualified names, or is there an ambiguous placeholder?
                if ambig_name in names:
                    # Ambiguous name alert!
#                    print "XXX: ambiguous name alert!"
                    names.remove(ambig_name)
                    already_seen = self.static[ambig_name]
                    del self.static[ambig_name]
                    self.static[print_name] = already_seen
                    return already_seen
                else:
                    return []

    def __get_disambig(self, print_name):
        """
        Returns the machine by its ambiguous name (i.e. the name before id_sep).
        Throws an exception if the word is ambiguous.
        """
        ambig_name = print_name.split(id_sep)[0]
        # Full name was passed with id
        if ambig_name != print_name:
            return self.static.get(print_name, [])
        else:
            static_keys = self.static_disambig.get(ambig_name, [])
#            print "YYY", print_name, len(static_keys), static_keys
            if len(static_keys) == 1:
                for static_key in static_keys:      # why no peek()?
                    return self.static[static_key]
            elif len(static_keys) == 0:
                return []
            else:
                raise ValueError('{0} is ambiguous'.format(print_name))

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

    def __recursive_replace(self, root, from_m, to_m, always=False, visited=None):
        """
        Replaces all instances of @p from_m with @p to_m in the tree under
        @p root. @p to_m inherits all properties (content of partitions, etc.)
        of @p from_m. This method cannot replace the root of the tree.

        @param always if @p False (the default), only replaces unmodified
                      machines; i.e. machines with empty partitions. @p True
                      when dealing with the definiendum.
        @param visited the set of already visited roots.
        """
        if visited is None:
            visited = set()
        if root in visited:
            return

        if to_m.printname().split('/')[0] == 'good':
            print "root"
            print root.to_debug_str(max_depth=1)
            print "visited"
            for m in visited:
                print m.to_debug_str(max_depth=1)


        # TODO: make person1[drunk], person2 DRINKS, person1 == person2?
        visited.add(root)
        to_visit = set()
        for part_i, part in enumerate(root.partitions):
            for m_i, m in enumerate(part):
                num_children = len(m.children())
                if m.printname() == from_m.printname() and m is not to_m:
                    if num_children == 0:
                        # TODO Machine.replace()?
                        part[m_i] = to_m
                        #root.remove(m, part_i)
                        #root.append(m, to_m, part_i)
                        to_m.parents |= m.parents
                        m.del_parent_link(root, part_i)
                    elif always and to_m.printname().split('/')[0] == 'good':
                        print "HERE", to_m
                        print "M"
                        print m.to_debug_str()
                        part[m_i] = to_m
                        to_m.parents |= m.parents
                        print "DELETING parent link", root, part_i
                        m.del_parent_link(root, part_i)
                        for p_i, p in enumerate(m.partitions):
                            for child in p:
                                print "CHILD"
                                print child.to_debug_str()
                                sys.stdout.flush()
                                to_m.append(child, p_i)
                                # Keeping parent links
                                print "DELETE child parent", m, p_i
                                sys.stdout.flush()
                                child.del_parent_link(m, p_i)
                                child.add_parent_link(to_m, p_i)
                    else:
                        # No replacement if from_m is modified
                        # TODO: w = 0 link from m to to_m
                        # TODO: test direct recursion
                        m.append(to_m, 0)
                if num_children > 0:
                    to_visit.add(m)
        for m in to_visit:
            self.__recursive_replace(m, from_m, to_m, always, visited)

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

