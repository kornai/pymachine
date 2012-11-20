import sys
from langtools.utils import readkr
import matcher


def subset(small, large):
    is_subset = True
    for key in small:
        if is_subset == False:
            break 
        if key not in large:
            is_subset = False
            break
        else:
            if type(small[key]).__name__ == 'dict':
                is_subset = subset(small[key], large[key])
            else:  
                  if small[key] != large[key]:
                       if len(small[key]) == 0 or small[key][0] != '@':
                          is_subset = False
    return is_subset    
    

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


def node_dictionary(nodes, kepzos, i):
    node = nodes[i]
    dictionary = {}
    dictionary['CAT'] = node.value 
    for ch_node in node.children:
        attr = ch_node.value
        if ch_node.children == []:
            value = 1     
        else:
            value = ch_node.children[0].value
        if attr == 'PLUR':
            attr, value = 'NUM', 'PLUR'
        dictionary[attr] = value
    if i > 0:
        dictionary['SRC'] = {}
        dictionary['SRC']['DERIV'] = {}
        kepzo = kepzos[i-1][0]
        dictionary['SRC']['DERIV']['CAT'] = kepzo.value
        if kepzo.children != []:
            dictionary['SRC']['DERIV']['TYPE'] = kepzo.children[0].value
        dictionary['SRC']['STEM'] = node_dictionary(nodes, kepzos, i - 1)
    return dictionary         


 
def kr_to_dictionary(kr_code):
    code = readkr.analyze(kr_code)[0]
    i = len(code.krNodes)
    return node_dictionary(code.krNodes, code.kepzos, i-1)



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
            kr_dict = kr_to_dictionary('stem/' + kr)
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

