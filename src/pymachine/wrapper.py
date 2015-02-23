#!/usr/bin/env python
import ConfigParser
from copy import deepcopy
import cPickle
import json
import logging
import os
import re
import sys
import traceback

from hunmisc.utils.huntool_wrapper import Hundisambig, Ocamorph, OcamorphAnalyzer, MorphAnalyzer  # nopep8
from stemming.porter2 import stem

from pymachine.construction import VerbConstruction
from pymachine.sentence_parser import SentenceParser
from pymachine.lexicon import Lexicon
from pymachine.operators import AppendToBinaryFromLexiconOperator  # nopep8
from pymachine.utils import MachineGraph
from pymachine.machine import Machine
from pymachine.control import ConceptControl
from pymachine.spreading_activation import SpreadingActivation
from pymachine.definition_parser import read as read_defs
from pymachine.sup_dic import supplementary_dictionary_reader as sdreader
from pymachine.dependency import DepsToMachines
#from demo_misc import add_verb_constructions, add_avm_constructions
from pymachine import np_grammar

class KeyDefaultDict(dict):
    def __missing__(self, key):
        return key

def jaccard(s1, s2):
    try:
        return float(len(s1 & s2)) / len(s1 | s2)
    except ZeroDivisionError:
        return 0.0

class Wrapper:

    dep_regex = re.compile("([a-z_-]*)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")
    num_re = re.compile(r'^[0-9.,]+$', re.UNICODE)

    stem_first = True

    def get_lemma(self, word, existing_only=False, stem_first=False,
                  debug=False):
        if debug:
            tried = []
        if stem_first:
            stemmed_word = stem(word)
            if debug:
                tried.append(stemmed_word)
            stemmed_lemma = self.get_lemma(
                stemmed_word, existing_only=existing_only, stem_first=False)
            if stemmed_lemma is not None:
                self.tok2lemma[word] = stemmed_lemma
                return stemmed_lemma

        if word in self.tok2lemma:
            return self.tok2lemma[word]
        elif word in self.oov and existing_only:
            return None
        elif word in self.definitions:
            self.tok2lemma[word] = word
            return word

        #logging.info(u'analyzing {0}'.format(word))
        disamb_lemma = list(self.analyzer.analyze(
            [[word]]))[0][0][1].split('||')[0].split('<')[0]

        if not existing_only or disamb_lemma in self.definitions:
            self.tok2lemma[word] = disamb_lemma
        else:
            if debug:
                tried.append(disamb_lemma)
            candidates = self.morph_analyzer.analyze([[word]]).next().next()
            for cand in candidates:
                lemma = cand.split('||')[0].split('<')[0]
                if debug:
                    tried.append(lemma)
                if lemma in self.definitions:
                    self.tok2lemma[word] = lemma
                    break
            else:
                if debug:
                    logging.info('new OOV: {0} (tried these: {1})'.format(
                        word, tried))
                self.oov.add(word)
                return None

        return self.tok2lemma[word]

    def get_analyzer(self):
        ocamorph = Ocamorph(
            os.path.join(self.hunmorph_path, "ocamorph"),
            os.path.join(self.hunmorph_path, "morphdb_en.bin"))
        ocamorph_analyzer = OcamorphAnalyzer(ocamorph)
        morph_analyzer = MorphAnalyzer(
            ocamorph,
            Hundisambig(
                os.path.join(self.hunmorph_path, "hundisambig"),
                os.path.join(self.hunmorph_path, "en_wsj.model")))

        return morph_analyzer, ocamorph_analyzer

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

    def __init__(self, cf, batch=False, include_longman=False):
        self.cfn = cf
        self.__read_config()
        self.batch = batch
        self.analyzer, self.morph_analyzer = self.get_analyzer()
        self.tok2lemma = {}
        #self.tok2lemma = Wrapper.get_tok2lemma(self.tok2lemma_fn)
        self.oov = set()
        self.wordlist = set()
        self.deps_to_machines = DepsToMachines(self.dep_map_fn)
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
        config = ConfigParser.SafeConfigParser()
        logging.info('reading machine config from {0}'.format(self.cfn))
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_files = [(s.split(":")[0].strip(), int(s.split(":")[1]))
                          for s in items["definitions"].split(",")]
        self.dep_map_fn = items.get("dep_map")
        self.tok2lemma_fn = items.get("tok2lemma")
        self.longman_deps_path = items.get("longman_deps")
        self.hunmorph_path = items.get("hunmorph_path")
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
                logging.info(
                    'loading 4lang definitions from {}...'.format(file_name))
                definitions = cPickle.load(file(file_name))
            else:
                logging.info('parsing 4lang definitions...')
                definitions = read_defs(
                    file(file_name), self.plural_fn, printname_index,
                    three_parts=True)

                logging.info('dumping 4lang definitions to file...')
                f = open('{0}.pickle'.format(file_name), 'w')
                cPickle.dump(definitions, f)

            for pn, machines in definitions.iteritems():
                if pn not in self.definitions:
                    self.definitions[pn] = machines
                else:
                    self.definitions[pn] |= machines

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
        if self.longman_deps_path.endswith('pickle'):
            logging.info(
                'loading pre-compiled Longman definitions from {}...'.format(
                    self.longman_deps_path))
            definitions = cPickle.load(file(self.longman_deps_path))

        elif self.longman_deps_path.endswith('json'):
            logging.info('compiling Longman definitions from {}...'.format(
                self.longman_deps_path))
            logging.info('this may take a few minutes')
            logging.info('loading JSON...')
            longman = json.load(open(self.longman_deps_path))
            logging.info('done!')
            logging.info('building definitions...')
            definitions = {}
            #entries = longman['entries']
            #print entries
            for entry in longman['entries']:
                #print entry
                #logging.info("entry: {0}".format(entry))
                if entry["to_filter"]:
                    continue
                word = entry['hw']
                if not entry['senses']:
                    #TODO these are words that only have pointers to an MWE
                    #that they are part of.
                    #logging.warning("word has no senses: {0}".format(word))
                    continue
                deps = entry['senses'][0]['definition']['deps']
                if not deps:
                    #TODO see previous comment
                    continue
                try:
                    machine = self.get_dep_definition(word, deps)
                except Exception:
                    logging.error(
                        'skipping "{0}" because of an exception:'.format(word))
                    logging.info("entry: {0}".format(entry))
                    traceback.print_exc()
                    continue
                if machine is None:
                    continue
                definitions[word] = machine

            logging.info('done!')
            logging.info('pickling Longman definitions...')
            pickle_fn = self.longman_deps_path.replace(".json", ".pickle")
            with open(pickle_fn, 'w') as out_file:
                cPickle.dump(definitions, out_file)
            logging.info('done!')

        else:
            raise Exception(
                'unknown format: {0}'.format(self.longman_deps_path))

        for word, machine in definitions.iteritems():
            if word not in self.definitions:
                self.definitions[word] = set([machine])

        logging.info('done')

    @staticmethod
    def parse_dependency(string):
        dep_match = Wrapper.dep_regex.match(string)
        if not dep_match:
            raise Exception('cannot parse dependency: {0}'.format(string))
        dep, word1, id1, word2, id2 = dep_match.groups()
        return dep, (word1, id1), (word2, id2)

    def get_dep_definition(self, word, dep_strings):
        #logging.info("word: {0}, deps: {1}".format(word, dep_strings))
        lexicon = Lexicon()
        deps = map(Wrapper.parse_dependency, dep_strings)
        #logging.info("parsed as: {0}".format(deps))
        root_deps = filter(lambda d: d[0] == 'root', deps)
        if len(root_deps) != 1:
            logging.warning(
                'no unique root dependency, skipping word "{0}"'.format(word))
            return None

        root_word, root_id = root_deps[0][2]
        root_lemma = self.get_lemma(root_word)
        root_lemma = root_lemma.replace('/', '_PER_')

        word2machine = {}
        for dep, (word1, id1), (word2, id2) in deps:
            lemma1 = self.get_lemma(word1)
            lemma2 = self.get_lemma(word2)
            if not lemma1:
                lemma1 = word1
            if not lemma2:
                lemma2 = word2
            #TODO
            lemma1 = lemma1.replace('/', '_PER_')
            lemma2 = lemma2.replace('/', '_PER_')
            #logging.info('w1: {0}, w2: {1}'.format(word1, word2))
            #logging.info('lemma1: {0}, lemma2: {1}'.format(lemma1, lemma2))
            machine1, machine2 = self._add_dependency(
                dep, (lemma1, id1), (lemma2, id2), temp_lexicon=lexicon)
            word2machine[lemma1] = machine1
            word2machine[lemma2] = machine2

        root_machine = word2machine[root_lemma]
        #logging.info("root machine: {0}".format(root_machine))
        word_machine = word2machine.get(word, Machine(word, ConceptControl()))
        word_machine.append(root_machine, 0)
        return word_machine

    def add_dependency(self, string):
        #e.g. nsubjpass(pushed-7, salesman-5)
        logging.debug('processing dependency: {}'.format(string))
        dep, (word1, id1), (word2, id2) = Wrapper.parse_dependency(string)
        lemma1 = self.get_lemma(word1)
        lemma2 = self.get_lemma(word2)
        self._add_dependency(dep, (lemma1, id1), (lemma2, id2),
                             use_lexicon=True, activate_machines=True)

    def _add_dependency(self, dep, (word1, id1), (word2, id2),
                        temp_lexicon=None):
        """Given a triplet from Stanford Dep.: D(w1,w2), we create and activate
        machines for w1 and w2, then run all operators associated with D on the
        sequence of the new machines (m1, m2)"""
        lexicon = temp_lexicon if temp_lexicon is not None else self.lexicon
        #logging.info(
        #    'adding dependency {0}({1}, {2})'.format(dep, word1, word2))
        machine1, machine2 = map(lexicon.get_machine, (word1, word2))

        self.deps_to_machines.apply_dep(dep, machine1, machine2, lexicon)
        return machine1, machine2

    def draw_single_graph(self, word):
        for w, machines in self.definitions.iteritems():
            if w != word:
                continue
            for c, machine in enumerate(machines):
                graph = MachineGraph.create_from_machines([machine])
                clean_word = Machine.d_clean(w)
                f = open('graphs/words/{0}_{1}.dot'.format(clean_word, c), 'w')
                f.write(graph.to_dot().encode('utf-8'))

    def draw_word_graphs(self):
        for c, (word, machines) in enumerate(self.definitions.iteritems()):
            if c % 1000 == 0:
                logging.info("{0}...".format(c))
            for i, machine in enumerate(machines):
                graph = MachineGraph.create_from_machines([machine])
                clean_word = Machine.d_clean(word)
                f = open('graphs/words/{0}_{1}.dot'.format(clean_word, i), 'w')
                f.write(graph.to_dot().encode('utf-8'))

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

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    w = Wrapper(sys.argv[1], include_longman=True)
    #w.draw_word_graphs()
    #f = open('wrapper.pickle', 'w')
    #cPickle.dump(w, f)
