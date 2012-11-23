"""Operator definitions."""
from machine import Machine
from monoid import Monoid
from control import KRPosControl, ConceptControl

class Operator(object):
    """The abstract superclass of the operator hierarchy."""
    def act(self, seq, working_area=None):
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

    def act(self, seq, working_area=None):
        seq[self.X].append(seq[self.Y], self.part)
        return [seq[self.X]]

class FeatChangeOperator(Operator):
    """ Changes one feature of input machines control, that is a dictionary
        representaion of a KR code
    """
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def act(self, seq, working_area=None):
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
    def __init__(self, from_m, to_m, keys):
        """
        @param from_m the index of the machine whose features are copied.
        @param to_m the index of the machine whose control is updated.
        @param keys the names of the features to be copied.
        """
        self.from_m = from_m
        self.to_m   = to_m
        self.keys   = keys

    def act(self, seq, working_area=None):
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

class AddArbitraryStringOperator(Operator):
    # TODO zseder: I wont implement this before talking to someone about
    # AppendOperator, these two should be integrated to one, maybe Operator
    # later will be changed to have working_area, so postponed until then
    def __init__(self, X, arbitrary_string, part=1):
        """
        @param X index of the machine to whose partition arbitrary_string will be appended.
        @param part the partition index.
        """
        self.X = X
        self.arbitrary_string = arbitrary_string
        self.part = part

    def act(self, seq, working_area=None):
        seq[self.X].append(self.arbitrary_string, self.part)
        return seq

class CreateBinaryOperator(Operator):
    """ Creates a binary machine and adds input machines to its partitions"""
    
    def __init__(self, what, first, second):
        # TODO type checking of what to be binary
        self.what = what 
        self.first = first
        self.second = second

    def act(self, seq, working_area=None):
        # HACK zseder: I will assume input of act as a sequence even though
        # I know this will be changed later, only in the sake of not seeming
        # LAZY
        m = Machine(Monoid(self.what, 2), ConceptControl())
        m.append(self.first, 1)
        m.append(self.second, 2)
        return [m]


###############################
###                         ###
### There be dragons ahead! ###
###                         ###
###############################


class FillArgumentOperator(Operator):
    """Fills the argument of the representation in the working area."""
    # TODO makrai
    def act(self, input, working_area=None):
        pass

class ExpandOperator(Operator):
    """Expands an active machine."""
    def __init__(self, lexicon):
        """
        @param lexicon the lexicon.
        """
        self.lexicon = lexicon

    def act(self, input, working_area=None):
        """
        @param input the machine read by the transition.
        @param working_area a list.
        """
        return self.lexicon.expand(input)
