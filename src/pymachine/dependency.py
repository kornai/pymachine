import logging

from machine import Machine
from operators import AppendOperator, AppendToBinaryOperator, AppendToBinaryFromLexiconOperator  # nopep8

class DepsToMachines():
    def __init__(self, dep_map_fn):
        self.dependencies = {}
        for line in file(dep_map_fn):
            l = line.strip()
            if not l or l.startswith('#'):
                continue
            dep = Dependency.create_from_line(l)
            self.dependencies[dep.name] = dep

    def apply_dep(self, dep_str, machine1, machine2, lexicon=None):
        self.dependencies[dep_str].apply(machine1, machine2, lexicon)

class Dependency():
    def __init__(self, name, operators=[]):
        self.name = name
        self.operators = operators

    @staticmethod
    def create_from_line(line):
        rel, reverse = None, False
        logging.debug('parsing line: {}'.format(line))
        fields = line.split('\t')
        if len(fields) == 2:
            dep, edges = fields
        elif len(fields) == 3:
            dep, edges, rel = fields
            if rel[0] == '!':
                rel = rel[1:]
                reverse = True
        else:
            raise Exception('lines must have 2 or 3 fields: {}'.format(
                fields))

        edge1, edge2 = map(lambda s: int(s) if s not in ('-', '?') else None,
                           edges.split(','))

        return Dependency(dep, Dependency.get_standard_operators(
            edge1, edge2, rel, reverse))

    @staticmethod
    def get_standard_operators(edge1, edge2, rel, reverse):
        operators = []
        if edge1 is not None:  # it can be zero, don't check for truth value!
            operators.append(AppendOperator(0, 1, part=edge1))
        if edge2 is not None:
            operators.append(AppendOperator(1, 0, part=edge2))
        if rel:
            rel_machine = Machine(rel)
            operators.append(
                AppendToBinaryOperator(rel_machine, 0, 1, reverse=reverse))
            #operators.append(
            #    AppendToBinaryFromLexiconOperator(rel, 0, 1, reverse=reverse))

        return operators

    def apply(self, machine1, machine2, lexicon=None):
        for operator in self.operators:
            if isinstance(operator, AppendToBinaryFromLexiconOperator):
                operator.act((machine1, machine2), lexicon)
            else:
                operator.act((machine1, machine2))
