#!/usr/bin/env python
from copy import deepcopy
import os
import cPickle
import re
import sys
import logging
import ConfigParser

from hunmisc.utils.huntool_wrapper import Hundisambig, Ocamorph, MorphAnalyzer

from construction import VerbConstruction
from sentence_parser import SentenceParser
from lexicon import Lexicon
from pymachine.src.machine import MachineGraph
from pymachine.src.machine import Machine
from pymachine.src.control import ConceptControl
from spreading_activation import SpreadingActivation
from definition_parser import read as read_defs
from sup_dic import supplementary_dictionary_reader as sdreader
from dep_map import dep_map_reader
#from demo_misc import add_verb_constructions, add_avm_constructions
import np_grammar

class KeyDefaultDict(dict):
    def __missing__(self, key):
        return key

def jaccard(s1, s2):
    try:
        return float(len(s1 & s2)) / len(s1 | s2)
    except ZeroDivisionError:
        return 0.0

class Wrapper:

    dep_regex = re.compile("([a-z_]*)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")
    num_re = re.compile(r'^[0-9.,]+$', re.UNICODE)

    def get_lemma(self, word):
        if word in self.tok2lemma:
            return self.tok2lemma[word]
        elif Wrapper.num_re.match(word):
            return word
        for char in ('.', ',', '=', '"', "'", '/'):
            for part in word.split(char):
                if part in self.tok2lemma:
                    logging.info('returning lemma of {0} instead of {1}')
                    return self.tok2lemma[part]

        logging.info(u'analyzing {0}'.format(word))
        self.tok2lemma[word] = list(self.analyzer.analyze(
            [[word]]))[0][0][1].split('||')[0].split('<')[0]
        logging.info(u'got this: {0}'.format(self.tok2lemma[word]))
        return self.tok2lemma[word]

    @staticmethod
    def get_analyzer():
        hunmorph_dir = os.environ['HUNMORPH_DIR']
        return MorphAnalyzer(
            Ocamorph(
                os.path.join(hunmorph_dir, "ocamorph"),
                os.path.join(hunmorph_dir, "morphdb_en.bin")),
            Hundisambig(
                os.path.join(hunmorph_dir, "hundisambig"),
                os.path.join(hunmorph_dir, "en_wsj.model")))

    @staticmethod
    def get_tok2lemma(tok2lemma_fn):
        tok2lemma = {}
        if tok2lemma_fn is None:
            return tok2lemma
        for line in file(tok2lemma_fn):
            try:
                tok, lemma = line.decode('utf-8').strip().split('\t')
            except (ValueError, UnicodeDecodeError), e:
                raise Exception(
                    'error parsing line in tok2lemma file: {0}\n{1}'.format(
                        e, line))
            tok2lemma[tok] = lemma

        return tok2lemma

    def __init__(self, cf, include_longman=False, batch=False):
        self.cfn = cf
        self.__read_config()
        self.batch = batch

        self.tok2lemma = Wrapper.get_tok2lemma(self.tok2lemma_fn)
        self.wordlist = set()
        self.dep_to_op = dep_map_reader(self.dep_map_fn)
        self.__read_definitions()
        if include_longman:
            self.get_longman_definitions()
        self.__read_supp_dict()
        self.reset_lexicon()

    def reset_lexicon(self, load_from=None, save_to=None):
        if load_from:
            self.lexicon = cPickle.load(open(load_from))
        else:
            self.lexicon = Lexicon()
            self.__add_definitions()
            self.__add_constructions()
        if save_to:
            cPickle.dump(self.lexicon, open(save_to, 'w'))

    def __read_config(self):
        machinepath = os.path.realpath(__file__).rsplit("/", 2)[0]
        if "MACHINEPATH" in os.environ:
            machinepath = os.environ["MACHINEPATH"]
        config = ConfigParser.SafeConfigParser({"machinepath": machinepath})
        logging.info('reading machine config from {0}'.format(self.cfn))
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_files = [(s.split(":")[0].strip(), int(s.split(":")[1]))
                          for s in items["definitions"].split(",")]
        self.dep_map_fn = items.get("dep_map")
        self.tok2lemma_fn = items.get("tok2lemma")
        self.longman_deps_path = items.get("longman_deps")
        self.supp_dict_fn = items.get("supp_dict")
        self.plural_fn = items.get("plurals")

    def __read_definitions(self):
        self.definitions = {}
        for file_name, printname_index in self.def_files:
            # TODO HACK makefile needed
            if (file_name.endswith("generated") and
                    not os.path.exists(file_name)):
                raise Exception(
                    "A definition file that should be generated" +
                    " by pymachine/scripts/generate_translation_dict.sh" +
                    " does not exist: {0}".format(file_name))

            if file_name.endswith('pickle'):
                logging.debug('loading 4lang definitions...')
                definitions = cPickle.load(file(file_name))
            else:
                logging.info('parsing 4lang definitions...')
                definitions = read_defs(
                    file(file_name), self.plural_fn, printname_index,
                    three_parts=True)

                logging.info('dumping 4lang definitions to file...')
                f = open('{0}.pickle'.format(file_name), 'w')
                cPickle.dump(definitions, f)

            self.definitions.update(definitions)

    def __add_definitions(self):
            definitions = deepcopy(self.definitions)
            self.lexicon.add_static(definitions.itervalues())
            self.lexicon.finalize_static()

    def __read_supp_dict(self):
        self.supp_dict = sdreader(
            file(self.supp_dict_fn)) if self.supp_dict_fn else {}

    def __add_constructions(self):
        for construction in np_grammar.np_rules:
            self.lexicon.add_construction(construction)
        #add_verb_constructions(self.lexicon, self.supp_dict)
        #add_avm_constructions(self.lexicon, self.supp_dict)

    def get_longman_definitions(self):
        #logging.info('adding Longman definitions')
        self.analyzer = Wrapper.get_analyzer()
        if self.longman_deps_path.endswith('pickle'):
            logging.info('loading Longman definitions...')
            definitions = cPickle.load(file(self.longman_deps_path))

        else:
            files = os.listdir(self.longman_deps_path)

            logging.info('only parsing first meanings for now')
            files = filter(lambda fn: '_' not in fn, files)
            #TODO

            logging.info('will now parse {0} definitions'.format(len(files)))
            definitions = {}
            for c, fn in enumerate(files):
                if c % 1000 == 0:
                    logging.info('{0}...'.format(c))
                word, _ = fn.split('.')
                deps = [
                    line.strip() for line in open(
                        os.path.join(self.longman_deps_path, fn))]
                machine = self.get_dep_definition(word, deps)
                if machine is None:
                    continue
                definitions[word] = machine

            logging.info('pickling Longman definitions...')
            f = open('{0}.pickle'.format(self.longman_deps_path), 'w')
            cPickle.dump(definitions, f)

        for word, machine in definitions.iteritems():
            if word not in self.definitions:
                self.definitions[word] = machine

        logging.info('done')

    @staticmethod
    def parse_dependency(string):
        dep_match = Wrapper.dep_regex.match(string)
        if not dep_match:
            raise Exception('cannot parse dependency: {0}'.format(string))
        dep, word1, id1, word2, id2 = dep_match.groups()
        return dep, (word1, id1), (word2, id2)

    def get_dep_definition(self, word, dep_strings):
        deps = map(Wrapper.parse_dependency, dep_strings)
        root_deps = filter(lambda d: d[0] == 'root', deps)
        root_word, root_id = root_deps[0][2]
        root_lemma = self.get_lemma(root_word)
        if len(root_deps) != 1:
            logging.warning(
                'no unique root dependency, skipping word "{0}"'.format(word))
            return None

        word2machine = {}
        for dep, (word1, id1), (word2, id2) in deps:
            lemma1 = self.get_lemma(word1)
            lemma2 = self.get_lemma(word2)
            #logging.info('lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
            machine1, machine2 = self._add_dependency(
                dep, (lemma1, id1), (lemma2, id2), word2machine=word2machine)
            word2machine[lemma1] = machine1
            word2machine[lemma2] = machine2

        root_machine = word2machine[root_lemma]
        machine = Machine(word, ConceptControl())
        machine.append(root_machine, 0)
        return machine

    def add_dependency(self, string):
        #e.g. nsubjpass(pushed-7, salesman-5)
        logging.debug('processing dependency: {}'.format(string))
        dep, (word1, id1), (word2, id2) = Wrapper.parse_dependency(string)
        lemma1 = self.get_lemma(word1)
        lemma2 = self.get_lemma(word2)
        self._add_dependency(dep, (lemma1, id1), (lemma2, id2),
                             use_lexicon=True, activate_machines=True)

    def _add_dependency(self, dep, (word1, id1), (word2, id2),
                        word2machine=None, use_lexicon=False,
                        activate_machines=False):
        """Given a triplet from Stanford Dep.: D(w1,w2), we create and activate
        machines for w1 and w2, then run all operators associated with D on the
        sequence of the new machines (m1, m2)"""
        machines = []
        for word in (word1, word2):
            if use_lexicon:
                machine = self.lexicon.get_machine(word)
            else:
                machine = word2machine.get(word,
                                           Machine(word, ConceptControl()))

            if activate_machines:
                logging.debug('activating {}'.format(machine))
                self.lexicon.add_active(machine)
                self.lexicon.expand(machine)
            machines.append(machine)

        machine1, machine2 = machines
        for operator in self.dep_to_op.get(dep, []):
            logging.info('operator {0} acting on machines {1} and {2}'.format(
                operator, machine1, machine2))
            operator.act((machine1, machine2))

        return machine1, machine2

    def draw_word_graphs(self):
        for word, machine in self.definitions.iteritems():
            graph = MachineGraph.create_from_machines([machine])
            clean_word = Machine.d_clean(word)
            f = open('graphs/words/{0}.dot'.format(clean_word), 'w')
            f.write(graph.to_dot().encode('utf-8'))

    def word_similarity(self, word1, word2, pos1, pos2):
        lemma1, lemma2 = map(self.get_lemma, (word1, word2))
        #logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
        if lemma1 == lemma2:
            return 1
        oov = filter(lambda l: l not in self.definitions, (lemma1, lemma2))
        if oov:
            logging.debug(u'OOV: {0}, no machine similarity')
            return None

        machine1, machine2 = map(self.definitions.get, (lemma1, lemma2))
        #map(self.lexicon.add_active, (machine1, machine2))
        #map(self.lexicon.expand, (machine1, machine2))
        zero_links_1 = set(filter(
            lambda s: not s.isupper(),
            [m.printname() for m in machine1.partitions[0]]))
        zero_links_2 = set(filter(
            lambda s: not s.isupper(),
            [m.printname() for m in machine2.partitions[0]]))
        #logging.info('machine1 0-links: {0}, machine2 0-links: {1}'.format(
        #    zero_links_1, zero_links_2))
        #sim = jaccard(zero_links_1, zero_links_2)
        union = zero_links_1 | zero_links_2
        intersection = zero_links_1 & zero_links_2
        if not intersection:
            sim = 0
        else:
            sim = float(len(intersection)) / len(union)
            #sim = float(len(intersection)) / min(len(zero_links_1),
            #                                     len(zero_links_2))
            logging.info(u'lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
            logging.info(u'shared: {0}'.format(intersection))
            logging.info('sim: {0}'.format(sim))

        draw_graphs = True
        if draw_graphs and not self.batch:
            graph = MachineGraph.create_from_machines(
                [machine1, machine2], max_depth=1)
            f = open('graphs/{0}_{1}.dot'.format(lemma1, lemma2), 'w')
            f.write(graph.to_dot().encode('utf-8'))
        return sim

    def run(self, sentence):
        """Parses a sentence, runs the spreading activation and returns the
        messages that have to be sent to the active plugins."""
        try:
            sp = SentenceParser()
            sa = SpreadingActivation(self.lexicon)
            machines = sp.parse(sentence)
            logging.debug('machines: {}'.format(machines))
            logging.debug('machines: {}'.format(
                [m for m in machines]))
            for machine_list in machines:
                for machine in machine_list:
                    if machine.control.kr['CAT'] == 'VERB':
                        logging.debug('adding verb construction for {}'.format(
                            machine))
                        self.lexicon.add_construction(VerbConstruction(
                            machine.printname(), self.lexicon, self.supp_dict))
            logging.info('constructions: {}'.format(
                self.lexicon.constructions))

            # results is a list of (url, data) tuples
            results = sa.activation_loop(machines)
            print 'results:', results
            print 'machines:', machines

            graph = MachineGraph.create_from_machines(
                [m[0] for m in machines], max_depth=1)
            f = open('machines.dot', 'w')
            f.write(graph.to_dot().encode('utf-8'))

            self.lexicon.clear_active()
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            raise(e)

        return results

def test_plain():
    print 'building wrapper...'
    w = Wrapper(sys.argv[1])
    test_sen = [
        ([
            ("The", "the/ART"),
            ("snake", "snake/NOUN")], 'NP'),
        ("ate", "eat/VERB<PAST>"),
        ([
            ("the", "the/ART"),
            ("elephant", "elephant/NOUN")], 'NP')]

    print 'running...'
    w.run(test_sen)

def test_dep():
    print 'building wrapper...'
    w = Wrapper(sys.argv[1])
    for line in sys.stdin:
        w.add_dependency(line)

    active_machines = w.lexicon.active_machines()
    logging.debug('active machines: {}'.format(active_machines))
    graph = MachineGraph.create_from_machines(active_machines)
    f = open('machines.dot', 'w')
    f.write(graph.to_dot().encode('utf-8'))

def build_ext_defs():
    return Wrapper(sys.argv[1], include_longman=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    w = build_ext_defs()
    w.draw_word_graphs()
    #f = open('wrapper.pickle', 'w')
    #cPickle.dump(w, f)
