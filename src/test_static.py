import pickle
import logging

from lexicon import Lexicon

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format=
            "%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")

    definitions = pickle.load(open(
            "/home/zseder/Proj/machine/pymachine/src/definitions.dump"))
    l = Lexicon()
    l.add_static(definitions.itervalues())
    l.finalize_static()

    #for pn, machines in w.lexicon.static.iteritems():
        #print pn
        #for m in machines:
            #print m.to_debug_str()
        #print
