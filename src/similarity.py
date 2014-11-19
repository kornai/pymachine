import logging

from pymachine.src.machine import MachineGraph

class WordSimilarity():
    def __init__(self, wrapper):
        self.wrapper = wrapper

    def get_links(self, machine):
        for hypernym in machine.partitions[0]:
            name = hypernym.printname()
            if name.isupper():
                continue
            yield name
            for link in self.get_links(hypernym):
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
        #logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
        if lemma1 == lemma2:
            return 1
        oov = filter(lambda l: l not in self.wrapper.definitions,
                     (lemma1, lemma2))
        if oov:
            logging.debug(u'OOV: {0}, no machine similarity')
            return None

        machine1, machine2 = map(self.wrapper.definitions.get,
                                 (lemma1, lemma2))
        links1 = set(link.split('/')[0] for link in self.get_links(machine1))
        links2 = set(link.split('/')[0] for link in self.get_links(machine2))
        #logging.info('machine1 links: {0}, machine2 links: {1}'.format(
        #    links1, links2))
        logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
        logging.info(u'links1: {0}, links2: {1}'.format(links1, links2))
        union = links1 | links2
        intersection = links1 & links2
        if not intersection:
            sim = 0
        else:
            sim = float(len(intersection)) / len(union)
            #sim = float(len(intersection)) / min(len(zero_links_1),
            #                                     len(zero_links_2))
            logging.info(u'shared: {0}'.format(intersection))
            logging.info('sim: {0}'.format(sim))

        draw_graphs = False  # use with caution
        if draw_graphs and not self.wrapper.batch:
            graph = MachineGraph.create_from_machines(
                [machine1, machine2], max_depth=1)
            f = open('graphs/{0}_{1}.dot'.format(lemma1, lemma2), 'w')
            f.write(graph.to_dot().encode('utf-8'))
        return sim
