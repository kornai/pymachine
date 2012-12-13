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

#kis zo2ld pingvin -- optimization of 9A for our implementation
np_rules.append(NPConstruction("1F2",
		"NOUN<BAR<1>> -> ADJ NOUN<BAR<1>>",
		[
		AppendOperator(1, 0)
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
        [
        FeatChangeOperator("BAR", 3),
        FeatChangeOperator("POSS", 0)
        ]))

#RG Eleme1rnek a zo2ld pingvine
np_rules.append(NPConstruction("",
        "NOUN<BAR<4>><POSS<0>> -> NOUN<BAR<3>><CAS<DAT>> NOUN<BAR<3>><POSS<1>><DET<1>>",
        [
        FeatChangeOperator("BAR", 4),
        FeatChangeOperator("POSS", 0)
        ]))

#RG Az e1n pingvinem, az o3 pingvine
np_rules.append(NPConstruction("",
        "NOUN<BAR<3>><DEF<1>> -> ART [PRON<PER>]/NOUN NOUN<BAR<2>><POSS>",
        [
        FeatChangeOperator("BAR", 3),
        FeatChangeOperator("DEF", 1)
        ]))
#8F-H are substituted with this rule (because I don't want pronoun features percolating to articles, so there)

#Here ends the original grammar of Kornai 1985

#ZSA saja1t pingvinem ??
np_rules.append(NPConstruction("",
        "NOUN<BAR<2>> -> [PRON<POSS>]/NOUN NOUN<BAR<2>>",
        []))

#ZSA ez a pingvin
# HACK only delete
np_rules.append(NPConstruction("11C",
        "NOUN<BAR<3>> -> [PRON<DEM>]/NOUN<BAR<0>> ART NOUN<BAR<2>><DEF<0>>",
        [
		DeleteOperator(1),
		DeleteOperator(0),
        FeatChangeOperator("BAR", 3),
        ]))

#ZSA minden pingvin
# HACK only delete
np_rules.append(NPConstruction("11A",
        "NOUN<BAR<3>> -> [PRON<GEN>]/NOUN NOUN<BAR<2>>",
        [
        DeleteOperator(0),
        AddArbitraryStringOperator(0, "PLUR"),
        FeatChangeOperator("BAR", 3)
        ]))

#ZSA ne1ha1ny pingvin
# HACK only delete
np_rules.append(NPConstruction("11B",
        "NOUN<BAR<2>> -> [PRON<INDEF>]/NOUN NOUN<BAR<2>>",
        [
		DeleteOperator(0)
        ]))

#Here ends the grammar of noun phrases

#kis zo2ld -> see 1F2
#np_rules.append(NPConstruction("", "ADJ -> ADJ ADJ", []))

#nagyon kicsi
np_rules.append(NPConstruction("9B",
        "ADJ -> ADV ADJ",
        [
		AppendOperator(1, 0)
        ]))

#elso3 ha1rom pingvin
#np_rules.append(NPConstruction("", "NUM -> NUM NUM", []))

#legala1bb ha1rom pingvin
np_rules.append(NPConstruction("10B",
        "NUM -> ADV NUM",
        [
        AppendOperator(1, 0)
        ]))

#np_rules.append(NPConstruction("", "NUM -> ADJ NUM", []))

#az elmu1lt nyolc e1v: PERF_PART
#a likvida1lando1 ha1rom miniszter: FUT_PART
#a felszo1lalo1 ke1t a1llamtitka1r: IMPERF_PART
#a puccsolhato1 frakcio1vezeto3: MODAL_PART
#a ta1je1kozatlan ke1t a1llamtitka1r: NEG_PERF_PART
np_rules.append(NPConstruction("10C1",
        "NOUN -> DET<DEF<1>> VERB[@a]/ADJ NUM NOUN",
        [
        ]))
#(a) kocsordi ke1t ojjektum
np_rules.append(NPConstruction("10C2",
        "NOUN -> DET<DEF<1>> NOUN[MET_ATTRIB]/ADJ NUM NOUN",
        [
        ]))

#np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[PERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[IMPERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NUM VERB[PERF_PART]/ADJ", []))
#np_rules.append(NPConstruction("", "ADJ -> NUM VERB[IMPERF_PART]/ADJ", []))

