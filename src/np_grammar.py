from construction import NPConstruction

np_rules = []

#zo2ld pingvin
np_rules.append(NPConstruction("1F",
		"NOUN<BAR<1>> -> ADJ NOUN<BAR<0>>",
		[
		AppendOperator(1, 0)
		])

#pingvin
np_rules.append(NPConstruction("", "NOUN<BAR<1>> -> NOUN<BAR<0>>

#zo2ld
np_rules.append(NPConstruction("", "NOUN<BAR<1>> -> ADJ

#ha1rom
np_rules.append(NPConstruction("", "NOUN<BAR<2>> -> NUM

#ha1rom (zo2ld) pingvin
np_rules.append(NPConstruction("", "NOUN<BAR<2> -> NUM NOUN<BAR<1>>

#(zo2ld) pingvin
np_rules.append(NPConstruction("", "NOUN<BAR<2>> -> NOUN<BAR<1>>

#a (zo2ld) pingvin, egy (zo2ld) pingvin
np_rules.append(NPConstruction("", "NOUN<BAR<3>><DEF<@a>> -> ART<DEF<@a>> NOUN<BAR<2>>

#Eleme1r
np_rules.append(NPConstruction("", "NOUN<BAR<3>><DEF<1>> -> NOUN<BAR<0>><DEF<1>>

#Az
np_rules.append(NPConstruction("", "NOUN<BAR<3>> -> ART

#Eleme1r zo2ld pingvine
np_rules.append(NPConstruction("", "NOUN<BAR<3>><POSS<0>> -> NOUN<BAR<3>><ANP<0>><CAS<NOM>> NOUN<BAR<2>><POSS<1>><DET<1>>
#Eleme1rnek a zo2ld pingvine
np_rules.append(NPConstruction("", "NOUN<BAR<4>><POSS<0>> -> NOUN<BAR<3>><CAS<DAT>> NOUN<BAR<3>><POSS<1>><DET<1>>

#Az e1n pingvinem, az o3 pingvine
np_rules.append(NPConstruction("", "NOUN<BAR<3>><DEF<1>> -> ART [PRON<PER>]/NOUN NOUN<BAR<2>><POSS>
#8F-H are substituted with this rule (because I don't want pronoun features percolating to articles, so there)

#Here ends the original grammar of Kornai 1985

#saja1t pingvinem
np_rules.append(NPConstruction("", "NOUN -> [PRON<POSS>]/NOUN NOUN<BAR<2>>

#ez a pingvin
np_rules.append(NPConstruction("", "NOUN -> [PRON<DEM>]/NOUN<BAR<0>> ART NOUN<BAR<2>><DEF<0>>

#minden pingvin
np_rules.append(NPConstruction("", "NOUN -> [PRON<GEN>]/NOUN NOUN<BAR<2>>

#ne1ha1ny pingvin
np_rules.append(NPConstruction("", "NOUN -> [PRON<INDEF>]/NOUN NOUN<BAR<2>>

#Here ends the grammar of noun phrases

np_rules.append(NPConstruction("", "ADJ -> ADJ ADJ
np_rules.append(NPConstruction("", "ADJ -> ADV ADJ
np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[PERF_PART]/ADJ
np_rules.append(NPConstruction("", "ADJ -> NOUN VERB[IMPERF_PART]/ADJ
np_rules.append(NPConstruction("", "ADJ -> NUM VERB[PERF_PART]/ADJ
np_rules.append(NPConstruction("", "ADJ -> NUM VERB[IMPERF_PART]/ADJ
np_rules.append(NPConstruction("", "NUM -> NUM NUM
np_rules.append(NPConstruction("", "NUM -> ADV NUM
np_rules.append(NPConstruction("", "NUM -> ADJ NUM

