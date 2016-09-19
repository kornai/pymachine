import logging
import os

import networkx as nx
from networkx.readwrite import json_graph

from pymachine.machine import Machine

def ensure_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)

class MachineTraverser():
    @staticmethod
    def get_nodes(
            machine, exclude_words=[], names_only=True, keep_upper=False):
        traverser = MachineTraverser()
        # logging.info('getting nodes for: {0}'.format(machine.printname()))
        return traverser._get_nodes(
            machine, 0, set(exclude_words), names_only, keep_upper)

    def __init__(self):
        self.seen_for_nodes = set()

    def _get_nodes(
            self, machine, depth, exclude_words, names_only, keep_upper):
        if machine in self.seen_for_nodes:
            return
        self.seen_for_nodes.add(machine)
        name = machine.printname()
        # logging.info(u'traversing: {0}'.format(name))
        if (keep_upper or not name.isupper()) and name not in exclude_words:
            if names_only:
                yield name
            else:
                yield machine

        for part in machine.partitions:
            for submachine in part:
                for node in self._get_nodes(
                        submachine, depth+1, exclude_words, names_only,
                        keep_upper):
                    yield node
        for parent, _ in machine.parents:
            for node in self._get_nodes(
                    parent, depth+1, exclude_words, names_only, keep_upper):
                yield node

class MachineGraph:
    @staticmethod
    def create_from_machines(iterable, max_depth=None, whitelist=None,
                             strict=False, machinegraph_options = None):
        g = MachineGraph()
        g.seen = set()
        # logging.debug('whitelist: {}'.format(whitelist))
        for machine in iterable:
            g._get_edges_recursively(machine, max_depth, whitelist,
                                     strict=strict, machinegraph_options=machinegraph_options)

        return g

    def _get_edges_recursively(self, machine, max_depth, whitelist,
                               strict=False, depth=0, machinegraph_options=None):
        #  if pn.isupper():
        #      if depth >= 2:
        #          return
        # pn = machine.unique_name()
        if machine in self.seen or (max_depth is not None and
                                    depth > max_depth):
            # logging.info(u'skipping machine: {}'.format(pn))
            return

        # logging.info(u'getting edges for machine: {}'.format(pn))
        # logging.info("{0}".format(machine.partitions))

        self.seen.add(machine)
        # if printname == 'from':
        #     logging.info('from machine: {0}'.format(machine))
        edges = set()
        neighbours = set()
        for color, part in enumerate(machine.partitions):
            for machine2 in part:
                if machine2 in self.seen:
                    continue
                neighbours.add(machine2)
                edges.add((machine, machine2, color))
        for parent, color in machine.parents:
            if parent in self.seen:
                continue
            neighbours.add(parent)
            edges.add((parent, machine, color))

        for machine1, machine2, color in edges:
            printname1 = machine1.printname()
            printname2 = machine2.printname()
            # TODO
            if (whitelist is not None and printname1 not in whitelist and
                    printname2 not in whitelist):
                continue
            elif (not machinegraph_options == None) and machinegraph_options.upper_excl == True and (printname1.isupper() or printname2.isupper()):
                continue
            elif whitelist is None or (printname1 in whitelist and
                                       printname2 in whitelist):
                self.add_edge(
                    machine1.unique_name(), machine1.printname().encode('utf-8'),
                    machine2.unique_name(), machine2.printname().encode('utf-8'), color, machinegraph_options)

        for neighbour in neighbours:
            self._get_edges_recursively(
                neighbour, max_depth, whitelist, depth=depth+1, machinegraph_options=machinegraph_options)

    def __init__(self):
        self.G = nx.MultiDiGraph()

    def add_edge(self, node1, name1, node2, name2, color, machinegraph_options):
        # logging.debug(u'adding edge: {} -> {}'.format(node1, node2))
        nn_option = 0
        if machinegraph_options is not None:
            nn_option = machinegraph_options.nodename_option
        if nn_option == 0:
            self.G.add_node(node1, str_name=name1)
            self.G.add_node(node2, str_name=name2)
            self.G.add_edge(node1, node2, color=color)
        elif nn_option == 1 or nn_option == 2:
            node1 = node1.encode('utf-8')
            node2 = node2.encode('utf-8')
            # name1 = name1.encode('utf-8')
            # name2 = name2.encode('utf-8')
            nodes_names = list()
            for (node, name) in [(node1,name1), (node2,name2)]:
                if nn_option == 1:
                    nodes_names.append(name)
                elif nn_option == 2:
                    # TODO: hack: have should be isupper HAS
                    if node.isupper() or name in ['lack', 'before', 'not', 'have']:
                        nodes_names.append(node)
                    else:
                        nodes_names.append(name)

            weight = 1
            alfa = 2
            if machinegraph_options.weighted == True:
                if machinegraph_options.embedding_model == None:
                    logging.error('fullgraph.weighted is set to true, but no embedding model is given')
                else:
                    if machinegraph_options.color_based == True:
                        if not color == 0:
                            weight = alfa
                    else:
                        weight = machinegraph_options.embedding_model.get_sim(nodes_names[0], nodes_names[1])
                        if weight == None:
                            weight = 2
                        else:
                            weight = 1 - weight
            self.G.add_edge(nodes_names[0], nodes_names[1], color=color, weight=weight)

    def to_dict(self):
        return json_graph.adjacency.adjacency_data(self.G)

    # @staticmethod
    # def to_dict(G):
    #     return json_graph.adjacency.adjacency_data(G)

    @staticmethod
    def from_dict(d):
        return json_graph.adjacency.adjacency_graph(d)

    def to_dot(self):
        lines = [u'digraph finite_state_machine {', '\tdpi=100;']
        # lines.append('\tordering=out;')
        # sorting everything to make the process deterministic
        node_lines = []
        for node, n_data in self.G.nodes(data=True):
            d_node = Machine.d_clean(node)
            printname = Machine.d_clean('_'.join(d_node.split('_')[:-1]))
            if 'expanded' in n_data and not n_data['expanded']:
                node_line = u'\t{0} [shape = circle, label = "{1}", style="filled"];'.format(  # nopep8
                    d_node, printname).replace('-', '_')
            else:
                node_line = u'\t{0} [shape = circle, label = "{1}"];'.format(
                    d_node, printname).replace('-', '_')
            node_lines.append(node_line)
        lines += sorted(node_lines)

        edge_lines = []
        for u,v,edata in self.G.edges(data=True):
            if 'color' in edata:
                d_node1 = Machine.d_clean(u)
                d_node2 = Machine.d_clean(v)
                edge_lines.append(
                    u'\t{0} -> {1} [ label = "{2}" ];'.format(
                        Machine.d_clean(d_node1), Machine.d_clean(d_node2),edata['color']))

        lines += sorted(edge_lines)
        lines.append('}')
        return u'\n'.join(lines)

    def to_dot_str_graph(self):
        lines = [u'digraph finite_state_machine {', '\tdpi=100;']
        node_lines = []
        for node in self.G.nodes():
            d_node = Machine.d_clean(node)
            d_node_id = d_node.replace('=', '_')
            if "_" in d_node_id:
                d_node = d_node_id.split('_')[-2]
            else:
                d_node= d_node_id
            node_lines.append(u'\t{0} [shape = circle, label = "{1}"];'.format(
                d_node_id, d_node).replace('-', '_'))
        lines += sorted(node_lines)

        edge_lines = []
        for u,v, edata in self.G.edges(data=True):
            d_u = Machine.d_clean(u)
            d_v = Machine.d_clean(v)
            d_u = d_u.replace('=', '_')
            d_v = d_v.replace('=', '_')
            edge_lines.append(
                u'\t{0} -> {1} [ label = "{2}" ];'.format(
                    d_u, d_v,edata['color']))

        lines += sorted(edge_lines)
        lines.append('}')
        return u'\n'.join(lines)

def harmonic_mean(seq):
    try:
        length = float(len(seq))
    except TypeError:  # must be a generator
        return harmonic_mean(list(seq))
    if length == 0:
        return 0.0

    try:
        return length / sum((1.0/e for e in seq))
    except ZeroDivisionError:
        return 0.0


def average(seq):
    try:
        length = float(len(seq))
    except TypeError:  # must be a generator
        return average(list(seq))
    if length == 0:
        return 0.0
    total = 0.0
    for element in seq:
        try:
            total += element
        except TypeError:
            raise Exception("can't add this to a float: {0}".format(
                repr(element)))
    return total / length
    # return sum(seq) / float(len(seq))

def my_max(seq, default=0.0):
    try:
        return max(seq)
    except ValueError:
        return default

def min_jaccard(seq1, seq2, log=False):
    set1, set2 = map(set, (seq1, seq2))
    shorter_length = min(len(set1), len(set2))
    intersection = set1 & set2
    if not intersection:
        return 0
    else:
        sim = float(len(intersection)) / shorter_length
        if log:
            logging.info(u'set1: {0}, set2: {1}'.format(set1, set2))
            logging.info(u'shared: {0}'.format(intersection))
            logging.info('sim: {0}'.format(sim))
        return sim

def jaccard(seq1, seq2, log=False):
    set1, set2 = map(set, (seq1, seq2))
    union = set1 | set2
    intersection = set1 & set2
    if not intersection:
        return 0
    else:
        sim = float(len(intersection)) / len(union)
        if log:
            logging.info(u'set1: {0}, set2: {1}'.format(set1, set2))
            logging.info(u'shared: {0}'.format(intersection))
            logging.info('sim: {0}'.format(sim))
        return sim