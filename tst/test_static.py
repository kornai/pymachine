import pickle
import logging
import sys

from pymachine.src.lexicon import Lexicon
from pymachine.src.machine import Machine
from pymachine.src.definition_parser import read as read_defs

def dump(argv):
    definitions = read_defs(file(argv[0]), 0)
    pickle.dump(definitions, open(argv[1], "w"))

def test_static(argv):
    fn = "/home/zseder/Proj/machine/pymachine/src/definitions.dump"
    if len(argv) > 1:
        fn = argv[0]
    definitions = pickle.load(open(fn))
    l = Lexicon()
    l.add_static(definitions.itervalues())
    l.finalize_static()

    #for pn, machines in w.lexicon.static.iteritems():
        #print pn
        #for m in machines:
            #print m.to_debug_str()
        #print

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

