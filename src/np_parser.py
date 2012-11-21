import sys
from langtools.utils import readkr
import matcher



def fill_def_values(dict_attributes):

    if dict_attributes['CAT'] == 'NOUN':
        if 'CAS' not in dict_attributes:
            dict_attributes['CAS'] = 'NOM'
        if 'NUM' not in dict_attributes:
            dict_attributes['NUM'] = 'SING'
        if 'ANP' not in dict_attributes:
            dict_attributes['ANP'] = '0'
        if 'DEF' not in dict_attributes:
            dict_attributes['DEF'] = '0'
        if 'POSS' not in dict_attributes:
            dict_attributes['POSS'] = '0'
    if dict_attributes['CAT'] == 'ADJ':
        if 'CAS' not in dict_attributes:
            dict_attributes['CAS'] = 'NOM'        
    if 'SRC' in dict_attributes:
        dict_attributes['SRC']['STEM'] = fill_def_values(dict_attributes['SRC']['STEM'])
    return dict_attributes


def find_next_kr(string):
    
    first = len(string)
    last = first 
    for index, char in enumerate(string):
        if char !=' ':
           first = index
           break
    last_char = '@'
    current = first
    for index, char in enumerate(string[first:]):
        if char.isupper() and (last_char == ')' or last_char == '>'):
            last = current
            break      
        elif char != ' ':
            last_char = char
            current = index
    return string[first:first + last + 1], string[first + last + 1:] 

   
def parse_rule(rule):
    right = rule.split('->')[1]
    matchers = []
    while len(right) > 0:
        kr, right = find_next_kr(right)
        if kr != '':
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

