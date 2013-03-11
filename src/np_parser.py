import sys

import matcher
from machine import Machine

def parse_rule(rule):
    right = rule.split('->')[1].strip()
    matchers = []
    for kr in right.split():        
            #kr_dict = readkr.kr_to_dictionary('stem/' + kr)
            #pattermatch = matcher.PatternMatcher(kr_dict)
            pattermatch = matcher.PatternMatcher(kr)
            matchers.append(pattermatch)
    return matchers

def parse_chunk(chunk):
    # HACK local import to avoid import circle
    from np_grammar import np_rules
    # Chunk constructions are run here to form the phrase machines.
    change = True
    while change:
        change = False
        try:
            for length in xrange(len(chunk), 0, -1):
                for begin, end in _subsequence_index(chunk, length):
                    part = chunk[begin:end]
                    #print begin, end, part
                    #for m in part:
                        #print m.control.kr
                    for c in np_rules:
                        if c.check(part):
                            print c.name
                            c_res = c.act(part)
                            if c_res is not None:
                                change = True
                                chunk[begin:end] = c_res  # c_res should contain a single machine here (?)
                                raise ValueError  # == break outer
        except ValueError:
            pass
    return chunk

def _subsequence_index(seq, length):
    """
    Returns the start and end indices of all subsequences of @p seq of length
    @p length as an iterator.
    """
    l = len(seq)
    if l < length:
        return
#    for begin in xrange(0, l - length + 1):
    for begin in xrange(l - length, -1, -1):
        yield begin, begin + length
    return

def test_on_something():
    from sentence_parser import SentenceParser
    from langtools.corpustools.bie1_reader import read_bie1_corpus
    import codecs
    sentences = read_bie1_corpus(codecs.open(sys.argv[1], "r", "utf-8"))
    for sen in sentences:
        print sen
        sp = SentenceParser()
        machines = sp.parse(sen)
        for chunk in filter(lambda c: len(c) > 1, machines):
            print chunk
            res = parse_chunk(chunk)
            print res
            for m in res:
                print Machine.to_debug_str(m)
            print 

def main():
    rules = sys.stdin.readlines()
    for rule in rules:
        if rule[0]=='#' or rule == '\n': continue
        krs_list = parse_rule(rule.strip())    
        for kr in krs_list:
            print kr.pattern


if __name__ == '__main__':
    test_on_something()
    #main()

