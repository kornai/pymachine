import logging
import copy
from itertools import chain

from pymachine.control import Control
from constants import deep_pre, avm_pre, enc_pre

class Machine(object):
    def __init__(self, name, control=None, part_num=3):
        self.printname_ = name
        #if name.isupper():
        #    part_num = 3  # TODO crude, but effective
        self.partitions = [[] for i in range(part_num)]
        self.set_control(control)
        self.parents = set()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __id__(self):
        return unicode(self)

    def __unicode__(self):
        if self.control is None:
            return u"{0} (no control)".format(self.printname())
        return u"{0} ({1})".format(
            self.printname(),
            self.control.to_debug_str().replace('\n', ' '))

    def __deepcopy__(self, memo):
        new_machine = self.__class__(self.printname_)
        memo[id(self)] = new_machine
        new_partitions = copy.deepcopy(self.partitions, memo)
        new_control = copy.deepcopy(self.control, memo)
        new_machine.partitions = new_partitions
        new_machine.control = new_control

        for part_i, part in enumerate(new_machine.partitions):
            for m in part:
                m.add_parent_link(new_machine, part_i)
        return new_machine

    def unify(self, machine2):
        for i, part in enumerate(machine2.partitions):
            for m in part:
                if m not in self.partitions[i]:
                    self.partitions[i].append(m)
                    m.add_parent_link(self, i)

        for parent, i in machine2.parents:
            parent.partitions[i].remove(machine2)
            parent.partitions[i].append(self)
            self.add_parent_link(parent, i)

    def d_printname(self):
        """printname for dot output"""
        #TODO
        pn = self.printname_.split('/')[0]
        if self.control is not None:
            pn = u"{0}_{1}".format(pn, str(id(self.control))[-2:])

        return Machine.d_clean(pn)

    @staticmethod
    def d_clean(string):
        s = string
        for c in ('=', '@', '-', ',', "'", '"'):
            s = s.replace(c, '_')
        if s == 'edge':
            s += '_'
        elif s == '$':
            s = '_dollars'
        return s

    def printname(self):
        if '/' in self.printname_:
            return self.printname_.split('/')[0]
        return self.printname_

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
        # TODO printname
        #logging.debug(u"{0}.append(
        #   {1},{2})".format(self.printname(), what.printname(),
        #   which_partition).encode("utf-8"))
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

###################################
### Machine-type-related methods

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
