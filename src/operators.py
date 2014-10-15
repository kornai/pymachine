"""Operator definitions."""

import logging

from pymachine.src.control import KRPosControl

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
        self.to_m = to_m
        self.keys = keys

    def act(self, seq):
        if not (isinstance(seq[self.from_m].control, KRPosControl) and
                isinstance(seq[self.to_m].control, KRPosControl)):
            raise TypeError("FeatCopyOperator can only work on machines " +
                            "with KRPosControl as their controls.")
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
        @param X index of the machine to whose partition arbitrary_string will
        be appended.
        @param part the partition index.
        """
        Operator.__init__(self, working_area)
        self.X = X
        self.arbitrary_string = arbitrary_string
        self.part = part

    def act(self, seq):
        seq[self.X].append(self.arbitrary_string, self.part)
        return seq

class AppendToBinaryOperator(Operator):
    """appends two machines to the partitions of a binary relation"""

    def __init__(self, bin_rel, first_pos, second_pos, working_area=None):
        # TODO type checking of what to be binary
        Operator.__init__(self, working_area)
        self.bin_rel = bin_rel
        self.first_pos = first_pos
        self.second_pos = second_pos

    def __str__(self):
        return "{0}({1}, {2})".format(
            self.bin_rel, self.first_pos, self.second_pos)

    def act(self, seq):
        self.bin_rel.append(seq[self.first_pos], 1)
        self.bin_rel.append(seq[self.second_pos], 2)
        return [self.bin_rel]


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
        logging.debug(
            "FillArgOp acting on input {0} and working area {1}".format(
                arg_mach, self.working_area[0]))
        self.seen_by_act = set()
        self._act(arg_mach, self.working_area[0])

    def _act(self, arg_mach, machine):
        """Recursive helper method for act()."""
        if machine.printname() in self.seen_by_act:
            return
        else:
            self.seen_by_act.add(machine.printname())

        logging.debug(
            "FillArgOp _acting on input {0} and working area {1}".format(
                arg_mach, machine))
        logging.debug(
            'working area partitions: {0}'.format(machine.partitions))
        success = False
        for part_ind, part in enumerate(machine.partitions):
            for submach_ind, submach in enumerate(part):
                if submach.printname() == self.case:
                    logging.info('Filling argument {0} of {1} with {2}'.format(
                        self.case, machine, arg_mach))
                    arg_mach.unify(submach)
                    part[submach_ind] = arg_mach  # TODO unify
                    success = True
                    break
                else:
                    self._act(arg_mach, submach)
            if success:
                break

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
        logging.debug(
            "ExpandOperator acting on input {0} and working area {0}".format(
                input, self.working_area[0]))
        self.lexicon.expand(input)
        self.working_area[0] = input
