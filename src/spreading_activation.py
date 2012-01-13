
class SpreadingActivation(object):
    """Implements spreading activation (surprise surprise)."""
    def __init__(self, lexicon):
        self.lexicon = lexicon

    def activation_loop(self, sources):
        """Implements the algorithm. It goes as follows:
        @arg Expand all unexpanded words
        @arg Unify along linkers (deep cases)
        @arg Check the lexicon to see if new words are activated by the ones
             already in the graph; if yes, add them to the graph. Repeat until
             no new words are found.
        The algorithm stops when ... I don't know."""
        # TODO: NPs/ linkers to be contended
        unexpanded = list(sources)
        expanded = []
        linking = {}  # {linker: [machines that have the linker on a partition]}

        # This condition will not work w/ the full lexicon, obviously.
        while len(unexpanded) > 0:
            # Step 1
            for machine in unexpanded:
                machine.expand()
                for partition in machine.base.partitions[1:]:
                    for submachine in partition:
                        if submachine in self.lexicon.deep_cases:
                            linking[submachine] = linking.get(submachine, []) + [machine]
            expanded += unexpanded
            unexpanded = []

            # Step 2
            # TODO: What if there are more than 2 of the same linker?
            linker_to_remove = []
            for linker, machines in linking.iteritems():
                if len(machines) > 1:
                    self._link(linker, machines)
                    linker_to_remove.append(linker)
            for linker in linker_to_remove:
                del linking[linker]

            # Step 3
            unexpanded = self.lexicon.activate(expanded)

    def _link(self, linker, machines):
        """Links the machines along @p linker."""
        for machine in machines:
            for partition in machine.base.find(linker):
                machine.remove(linker, partition)
                for to_add in machines:
                    if to_add != machine:
                        machine.append_if_not_there(to_add, partition)

