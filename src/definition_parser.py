import logging
import sys
import string
import re

try:
    import pyparsing
    from pyparsing import Literal, Word, Group, Combine, Optional, Forward, alphanums, SkipTo, LineEnd, nums, delimitedList 
except ImportError:
    logging.critical("PyParsing has to be installed on the computer")
    sys.exit(-1)

from langtools.utils.accents import proszeky_to_utf

from machine import Machine
from monoid import Monoid
from constants import deep_cases
from control import ConceptControl

def create_machine(name, partitions):
    return Machine(Monoid(proszeky_to_utf(name), partitions),
                   ConceptControl())

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
    at = "@"
    dollar = "#"
    hashmark = "*"
    unary_p = re.compile("^[a-z_#\-/0-9]+$")
    binary_p = re.compile("^[A-Z_]+$")

    def __init__(self):
        self.init_parser()

    @classmethod
    def _is_binary(cls, s):
        return (type(s) in cls._str and
               (cls.binary_p.match(s) is not None
                and not s in deep_cases))
    
    @classmethod
    def _is_unary(cls, s):
        return (type(s) in cls._str and
               (cls.unary_p.match(s) is not None
                or s in deep_cases))
    
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
        self.at_lit = Literal(DefinitionParser.at)
        self.hashmark_lit = Literal(DefinitionParser.hashmark)
        self.dollar_lit = Literal(DefinitionParser.dollar)
        
        self.deep_cases = reduce(lambda a, b: a | b,
            (Literal(dc) for dc in deep_cases))
        
        self.unary = Combine(Optional("-") + Word(string.lowercase + "_" + nums) +
                             Optional(Word(nums))) | self.deep_cases
        self.binary = Word(string.uppercase + "_" + nums)
        self.syntax_supp = self.dollar_lit + Word(string.uppercase + "_")
        self.syntax_avm = self.dollar_lit + Word(string.ascii_letters + "_")
        self.dontcare = SkipTo(LineEnd())
        
        # main expression
        self.expression = Forward()
        self.binexpr = Forward()
        self.unexpr = Forward()
        self.argexpr = Forward()
        
        # "enumerable expression"
        # D -> E | E, D
        self.definition = Group(delimitedList(self.expression,
            delim=DefinitionParser.arg_sep))

        self.expression << Group(
            # E -> UE
            (self.unexpr) ^

            # E -> BE
            (self.binexpr) ^

            # E -> U ( BE )
            (self.unary + self.lp_lit + self.binexpr + self.rp_lit)
        )

        self.binexpr << Group(
            # BE -> A B
            (self.argexpr + self.binary) ^

            # BE -> B A
            (self.binary + self.argexpr) ^

            # BE -> A B A
            (self.argexpr + self.binary + self.argexpr) ^

            # BE -> B [ E; E ]
            (self.binary + self.lb_lit + self.expression + self.part_sep_lit + self.expression + self.rb_lit) ^

            # BE -> 'B
            (self.prime_lit + self.binary) ^

            # BE -> B'
            (self.binary + self.prime_lit)
        )

        self.unexpr << Group(
            # UE -> U
            (self.unary) ^

            # UE -> SS
            (self.syntax_supp) ^

            # UE -> AVM
            (self.syntax_avm) ^

            # UE -> U [ D ]
            (self.unary + self.lb_lit + self.definition + self.rb_lit) ^

            # UE -> U ( U )
            (self.unary + self.lp_lit + self.unary + self.rp_lit)
        )

        self.argexpr << Group(
            # A -> UE
            (self.unexpr) ^

            # A -> [ D ]
            (self.lb_lit + self.definition + self.rb_lit)
        )
        
        self.hu, self.pos, self.en, self.lt, self.pt = (Word(alphanums + "#-/_" ),) * 5
        self.defid = Word(nums)
        self.word = Group(self.hu + self.pos + self.en + self.lt + self.pt)

        # S -> W : D | W : D % _
        self.sen = (self.defid + self.word + self.def_sep_lit.suppress() + Optional(self.definition) + Optional(self.comment_sep_lit + self.dontcare).suppress()) + LineEnd()
    
    def parse(self, s):
        return self.sen.parseString(s).asList()

    def __parse_expr(self, expr, parent, root):
        """
        creates machines from a parse node and its children
        there should be one handler for every rule
        """

        logging.debug("Parsing expression: {0}".format(expr))

        # name shortening for classmethods
        cls = DefinitionParser

        is_binary = cls._is_binary
        is_unary = cls._is_unary
        is_tree = lambda r: type(r) == list

        if (len(expr) == 1):
            # E -> UE | BE
            # A -> UE
            if (is_tree(expr[0])):
                return self.__parse_expr(expr[0], parent, root)

            # UE -> U
            if (is_unary(expr[0])):
                return create_machine(expr[0], 1)

        if (len(expr) == 2):
            # BE -> A B
            if (is_tree(expr[0]) and
                    is_binary(expr[1])):
                m = create_machine(expr[1], 2)
                m.append(self.__parse_expr(expr[0], m, root), 1)
                m.append(root, 2)
                return m

            # BE -> B A
            if (is_binary(expr[0]) and
                    is_tree(expr[1])):
                m = create_machine(expr[0], 2)
                m.append(self.__parse_expr(expr[1], m, root), 2)
                m.append(root, 1)
                return m

            # BE -> 'B
            if (expr[0] == "'" and
                    is_binary(expr[1])):
                m = create_machine(expr[1], 2)
                m.append(parent, 2)
                # nothing to append to any partitions
                return None

            # BE -> B'
            if (is_binary(expr[0]) and
                    expr[1] == "'"):
                m = create_machine(expr[0], 2)
                m.append(parent, 1)
                # nothing to append to any partitions
                return None

            # UE -> SS
            if (expr[0] == cls.dollar):
                return create_machine(cls.dollar + expr[1], 1)

            # UE -> AVM
            if (expr[0] == cls.hashmark):
                return create_machine(cls.hashmark + expr[1], 1)


        if (len(expr) == 3):
            # UB -> A B A
            if (is_tree(expr[0]) and
                    is_binary(expr[1]) and
                    is_tree(expr[2])):
                m = create_machine(expr[1], 2)
                m.append(self.__parse_expr(expr[0], m, root), 1)
                m.append(self.__parse_expr(expr[2], m, root), 2)
                return m

            # A -> [ D ]
            if (expr[0] == "[" and
                    is_tree(expr[1]) and
                    expr[2] == "]"):
                return list(self.__parse_definition(expr[1], parent, root))
        
        if (len(expr) == 4):
            # E -> U ( BE )
            if (is_unary(expr[0]) and
                    expr[1] == "(" and
                    is_tree(expr[2]) and
                    expr[3] == ")"):
                m = self.__parse_expr(expr[2], parent, root)

                # if BE was an expression with an apostrophe, then
                # return of __parse_expr() is None
                if m is not None:
                    m.append(create_machine(expr[1], 1), 0)
                return m

            # UE -> U [ D ]
            if (is_unary(expr[0]) and
                    expr[1] == "[" and
                    is_tree(expr[2]) and
                    expr[3] == "]"):
                m = create_machine(expr[0], 1)
                for parsed_expr in self.__parse_definition(expr[2], m, root):
                    m.append(parsed_expr, 1)
                return m

            # UE -> U ( U )
            if (is_unary(expr[0]) and
                    expr[1] == "(" and
                    is_unary(expr[2]) and
                    expr[3] == ")"):
                m = create_machine(expr[2], 1)
                m.append(create_machine(expr[0], 1), 1)
                return m

        if (len(expr) == 6):
            # BE -> B [E; E]
            if (is_binary(expr[0]) and
                    expr[1] == "[" and
                    is_tree(expr[2]) and
                    expr[3] == ";" and
                    is_tree(expr[4]) and
                    expr[5] == "]"):
                m = create_machine(expr[0], 2)
                m.append(self.__parse_expr(expr[2], m, root), 1)
                m.append(self.__parse_expr(expr[4], m, root), 2)
                return m

        pe = ParserException("Unknown expression in definition")
        logging.debug(str(pe))
        logging.debug(expr)
        raise pe

    def __parse_definition(self, definition, parent, root):
        for d in definition:
            yield self.__parse_expr(d, parent, root)
    
    def parse_into_machines(self, s, printname_index=0):
        parsed = self.parse(s)
        
        # HACK printname is now set to hungarian
        machine = create_machine(parsed[1][printname_index], 1)
        if len(parsed) > 2:
            for parsed_expr in self.__parse_definition(parsed[2], machine, machine):
                machine.append(parsed_expr, 1)
        return machine

def read(f, printname_index=0):
    d = {}
    dp = DefinitionParser()
    for line in f:
        l = line.strip()
        logging.info("Parsing: {0}".format(l))
        if len(l) == 0:
            continue
        if l.startswith("%"):
            continue
        try:
            m = dp.parse_into_machines(l, printname_index)
            d[m.printname()] = m
        except pyparsing.ParseException, pe:
            print l
            print "Error: ", str(pe)

    return d

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s : %(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    dp = DefinitionParser()
    pstr = sys.argv[-1]
    if sys.argv[1] == "-d":
        print Machine.to_debug_str(dp.parse_into_machines(pstr))
    elif sys.argv[1] == "-f":
        lexicon = read(file(sys.argv[2]))
    else:
        print dp.parse(pstr)

