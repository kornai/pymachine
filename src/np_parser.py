import sys
from langtools.utils import readkr
import matcher
from np_grammar import np_rules

def parse_rule(rule):
    right = rule.split('->')[1].strip()
    matchers = []
    for kr in right.split():        
            kr_dict = readkr.kr_to_dictionary('stem/' + kr)
            pattermatch = matcher.PatternMatcher(kr_dict)
            matchers.append(pattermatch)
    return matchers

def parse_chunk(chunk):
    # Chunk constructions are run here to form the phrase machines.
    change = True
    while change:
        change = False
        try:
            for length in xrange(2, len(chunk) + 1):
                for begin, end in _subsequence_index(chunk, length):
                    part = chunk[begin:end]
                    for c in np_rules:
                        if c.check(part):
                            c_res = c.act(part)
                            if c_res is not None:
                                change = True
                                chunk[begin:end] = c_res  # c_res should contain a single machine here (?)
                                raise ValueError  # == break outer
        except ValueError:
            pass

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

def main():
    rules = sys.stdin.readlines()
    for rule in rules:
        if rule[0]=='#' or rule == '\n': continue
        krs_list = parse_rule(rule.strip())    
        for kr in krs_list:
            print kr.pattern


if __name__ == '__main__':
    main()

