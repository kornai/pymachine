from collections import defaultdict
from matcher import PosControlMatcher as PosMatcher

def supplementary_dictionary_reader(f):
    d = defaultdict(list)
    for l in f:
        l = l.split("#")[0].strip()
        le = l.split()
        d["@" + le[0]].append(le[1])

    d = dict([(k, PosMatcher("|".join(v))) for k, v in d.iteritems()])
    return d
