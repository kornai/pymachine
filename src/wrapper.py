import ConfigParser

from sentence_parser import SentenceParser
from lexicon import Lexicon
from spreading_activation import SpreadingActivation
from definition_parser import read as read_defs
from construction import *
from sup_dic import supplementary_dictionary_reader as sdreader

config_filename = "machine.cfg"

class Wrapper:
    def __init__(self, cf=config_filename):
        self.cfn = cf
        self.__read_config()

        self.lexicon = Lexicon()
        self.__read_files()
        self.__add_constructions()

    def __read_config(self):
        config = ConfigParser.SafeConfigParser()
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_fn = items["definitions"]
        self.supp_dict_fn = items["supp_dict"]

    def __read_files(self):
        self.__read_definitions()
        self.__read_supp_dict()

    def __read_definitions(self):
        definitions = read_defs(file(self.def_fn))
        self.lexicon.add_static(definitions.itervalues())

    def __read_supp_dict(self):
        self.supp_dict = sdreader(file(self.supp_dict_fn))

    def __add_constructions(self):
        # TODO this should be created automatically, maybe from knowing,
        # that "megy" is actually a verb, there is a POS in the definitions
        try:
            megy_construction = VerbConstruction("megy", self.lexicon.static[
                "megy"], self.supp_dict)
            del self.lexicon.static["megy"]
            self.lexicon.add_construction(megy_construction)
        except KeyError:
            pass
        try:
            tesz_construction = VerbConstruction("tesz", self.lexicon.static[
                "tesz"], self.supp_dict)
            del self.lexicon.static["tesz"]
            self.lexicon.add_construction(tesz_construction)
        except KeyError:
            pass
        self.lexicon.add_construction(ElviraConstruction())

        self.lexicon.add_construction(DummyNPConstruction())
        self.lexicon.add_construction(TheConstruction())
        self.lexicon.add_construction(MaxNP_InBetweenPostP_Construction())
        self.lexicon.add_construction(PostPConstruction())
        

        # TODO create shrdlu construction

    def run(self, sentence):
        """Parses a sentence, runs the spreading activation and returns the
        messages that have to be sent to the active plugins."""
        try:
            sp = SentenceParser()
            sa = SpreadingActivation(self.lexicon)
            machines = sp.parse(sentence)

            # results is a list of (url, data) tuples
            results = sa.activation_loop(machines)
            self.lexicon.clear_active()
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            raise(e)

        return results

def test():
    w = Wrapper(config_filename)
    w.run([([("a", "DET"),
             ("kek", "ADJ"),
             ("kockat", "NOUN<CAS<ACC>>")
            ], "ACC")])

if __name__ == "__main__":
    test() 
