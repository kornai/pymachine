from control import PluginControl

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
        unexpanded = list(self.lexicon.unexpanded())
        expanded = []
        linking = {}  # {linker: [machines that have the linker on a partition]}

        # This condition will not work w/ the full lexicon, obviously.
        while len(unexpanded) > 0:
            # Step 1
            for machine in unexpanded:
                self.lexicon.expand(machine)
                for partition in machine.base.partitions[1:]:
                    for submachine in partition:
                        if submachine in self.lexicon.deep_cases:
                            linking[submachine] = linking.get(submachine, []) + [machine]
            # XXX: activate Elvira here?
            expanded += unexpanded

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
            self.lexicon.activate(expanded)
            unexpanded = list(self.lexicon.unexpanded())

        # TODO: return messages to active plugins
        ret = []
        for m in self.lexicon.expanded():
            if isinstance(m.control, PluginControl):
                ret.append(m.control.message())
        return ret

    def _link(self, linker, machines):
        """Links the machines along @p linker."""
        for machine in machines:
            for partition in machine.base.find(linker):
                machine.remove(linker, partition)
                for to_add in machines:
                    if to_add != machine:
                        machine.append_if_not_there(to_add, partition)

