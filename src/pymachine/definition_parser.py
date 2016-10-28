import argparse
from collections import defaultdict
import logging
import re
import string
import sys

try:
    import pyparsing
    from pyparsing import Literal
    from pyparsing import Word
    from pyparsing import Group
    from pyparsing import Combine
    from pyparsing import Optional
    from pyparsing import Forward
    from pyparsing import alphanums
    from pyparsing import SkipTo
    from pyparsing import LineEnd
    from pyparsing import nums
    from pyparsing import delimitedList 
except ImportError:
    logging.critical("PyParsing has to be installed on the computer")
    sys.exit(-1)

from hunmisc.xstring.encoding import decode_from_proszeky

from constants import deep_cases, avm_pre, deep_pre, enc_pre, id_sep
from pymachine.machine import Machine
from pymachine.control import ConceptControl

class ParserException(Exception):
    pass

class DefinitionParser(object):
    _str = set([str, unicode])

    lb = "["
    rb = "]"
    lp = "("
    rp = ")"
    left_defa = '<'
    right_defa = '>'

    clause_sep = ","
    part_sep = ";"
    prime = "'"
    hyphen = "-"
    langspec_pre = "$"  # starts langspec deep case
    unary_p = re.compile("^[a-z_#\-/0-9]+(/[0-9]+)?$")
    binary_p = re.compile("^[A-Z_0-9]+(/[0-9]+)?$")

    def __init__(self):
        self.init_parser()

    @classmethod
    def _is_binary(cls, s):
        return ((type(s) in cls._str and cls.binary_p.match(s)) or
                (type(s) is list and s[0] == deep_pre and s[1] == "REL"))

    @classmethod
    def _is_unary(cls, s):
        return ((type(s) in cls._str and cls.unary_p.match(s) is not None) or
                (type(s) is list and (
                    (s[0] == deep_pre) or
                    (s[0] == cls.langspec_pre) or
                    (s[0] == enc_pre) or
                    (s[0] == cls.left_defa)
                )))

    @classmethod
    def _is_deep_case(cls, s):
        return s in deep_cases

    def init_parser(self):
        self.lb_lit = Literal(DefinitionParser.lb)
        self.rb_lit = Literal(DefinitionParser.rb)
        self.lp_lit = Literal(DefinitionParser.lp)
        self.rp_lit = Literal(DefinitionParser.rp)
        self.left_defa_lit = Literal(DefinitionParser.left_defa)
        self.right_defa_lit = Literal(DefinitionParser.right_defa)

        self.clause_sep_lit = Literal(DefinitionParser.clause_sep)
        self.part_sep_lit = Literal(DefinitionParser.part_sep)
        self.prime_lit = Literal(DefinitionParser.prime)
        self.hyphen_lit = Literal(DefinitionParser.hyphen)
        self.enc_pre_lit = Literal(enc_pre)
        self.deep_pre_lit = Literal(deep_pre)
        self.avm_pre_lit = Literal(avm_pre)
        self.langspec_pre_lit = Literal(DefinitionParser.langspec_pre)
        self.id_sep_lit = Literal(id_sep)

        self.disambig_id = self.id_sep_lit + Word(nums)

        self.deep_cases = Group(self.deep_pre_lit + Word(string.uppercase))

        self.unary = Forward()
        self.unary << (Combine(Optional("-") +
                       Word(string.lowercase + "_" + nums) +
                       Optional(self.disambig_id))
                       | self.deep_cases
                       | Group(self.langspec_pre_lit +
                               Word(string.uppercase + "_"))
                       | Group(self.avm_pre_lit +
                               Word(string.ascii_letters + "_"))
                       | Group(self.enc_pre_lit + Word(alphanums + "_-"))
                       | Group(self.left_defa_lit + self.unary +
                               self.right_defa_lit))

        self.binary = (Combine(Word(string.uppercase + "_" + nums) +
                       Optional(self.disambig_id))
                       | Group(self.deep_pre_lit + 'REL'))
        self.dontcare = SkipTo(LineEnd())

        # main expression
        self.expression = Forward()
        self.binexpr = Forward()
        self.unexpr = Forward()
        self.argexpr = Forward()

        # "enumerable expression"
        # D -> E | E, D
        self.definition = Group(delimitedList(self.expression,
                                delim=DefinitionParser.clause_sep))

        self.expression << Group(
            # E -> UE
            (self.unexpr) ^

            # E -> BE
            (self.binexpr) ^

            # E -> U ( E )
            (self.unary + self.lp_lit + self.expression + self.rp_lit) ^

            # E -> < E >
            (self.left_defa_lit + self.expression + self.right_defa_lit)
        )

        self.binexpr << Group(
            # BE -> A B
            (self.argexpr + self.binary) ^

            # BE -> B A
            (self.binary + self.argexpr) ^

            # BE -> A B A
            (self.argexpr + self.binary + self.argexpr) ^

            # BE -> B [ E; E ]
            (self.binary + self.lb_lit + self.expression + self.part_sep_lit
             + self.expression + self.rb_lit)
        )

        self.unexpr << Group(
            # UE -> U
            (self.unary) ^

            # UE -> U [ D ]
            (self.unary + self.lb_lit + self.definition + self.rb_lit) ^

            # UE -> U ( U )
            (self.unary + self.lp_lit + self.unary + self.rp_lit)
        )

        self.argexpr << Group(
            # A -> UE
            (self.unexpr) ^

            # A -> [ D ]
            (self.lb_lit + self.definition + self.rb_lit) ^

            # A -> < A >
            (self.left_defa_lit + self.argexpr + self.right_defa_lit) ^

            # A -> '
            (self.prime_lit)
        )

        self.hu, self.pos, self.en, self.lt, self.pt = (
            Word(alphanums + "#-/_.'"),) * 5
        self.defid = Word(nums)
        self.word = Group(self.hu + self.pos + self.en + self.lt + self.pt)

        # S -> W : D | W : D % _
        #self.sen = self.definition + LineEnd()

    def parse(self, s):
        return self.definition.parseString(s, parseAll=True).asList()

    def create_machine(self, name, partitions):
        # lists are accepted because of ["=", "AGT"]
        if type(name) is list:
            name = "".join(name)

        # HACK until we find a good solution for defaults
        name = name.strip('<>') 

        m = Machine(decode_from_proszeky(name), ConceptControl(), partitions) 
        return m

    def unify(self, machine):
        def __collect_machines(m, machines, is_root=False):
            # cut the recursion
            key = m.printname(), __has_other(m)
            if (key in machines and m in machines[key]):
                return

            if not is_root:
                machines[m.printname(), __has_other(m)].append(m)
            for partition in m.partitions:
                for m_ in partition:
                    __collect_machines(m_, machines)

        def __has_other(m):
            for m_ in m.partitions[0]:
                if m_.printname() == "other":
                    return True
            return False

        def __get_unified(machines, res=None):
            # if nothing to unify, don't
            if len(machines) == 1:
                return machines[0]

            # if a return machine is given, don't create a new one
            if res is None:
                prototype = machines[0]
                res = self.create_machine(prototype.printname(),
                                          len(prototype.partitions))
            for m in machines:
                # if the same machine, don't add anything
                if id(m) == id(res):
                    continue

                for p_i, p in enumerate(m.partitions):
                    for part_m in p:
                        if part_m.printname() != "other":
                            res.partitions[p_i].append(part_m)

                            part_m.del_parent_link(m, p_i)
                            part_m.add_parent_link(res, p_i)

            return res

        def __replace(where, for_what, is_other=False, visited=None):
            if visited is None:
                visited = set()

            if id(where) in visited:
                return

            visited.add(id(where))

            pn = for_what.printname()
            for p_i, p in enumerate(where.partitions):
                # change the partition machines
                for part_m_i, part_m in enumerate(p):
                    if part_m.printname() == pn and __has_other(
                            part_m) == is_other:
                        where.partitions[p_i][part_m_i] = for_what
                        for_what.add_parent_link(where, p_i)
                    __replace(where.partitions[p_i][part_m_i],
                              for_what, is_other, visited)

                # unification if there is a machine more than once on the same
                # partition
                where.partitions[p_i] = list(set(p))

        machines = defaultdict(list)
        __collect_machines(machine, machines, is_root=True)
        for k, machines_to_unify in machines.iteritems():

            if len(machines_to_unify[0].partitions) > 1:
                continue

            printname, is_other = k
            #if unification affects the root (machine),
            #be that the result machine
            if printname == machine.printname():
                unified = __get_unified(machines_to_unify, machine)
            else:
                unified = __get_unified(machines_to_unify)
            __replace(machine, unified, is_other)

    def __parse_expr(self, expr, root, loop_to_defendum=True):
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

        most_part = 0
        left_part = 1
        right_part = 2

        if (len(expr) == 1):
            # UE -> U
            if (is_unary(expr[0])):
                logging.debug("Parsing {0} as a unary.".format(expr[0]))
                return [self.create_machine(expr[0], 1)]

            # E -> UE | BE, A -> UE
            if (is_tree(expr[0])):
                logging.debug("Parsing {0} as a tree.".format(expr[0]))
                return self.__parse_expr(expr[0], root, loop_to_defendum)

        if (len(expr) == 2):
            # BE -> A B
            if (is_tree(expr[0]) and
                    is_binary(expr[1])):
                m = self.create_machine(expr[1], most_part)
                if expr[0] != ["'"]:
                    m.append_all(
                        self.__parse_expr(expr[0], root, loop_to_defendum),
                        left_part)
                if loop_to_defendum:
                    m.append(root, right_part)
                return [m]

            # BE -> B A
            if (is_binary(expr[0]) and
                    is_tree(expr[1])):
                m = self.create_machine(expr[0], most_part)
                if expr[1] != ["'"]:
                    m.append_all(
                        self.__parse_expr(expr[1], root, loop_to_defendum),
                        right_part)
                if loop_to_defendum:
                    m.append(root, left_part)
                return [m]

            # BE -> 'B
            if (expr[0] == ["'"] and
                    is_binary(expr[1])):
                m = self.create_machine(expr[1], most_part)
                #m.append(parent, 1)
                if loop_to_defendum:
                    m.append(root, right_part)
                return [m]

            # BE -> B'
            if (is_binary(expr[0]) and
                    expr[1] == ["'"]):
                m = self.create_machine(expr[0], most_part)
                # m.append(parent, 0)
                if loop_to_defendum:
                    m.append(root, left_part)
                return [m]

            # U -> =AGT
            if expr[0] == deep_pre:
                return [self.create_machine(deep_pre + expr[1], 1)]

            # U -> $HUN_FROM
            if (expr[0] == cls.langspec_pre):
                return [self.create_machine(cls.langspec_pre + expr[1], 1)]

            # U -> #AVM
            if (expr[0] == avm_pre):
                return [self.create_machine(avm_pre + expr[1], 1)]

            # U -> @External_url
            if (expr[0] == enc_pre):
                return [self.create_machine(enc_pre + expr[1], 1)]

        if (len(expr) == 3):
            # UB -> A B A
            if (is_tree(expr[0]) and
                    is_binary(expr[1]) and
                    is_tree(expr[2])):
                m = self.create_machine(expr[1], most_part)
                logging.debug(expr[1])
                if expr[0] != [DefinitionParser.prime]:
                    logging.debug(expr[0])
                    m.append_all(
                        self.__parse_expr(expr[0], root, loop_to_defendum),
                        left_part)
                if expr[2] != [DefinitionParser.prime]:
                    m.append_all(
                        self.__parse_expr(expr[2], root, loop_to_defendum),
                        right_part)
                return [m]

            # A -> [ D ]
            if (expr[0] == "[" and
                    is_tree(expr[1]) and
                    expr[2] == "]"):
                logging.debug(
                    "Parsing expr {0} as an embedded definition".format(expr))
                res = list(
                    self.__parse_definition(expr[1], root, loop_to_defendum))
                return res

            # E -> < E >, U -> < U >
            if expr[0] == '<' and expr[2] == '>':
                logging.debug('E -> < E >' + str(expr[1]))
                return list(self.__parse_expr(expr[1], root, loop_to_defendum))

        if (len(expr) == 4):
            # UE -> U ( U )
            # E -> U ( BE ) provisional
            if (is_unary(expr[0]) and
                    expr[1] == "(" and
                    expr[3] == ")"):
                logging.debug('X -> U ( Y )')
                if is_unary(expr[2]):
                    m = self.create_machine(expr[2], 1)
                else:
                    m = self.__parse_expr(expr[2], root, loop_to_defendum)[0]
                m.append(self.create_machine(expr[0], 1), 0)
                return [m]

            # UE -> U [ D ]
            if (is_unary(expr[0]) and
                    expr[1] == "[" and
                    is_tree(expr[2]) and
                    expr[3] == "]"):
                m = self.create_machine(expr[0], 1)
                for parsed_expr in self.__parse_definition(expr[2], root,
                                                           loop_to_defendum):
                    m.append(parsed_expr, 0)
                return [m]

            # E -> U ( BE )
            #if (is_unary(expr[0]) and
            #        expr[1] == "(" and
            #        is_tree(expr[2]) and
            #        expr[3] == ")"):
            #    ms = self.__parse_expr(expr[2], root, loop_to_defendum)
            #    # if BE was an expression with an apostrophe, then
            #    # return of __parse_expr() is None
            #    if len(ms) != 0:
            #        ms[0].append(self.create_machine(expr[0], 1), 0)
            #    # if len(ms) == 3 and ms[0] == '<':
            #    #        ms = ms[1]
            #    if len(ms) != 1:
            #        logging.warning("0th partition of binary machines " +
            #                        "is not implemented "+str(ms))
            #    return ms
            logging.warning('machine cannot be built '+str(expr))

        if (len(expr) == 6):
            # BE -> B [E; E]
            if (is_binary(expr[0]) and
                    expr[1] == "[" and
                    is_tree(expr[2]) and
                    expr[3] == ";" and
                    is_tree(expr[4]) and
                    expr[5] == "]"):
                m = self.create_machine(expr[0], 2)
                m.append_all(
                    self.__parse_expr(expr[2], m, root, loop_to_defendum),
                    0)
                m.append_all(
                    self.__parse_expr(expr[4], m, root, loop_to_defendum),
                    1)
                return [m]

        pe = ParserException(
            "Unknown expression in definition: {0} (len={1})".format(
                expr,
                len(expr)))
        logging.debug(str(pe))
        logging.debug(expr)
        raise pe

    def __parse_definition(self, definition, root, loop_to_defendum=True):
        logging.debug(str(definition))
        for d in definition:
            yield self.__parse_expr(d, root, loop_to_defendum)[0]

    def parse_into_machines(self, printname, id_, def_, add_indices=False,
                            loop_to_defendum=True):

        machine = self.create_machine(printname.lower(), 1)

        if add_indices:
            machine.printname_ = machine.printname() + id_sep + id_

        #if def_ != '':
        logging.debug(def_)
        parsed = self.parse(def_)
        logging.debug(parsed)
        for parsed_expr in self.__parse_definition(
                parsed[0], machine, loop_to_defendum):
            machine.append(parsed_expr, 0)

        self.unify(machine)
        return machine

def read_defs(f, language_index=0, add_indices=False, loop_to_defendum=True):
    def_parser = DefinitionParser()
    for line in f:
        fields = line.strip('\n').split('\t')
        if len(fields) != 9:
            logging.warning(
                "Wrong number of fields ({}) in {}".format(len(fields), fields))
            continue
        forms_in_langs = fields[:4] 
        id_, dv, pos, def_, comment = fields[4:]
        if not def_:
            continue
        logging.debug("Parsing: {0}".format(line))
        printname = forms_in_langs[language_index]
        try:
            m = def_parser.parse_into_machines(printname, id_, def_,
                                               add_indices, loop_to_defendum)
            if m.partitions[0] == []:
                logging.debug('dropping empty definition of '+m.printname())
                continue
            pn = m.printname()
            if pn in d:
                continue
                # logging.warning('duplicate pn: {0}, machines: {1}, {2}'.format(
                #    pn, d[pn], "{0}:{1}".format(m, m.partitions)))
            d[pn].add(m)
            logging.debug('\n'+m.to_debug_str())
            yield m
        except pyparsing.ParseException, pe:
            logging.error('Cannot parse {}/{}: {}\n{}'.format(printname, id_,
                                                              def_, pe))


def parse_args(): 
    parser = argparse.ArgumentParser(
        description='Parse manually written 4lang definitions')
    parser.add_argument('formula_or_lexicon')
    parser.add_argument('-s', '--singe_formula', action='store_true',
                        help='default: the input is the lexicon file')
    parser.add_argument('-d', '--debug_machine', action='store_true')
    return parser.parse_args()


if __name__ == "__main__":
    format_ = "%(asctime)s: %(module)s (%(lineno)s) %(levelname)s %(message)s"
    logging.basicConfig(level=logging.INFO, format=format_)
    args = parse_args()
    if args.singe_formula:
        def_parser = DefinitionParser()
        machine_iterable = [
            def_parser.parse_into_machines('NO PRINTNAME', 'NO ID', args.formula_or_lexicon)]
    else:
        machine_iterable = read_defs(file(args.formula_or_lexicon))
    # in some third case: print def_parser.parse(args.formula_or_lexicon)
    for machine in machine_iterable:
        debug_str = Machine.to_debug_str(machine)
        if args.debug_machine:
            print debug_str
