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

################################################################################
### To discuss:                                                              ###
### 1. What should the act method return?                                    ###
###    a. The machines affected by the changes (don't think so)              ###
###    b. The whole seq, except for the machines that have been "dealt with" ###
###       by the operation (e.g. Y in AppendOperator) -- this is consistent  ###
###       with how Construction.act(s) works.                                ###
###    c. Nothing -- but then what will XConst.act() return?                 ###
################################################################################

