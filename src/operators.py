"""Operator definitions."""

import logging

from machine import Machine
from control import KRPosControl, ConceptControl

class Operator(object):
    """The abstract superclass of the operator hierarchy."""
    def __init__(self, working_area=None):
        """The working area is that of the enclosing Construction."""
        self.working_area = working_area

    def act(self, seq):
        """
        Acts on the machines in the randomly accessible sequence @p seq.
        @note The indices of the machines affected by the operation must be
              specified in the constructor.
        """
        pass

class AppendOperator(Operator):
    """Appends a machine to another's partition: <tt>X, Y -> X[Y]</tt>."""
    def __init__(self, X, Y, part=0, working_area=None):
        """
        @param X index of the machine to whose partition Y will be appended.
        @param Y index of the machine to be appended.
        @param part the partition index.
        """
        Operator.__init__(self, working_area)
        self.X = X
        self.Y = Y
        self.part = part

    def act(self, seq):
        seq[self.X].append(seq[self.Y], self.part)
        return [seq[self.X]]

class FeatChangeOperator(Operator):
    """ Changes one feature of input machines control, that is a dictionary
        representaion of a KR code
    """
    def __init__(self, key, value, working_area=None):
        Operator.__init__(self, working_area)
        self.key = key
        self.value = value

    def act(self, seq):
        if len(seq) > 1:
            raise ValueError("FeatChangeOperator can now only change " +
                             "one machine as its input")
        if not isinstance(seq[0].control, KRPosControl):
            raise TypeError("Input machine of FeatChangeOperator can only " +
                            "have KRPosControl as its control")
        seq[0].control.kr[self.key] = self.value
        return [seq[0]]

class FeatCopyOperator(Operator):
    """
    Copies the specified feature from the KR POS control of one machine to the
    others. This Operator does not change the sequence.

    @note Does not support the copying of embedded (derivational) features.
    """
    def __init__(self, from_m, to_m, keys, working_area=None):
        """
        @param from_m the index of the machine whose features are copied.
        @param to_m the index of the machine whose control is updated.
        @param keys the names of the features to be copied.
        """
        Operator.__init__(self, working_area)
        self.from_m = from_m
        self.to_m   = to_m
        self.keys   = keys

    def act(self, seq):
        if not (isinstance(seq[self.from_m].control, KRPosControl) and
                isinstance(seq[self.to_m].control, KRPosControl)):
            raise TypeError("FeatCopyOperator can only work on machines with " +
                            "KRPosControl as their controls.")
        for key in self.keys:
            try:
                seq[self.to_m].control.kr[key] = \
                        seq[self.from_m].control.kr[key]
            except KeyError:
                pass
        return seq

class DeleteOperator(Operator):
    """Deletes the <tt>n</tt>th machine from the input sequence."""
    def __init__(self, n, working_area=None):
        Operator.__init__(self, working_area)
        self.n = n

    def act(self, seq):
        del seq[self.n]
        return seq

class AddArbitraryStringOperator(Operator):
    # TODO zseder: I wont implement this before talking to someone about
    # AppendOperator, these two should be integrated to one, maybe Operator
    # later will be changed to have working_area, so postponed until then
    def __init__(self, X, arbitrary_string, part=0, working_area=None):
        """
        @param X index of the machine to whose partition arbitrary_string will be appended.
        @param part the partition index.
        """
        Operator.__init__(self, working_area)
        self.X = X
        self.arbitrary_string = arbitrary_string
        self.part = part

    def act(self, seq):
        seq[self.X].append(self.arbitrary_string, self.part)
        return seq

class CreateBinaryOperator(Operator):
    """ Creates a binary machine and adds input machines to its partitions"""
    
    def __init__(self, what, first, second, working_area=None):
        # TODO type checking of what to be binary
        Operator.__init__(self, working_area)
        self.what = what 
        self.first = first
        self.second = second

    def act(self, seq):
        # HACK zseder: I will assume input of act as a sequence even though
        # I know this will be changed later, only in the sake of not seeming
        # LAZY
        m = Machine(self.what, ConceptControl(), 2)
        m.append(self.first, 0)
        m.append(self.second, 1)
        return [m]


###############################
###                         ###
### There be dragons ahead! ###
###                         ###
###############################


class FillArgumentOperator(Operator):
    """Fills the argument of the representation in the working area."""

    def __init__(self, case, working_area=None):
        Operator.__init__(self, working_area)
        self.case = case

    def act(self, arg_mach):
        logging.debug("FillArgOp acting on input {0} and working area {0}".format(arg_mach, self.working_area[0]))
        self._act(arg_mach, self.working_area[0])

    def _act(self, arg_mach, machine):
        """Recursive helper method for act()."""
        for part_ind, part in enumerate(machine.partitions):
            for submach_ind, submach in enumerate(part):
                if submach.printname() == self.case:
                    part[submach_ind] = arg_mach  # TODO unify
                else:
                    self._act(arg_mach, submach)

class ExpandOperator(Operator):
    """Expands an active machine."""
    def __init__(self, lexicon, working_area=None):
        """
        @param lexicon the lexicon.
        """
        Operator.__init__(self, working_area)
        self.lexicon = lexicon

    def act(self, input):
        """
        @param input the machine read by the transition.
        """
        logging.debug("ExpandOperator acting on input {0} and working area {0}".format(input, self.working_area[0]))
        self.lexicon.expand(input)
        self.working_area[0] = input

