from construction import NPConstruction
from operators import AppendOperator, FeatChangeOperator, FeatCopyOperator, \
                      AddArbitraryStringOperator, CreateBinaryOperator, \
                      DeleteOperator

np_rules = []

#zo2ld pingvin
np_rules.append(NPConstruction("1F",
		"NOUN<BAR<1>> -> ADJ NOUN<BAR<0>>",
		[
		AppendOperator(1, 0),
        FeatChangeOperator("BAR", "1")    
		]))

#PK pingvin
np_rules.append(NPConstruction("1f",
        "NOUN<BAR<1>> -> NOUN<BAR<0>>",
        [
        FeatChangeOperator("BAR", "1")
        ]))

#PK zo2ld
np_rules.append(NPConstruction("1G",
        "NOUN<BAR<1>> -> ADJ",
        [
        FeatChangeOperator("CAT", "NOUN"),
        FeatChangeOperator("BAR", "1")    
        ]))

#PK ha1rom
np_rules.append(NPConstruction("2H",
        "NOUN<BAR<2>> -> NUM",
        [
        FeatChangeOperator("CAT", "NOUN"),
        FeatChangeOperator("BAR", "2"), 
        AddArbitraryStringOperator(0, "PLUR")

        ]))

#PK ha1rom (zo2ld) pingvin
np_rules.append(NPConstruction("2F",
        "NOUN<BAR<2> -> NUM NOUN<BAR<1>>",
        [
        AppendOperator(1, 0),
        FeatChangeOperator("BAR", "2"),
        AddArbitraryStringOperator(0, "PLUR")    
        ]))

#PK (zo2ld) pingvin
np_rules.append(NPConstruction("2f",
        "NOUN<BAR<2>> -> NOUN<BAR<1>>",
        [
        FeatChangeOperator("BAR", "2")    
        ]))

#ND a (zo2ld) pingvin, egy (zo2ld) pingvin
np_rules.append(NPConstruction("3F",
        "NOUN<BAR<3>><DEF<@a>> -> ART<DEF<@a>> NOUN<BAR<2>>",
        [
        FeatCopyOperator(0, 1, "DEF"),
        DeleteOperator(0)
        ]))

#PK Eleme1r
np_rules.append(NPConstruction("3G",
        "NOUN<BAR<3>><DEF<1>> -> NOUN<BAR<0>><DEF<1>>",
        [
        FeatChangeOperator("BAR", "3")
        ]))

#PK Az
np_rules.append(NPConstruction("3H",
        "NOUN<BAR<3>> -> ART",
        [
        FeatChangeOperator("BAR", "3"),
        FeatChangeOperator("CAT", "NOUN")    
        ]))

#RG Eleme1r ha1rom zo2ld pingvine
np_rules.append(NPConstruction("",
        "NOUN<BAR<3>><POSS<0>> -> NOUN<BAR<3>><ANP<0>><CAS<NOM>> NOUN<BAR<2>><POSS<1>><DET<1>>",
        []))
#RG Eleme1rnek a zo2ld pingvine
np_rules.append(NPConstruction("",
        "NOUN<BAR<4>><POSS<0>> -> NOUN<BAR<3>><CAS<DAT>> NOUN<BAR<3>><POSS<1>><DET<1>>",
        []))

#RG Az e1n pingvinem, az o3 pingvine
np_rules.append(NPConstruction("",
        "NOUN<BAR<3>><DEF<1>> -> ART [PRON<PER>]/NOUN NOUN<BAR<2>><POSS>",
        []))
#8F-H are substituted with this rule (because I don't want pronoun features percolating to articles, so there)

#Here ends the original grammar of Kornai 1985

#ZSA saja1t pingvinem
np_rules.append(NPConstruction("",
        "NOUN -> [PRON<POSS>]/NOUN NOUN<BAR<2>>",
        []))

#ZSA ez a pingvin
np_rules.append(NPConstruction("",
        "NOUN -> [PRON<DEM>]/NOUN<BAR<0>> ART NOUN<BAR<2>><DEF<0>>",
        []))

#ZSA minden pingvin
np_rules.append(NPConstruction("",
        "NOUN -> [PRON<GEN>]/NOUN NOUN<BAR<2>>",
        []))

#ZSA ne1ha1ny pingvin
np_rules.append(NPConstruction("",
        "NOUN -> [PRON<INDEF>]/NOUN NOUN<BAR<2>>",
        []))

#Here ends the grammar of noun phrases

#np_rules.append(NPConstruction("", "ADJ -> ADJ ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> ADV ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[PERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[IMPERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NUM VERB[PERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NUM VERB[IMPERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "NUM -> NUM NUM", []))
#np_rules.append(NPConstruction("", "NUM -> ADV NUM", []))
#np_rules.append(NPConstruction("", "NUM -> ADJ NUM", []))

