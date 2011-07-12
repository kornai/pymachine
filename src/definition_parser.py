from pyparsing import Literal, Word, Group, Optional, Forward, alphanums, SkipTo, LineEnd, OneOrMore, nums
import string

from machine import Machine
from monoid import Monoid

import sys
class ParserException(Exception):
    pass

class DefinitionParser:
    _str = set([str, unicode])
    _deep_cases = ["NOM" , "ACC" , "DAT" , "INS" , "ABL", "SUB" ]
    def __init__(self):
        
        self.init_parser()
    
    def init_parser(self):
        self.id = Word(nums)
        self.lb = Literal("[")
        self.rb = Literal("]")
        self.lp = Literal("(")
        self.rp = Literal(")")

        self.def_sep = Literal(":")
        self.arg_sep = Literal(",")
        self.part_sep = Literal(";")
        self.comment_sep = Literal("%")
        self.prime = Literal("'")
        
        #self.deep_cases = (Literal("NOM") | Literal("ACC") | Literal("DAT") | Literal("INS") | Literal("ABL"))
        self.deep_cases = reduce(lambda a, b: a | b, (Literal(dc) for dc in DefinitionParser._deep_cases))
        
        self.unary = Word(string.lowercase + "_" + nums) | self.deep_cases
        self.binary = Word(string.uppercase + "_" + nums)
        self.dontcare = SkipTo(LineEnd())
        
        # main expression
        self.expression = Forward()
        
        # "enumerable expression
        self.definition = (self.expression + Optional(OneOrMore(self.arg_sep.suppress() + self.expression)))
        
        self.expression << Group(
                            # E -> U [ D ]
                            (self.unary + self.lb.suppress() + Group(self.definition) + self.rb.suppress() ) ^ 

                            # E -> U ( U )
                            (self.unary + self.lp + self.unary + self.rp ) ^

                            # E -> U B E
                            (self.unary + self.binary + self.expression) ^

                            # E -> U B
                            (self.unary + self.binary) ^
                            
                            # E -> U
                            (self.unary) ^

                            # E -> B [ E ; E ] 
                            (self.binary + self.lb.suppress() + Group(self.expression) + self.part_sep.suppress() + Group(self.expression) + self.rb.suppress()) ^
                            
                            # E -> [ E ] B [ E ]
                            (self.lb.suppress() + Group(self.expression) + self.rb.suppress() + self.binary + self.lb.suppress() + Group(self.expression) + self.rb.suppress()) ^
                            
                            # E -> B [ E ]
                            (self.binary + self.lb.suppress() + Group(self.expression) + self.rb.suppress()) ^
                            
                            # E -> [ E ] B
                            (self.lb.suppress() + Group(self.expression) + self.rb.suppress() + self.binary) ^
                            
                            # E -> B E
                            (self.binary + self.expression) ^

                            # E -> 'B
                            (self.prime + self.binary) ^

                            # E -> B'
                            (self.binary + self.prime)
                           )
        
        self.hu, self.pos, self.en, self.lt, self.pt = (Word(alphanums + "#-/_" ),) * 5
        self.word = Group(self.hu + self.pos + self.en + self.lt + self.pt)
        self.sen = (self.id + self.word + self.def_sep.suppress() + self.definition + Optional(self.comment_sep + self.dontcare).suppress()) + LineEnd()
    
    def parse(self, s):
        return self.sen.parseString(s).asList()
        
    
    @classmethod
    def __flatten__(cls, _l):
        _str = cls._str
        result = None
        if type(_l) == list:
            if len(_l) == 1 and type(_l[0]) == list and len(_l[0]) == 1 and type(_l[0][0]) in _str:
                result = DefinitionParser.__flatten__(_l[0])
            else:
                result = [DefinitionParser.__flatten__(e) for e in _l]
        else:
            result = _l
        return result
    
    @classmethod
    def _is_binary(cls, s):
        return s.isupper() and not s in cls._deep_cases
    
    @classmethod
    def _is_unary(cls, s):
        return s.islower() or s in cls._deep_cases
    
    @classmethod
    def _is_deep_case(cls, s):
        return s in cls._deep_cases
    
    @classmethod
    def _parse_expr(cls, l):
        is_binary = cls._is_binary
        is_unary = cls._is_unary
        _str = cls._str
        if len(l) == 1:
            # unary
            # later here should be a lookup to find out if we already know this machine
            if type(l[0]) == list:
                return cls._parse_expr(l[0])
            else:
                if is_unary(l[0]):
                    return Machine(Monoid(l[0]))
                else:
                    raise ParserException("Only lower case strings or deep cases can be at unary position(" + str(l[0]) + ")")
        
        elif len(l) == 2:
            
            if type(l[0]) in _str:
                if is_unary(l[0]):
                    # unary with one partition
                    m = Machine(Monoid(l[0]))
                    m.base.partitions.append([])
                    m.base.partitions[1].append(cls._parse_expr(l[1]))
                    return m
                elif is_binary(l[0]):
                    # binary with right partition filled - prefix 
                    m = Machine(Monoid(l[0]))
                    m.base.partitions.append([])
                    m.base.partitions.append([])
                    if type(l[1]) == list and len(l[1]) > 1:
                        raise ParserException("Binary primitives have to have one property per argument")
                    m.base.partitions[2].append(cls._parse_expr(l[1]))
                    
                    return m
            elif type(l[1]) in _str:
                if is_binary(l[1]):
                    # binary with left partition filled - infix
                    m = Machine(Monoid(l[1]))
                    m.base.partitions.append([])
                    if type(l[0]) == list and len(l[0]) > 1:
                        raise ParserException("Binary primitives have to have one property per argument")
                    m.base.partitions[1].append(cls._parse_expr(l[0]))
                    m.base.partitions.append([])
                    return m

        elif len(l) == 3:
            # binary with two partitions
            later = None
            m = None
            if type(l[0]) in _str:
                if is_binary(l[0]):
                    m = Machine(Monoid(l[0]))
                    later = l[1], l[2]
                else:
                    raise ParserException("not uppercase string at binary position")
            elif type(l[1]) in _str:
                if is_binary(l[1]):
                    m = Machine(Monoid(l[1]))
                    later = l[0], l[2]
                else:
                    raise ParserException("not uppercase string at binary position")
            else:
                raise ParserException("not uppercase string at any possible binary position")
            
            m.base.partitions.append([cls._parse_expr(later[0])])
            m.base.partitions.append([cls._parse_expr(later[1])])
            return m
        
        elif len(l) == 4:
            # U ( U ) rule
            if is_unary(l[0]) and l[1] == "(" and is_unary(l[2]) and l[3] == ")":
                m = Machine(Monoid(l[2]))
                m.base.partitions.append([])
                m.base.partitions[1].append(Machine(Monoid(l[0])))
                return m
            else:
                raise ParserException("there shouldn't be 4 nodes in a tree only if 2 of them are parentheses")
    
    def parse_into_machines(self, s, dict_into=None):
        parsed = self.parse(s)
        parsed = DefinitionParser.__flatten__(parsed)
        
        machine = Machine(Monoid(parsed[1][2]))
        machine.base.partitions.append([])
        for d in parsed[2:]:
            machine.base.partitions[1].append(DefinitionParser._parse_expr(d))
        if dict_into is None:
            return machine
        else:
            dict_into[tuple(parsed[1])] = machine

def read(f):
    d = {}
    dp = DefinitionParser()
    for line in f:
        l = line.strip()
        if len(l) == 0:
            continue
        dp.parse_into_machines(line.strip(), d)
    return d

if __name__ == "__main__":
    dp = DefinitionParser()
    pstr = sys.argv[-1]
    if sys.argv[1] == "-g":
      m = dp.parse_into_machines(pstr)
      print m.to_dot(True)
    else:
      print dp.parse(pstr)
    #print dp.parse("1 a1bra1zat N expression facies mina: HAS mouth[open], ISA dog,   [a]HAS[b]")
    #m = dp.parse_into_machines("1 a1bra1zat N expression facies mina: HAS[mouth[open]], ISA dog,   [a]HAS[b]")
    #m = dp.parse_into_machines("1 a1bra1zat N expression facies mina: HAS[mouth[ACC]], ISA dog,   [a]HAS[b]")
    #print m.to_dot(True)
