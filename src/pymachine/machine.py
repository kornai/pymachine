import logging
import copy
from itertools import chain
import re

from pymachine.control import Control
from constants import deep_pre, avm_pre, enc_pre

class Machine(object):
    def __init__(self, name, control=None, part_num=3):
        if not name:
            logging.warning('empty printname! replacing with "???"')
            name = "???"
        self.printname_ = name
        # if name.isupper():
        #     part_num = 3  # TODO crude, but effective
        self.partitions = [[] for i in range(part_num)]
        self.set_control(control)
        self.parents = set()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        if self.control is None:
            return u"{0}, no control".format(self.unique_name())
        return u"{0}, {1}".format(
            self.unique_name(), self.control.to_debug_str().replace('\n', ' '))

    def __deepcopy__(self, memo):
        if id(self) in memo:
            return memo[id(self)]
        new_machine = self.__class__(self.printname_)
        memo[id(self)] = new_machine
        new_partitions = copy.deepcopy(self.partitions, memo)
        # new_parents = copy.deepcopy(self.parents, memo)
        new_control = copy.deepcopy(self.control, memo)
        new_machine.partitions = new_partitions
        # new_machine.parents = new_parents
        new_machine.control = new_control

        # for parent, i in new_machine.parents:
        #    parent.append(new_machine, i)

        for part_i, part in enumerate(new_machine.partitions):
            for m in part:
                m.add_parent_link(new_machine, part_i)
        copy.deepcopy(self.parents, memo)
        return new_machine

    def unify(self, machine2, exclude_0_case=False, exclude_negation=False,
              keep_orig=False):
        """
        moves all incoming and outgoing links of machine2 to machine1.
        The list() part is essential in all three places (going through
        partitions, machines of partitions, and parents), because that creates
        a new list, but doesn't copy the machines themselves, as deepcopy would
        """
        # logging.info('unifying {0}'.format(machine2.printname()))
        for i, part in enumerate(list(machine2.partitions)):
            for m in list(part):
                if (
                        i == 0 and m.printname().startswith('=') and
                        exclude_0_case):
                    continue
                if exclude_negation and m.printname() == 'not':
                    continue
                # logging.info('actually moving edge')
                self.append(m, i)
                if not keep_orig:
                    machine2.remove(m, i)

        # logging.info('parents: {0}'.format(list(machine2.parents)))
        for parent, i in list(machine2.parents):
            # logging.info('parent: {0}'.format(parent.printname()))
            if not keep_orig:
                parent.remove(machine2, i)
            parent.append(self, i)

    def dot_id(self):
        """node id for dot output"""
        return u"{0}_{1}".format(
            Machine.d_clean(self.dot_printname()), str(id(self))[-4:])

    def dot_printname(self):
        """printname for dot output"""
        return self.printname_.split('/')[0].replace('-', '_')

    @staticmethod
    def d_clean(string):
        s = string
        for c in '\\=@-,\'".!:;':
            s = s.replace(c, '_')
        s = s.replace('$', '_dollars')
        s = s.replace('%', '_percent')
        if s == '#':
            s = '_number'
        keywords = ("graph", "node", "strict", "edge")
        if re.match('^[0-9]', s) or s in keywords:
            s = "X" + s
        return s

    def printname(self):
        if '/' in self.printname_:
            return self.printname_.split('/')[0]
        return self.printname_

    def unique_name(self):
        return u"{0}_{1}".format(self.printname(), id(self))

    def set_control(self, control):
        """Sets the control."""
        # control will be an FST representation later
        if not isinstance(control, Control) and control is not None:
            raise TypeError("control should be a Control instance, " +
                            "got {} instead".format(type(control)))
        self.control = control
        if control is not None:
            control.set_machine(self)

    def allNames(self):
        return set([self.__unicode__()]).union(
            *[partition[0].allNames() for partition in self.partitions])

    def children(self):
        """Returns all direct children of the machine."""
        return set(chain(*self.partitions))

    def unique_machines_in_tree(self):
        """Returns all unique machines under (and including)
        the current one."""
        def __recur(m):
            visited.add(m)
            for child in m.children():
                if child not in visited:
                    __recur(child)

        visited = set()
        __recur(self)
        return visited

    def append_all(self, what_iter, which_partition=0):
        """ Mass append function that calls append() for every object """
        from collections import Iterable
        if isinstance(what_iter, Iterable):
            for what in what_iter:
                self.append(what, which_partition)
        else:
            raise TypeError("append_all only accepts iterable objects.")

    def append(self, what, which_partition=0):
        """
        Adds @p Machine instance to the specified partition.
        """
        #  TODO printname
        # logging.debug(u"{0}.append(
        #    {1},{2})".format(self.printname(), what.printname(),
        #    which_partition).encode("utf-8"))
        if len(self.partitions) > which_partition:
            if what in self.partitions[which_partition]:
                return
        else:
            self.partitions += [[] for i in range(which_partition + 1 -
                                len(self.partitions))]

        self.__append(what, which_partition)

    def __append(self, what, which_partition):
        """Helper function for append()."""
        if isinstance(what, Machine):
            self.partitions[which_partition].append(what)
            what.add_parent_link(self, which_partition)
        elif what is None:
            pass
        else:
            raise TypeError(
                "Only machines and strings can be added to partitions")

    def remove_all(self, what_iter, which_partition=None):
        """ Mass remove function that calls remove() for every object """
        from collections import Iterable
        if isinstance(what_iter, Iterable):
            for what in what_iter:
                self.remove(what, which_partition)
        else:
            raise TypeError("append_all only accepts iterable objects.")

    def remove(self, what, which_partition=None):
        """
        Removes @p what from the specified partition. If @p which_partition
        is @c None, @p what is removed from all partitions on which it is
        found.
        """
        if which_partition is not None:
            if len(self.partitions) > which_partition:
                self.partitions[which_partition].remove(what)
        else:
            for partition, _ in enumerate(self.partitions):
                self.partitions[partition].remove(what)

        if isinstance(what, Machine):
            what.del_parent_link(self, which_partition)

    def add_parent_link(self, whose, part):
        self.parents.add((whose, part))

    def del_parent_link(self, whose, part):
        self.parents.remove((whose, part))

# ##################################
# ## Machine-type-related methods

    def unary(self):
        return len(self.partitions) == 1

    def binary(self):
        return len(self.partitions) >= 2

    def deep_case(self):
        return self.printname_[0] == deep_pre

    def named_entity(self):
        return self.printname_[0] == enc_pre

    def avm(self):
        return self.printname_[0] == avm_pre

    # TODO: langspec

    def fancy(self):
        return self.deep_case() or self.avm() or self.named_entity()

    def to_debug_str(self, depth=0, max_depth=3, parents_to_display=3,
                     stop=None):
        """An even more detailed __str__, complete with object ids and
        recursive."""
        return self.__to_debug_str(0, max_depth, parents_to_display, stop=stop)

    def __to_debug_str(self, depth, max_depth=3, parents_to_display=3,
                       lines=None, stop=None, at_partition=""):
        """Recursive helper method for to_debug_str.
        @param depth the depth of the recursion.
        @param max_depth the maximum recursion depth.
        @param stop the machines already visited (to detect cycles)."""
        if stop is None:
            stop = set()
        if lines is None:
            lines = []

        pn = self.printname()
        if (depth != 0 and self in stop) or depth == max_depth:
            prnts_str = '...'
        else:
            prnts = [m[0].printname() + ':' + str(id(m[0])) + ':' + str(m[1])
                     for m in self.parents]
            prnts_str = ','.join(prnts[:parents_to_display])
            if len(prnts) > parents_to_display:
                prnts_str += ', ..'
        lines.append(u'{0:>{1}}:{2}:{3} p[{4}]'.format(
            at_partition, 2 * depth + len(str(at_partition)), pn, id(self),
            prnts_str))
        if not ((depth != 0 and self in stop) or depth == max_depth):
            stop.add(self)
            for part_i in xrange(len(self.partitions)):
                part = self.partitions[part_i]
                for m in part:
                    m.__to_debug_str(depth + 1, max_depth, parents_to_display,
                                     lines, stop, part_i)

        if depth == 0:
            return u"\n".join(lines)

def test_printname():
    m_unicode = Machine(u"\u00c1")
    print unicode(m_unicode).encode("utf-8")
    print m_unicode.printname().encode("utf-8")
    logging.error(unicode(m_unicode).encode("utf-8"))


if __name__ == "__main__":
    test_printname()
