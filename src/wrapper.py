import os
import ConfigParser

from sentence_parser import SentenceParser
from lexicon import Lexicon
from spreading_activation import SpreadingActivation
from definition_parser import read as read_defs
from construction import *
from matcher import *
from sup_dic import supplementary_dictionary_reader as sdreader
from avm import AVM

class Wrapper:
    def __init__(self, cf):
        self.cfn = cf
        self.__read_config()

        self.lexicon = Lexicon()
        self.__read_files()
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
        self.supp_dict_fn = items["supp_dict"]
        self.stations_fn = items["stations"]

    def __read_files(self):
        self.__read_definitions()
        self.__read_supp_dict()

    def __read_definitions(self):
        for file_name, printname_index in self.def_files:
            # TODO HACK makefile needed
            if (file_name.endswith("generated") and
                not os.path.exists(file_name)):
                raise Exception("A definition file that supposed to be " +
                    "generated by pymachine/scripts/generate_translation_dict.sh" +
                    " does not exist: {0}".format(file_name))
            definitions = read_defs(file(file_name), printname_index)
            logging.debug("{0}: {1}".format(file_name, definitions.keys()))
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
            #self.lexicon.add_construction(megy_construction)
        except KeyError:
            pass
        try:
            tesz_construction = VerbConstruction("tesz", self.lexicon.static[
                "tesz"], self.supp_dict)
            del self.lexicon.static["tesz"]
            self.lexicon.add_construction(tesz_construction)
        except KeyError:
            pass
        #self.lexicon.add_construction(ElviraConstruction())

        self.lexicon.add_construction(DummyNPConstruction())
        self.lexicon.add_construction(TheConstruction())
        self.lexicon.add_construction(MaxNP_InBetweenPostP_Construction())
        self.lexicon.add_construction(PostPConstruction())

        station_matcher = FileContainsMatcher(self.stations_fn)
        ic_name_matcher = AndMatcher(
                EnumMatcher("ic_name", self.lexicon),
                PosMatcher("<DET>")
                )
        src_matcher = AndMatcher(self.supp_dict["@HUN_GO_SRC"],
                                 station_matcher)
        tgt_matcher = AndMatcher(self.supp_dict["@HUN_GO_TGT"],
                                 station_matcher)
        ea = elvira_avm = AVM('ElviraAVM')
        ea.add_attribute("vonat", PrintnameMatcher("train"), AVM.RREQ, None)
        ea.add_attribute("menetrend", PrintnameMatcher("schedule"), AVM.RREQ, None)
        ea.add_attribute("src", src_matcher, AVM.RREQ, "Budapest")
        ea.add_attribute("tgt", tgt_matcher, AVM.RREQ, None)
        ea.add_attribute("date", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
        ea.set_satisfaction('vonat and menetrend and tgt')
        elvira_const = AVMConstruction(ea)
        self.lexicon.add_avm_construction(elvira_const)

        pta = plain_ticket_avm = AVM('PlainTicketAvm')
        pta.add_attribute("BKSZ", PrintnameMatcher("bksz"), AVM.ROPT, None)
        pta.add_attribute("CLASS", EnumMatcher("class", self.lexicon),
                          AVM.RREQ, "2")
        pta.add_attribute("DATE", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
        pta.add_attribute("DEST", tgt_matcher, AVM.RREQ, None)
        pta.add_attribute("INV", PrintnameMatcher("invoice"), AVM.ROPT, None)
        pta.add_attribute("RED", EnumMatcher("mav_reduction", self.lexicon),
                          AVM.RREQ, "full_price")
        pta.add_attribute("RET", EnumMatcher("ticket_type", self.lexicon),
                          AVM.RREQ, "one_way")
        pta.add_attribute("SRC", src_matcher, AVM.RREQ, u"Budapest-Nyugati")
        # Elvira takes precedence
        pta.add_attribute("ELVIRA", AndMatcher(
            PrintnameMatcher('ElviraAVM'),
            SatisfiedAVMMatcher()), AVM.RNEG, None)
        # If there is an invalid seat ticket request, do not return a ticket either
        pta.add_attribute('SEAT_TICKET', AndMatcher(
            PrintnameMatcher('ICTicketAvm'),
            SatisfiedAVMMatcher(False)), AVM.RNEG, None)
        pta.add_attribute('JEGY', AndMatcher(
            PrintnameMatcher('^(?:jegy|menetjegy|vonatjegy)$'), NotMatcher(ConceptMatcher())),
            AVM.ROPT, None)
        pta.add_attribute('HELYJEGY', AndMatcher(
            PrintnameMatcher('^helyjegy$'), NotMatcher(ConceptMatcher())),
            AVM.ROPT, None)
        pta.add_attribute("IC", ic_name_matcher, AVM.ROPT, None)
        pta.set_satisfaction('SRC and CLASS and RED and RET and (IC or DEST) and not ELVIRA and not SEAT_TICKET and not (HELYJEGY and not JEGY)')
        pt_const = AVMConstruction(pta)
        self.lexicon.add_construction(pt_const)

        ita = ic_ticket_avm = AVM('ICTicketAvm')
        ita.add_attribute("CLASS", EnumMatcher("class", self.lexicon), AVM.RREQ, "2")
        ita.add_attribute("DATE", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
        ita.add_attribute("DEST", tgt_matcher, AVM.RREQ, None)
        ita.add_attribute("INV", PrintnameMatcher("invoice"), AVM.ROPT, None)
        ita.add_attribute("PLACE", EnumMatcher("seat", self.lexicon), AVM.ROPT, None)
        ita.add_attribute("SRC", src_matcher, AVM.RREQ, u"Budapest-Nyugati")
        ita.add_attribute("IC", ic_name_matcher, AVM.ROPT, None)
        ita.add_attribute("TIME", PosMatcher("\[TIME\]"), AVM.RREQ, None)
        ita.set_satisfaction('SRC and CLASS and (IC or (TIME and DEST))')
        it_const = AVMConstruction(ita)
        self.lexicon.add_avm_construction(it_const)

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
