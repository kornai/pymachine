import pickle
import logging
import sys
import traceback

from pymachine.src.lexicon import Lexicon
from pymachine.src.definition_parser import read as read_defs

def dump(argv):
    plur_filen = '../../res/4lang/4lang.plural'
    logging.info('reading plurals from {}'.format(plur_filen))
    definitions = read_defs(file(argv[0]), plur_filen, add_indices=True, three_parts=True)
    pickle.dump(definitions, open(argv[1], "w"))

def print_to_debug_strs(graph, cano_machs):
    for pn, machines in graph.iteritems():
        print pn
        for m in machines:
            print m.to_debug_str(max_depth=42,parents_to_display=7,stop=cano_machs)
        print

def test_static(argv):
    fn = "/home/zseder/Proj/machine/pymachine/src/definitions.dump"
    if len(argv) > 0:
        fn = argv[0]
    definitions = pickle.load(open(fn))
    l = Lexicon()
    try:
        l.add_static(definitions.itervalues())
    except Exception as e:
        print "Exception", e
        print traceback.print_exc(file=sys.stdout)
        print traceback.print_exc(file=sys.stderr)
    l.finalize_static()

    cano_machs = set([ machs_with_name[0] for machs_with_name in l.static.itervalues() ])
    # TODO fix stop
    def_graph = l.extract_definition_graph(deep_cases=True)
    # print_to_debug_strs(l.static)
    # print_to_debug_strs(def_graph)
    with open(sys.argv[3], mode='w') as tsv_out:
        for pn, machines in def_graph.iteritems():
            tsv_out.write(pn)
            for m in machines:
                tsv_out.write('\n{}'.format(m.to_debug_str(max_depth=7,parents_to_display=7,stop=cano_machs)))
            tsv_out.write('\n')

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=
            "%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")

    command = sys.argv[1]
    if command == "dump":
        dump(sys.argv[2:])
    elif command == "add_static":
        test_static(sys.argv[2:])
    else:
        raise Exception("Unknown command")


