from math import factorial as fac
import logging
import itertools

from control import PluginControl
from construction import Construction
from np_parser import parse_chunk

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(s, r) for r in range(len(s)+1))

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

        @param chunks a list of lists of machines that make up the chunks in
            the sentence (and the rest, too).
        """
        # chunks contains the chunks of the sentence -- at the beginning, all
        # words are considered chunks, but then are merged by the syntactic
        # constructions

        sentence = itertools.chain(*chunks)
        self.lexicon.add_active(sentence)
        last_active = len(self.lexicon.active)
        unexpanded = list(self.lexicon.get_unexpanded())
        chunk_constructions = set([c for c in self.lexicon.constructions
                                  if c.type_ == Construction.CHUNK])
        chunk_dbg_str = ', '.join(
            c.name.encode('utf-8')
            for c in chunk_constructions)
        logging.debug(
            "\n\nCHUNK CONSTRUCTIONS:" + ' ' + chunk_dbg_str + "\n\n")

        semantic_constructions = set([c for c in self.lexicon.constructions
                                      if c.type_ == Construction.SEMANTIC])
        semantic_dbg_str = ', '.join(
            c.name.encode('utf-8') for c in semantic_constructions)
        logging.info(
            "\n\nSEMANTIC CONSTRUCTIONS:" + ' ' + semantic_dbg_str + "\n\n")

        avm_constructions = set()

        # Chunk constructions are run here to form the phrase machines.
        for chunk in filter(lambda c: len(c) > 1, chunks):
            parse_chunk(chunk)

        # This condition works for the demo, but we need to find another one
        # for the whole lexicon
        plugin_found = False
        safety_zone = 0
        while not plugin_found or safety_zone < 5:
            if plugin_found:
                safety_zone += 1
            active_dbg_str = ', '.join(
                k.encode('utf-8') + ':' + str(len(v))
                for k, v in self.lexicon.active.iteritems())
            static_dbg_str = ', '.join(
                k.encode('utf-8') for k in sorted(self.lexicon.static.keys()))
            logging.debug(
                "\n\nACTIVE:" + str(last_active) + ' ' + active_dbg_str)
            logging.info("\n\nACTIVE DICT: {}".format(self.lexicon.active))
            logging.debug("\n\nSTATIC:" + ' ' + static_dbg_str)
            logging.debug("\n\nSTATIC DICT: {}".format(self.lexicon.static))
#            logging.debug('ACTIVE')
#            from machine import Machine
#            for ac in self.lexicon.active.values():
#                for m in ac:
#                    logging.debug(Machine.to_debug_str(m))
            # Step 1: expansion
            for machine in unexpanded:
                logging.debug("EXPANDING: " + unicode(machine).encode('utf-8'))

                self.lexicon.expand(machine)

            # Step 2a: semantic constructions:
            for c in semantic_constructions:
                # The machines that can take part in constructions
                logging.info("CONST " + c.name)
                accepted = []
                # Find the sequences that match the construction
                # TODO: combinatorial explosion alert!
                no_active = len(self.lexicon.active_machines())
                max_length = 3
                no_all_combinations = sum((fac(no_active)/fac(no_active-i-1)
                                          for i in range(max_length)))
                logging.info((
                    '# of active machines: {0}, ' +
                    'trying all sequences of at most {1} machines, ' +
                    'total # of sequences: {2}').format(
                    no_active, max_length, no_all_combinations))
                """
                for i, seq in enumerate(powerset(
                        self.lexicon.active_machines())):
                """
                count = 0
                for elems in xrange(
                        min(len(self.lexicon.active_machines()), max_length)):
                #for elems in xrange(len(constable)):
                    for i, seq in enumerate(itertools.permutations(
                            self.lexicon.active_machines(), elems + 1)):
                        count += 1
                        if count % 100 == 0:
                            logging.info("{0}".format(count))

                        if c.check(seq):
                            #quit()
                            accepted.append(seq)

                # The sequence preference order is longer first
                # TODO: obviously this won't work for every imaginable
                #       combination; maybe this step should be combination-
                #       dependent.
                accepted.sort(key=lambda seq: len(seq))
                if not accepted:
                    logging.info("NOTHING ACCEPTED")
                else:
                    logging.info(
                        "ACCEPTED {0} sequences".format(len(accepted)))
                for seq in accepted:
                    logging.debug(
                        u" ".join(unicode(m) for m in seq).encode('utf-8'))

                # No we try to act() on these sequences. We stop at the first
                # sequence that is accepted by act().
                while len(accepted) > 0:
                    seq = accepted[-1]
                    logging.debug('trying to make construction act')
                    c_res = c.act(seq)
                    if c_res is not None:
                        logging.info("SUCCESS: " + u" ".join(unicode(m)
                                     for m in seq).encode("utf-8"))
                        # We remove the machines that were consumed by the
                        # construction and add the machines returned by it
                        for m in c_res:
                            self.lexicon.unify_recursively(m)

                        # If one of the returned machines has a PluginControl,
                        # we can stop the activation loop
                        for m in c_res:
                            if isinstance(m.control, PluginControl):
                                plugin_found = True
                                logging.debug('Plugin found: ' + m.printname())
                                break
                        break
                    else:
                        del accepted[-1]

            avm_constructions = set([c for c in self.lexicon.constructions
                                    if c.type_ == Construction.AVM])
            active_avm_dbg_str = ', '.join(
                c.name.encode('utf-8') for c in avm_constructions)
            logging.debug(
                "\n\nAVM CONSTRUCTIONS:" + ' ' + active_avm_dbg_str + "\n\n")
            # Step 2b: AVM constructions
            for c in avm_constructions:
                logging.debug(u"AVM {0} before: {1}".format(
                    c.name, unicode(c.avm)).encode("utf-8"))
                attr_vals = set(self.lexicon.active_machines()) | set(
                    c.avm for c in avm_constructions)
                for m in attr_vals:
                    if c.check([m]):
                        c.act([m])
                        if c.avm.satisfied():
                            plugin_found = True
                            logging.debug('AVM found: ' + c.name)
                logging.debug(u"AVM {0} after: {1}".format(
                    c.name, unicode(c.avm)).encode("utf-8"))

            # Step 3: activation
            self.lexicon.activate()

            # Step 4: housekeeping
            unexpanded = list(self.lexicon.get_unexpanded())
            if len(self.lexicon.active) + len(
                    avm_constructions) == last_active:
                break
            else:
                last_active = len(self.lexicon.active) + len(avm_constructions)

        # Return messages to active plugins
        # TODO: add AVMs. What is the relation between AVMs and Plugins?
        logging.debug("\n\nENDE\n\n")
        ret = []
        for c in avm_constructions:
            if c.avm.satisfied():
                ret.append(c.avm.get_basic_dict())

        logging.debug('Returning ' + str(ret))
        return ret
