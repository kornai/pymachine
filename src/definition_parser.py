import logging
try:
    from pyparsing import Literal, Word, Group, Combine, Optional, Forward, alphanums, SkipTo, LineEnd, nums, delimitedList 
except ImportError:
    import sys
    logging.critical("PyParsing have to be installed on the computer")
    sys.exit(-1)
import string

from machine import Machine
from monoid import Monoid
from constants import deep_cases

import sys
class ParserException(Exception):
    pass

class DefinitionParser:
    _str = set([str, unicode])

    lb = "["
    rb = "]"
    lp = "("
    rp = ")"

    def_sep = ":"
    arg_sep = ","
    part_sep = ";"
    comment_sep = "%"
    prime = "'"
    hyphen = "-"

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
        self.hyphen_lit = Literal(DefinitionParser.hyphen)
        
        self.deep_cases = reduce(lambda a, b: a | b,
            (Literal(dc) for dc in deep_cases))
        
        self.unary = Combine(Optional("-") + Word(string.lowercase + "_") +
                             Optional(Word(nums))) | self.deep_cases
        self.binary = Word(string.uppercase + "_" + nums)
        self.dontcare = SkipTo(LineEnd())
        
        # main expression
        self.expression = Forward()
        
        # "enumerable expression"
        # D -> E | E, D
        self.definition = Group(delimitedList(self.expression,
            delim=DefinitionParser.arg_sep))
        self.expression << Group(
            # E -> U
            (self.unary) ^

            # E -> U [ D ]
            (self.unary + self.lb_lit.suppress() + self.definition + self.rb_lit.suppress() ) ^ 

            # E -> U ( U ) | U ( U [ E ] )
            (self.unary + self.lp_lit + self.unary + Optional(self.lb_lit.suppress() + self.expression + self.rb_lit.suppress()) + self.rp_lit ) ^

            # E -> U B
            (self.unary + self.binary) ^
            
            # E -> U B E
            (self.unary + self.binary + self.expression) ^

            # E -> B E
            (self.binary + self.expression) ^

            # E -> B [ E ]
            (self.binary + self.lb_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
            
            # E -> B [ E ; E ] 
            (self.binary + self.lb_lit.suppress() + self.expression + self.part_sep_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
            
            # E -> [ E ] B
            (self.lb_lit.suppress() + self.expression + self.rb_lit.suppress() + self.binary) ^
            
            # E -> [ E ] B [ E ]
            (self.lb_lit.suppress() + self.expression + self.rb_lit.suppress() + self.binary + self.lb_lit.suppress() + self.expression + self.rb_lit.suppress()) ^
            
            # E -> [ E ] B E
            (self.lb_lit.suppress() + self.expression + self.rb_lit.suppress() + self.binary + self.expression ) ^
            
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
        return type(s) in cls._str and s.isupper() and not s in deep_cases
    
    @classmethod
    def _is_unary(cls, s):
        # TODO unaries can contain hyphens
        return type(s) in cls._str and s.islower() or s in deep_cases
    
    @classmethod
    def _is_deep_case(cls, s):
        return s in deep_cases
    
    @classmethod
    def __parse_expr(cls, expr):
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
                m.append(1, cls.__parse_expr(_property))
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
            m.append(2, cls.__parse_expr(expr[2]))
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
            m.append(1, cls.__parse_expr(expr[1]))
            m.append(2, cls.__parse_expr(expr[2]))
            return m

        # E -> [ E ] B [ E ]
        # [['unary'], 'BINARY', ['unary']]
        if (len(expr) == 3 and
              is_tree(expr[0]) and
              is_binary(expr[1]) and
              is_tree(expr[2])):
            m = Machine(Monoid(expr[1]))
            m.append(1, cls.__parse_expr(expr[0]))
            m.append(2, cls.__parse_expr(expr[2]))
            return m

        # E -> B [ E ]
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = Machine(Monoid(expr[0]))
            m.append(2, cls.__parse_expr(expr[1]))
            return m

        # E -> [ E ] B
        # [['unary'], 'BINARY']
        if (len(expr) == 2 and
            is_tree(expr[0]) and
            is_binary(expr[1])):
            m = Machine(Monoid(expr[1]))
            m.append(1, cls.__parse_expr(expr[0]))
            m.base.partitions.append([])
            return m

        # E -> B E
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = Machine(Monoid(expr[0]))
            m.append(2, cls.__parse_expr(expr[1]))
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
            machine.append(1, DefinitionParser.__parse_expr(d))
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

