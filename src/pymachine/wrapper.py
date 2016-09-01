#!/usr/bin/env python
from copy import deepcopy
import cPickle
import logging
import os
import re
import sys

from pymachine.construction import VerbConstruction
from pymachine.sentence_parser import SentenceParser
from pymachine.lexicon import Lexicon
from pymachine.utils import ensure_dir, MachineGraph, MachineTraverser
from pymachine.machine import Machine
from pymachine.spreading_activation import SpreadingActivation
from pymachine.definition_parser import read_defs
from pymachine.sup_dic import supplementary_dictionary_reader as sdreader
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

    num_re = re.compile(r'^[0-9.,]+$', re.UNICODE)

    def __init__(self, cfg, batch=False, include_ext=True):
        self.cfg = cfg
        self.__read_config()
        self.batch = batch
        self.wordlist = set()
        self.__read_definitions()
        if include_ext:
            self.get_ext_definitions()
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
        items = dict(self.cfg.items("machine"))
        self.def_files = [(s.split(":")[0].strip(), int(s.split(":")[1]))
                          for s in items["definitions"].split(",")]
        self.dep_map_fn = items.get("dep_map")
        self.tok2lemma_fn = items.get("tok2lemma")
        self.ext_defs_path = items.get("ext_definitions")
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
                    file(file_name), printname_index=printname_index,
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
        # add_verb_constructions(self.lexicon, self.supp_dict)
        # add_avm_constructions(self.lexicon, self.supp_dict)

    def get_ext_definitions(self):
        if self.ext_defs_path.endswith('pickle'):
            logging.info(
                'loading external definitions from {}...'.format(
                    self.ext_defs_path))
            definitions = cPickle.load(file(self.ext_defs_path))

        else:
            raise Exception("building machines from deps has moved to 4lang")
        for word, machine in definitions.iteritems():
            if word not in self.definitions:
                self.definitions[word] = set([machine])

        logging.info('done')

    def draw_single_graph(self, word, path):
        clean_word = Machine.d_clean(word)
        for c, machine in enumerate(self.definitions[word]):
            graph = MachineGraph.create_from_machines([machine])
            file_name = os.path.join(path, '{0}_{1}.dot'.format(clean_word, c))
            with open(file_name, 'w') as file_obj:
                file_obj.write(graph.to_dot().encode('utf-8'))

    def draw_word_graphs(self):
        ensure_dir('graphs/words')
        for c, (word, machines) in enumerate(self.definitions.iteritems()):
            if c % 1000 == 0:
                logging.info("{0}...".format(c))
            for i, machine in enumerate(machines):
                graph = MachineGraph.create_from_machines([machine])
                clean_word = Machine.d_clean(word)
                if clean_word[0] == 'X':
                    clean_word = clean_word[1:]
                f = open('graphs/words/{0}_{1}.dot'.format(clean_word, i), 'w')
                f.write(graph.to_dot().encode('utf-8'))

    def get_def_words(self, stream):
        for headword, machines in self.definitions.iteritems():
            if headword[0] == '@':
                continue
            for machine in machines:
                def_words = [
                    word for word in MachineTraverser.get_nodes(machine)
                    if word[0] not in '=@']
                stream.write(
                    u"{0}\t{1}\n".format(
                        headword, u"\t".join(def_words)).encode("utf-8"))

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
    w = Wrapper(sys.argv[1])
    w.draw_word_graphs()
