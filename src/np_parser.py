import sys
from langtools.utils import readkr
import matcher

def parse_rule(rule):
    right = rule.split('->')[1].strip()
    matchers = []
    for kr in right.split():        
            kr_dict = readkr.kr_to_dictionary('stem/' + kr)
            pattermatch = matcher.PatternMatcher(kr_dict)
            matchers.append(pattermatch)
    return matchers

def main():
    rules = sys.stdin.readlines()
    for rule in rules:
        krs_list = parse_rule(rule.strip())    
        for kr in krs_list:
            print kr.pattern


if __name__ == '__main__':
    main()

