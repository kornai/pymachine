from pyparsing import Literal, Word, Group, Optional, Forward, alphanums, SkipTo, LineEnd, nums, delimitedList
import string
import logging

from machine import Machine
from monoid import Monoid

import sys
class ParserException(Exception):
    pass

class DefinitionParser:
    _str = set([str, unicode])
    _deep_cases = ["NOM" , "ACC" , "DAT" , "INS" , "OBL"
                   , "SUB", "SUE", "DEL"         # ON
                   , "ILL", "INE", "ELA"         # IN
                   , "ALL", "ADE", "ABL"         # AT
                   ]

    lb = "["
    rb = "]"
    lp = "("
    rp = ")"

    def_sep = ":"
    arg_sep = ","
    part_sep = ";"
    comment_sep = "%"
    prime = "'"

    def __init__(self):
        self.init_parser()
    
    def init_parser(self):
        self.id = Word(nums)
        self.lb_lit = Literal(DefinitionParser.lb)
        self.rb_lit = Literal(DefinitionParser.rb)
        self.lp_lit = Literal(DefinitionParser.lp)
        self.rp_lit = Literal(DefinitionParser.rp)

        self.def_sep_lit = Literal(DefinitionParser.def_sep)
        self.arg_sep_lit = Literal(DefinitionParser.arg_sep)
        self.part_sep_lit = Literal(DefinitionParser.part_sep)
        self.comment_sep_lit = Literal(DefinitionParser.comment_sep)
        self.prime_lit = Literal(DefinitionParser.prime)
        
        #self.deep_cases = (Literal("NOM") | Literal("ACC") | Literal("DAT") | Literal("INS") | Literal("ABL"))
        self.deep_cases = reduce(lambda a, b: a | b, (Literal(dc) for dc in DefinitionParser._deep_cases))
        
        self.unary = Word(string.lowercase + "_" + nums) | self.deep_cases
        self.binary = Word(string.uppercase + "_" + nums)
        self.dontcare = SkipTo(LineEnd())
        
        # main expression
        self.expression = Forward()
        
        # "enumerable expression"
        # D -> E | E, D
        self.definition = Group(delimitedList(self.expression, delim=DefinitionParser.arg_sep))
        self.expression << Group(
                            # E -> U [ D ]
                            (self.unary + self.lb_lit.suppress() + self.definition + self.rb_lit.suppress() ) ^ 

                            # E -> U ( U ) | U ( U [ E ] )
                            (self.unary + self.lp_lit + self.unary + Optional(self.lb_lit + self.expression + self.rb_lit) + self.rp_lit ) ^

                            # E -> U B E
                            (self.unary + self.binary + self.expression) ^

                            # E -> U B
                            (self.unary + self.binary) ^
                            
                            # E -> U
                            (self.unary) ^

                            # E -> B [ E ; E ] 
                            (self.binary + self.lb_lit.suppress() + self.expression + self.part_sep_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
                            
                            # E -> [ E ] B [ E ]
                            (self.lb_lit.suppress() + self.expression + self.rb_lit.suppress() + self.binary + self.lb_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
                            
                            # E -> B [ E ]
                            (self.binary + self.lb_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
                            
                            # E -> [ E ] B
                            (self.lb_lit.suppress() + self.expression + self.rb_lit.suppress() + self.binary) ^
                            
                            # E -> B E
                            (self.binary + self.expression) ^

                            # E -> 'B
                            (self.prime_lit + self.binary) ^

                            # E -> B'
                            (self.binary + self.prime_lit)
                           )
        
        self.hu, self.pos, self.en, self.lt, self.pt = (Word(alphanums + "#-/_" ),) * 5
        self.word = Group(self.hu + self.pos + self.en + self.lt + self.pt)

        # S -> W : D | W : D % _
        self.sen = (self.id + self.word + self.def_sep_lit.suppress() + self.definition + Optional(self.comment_sep_lit + self.dontcare).suppress()) + LineEnd()
    
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
        return type(s) in cls._str and s.isupper() and not s in cls._deep_cases
    
    @classmethod
    def _is_unary(cls, s):
        return type(s) in cls._str and s.islower() or s in cls._deep_cases
    
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
                    raise ParserException("Only lower case strings or deep cases or filled binaries can be at unary position(" + str(l[0]) + ")")
        
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
                pe = ParserException("there shouldn't be 4 nodes in a tree only if 2 of them are parentheses")
                logging.debug(str(pe))
                logging.debug(str(l))
                raise pe

    @classmethod
    def __parse_expr_v2(cls, expr):
        """
        creates machines from a parse node and its children
        there should be one handler for every rule
        """
        is_binary = cls._is_binary
        is_unary = cls._is_unary
        is_tree = lambda r: type(r) == list

        # E -> U [ D ]
        # ['unary', [['unary'], ['unary']]]
        if (len(expr) == 2 and
              is_unary(expr[0]) and
              is_tree(expr[1])):
            m = Machine(Monoid(expr[0]))
            for _property in expr[1]:
                m.append(1, cls.__parse_expr_v2(_property))
            return m

        # E -> U ( U ) | U ( U [ E ] )
        # ['unary', '(', 'unary', ')']
        if (len(expr) == 4 and
              is_unary(expr[0]) and
              expr[1] == cls.lp and
              is_unary(expr[2]) and
              expr[3] == cls.rp):
            m = Machine(Monoid(expr[2]))
            m.append(1, Machine(Monoid(expr[0])))
            return m
        # ???

        # E -> U B E
        # ['unary', 'BINARY', ['unary']]
        if (len(expr) == 3 and
              is_unary(expr[0]) and
              is_binary(expr[1]) and
              is_tree(expr[2])):
            m = Machine(Monoid(expr[1]))
            m.append(1, Machine(Monoid(expr[0])))
            m.append(2, cls.__parse_expr_v2(expr[2]))
            return m

        # E -> U B
        # ['unary', 'BINARY']
        if (len(expr) == 2 and
              is_unary(expr[0]) and
              is_binary(expr[1])):
            m = Machine(Monoid(expr[1]))
            m.append(1, Machine(Monoid(expr[0])))
            m.base.partitions.append([])
            return m

        # E -> U
        # ['unary']
        if (len(expr) == 1 and
              is_unary(expr[0])):
            return Machine(Monoid(expr[0]))

        # E -> B [ E ; E ] 
        # ['BINARY', ['unary'], ['unary']]
        if (len(expr) == 3 and
              is_binary(expr[0]) and
              is_tree(expr[1]) and
              is_tree(expr[2])):
            m = Machine(Monoid(expr[0]))
            m.append(1, cls.__parse_expr_v2(expr[1]))
            m.append(2, cls.__parse_expr_v2(expr[2]))
            return m

        # E -> [ E ] B [ E ]
        # [['unary'], 'BINARY', ['unary']]
        if (len(expr) == 3 and
              is_tree(expr[0]) and
              is_binary(expr[1]) and
              is_tree(expr[2])):
            m = Machine(Monoid(expr[1]))
            m.append(1, cls.__parse_expr_v2(expr[0]))
            m.append(2, cls.__parse_expr_v2(expr[2]))
            return m
            

        # E -> B [ E ]
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = Machine(Monoid(expr[0]))
            m.append(2, cls.__parse_expr_v2(expr[1]))
            return m

        # E -> [ E ] B
        # [['unary'], 'BINARY']
        if (len(expr) == 2 and
            is_tree(expr[0]) and
            is_binary(expr[1])):
            m = Machine(Monoid(expr[1]))
            m.append(1, cls.__parse_expr_v2(expr[0]))
            m.base.partitions.append([])
            return m

        # E -> B E
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = Machine(Monoid(expr[0]))
            m.append(2, cls.__parse_expr_v2(expr[1]))
            return m

        # E -> 'B
        # ["'", 'BINARY']
        if (len(expr) == 2 and
            expr[0] == cls.prime and
            is_binary(expr[1])):
            raise NotImplementedError()

        # E -> B'
        # ['BINARY', "'"]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            expr[1] == cls.prime):
            raise NotImplementedError()

        
        pe = ParserException("Unknown expression in definition")
        logging.debug(str(pe))
        logging.debug(expr)
        raise pe
    
    def parse_into_machines(self, s):
        parsed = self.parse(s)
        #parsed = DefinitionParser.__flatten__(parsed)
        
        machine = Machine(Monoid(parsed[1][2]))
        machine.base.partitions.append([])
        for d in parsed[2]:
            machine.append(1, DefinitionParser.__parse_expr_v2(d))
        return (machine, tuple(parsed[1]))

def read(f):
    from langtools.utils import accents
    d = {}
    dp = DefinitionParser()
    for line in f:
        l = line.strip()
        if len(l) == 0:
            continue
        if l.startswith("#"):
            continue
        m, t = dp.parse_into_machines(line.strip())
        tl = list(t)
        tl[0] = accents.proszeky_to_utf(tl[0].encode("utf-8"))
        d[tuple(tl)] = m
    return d

if __name__ == "__main__":
    dp = DefinitionParser()
    pstr = sys.argv[-1]
    if sys.argv[1] == "-g":
      m, _ = dp.parse_into_machines(pstr)
      print m.to_dot(True)
    else:
      print dp.parse(pstr)
    #print dp.parse("1 a1bra1zat N expression facies mina: HAS mouth[open], ISA dog,   [a]HAS[b]")
    #m = dp.parse_into_machines("1 a1bra1zat N expression facies mina: HAS[mouth[open]], ISA dog,   [a]HAS[b]")
    #m = dp.parse_into_machines("1 a1bra1zat N expression facies mina: HAS[mouth[ACC]], ISA dog,   [a]HAS[b]")
    #print m.to_dot(True)
