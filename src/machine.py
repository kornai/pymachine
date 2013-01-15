import logging
import copy
from itertools import chain

import control as ctrl

class Machine(object):
    def __init__(self, name, control=None, part_num=1):
        self.printname = name
        self.partitions = []
        for _ in xrange(part_num):
            self.partitions.append([])

        self.set_control(control)

        logging.debug(u"{0} created with {1} partitions".format(name, len(self.partitions)))
        
        self._parents = set()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.printname()

    def __deepcopy__(self, memo):
        new_machine = self.__class__(self.printname)
        memo[id(self)] = new_machine
        new_partitions = copy.deepcopy(self.partitions, memo)
        new_control = copy.deepcopy(self.control, memo)
        new_machine.partitions = new_partitions
        new_machine.control = new_control

        for part_i, part in enumerate(new_partitions.partitions):
            for m in part:
                m.__add_parent_link(new_machine, part_i)
        return new_machine

    def printname(self):
        return self.printname

    def set_control(self, control):
        """Sets the control."""
        # control will be an FST representation later
        if not isinstance(control, ctrl.Control) and control is not None:
            raise TypeError("control should be a Control instance")
        self.control = control
        if control is not None:
            control.set_machine(self)

    def allNames(self):
        return set([self.__unicode__()]).union(*[partition[0].allNames()
            for partition in self.partitions])

    def children(self):
        """Returns all direct children of the machine."""
        return set(chain(*self.partitions))

    def unique_machines_in_tree(self):
        """Returns all unique machines under (and including) the current one."""
        def __recur(m):
            visited.add(m)
            for child in m.children():
                if child not in visited:
                    __recur(child, visited)

        visited = set()
        __recur(self)
        return visited
        
    def append(self, what, which_partition=0):
        """
        Adds @p what to the specified partition. @p what can either be a
        Machine, a string, or a list thereof.
        """
        logging.debug(u"{0}.append({1},{2})".format(self.printname(),
           what.printname(), which_partition).encode("utf-8"))
        if len(self.partitions) > which_partition:
            if what in self.partitions[which_partition]:
                return
        else:
            self.partitions += [[]] * (which_partition + 1 -
                len(self.partitions))

        self.__append(what, which_partition)

    def __append(self, what, which_partition):
        """Recursive helper function for append()."""
        if isinstance(what, Machine):
            self.partitions[which_partition].append(what)
            what.__add_parent_link(self, which_partition)
        elif what is None:
            pass
        elif isinstance(what, list):
            for what_ in what:
                self.__append(what_, which_partition)
        else:
            raise TypeError("Only machines and strings can be added to partitions")

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
            what.__del_parent_link(self, which_partition)

    def __add_parent_link(self, whose, part):
        self._parents.add((whose, part))

    def __del_parent_link(self, whose, part):
        self._parents.remove((whose, part))

    def to_debug_str(self, depth=0, lines=None, stop=None):
        """An even more detailed __str__, complete with object ids and
        recursive."""
        return machine.__to_debug_str(0)

    def __to_debug_str(self, depth, lines=None, stop=None):
        """Recursive helper method for to_debug_str.
        @param depth the depth of the recursion.
        @param stop the machines already visited (to detect cycles)."""
        if stop is None:
            stop = set()
        if lines is None:
            lines = []

        if self in stop:
            lines.append('{0:>{1}}:{2}'.format(
                str(self), 2 * depth + len(str(self)), id(self)))
        else:
            stop.add(self)
            lines.append('{0:>{1}}:{2}'.format(
                str(self), 2 * depth + len(str(self)), id(self)))
            for part in self.partitions:
                for m in part:
                    m.__to_debug_str(depth + 1, lines, stop)

        if depth == 0:
            return "\n".join(lines)

def test_printname():
    m_unicode = Machine(u"\u00c1")
    print unicode(m_unicode).encode("utf-8")
    print m_unicode.printname()
    logging.error(unicode(m_unicode).encode("utf-8"))


if __name__ == "__main__":
    test_printname()

