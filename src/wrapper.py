#!/usr/bin/env python

from copy import deepcopy
import os
import pickle
import re
import sys
import logging
import ConfigParser

from construction import VerbConstruction
from sentence_parser import SentenceParser
from lexicon import Lexicon
from pymachine.src.machine import MachineGraph
from spreading_activation import SpreadingActivation
from definition_parser import read as read_defs
from sup_dic import supplementary_dictionary_reader as sdreader
from dep_map import dep_map_reader
#from demo_misc import add_verb_constructions, add_avm_constructions
import np_grammar

class Wrapper:

    dep_regex = re.compile('([a-z_]*)\((.*?)-([0-9]*), (.*?)-([0-9]*)\)')

    @staticmethod
    def get_lemma(word, tok2lemma):
        if word in tok2lemma:
            return tok2lemma[word]
        for char in ('.', ',', '='):
            for part in word.split(char):
                if part in tok2lemma:
                    return tok2lemma[part]
        raise Exception(
            "can't find lemma for word '{}', tok2lemma: {}".format(
                word, tok2lemma))

    def __init__(self, cf):
        self.cfn = cf
        self.__read_config()

        self.wordlist = set()
        self.__read_definitions()
        self.__read_supp_dict()
        self.reset_lexicon()

    def reset_lexicon(self):
        self.lexicon = Lexicon()
        self.__add_definitions()
        #TODO
        self.dep_to_op = dep_map_reader(self.dep_map_fn, self.lexicon)
        self.__add_constructions()

    def __read_config(self):
        machinepath = os.path.realpath(__file__).rsplit("/", 2)[0]
        if "MACHINEPATH" in os.environ:
            machinepath = os.environ["MACHINEPATH"]
        config = ConfigParser.SafeConfigParser({"machinepath": machinepath})
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_files = [(s.split(":")[0].strip(), int(s.split(":")[1]))
                          for s in items["definitions"].split(",")]
        self.dep_map_fn = items.get("dep_map")
        self.supp_dict_fn = items.get("supp_dict")
        self.plural_fn = items.get("plurals")

    def __read_definitions(self):
        for file_name, printname_index in self.def_files:
            # TODO HACK makefile needed
            if (file_name.endswith("generated") and
                    not os.path.exists(file_name)):
                raise Exception(
                    "A definition file that should be generated" +
                    " by pymachine/scripts/generate_translation_dict.sh" +
                    " does not exist: {0}".format(file_name))

            if file_name.endswith('pickle'):
                logging.debug('loading definitions...')
                self.definitions = pickle.load(file(file_name))
            else:
                logging.debug('parsing definitions...')
                self.definitions = read_defs(
                    file(file_name), self.plural_fn, printname_index,
                    three_parts=True)

                logging.debug('dumping definitions to file...')
                f = open('definitions.pickle', 'w')
                pickle.dump(self.definitions, f)

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

    def add_dependency(self, string, tok2lemma):
        #e.g. nsubjpass(pushed-7, salesman-5)
        """Given a triplet from Stanford Dep.: D(w1,w2), we create and activate
        machines for w1 and w2, then run all operators associated with D on the
        sequence of the new machines (m1, m2)"""
        logging.debug('processing dependency: {}'.format(string))
        dep_match = Wrapper.dep_regex.match(string)
        if not dep_match:
            raise Exception('cannot parse dependency: {0}'.format(string))
        dep, word1, id1, word2, id2 = dep_match.groups()
        lemma1 = Wrapper.get_lemma(word1, tok2lemma)
        lemma2 = Wrapper.get_lemma(word2, tok2lemma)
        self.wordlist.add(lemma1)
        self.wordlist.add(lemma2)
        machine1 = self.lexicon.get_machine(lemma1)
        machine2 = self.lexicon.get_machine(lemma2)

        for machine in (machine1, machine2):
            logging.debug('activating {}'.format(machine))
            self.lexicon.add_active(machine)

        for operator in self.dep_to_op.get(dep, []):
            logging.debug('operator {0} acting on machines {1} and {2}'.format(
                operator, machine1, machine2))
            operator.act((machine1, machine2))

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
            f.write(graph.to_dot())

            self.lexicon.clear_active()
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            raise(e)

        return results

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    print 'building wrapper...'
    w = Wrapper(sys.argv[1])

    #dg = w.lexicon.extract_definition_graph()
    #print dg
    test_sen = [
        ([
            ("The", "the/ART"),
            ("snake", "snake/NOUN")], 'NP'),
        ("ate", "eat/VERB<PAST>"),
        ([
            ("the", "the/ART"),
            ("elephant", "elephant/NOUN")], 'NP')]

    """
    test_sen = [
        ([("vets", "vet/NOUN<PLUR>")], 'NP'),
        ("heal", "heal/VERB"),
        ([
            #("sick", "sick/ADJ"),
            ("zebras", "zebra/NOUN<PLUR>")], 'NP')]
    """
    print 'running...'
    #w.run(test_sen)
    #quit()
    for line in sys.stdin:
        w.add_dependency(line)

    active_machines = w.lexicon.active_machines()
    logging.debug('active machines: {}'.format(active_machines))
    graph = MachineGraph.create_from_machines(active_machines)
    f = open('machines.dot', 'w')
    f.write(graph.to_dot())
    #import pickle
    #pickle.dump(dg, open('foo', 'w'))
    #dg = w.lexicon.extract_definition_graph()
    #print dg
