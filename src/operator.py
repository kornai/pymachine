"""Operator definitions."""
#from machine import Machine

class Operator(object):
    """The abstract superclass of the operator hierarchy."""
    def act(self, seq):
        """
        Acts on the machines in the randomly accessible sequence @p seq.
        @note The indices of the machines affected by the operation must be
              specified in the constructor.
        """
        pass

class AppendOperator(object):
    """Appends a machine to another's partition: <tt>X, Y -> X[Y]</tt>."""
    def __init__(self, X, Y, part=1):
        """
        @param X index of the machine to whose partition Y will be appended.
        @param Y index of the machine to be appended.
        @param part the partition index.
        """
        self.X = X
        self.Y = Y
        self.part = part

    def act(self, seq):
        seq[self.X].append(seq[self.Y], self.part)

