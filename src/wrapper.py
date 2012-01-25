import ConfigParser

from sentence_parser import SentenceParser
from lexicon import Lexicon
from spreading_activation import SpreadingActivation
from definition_parser import read

config_filename = "machine.cfg"

class Wrapper:
    def __init__(self, cf=config_filename):
        self.cfn = cf
        self.__read_config()

        self.lexicon = Lexicon()
        self.__read_files()

    def __read_config(self):
        config = ConfigParser.SafeConfigParser()
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_fn = items["definitions"]
        #self.con_fn = items["constructions"]
        #self.inference_rules = items["inference_rules"]

    def __read_files(self):
        self.__read_definitions()
        #self.__read_constructions()

    def __read_definitions(self):
        definitions = read(file(self.def_fn))
        self.lexicon.add_static(definitions.itervalues())

    #def __read_constructions(self):
       #from constructions import read_constructions
       #self.constructions = read_constructions(file(self.con_fn), self.definitions)

    #def __run_infer(self, machine):
        #"""
        #run inference engine over the machines
        #(usually called after constructions has been run)
        #"""
        #from inference import InferenceEngine as IE
        #ie = IE()
        #ie.load(self.inference_rules)
        #ie.infer(machine)

    def run(self, sentence):
        """Parses a sentence, runs the spreading activation and returns the
        messages that have to be sent to the active plugins."""
        sp = SentenceParser()
        sa = SpreadingActivation(self.lexicon)
        machines = sp.parse(sentence)
        self.lexicon.add_active(machines)

        # results is a list of (url, data) tuples
        results = sa.activation_loop()

        return results

if __name__ == "__main__":
    pass 
