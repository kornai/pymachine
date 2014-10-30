#!/env/python
import logging

from pymachine.src.machine import Machine
from pymachine.src.control import ConceptControl
from operators import AppendOperator, AppendToBinaryOperator

def dep_map_reader(fn, lexicon=None):
    dep_to_op = {}
    if not fn:
        return {}
    for line in file(fn):
        rel_machine, reverse = None, False
        l = line.strip()
        if not l or l.startswith('#'):
            continue
        logging.debug('parsing line: {}'.format(line))
        fields = l.split('\t')
        if len(fields) == 2:
            dep, edges = fields
        elif len(fields) == 3:
            dep, edges, rel = fields
            if rel[0] == '!':
                rel = rel[1:]
                reverse = True
            logging.debug(
                'trying to find machine for this relation: {}'.format(rel))
            if lexicon is not None:
                rel_machine = get_rel_machine(rel, lexicon)
            else:
                rel_machine = Machine(rel, ConceptControl(), 3)
            logging.debug('found this: {}'.format(rel_machine))
        else:
            raise Exception('lines must have 2 or 3 fields: {}'.format(
                fields))

        edge1, edge2 = map(lambda s: int(s) if s not in ('-', '?') else None,
                           edges.split(','))
        logging.debug(
            'dependency: {0}, edge1: {1}, edge2: {2}, rel_machine: {3}'.format(
                dep, edge1, edge2, rel_machine))
        dep_to_op[dep] = create_operators(edge1, edge2, rel_machine, reverse)

    return dep_to_op

def get_rel_machine(rel, lexicon):
    machines = lexicon.active.get(rel)
    if not machines:
        m = Machine(rel, ConceptControl(), 3)
        lexicon.add_active(m)
        return m
    elif len(machines) > 1:
        raise Exception('ambiguous relation: "{0}"'.format(rel))
    else:
        return machines.keys()[0]

def create_operators(edge1, edge2, rel, reverse):
    operators = []
    if edge1 is not None:  # it can be zero, so don't check for truth value!
        operators.append(AppendOperator(0, 1, part=edge1))
    if edge2 is not None:
        operators.append(AppendOperator(1, 0, part=edge2))
    if rel:
        if not reverse:
            operators.append(AppendToBinaryOperator(rel, 0, 1))
        else:
            operators.append(AppendToBinaryOperator(rel, 1, 0))

    return operators
