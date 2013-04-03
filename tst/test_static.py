import pickle
import logging
import sys
import traceback

from pymachine.src.lexicon import Lexicon
from pymachine.src.definition_parser import read as read_defs

def dump(argv):
    definitions = read_defs(file(argv[0]), 2, add_indices=True)
    pickle.dump(definitions, open(argv[1], "w"))

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
    print "\n\n===========\n\n"

    for pn, machines in l.static.iteritems():
        print pn
        for m in machines:
            print m.to_debug_str()
        print

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

