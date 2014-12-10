import logging

from pymachine.src.machine import MachineGraph
from pymachine.src.utils import jaccard, min_jaccard
assert jaccard, min_jaccard  # silence pyflakes

class WordSimilarity():
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.lemma_sim_cache = {}
        self.machine_sim_cache = {}
        self.links_nodes_cache = {}

    def get_links_nodes(self, machine):
        if machine not in self.links_nodes_cache:
            self.seen_for_links = set()
            self.seen_for_nodes = set()
            links = set()
            nodes = set()
            for link, node in self._get_links_nodes(machine, depth=0):
                if link is not None:
                    links.add(link)
                if node is not None:
                    nodes.add(node)
            self.links_nodes_cache[machine] = (links, nodes)
        return self.links_nodes_cache[machine]

    def _get_links_nodes(self, machine, depth):
        if machine in self.seen_for_links or depth > 5:
            return
        self.seen_for_links.add(machine)
        for hypernym in machine.partitions[0]:
            name = hypernym.printname()
            if name == '=AGT' or not name.isupper():
                yield name, None

            for link, node in self._get_links_nodes(hypernym, depth=depth+1):
                yield link, node

        for link, node in self.get_binary_links_nodes(machine):
            yield link, node

        for node in self._get_nodes(machine, depth=depth+1):
            yield None, node

    def _get_nodes(self, machine, depth):
        if machine in self.seen_for_nodes:
            return
        self.seen_for_nodes.add(machine)
        name = machine.printname()
        if not name.isupper():
            yield name
        for part in machine.partitions:
            for submachine in part:
                for node in self._get_nodes(submachine, depth=depth+1):
                    yield node

    def get_binary_links_nodes(self, machine):
        for parent, partition in machine.parents:
            parent_pn = parent.printname()
            if not parent_pn.isupper() or partition == 0:
                continue
            if partition == 1:
                links = set([(parent_pn, other.printname())
                            for other in parent.partitions[2]])
                nodes = [m.printname() for m in parent.partitions[2]]
            elif partition == 2:
                links = set([(other.printname(), parent_pn)
                            for other in parent.partitions[1]])
                nodes = [m.printname() for m in parent.partitions[1]]
            else:
                raise Exception(
                    'machine {0} has more than 3 partitions!'.format(machine))

            for link in links:
                yield link, None
            for node in nodes:
                yield None, node

    def link_similarity(self, links1, links2):
        pass

    def contains(self, links, machine):
        pn = machine.printname()
        for link in links:
            if link == pn or pn in link:
                return True
        else:
            return False

    def machine_similarity(self, machine1, machine2):
        if (machine1, machine2) in self.machine_sim_cache:
            return self.machine_sim_cache[(machine1, machine2)]
        sim = 0
        links1, nodes1 = self.get_links_nodes(machine1)
        links2, nodes2 = self.get_links_nodes(machine2)
        if self.contains(links1, machine2) or self.contains(links2, machine1):
            sim = max(sim, 0.35)
        elif (self.contains(nodes1, machine2) or
              self.contains(nodes2, machine1)):
            sim = max(sim, 0.25)
        logging.info('links1: {0}, links2: {1}'.format(links1, links2))
        logging.info('nodes1: {0}, nodes2: {1}'.format(nodes1, nodes2))
        pn1, pn2 = machine1.printname(), machine2.printname()
        if pn1 in links2 or pn2 in links1:
            logging.info("{0} and {1} connected by 0-path, returning 1".format(
                pn1, pn2))
            return 1
        entities1 = filter(lambda l: "@" in l, links1)
        entities2 = filter(lambda l: "@" in l, links2)
        if entities1 or entities2:
            sim = max(sim, jaccard(entities1, entities2))
        else:
            sim = max(sim, jaccard(links1, links2))
            sim = max(sim, jaccard(nodes1, nodes2))

        self.machine_sim_cache[(machine1, machine2)] = sim
        return sim

    def word_similarity(self, word1, word2, pos1, pos2):
        lemma1, lemma2 = [self.wrapper.get_lemma(word, existing_only=True)
                          for word in (word1, word2)]
        if lemma1 is None or lemma2 is None:
            return None
        if (lemma1, lemma2) in self.lemma_sim_cache:
            return self.lemma_sim_cache[(lemma1, lemma2)]
        logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
        if lemma1 == lemma2:
            return 1

        machines1 = self.wrapper.definitions[lemma1]
        machines2 = self.wrapper.definitions[lemma2]

        pairs_by_sim = sorted([
            (self.machine_similarity(machine1, machine2), (machine1, machine2))
            for machine1 in machines1 for machine2 in machines2], reverse=True)

        sim, (machine1, machine2) = pairs_by_sim[0]

        draw_graphs = True  # use with caution
        if draw_graphs and not self.wrapper.batch:
            graph = MachineGraph.create_from_machines(
                [machine1, machine2])  # , max_depth=1)
            f = open('graphs/{0}_{1}.dot'.format(lemma1, lemma2), 'w')
            f.write(graph.to_dot().encode('utf-8'))

        sim = sim if sim >= 0 else 0
        self.lemma_sim_cache[(lemma1, lemma2)] = sim
        return sim
