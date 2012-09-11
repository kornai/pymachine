from control import PluginControl
from construction import Construction
import logging
import itertools

def subsequence_index(seq, length):
    """
    Returns the start and end indices of all subsequences of @p seq of length
    @p length as an iterator.
    """
    l = len(seq)
    if l < length:
        return
    for begin in xrange(0, l - length + 1):
        yield begin, begin + length
    return

class SpreadingActivation(object):
    """Implements spreading activation (surprise surprise)."""
    def __init__(self, lexicon):
        self.lexicon = lexicon

    def activation_loop(self, chunks):
        """
        Implements the algorithm. It goes as follows:
        @arg Expand all unexpanded words
        @arg Link along linkers (deep cases)
        @arg Check the lexicon to see if new words are activated by the ones
             already in the graph; if yes, add them to the graph. Repeat until
             no new words are found.
        @return Messages to be sent to active plugins.
        The algorithm stops when ... I don't know.
        
        @param chunks a list of lists of machines that make up the chunks in the
                      sentence (and the rest, too).
        """
        # TODO: NPs/ linkers to be contended
        # chunks contains the chunks of the sentence -- at the beginning, all
        # words are considered chunks, but then are merged by the syntactic
        # constructions
        sentence = itertools.chain(*chunks)
        self.lexicon.add_active(sentence)
        last_active = len(self.lexicon.active)
        unexpanded = list(self.lexicon.get_unexpanded())
        plugin_found = False
        chunk_constructions = set([c for c in self.lexicon.constructions
                                   if c.type_ == Construction.CHUNK])
        semantic_constructions = set([c for c in self.lexicon.constructions
                                      if not c.type_ == Construction.SEMANTIC])
        avm_constructions = set([c for c in self.lexicon.constructions
                                   if c.type_ == Construction.AVM])

        # Chunk constructions are run here to form the phrase machines.
        for chunk in filter(lambda c: len(c) > 1, chunks):
            change = True
            while change:
                change = False
                try:
                    for length in xrange(2, len(chunk) + 1):
                        for begin, end in subsequence_index(chunk, length):
                            part = chunk[begin:end]
                            for c in chunk_constructions:
                                if c.check(part):
                                    c_res = c.act(part)
                                    if c_res is not None:
                                        change = True
                                        chunk[begin:end] = [c_res]  # c_res should be a single machine
                                        raise ValueError  # == break outer
                except ValueError:
                    pass

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

            # Step 2b: constructions:
            for c in semantic_constructions:
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

