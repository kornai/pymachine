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

class AppendOperator(Operator):
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
        return seq[self.X]

class ExpandOperator(Operator):
    """Expands an active machine."""
    def __init__(self, lexicon, i):
        """
        @param lexicon the lexicon.
        """
        self.lexicon = lexicon

    def act(self, input):
        """
        @param input the machine read by the transition.
        @param working_area a list.
        """
        return self.lexicon.expand(input)

class FillArgumentOperator(Operator):
    """Fills the argument of the representation in the working area."""
    def act(self, input):
        pass
