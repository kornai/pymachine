import logging
import sys
import string

try:
    import pyparsing
    from pyparsing import Literal, Word, Group, Combine, Optional, Forward, alphanums, SkipTo, LineEnd, nums, delimitedList 
except ImportError:
    logging.critical("PyParsing have to be installed on the computer")
    sys.exit(-1)

from machine import Machine
from monoid import Monoid
from constants import deep_cases
from lexicon import Lexicon

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
        self.lexicon = Lexicon()

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
    
    def init_parser(self):
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
        self.defid = Word(nums)
        self.word = Group(self.hu + self.pos + self.en + self.lt + self.pt)

        # S -> W : D | W : D % _
        self.sen = (self.defid + self.word + self.def_sep_lit.suppress() + Optional(self.definition) + Optional(self.comment_sep_lit + self.dontcare).suppress()) + LineEnd()
    
    def parse(self, s):
        return self.sen.parseString(s).asList()

    def get_machine(self, printname):
        if printname not in self.lexicon.static:
            part_num = 0
            if DefinitionParser._is_unary(printname):
                part_num = 1
            elif DefinitionParser._is_binary(printname):
                part_num = 2
            if part_num == 0:
                raise ValueError("get_machine() is called with an invalid printname argument")
            self.lexicon.add_static(Machine(Monoid(printname, part_num)))
        return self.lexicon.static[printname]
    
    def __parse_expr(self, expr, parent):
        """
        creates machines from a parse node and its children
        there should be one handler for every rule
        """
        # name shortening for classmethods
        cls = DefinitionParser

        is_binary = cls._is_binary
        is_unary = cls._is_unary
        is_tree = lambda r: type(r) == list

        # E -> U [ D ]
        # ['unary', [['unary'], ['unary']]]
        if (len(expr) == 2 and
              is_unary(expr[0]) and
              is_tree(expr[1])):
            m = self.get_machine(expr[0])
            for _property in expr[1]:
                m.append(1, self.__parse_expr(_property, m))
            return m

        # E -> U ( U ) | U ( U [ E ] )
        # ['unary', '(', 'unary', ')']
        if (len(expr) == 4 and
              is_unary(expr[0]) and
              expr[1] == cls.lp and
              is_unary(expr[2]) and
              expr[3] == cls.rp):
            m = self.get_machine(expr[2])
            m.append(1, self.get_machine(expr[0]))
            return m

        # E -> U B E
        # ['unary', 'BINARY', ['unary']]
        if (len(expr) == 3 and
              is_unary(expr[0]) and
              is_binary(expr[1]) and
              is_tree(expr[2])):
            m = self.get_machine(expr[1])
            m.append(1, self.get_machine(expr[0]))
            m.append(2, self.__parse_expr(expr[2], m))
            return m

        # E -> U B
        # ['unary', 'BINARY']
        if (len(expr) == 2 and
              is_unary(expr[0]) and
              is_binary(expr[1])):
            m = self.get_machine(expr[1])
            m.append(1, self.get_machine(expr[0]))
            return m

        # E -> U
        # ['unary']
        if (len(expr) == 1 and
              is_unary(expr[0])):
            return self.get_machine(expr[0])

        # E -> B [ E ; E ] 
        # ['BINARY', ['unary'], ['unary']]
        if (len(expr) == 3 and
              is_binary(expr[0]) and
              is_tree(expr[1]) and
              is_tree(expr[2])):
            m = self.get_machine(expr[0])
            m.append(1, self.__parse_expr(expr[1], m))
            m.append(2, self.__parse_expr(expr[2], m))
            return m

        # E -> [ E ] B [ E ]
        # [['unary'], 'BINARY', ['unary']]
        if (len(expr) == 3 and
              is_tree(expr[0]) and
              is_binary(expr[1]) and
              is_tree(expr[2])):
            m = self.get_machine(expr[1])
            m.append(1, self.__parse_expr(expr[0], m))
            m.append(2, self.__parse_expr(expr[2], m))
            return m

        # E -> B [ E ]
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = self.get_machine(expr[0])
            m.append(2, self.__parse_expr(expr[1], m))
            return m

        # E -> [ E ] B
        # [['unary'], 'BINARY']
        if (len(expr) == 2 and
            is_tree(expr[0]) and
            is_binary(expr[1])):
            m = self.get_machine(expr[1])
            m.append(1, self.__parse_expr(expr[0], m))
            return m

        # E -> B E
        # ['BINARY', ['unary']]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            is_tree(expr[1])):
            m = self.get_machine(expr[0])
            m.append(2, self.__parse_expr(expr[1], m))
            return m

        # E -> 'B
        # ["'", 'BINARY']
        if (len(expr) == 2 and
            expr[0] == cls.prime and
            is_binary(expr[1])):
            m = self.get_machine(expr[1])
            m.append(parent, 2)
            return None

        # E -> B'
        # ['BINARY', "'"]
        if (len(expr) == 2 and
            is_binary(expr[0]) and
            expr[1] == cls.prime):
            m = self.get_machine(expr[0])
            m.append(parent, 1)
            return None
        
        pe = ParserException("Unknown expression in definition")
        logging.debug(str(pe))
        logging.debug(expr)
        raise pe
    
    def parse_into_machines(self, s):
        parsed = self.parse(s)
        
        # HACK printname is now set to english
        machine = self.get_machine(parsed[1][3])
        if len(parsed) > 2:
            for d in parsed[2]:
                machine.append(self.__parse_expr(d, machine), 1)

def read(f):
    dp = DefinitionParser()
    for line in f:
        l = line.strip()
        logging.info("Parsing: {0}".format(l))
        if len(l) == 0:
            continue
        if l.startswith("#"):
            continue
        try:
            dp.parse_into_machines(l)
            print l
            print "Parsing ok"
        except pyparsing.ParseException, pe:
            print l
            print "Error: ", str(pe)

    return dp.lexicon

if __name__ == "__main__":
    dp = DefinitionParser()
    pstr = sys.argv[-1]
    if sys.argv[1] == "-g":
        dp.parse_into_machines(pstr)
    elif sys.argv[1] == "-f":
        lexicon = read(file(sys.argv[2]))
    else:
        print dp.parse(pstr)

