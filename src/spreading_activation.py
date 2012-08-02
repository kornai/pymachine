from control import PluginControl
import logging
import itertools

class SpreadingActivation(object):
    """Implements spreading activation (surprise surprise)."""
    def __init__(self, lexicon):
        self.lexicon = lexicon

    def activation_loop(self):
        """Implements the algorithm. It goes as follows:
        @arg Expand all unexpanded words
        @arg Link along linkers (deep cases)
        @arg Check the lexicon to see if new words are activated by the ones
             already in the graph; if yes, add them to the graph. Repeat until
             no new words are found.
        @return Messages to be sent to active plugins.
        The algorithm stops when ... I don't know."""
        # TODO: NPs/ linkers to be contended
        last_active = len(self.lexicon.active)
        unexpanded = list(self.lexicon.get_unexpanded())
        linking = {}  # {linker: set([machines that have the linker on a partition])}
        plugin_found = False

        # This condition will not work w/ the full lexicon, obviously.
        while len(unexpanded) > 0 and not plugin_found:
            dbg_str = ', '.join(k.encode('utf-8') + ':' + str(len(v)) for k, v in self.lexicon.active.iteritems())
            logging.debug("\n\nLOOP:" + str(last_active) + ' ' + dbg_str + "\n\n")
#            logging.debug('ACTIVE')
#            from machine import Machine
#            for ac in self.lexicon.active.values():
#                for m in ac:
#                    logging.debug(Machine.to_debug_str(m))
            # Step 1: expansion
            for machine in unexpanded:
                logging.debug("EXPANDING: " + unicode(machine).encode('utf-8'))

                self.lexicon.expand(machine)
                for partition in machine.base.partitions[1:]:
                    for submachine in partition:
                        if self.lexicon.is_deep_case(submachine):
                            logging.debug("LINKING CUMO: " + unicode(submachine).encode('utf-8'))
                            # XXX: This only works if strs and machines are
                            # cross-hashed
                            s = linking.get(submachine, set())
                            s.add(machine)
                            linking[submachine] = s
            # XXX: activate Elvira here?

            # Step 2b: constructions:
            for c in self.lexicon.constructions:
                # The machines that can take part in constructions
                logging.debug("CONST " + c.name)
                accepted = []
                # Find the sequences that match the construction
                # TODO: combinatorial explosion alert!
                for elems in xrange(min(len(self.lexicon.active_machines()), 4)):
                #for elems in xrange(len(constable)):
                    for seq in itertools.permutations(
                            self.lexicon.active_machines(), elems + 1):
                        if c.check(seq):
                            accepted.append(seq)

                # The sequence preference order is longer first
                # TODO: obviously this won't work for every imaginable
                #       combination; maybe this step should be combination-
                #       dependent.
                accepted.sort(key=lambda seq: len(seq))
                logging.debug("ACCEPTED")
                for seq in accepted:
                    logging.debug(u" ".join(unicode(m) for m in seq).encode('utf-8'))

                # No we try to act() on these sequences. We stop at the first
                # sequence that is accepted by act().
                while len(accepted) > 0:
                    seq = accepted[-1]
                    c_res = c.act(seq)
                    if c_res is not None:
                        logging.debug("SUCCESS: " + u" ".join(unicode(m) for m in seq).encode("utf-8"))
                        # We remove the machines that were consumed by the
                        # construction and add the machines returned by it
                        for m in c_res:
                            self.lexicon.unify_recursively(m)

                        # If one of the returned machines has a PluginControl,
                        # we can stop the activation loop
                        for m in c_res:
                            if isinstance(m.control, PluginControl):
                                plugin_found = True
                                break
                        break
                    else:
                        del accepted[-1]



            # Step 2: linking
            # TODO: replace w/ constructions
            # XXX: What if there are more than 2 of the same linker?
            logging.debug("\n\nLINKING: {0}\n\n".format(linking))
            linker_to_remove = []
            for linker, machines in linking.iteritems():
                if len(machines) > 1:
                    self._link(linker, machines)
                    linker_to_remove.append(linker)
            for linker in linker_to_remove:
                del linking[linker]

            # Step 3: activation
            self.lexicon.activate()
            unexpanded = list(self.lexicon.get_unexpanded())
            if len(self.lexicon.active) == last_active:
                break
            else:
                last_active = len(self.lexicon.active)

        # Return messages to active plugins
        logging.debug("\n\nENDE\n\n")
        ret = []
        for m in self.lexicon.active_machines():
            if isinstance(m.control, PluginControl):
                # TODO: rename to activate() or sth and get rid of the
                # call to isinstance()
                msg = m.control.message()
                if msg is not None:
                    ret.append(msg)
        logging.debug('Returning ' + str(ret))
        return ret

    def _link(self, linker, machines):
        """Links the machines along @p linker."""
        logging.debug("Linking " + ','.join(str(m) for m in machines) + " along " + str(linker))
        for machine in machines:
            for partition in machine.base.find(linker):
                machine.remove(linker, partition)
                for to_add in machines:
                    if to_add != machine:
                        machine.append_if_not_there(to_add, partition)

