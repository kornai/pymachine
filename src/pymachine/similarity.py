from collections import defaultdict
import logging

from nltk.corpus import stopwords as nltk_stopwords
from utils import average, harmonic_mean, jaccard, min_jaccard, MachineGraph, MachineTraverser, my_max  # nopep8
assert jaccard, min_jaccard  # silence pyflakes

class WordSimilarity():
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.lemma_sim_cache = {}
        self.machine_sim_cache = {}
        self.links_nodes_cache = {}
        self.stopwords = set(nltk_stopwords.words('english'))

    def get_links_nodes(self, machine):
        if machine not in self.links_nodes_cache:
            self.seen_for_links = set()
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

        for node in MachineTraverser.get_nodes(machine):
            yield None, node

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

    def machine_similarity(self, machine1, machine2, sim_type):
        pn1, pn2 = machine1.printname(), machine2.printname()
        if (pn1, pn2) in self.machine_sim_cache:
            return self.machine_sim_cache[(pn1, pn2)]
        if sim_type == 'default':
            #sim = harmonic_mean((
            #    self._all_pairs_similarity(machine1, machine2),
            #    self._links_and_nodes_similarity(machine1, machine2)))
            sim = self._links_and_nodes_similarity(machine1, machine2)
        elif sim_type == 'all_pairs':
            sim = self._all_pairs_similarity(machine1, machine2)
        elif sim_type == 'links_and_nodes':
            sim = self._links_and_nodes_similarity(machine1, machine2)
        elif sim_type == 'strict_links_and_nodes':
            sim = self._links_and_nodes_similarity(machine1, machine2,
                                                   no_contain_score=True)
        elif sim_type == 'links':
            sim = self._links_and_nodes_similarity(machine1, machine2,
                                                   exclude_nodes=True)
        elif sim_type == 'strict_links':
            sim = self._links_and_nodes_similarity(machine1, machine2,
                                                   exclude_nodes=True,
                                                   no_contain_score=True)
        else:
            raise Exception("unknown similarity type: {0}".format(sim_type))
        self.machine_sim_cache[(pn1, pn2)] = sim
        self.machine_sim_cache[(pn2, pn1)] = sim
        return sim

    def _all_pairs_similarity(self, machine1, machine2):
        words1 = set(MachineTraverser.get_nodes(machine1,
                                                exclude_words=self.stopwords))
        words2 = set(MachineTraverser.get_nodes(machine2,
                                                exclude_words=self.stopwords))
        pair_sims_by_word = defaultdict(dict)
        for word1 in words1:
            for word2 in words2:
                sim = self.word_similarity(word1, word2, -1, -1,
                                           sim_type="strict_links_and_nodes")
                pair_sims_by_word[word1][word2] = sim if sim else 0.0
                pair_sims_by_word[word2][word1] = sim if sim else 0.0

        max_sims_by_word = dict((
            (word, my_max(pair_sims_by_word[word].itervalues()))
            for word in words1 | words2))

        sim = average((average((max_sims_by_word[w] for w in words1)),
                       average((max_sims_by_word[w] for w in words2))))
        #sim = max((my_max((max_sims_by_word[w] for w in words1)),
        #           my_max((max_sims_by_word[w] for w in words2))))
        if sim:
            logging.info(
                "{0} - {1} all_pairs similarity: {2} based on: {3}".format(
                    machine1.printname(), machine2.printname(), sim,
                    pair_sims_by_word))
        return sim

    def _links_and_nodes_similarity(self, machine1, machine2,
                                    exclude_nodes=False,
                                    no_contain_score=False):
        sim = 0
        links1, nodes1 = self.get_links_nodes(machine1)
        links2, nodes2 = self.get_links_nodes(machine2)
        if not no_contain_score:
            if (self.contains(links1, machine2) or
                    self.contains(links2, machine1)):
                sim = max(sim, 0.35)
            elif (not exclude_nodes) and (self.contains(nodes1, machine2) or
                                          self.contains(nodes2, machine1)):
                sim = max(sim, 0.25)
        logging.info('links1: {0}, links2: {1}'.format(links1, links2))
        logging.info('nodes1: {0}, nodes2: {1}'.format(nodes1, nodes2))
        if True:
            pn1, pn2 = machine1.printname(), machine2.printname()
            if pn1 in links2 or pn2 in links1:
                logging.info(
                    "{0} and {1} connected by 0-path, returning 1".format(
                        pn1, pn2))
                return 1
        entities1 = filter(lambda l: "@" in l, links1)
        entities2 = filter(lambda l: "@" in l, links2)
        if entities1 or entities2:
            sim = max(sim, jaccard(entities1, entities2))
        else:
            sim = max(sim, jaccard(links1, links2))
            if not exclude_nodes:
                sim = max(sim, jaccard(nodes1, nodes2))

        return sim

    def word_similarity(self, word1, word2, pos1, pos2, sim_type='default',
                        fallback=lambda a, b, c, d: None):
        lemma1, lemma2 = [self.wrapper.get_lemma(word, existing_only=True)
                          for word in (word1, word2)]
        if lemma1 is None or lemma2 is None:
            return fallback(word1, word2, pos1, pos2)
        return self.lemma_similarity(lemma1, lemma2, sim_type)

    def lemma_similarity(self, lemma1, lemma2, sim_type):
        if (lemma1, lemma2) in self.lemma_sim_cache:
            return self.lemma_sim_cache[(lemma1, lemma2)]
        elif lemma1 == lemma2:
            return 1
        logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))

        machines1 = self.wrapper.definitions[lemma1]
        machines2 = self.wrapper.definitions[lemma2]

        pairs_by_sim = sorted([
            (self.machine_similarity(machine1, machine2, sim_type),
             (machine1, machine2))
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

class SentenceSimilarity():
    def __init__(self, machine_wrapper):
        self.wrapper = machine_wrapper
        self.word_sim = WordSimilarity(machine_wrapper)

    def process_line(self, line, parser, sen_filter, fallback_sim):
        fields = line.decode('latin1').strip().split('\t')
        sen1, sen2, tags1, tags2 = parser(fields)
        sen1 = sen_filter([{"token": sen1[i], "pos": pos, "ner": ner}
                          for i, (pos, ner) in enumerate(tags1)])
        sen2 = sen_filter([{"token": sen2[i], "pos": pos, "ner": ner}
                          for i, (pos, ner) in enumerate(tags2)])

        sim = self.sentence_similarity(sen1, sen2, fallback=fallback_sim)
        print sim

    def directional_sen_similarity(self, sen1, sen2, fallback):
        return average((
            my_max((self.word_sim.word_similarity(
                word1['token'], word2['token'], -1, -1,
                fallback=fallback)
                for word2 in sen2))
            for word1 in sen1))

    def sentence_similarity(self, sen1, sen2, fallback=lambda a, b, c, d: 0.0):
        return harmonic_mean((
            self.directional_sen_similarity(sen1, sen2, fallback),
            self.directional_sen_similarity(sen2, sen1, fallback)))
