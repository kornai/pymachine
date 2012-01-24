from control import PluginControl
import logging

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

        # This condition will not work w/ the full lexicon, obviously.
        while len(unexpanded) > 0:
            dbg_str = ', '.join(k + ':' + str(len(v)) for k, v in self.lexicon.active.iteritems())
            logging.debug('LOOP:' + str(last_active) + ' ' + dbg_str)
            # Step 1
            for machine in unexpanded:
                logging.debug('Uzenet ' + str(machine))
                self.lexicon.expand(machine)
                for partition in machine.base.partitions[1:]:
                    for submachine in partition:
                        if submachine in self.lexicon.deep_cases:
                            s = linking.get(submachine, set())
                            s.add(machine)
                            linking[submachine] = s
            # XXX: activate Elvira here?

            # Step 2
            # XXX: What if there are more than 2 of the same linker?
            linker_to_remove = []
            for linker, machines in linking.iteritems():
                if len(machines) > 1:
                    self._link(linker, machines)
                    linker_to_remove.append(linker)
            for linker in linker_to_remove:
                del linking[linker]

            # Step 3
            self.lexicon.activate()
            unexpanded = list(self.lexicon.get_unexpanded())
            if len(self.lexicon.active) == last_active:
                break
            else:
                last_active = len(self.lexicon.active)

        # TODO: return messages to active plugins
        ret = []
        for m in self.lexicon.get_expanded():
            if isinstance(m.control, PluginControl):
                msg = ret.append(m.control.message())
                if msg is not None:
                    ret.append(msg)
        logging.debug('Returning...')
        return ret

    def _link(self, linker, machines):
        """Links the machines along @p linker."""
        print "Linking " + ','.join(str(m) for m in machines) + " along " + str(linker)
        for machine in machines:
            for partition in machine.base.find(linker):
#                logging.debug('Partition ' + ','.join(partition))
                machine.remove(linker, partition)
                for to_add in machines:
                    if to_add != machine:
                        machine.append_if_not_there(to_add, partition)

