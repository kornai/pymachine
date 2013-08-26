# vim: set fileencoding=utf-8 :

from construction import VerbConstruction, AVMConstruction
from matcher import FileContainsMatcher, EnumMatcher, PrintnameMatcher,\
        AndMatcher, NotMatcher, ConceptMatcher,\
        SatisfiedAVMMatcher
from avm import AVM

def add_verb_constructions(lexicon, supp_dict):
    megy_construction = VerbConstruction("megy", lexicon, supp_dict)
    lexicon.add_construction(megy_construction)
    tesz_construction = VerbConstruction("tesz", lexicon, supp_dict)
    lexicon.add_construction(tesz_construction)

def add_avm_constructions(lexicon, supp_dict):
    ## Creating elvira construction for calling elvira
    station_matcher = FileContainsMatcher(stations_fn)
    ic_name_matcher = AndMatcher(
            EnumMatcher("ic_name", lexicon)#,
            #PosMatcher("<DET>")
            )
    src_matcher = AndMatcher(supp_dict["$HUN_GO_SRC"], station_matcher)
    tgt_matcher = AndMatcher(supp_dict["$HUN_GO_TGT"], station_matcher)
    ea = elvira_avm = AVM('ElviraAVM')
    ea.add_attribute("vonat", PrintnameMatcher("train"), AVM.RREQ, None)
    ea.add_attribute("menetrend", PrintnameMatcher("schedule"), AVM.RREQ, None)
    ea.add_attribute("src", src_matcher, AVM.RREQ, "Budapest")
    ea.add_attribute("tgt", tgt_matcher, AVM.RREQ, None)
    #ea.add_attribute("date", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
    ea.set_satisfaction('vonat and menetrend and tgt')
    elvira_const = AVMConstruction(ea)
    lexicon.add_avm_construction(elvira_const)

    ## Creating plain ticket construction
    pta = plain_ticket_avm = AVM('PlainTicketAvm')
    pta.add_attribute("BKSZ", PrintnameMatcher("bksz"), AVM.ROPT, None)
    pta.add_attribute("CLASS", EnumMatcher("class", lexicon),
                      AVM.RREQ, "2")
    #pta.add_attribute("DATE", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
    pta.add_attribute("DEST", tgt_matcher, AVM.RREQ, None)
    pta.add_attribute("INV", PrintnameMatcher("invoice"), AVM.ROPT, None)
    pta.add_attribute("RED", EnumMatcher("mav_reduction", lexicon),
                      AVM.RREQ, "full_price")
    pta.add_attribute("RET", EnumMatcher("ticket_type", lexicon),
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
    lexicon.add_construction(pt_const)

    ## Creating ic ticket construction
    ita = ic_ticket_avm = AVM('ICTicketAvm')
    ita.add_attribute("CLASS", EnumMatcher("class", lexicon), AVM.RREQ, "2")
    #ita.add_attribute("DATE", PosMatcher("\[DATE\]$"), AVM.ROPT, None)
    ita.add_attribute("DEST", tgt_matcher, AVM.RREQ, None)
    ita.add_attribute("INV", PrintnameMatcher("invoice"), AVM.ROPT, None)
    ita.add_attribute("PLACE", EnumMatcher("seat", lexicon), AVM.ROPT, None)
    ita.add_attribute("SRC", src_matcher, AVM.RREQ, u"Budapest-Nyugati")
    ita.add_attribute("IC", ic_name_matcher, AVM.ROPT, None)
    #ita.add_attribute("TIME", PosMatcher("\[TIME\]"), AVM.RREQ, None)
    ita.set_satisfaction('SRC and CLASS and (IC or (TIME and DEST))')
    it_const = AVMConstruction(ita)
    lexicon.add_avm_construction(it_const)
