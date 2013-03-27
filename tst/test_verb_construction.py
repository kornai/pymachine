import itertools

from pymachine.src.sentence_parser import SentenceParser
from pymachine.src.construction import VerbConstruction

def test_verb_const(lexicon, supp_dict):
    # maybe this is obsolete?
    sentence = [((u'Mikor', u'mikor/ADV'), "O"), ((u'Megy', u'megy/VERB'), "O"), ([(u'Vonat', u'vonat/NOUN')], u'N_1'), ([(u'Budapestr\u0151l', u'budapest/NOUN<CAS<DEL>>')], u'N_1'), ([(u'Szegedre', u'szeged/NOUN<CAS<SBL>>')], u'N_1'), ((u'?', u'?/PUNCT'), "O")]
    sp = SentenceParser()
    machines = sp.parse(sentence)
    lexicon.add_active(itertools.chain(*machines))
    vc = VerbConstruction("megy", lexicon, supp_dict)
    vc.check(machines)
    for machine in itertools.chain(*machines):
        print machine.control.to_debug_str()
