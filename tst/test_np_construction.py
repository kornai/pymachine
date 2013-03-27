from pymachine.src.sentence_parser import SentenceParser
from pymachine.src.construction import NPConstruction
from pymachine.src.operators import AppendOperator

def test_np_const():
    npc = NPConstruction("1F", "asdf-> ADJ<CAS<NOM>> NOUN", [AppendOperator(1, 0)])
    test_np = [([
         ("piros", "piros", "piros/ADJ"),
         ("kockat", "kocka", "kocka/NOUN<CAS<ACC>>")], "ACC")]

    sp = SentenceParser()
    machines = sp.parse(test_np)[0]
    if npc.check(machines):
        print npc.act(machines).to_debug_str()
    else:
        print "In your face!"
