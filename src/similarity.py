import logging

from pymachine.src.machine import MachineGraph
from pymachine.src.utils import jaccard

class WordSimilarity():
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.sim_cache = {}
        self.links_cache = {}

    def get_links(self, machine):
        if machine not in self.links_cache:
            self.seen = set()
            self.links_cache[machine] = set(self._get_links(machine, depth=0))
        return self.links_cache[machine]

    def _get_links(self, machine, depth):
        if machine in self.seen or depth > 5:
            return
        self.seen.add(machine)
        for hypernym in machine.partitions[0]:
            name = hypernym.printname()
            if name.isupper():
                if name != '=AGT':
                    continue
            else:
                yield name
            for link in self._get_links(hypernym, depth=depth+1):
                yield link

        for link in self.get_binary_links(machine):
            yield link

    def get_binary_links(self, machine):
        for parent, partition in machine.parents:
            parent_pn = parent.printname()
            if not parent_pn.isupper() or partition == 0:
                continue
            if partition == 1:
                links = set(["{0} {1}".format(parent_pn, other.printname())
                            for other in parent.partitions[2]])
            elif partition == 2:
                links = set(["{0} {1}".format(other.printname(), parent_pn)
                            for other in parent.partitions[1]])
            else:
                raise Exception(
                    'machine {0} has more than 3 partitions!'.format(machine))

            for link in links:
                yield link

    def word_similarity(self, word1, word2, pos1, pos2):
        lemma1, lemma2 = map(self.wrapper.get_lemma, (word1, word2))
        if lemma1 is None or lemma2 is None:
            return None
        if (lemma1, lemma2) in self.sim_cache:
            return self.sim_cache[(lemma1, lemma2)]
        logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
        if lemma1 == lemma2:
            return 1

        machine1 = self.wrapper.definitions[lemma1]
        machine2 = self.wrapper.definitions[lemma2]

        links1 = self.get_links(machine1)
        links2 = self.get_links(machine2)
        logging.info('links1: {0}, links2: {1}'.format(links1, links2))
        pn1, pn2 = machine1.printname(), machine2.printname()
        if pn1 in links2 or pn2 in links1:
            logging.info("{0} and {1} connected by 0-path, returning 1".format(
                pn1, pn2))
            return 1
        entities1 = filter(lambda l: "@" in l, links1)
        entities2 = filter(lambda l: "@" in l, links2)
        if entities1 or entities2:
            sim = jaccard(entities1, entities2, log=True)
        else:
            sim = jaccard(links1, links2, log=True)
        #logging.info('machine1 links: {0}, machine2 links: {1}'.format(
        #    links1, links2))
            #sim = float(len(intersection)) / min(len(zero_links_1),
            #                                     len(zero_links_2))

        draw_graphs = True  # use with caution
        if draw_graphs and not self.wrapper.batch:
            graph = MachineGraph.create_from_machines(
                [machine1, machine2], max_depth=1)
            f = open('graphs/{0}_{1}.dot'.format(lemma1, lemma2), 'w')
            f.write(graph.to_dot().encode('utf-8'))

        sim = sim if sim >= 0 else 0
        self.sim_cache[(lemma1, lemma2)] = sim
        return sim
