import logging

class Monoid(object):
    """
    Our monoid class
    """
    
    def __init__(self, name, part_num=1):
        self.partitions = []
        self.partitions.append(name)
        for _ in xrange(part_num):
            self.partitions.append([])

        logging.debug(u"{0} created with {1} partitions".format(name, len(self.partitions[1:])))
        
        self.operations = None
        self.unit = None
        self.distinguished_partition = None
    
    def __eq__(self, other):
        return (self.partitions == other.partitions and
                self.operations == other.operations and
                self.unit == other.unit and
                self.distinguished_partition == other.distinguished_partition)

    def append(self, what, which_partition):
        if len(self.partitions) > which_partition:
            from machine import Machine
            if isinstance(what, Machine) or isinstance(what, str):
                self.partitions[which_partition].append(what)
            elif what is None:
                pass
            elif isinstance(what, list):
                for what_ in what:
                    self.append(what_, which_partition)
            else:
                raise TypeError("Only machines and strings can be added to partitions")
        else:
            raise IndexError("That partition does not exist")

    def remove(self, what, which_partition=None):
        """Removes @p what from the specified partition."""
        if which_partition is not None:
            if len(self.partitions) > which_partition:
                self.partitions[which_partition].remove(what)
        else:
            for partition, _ in enumerate(self.partitions):
                self.remove(partition, what)

    def find(self, what):
        """Returns the list of partitions on which @p what is found."""
        return [i for i, p in enumerate(self.partitions) if what in p]

