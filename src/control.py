"""
Control class works as the control part of the machine
control does syntax-related things

TODO
now it's implemented to use only strings as pos tags
later control should be an FST
"""

import re
import logging

import machine as mach
from constants import deep_cases

class Control(object):
    def __init__(self, machine=None):
        self.set_machine(machine)

    def __hash__(self):
        pass

    def __eq__(self, other):
        pass

    def __cmp__(self, other):
        pass

    def is_a(self, other):
        if not isinstance(other, Control):
            raise Exception("Control can be compared only with other Control")

    def set_machine(self, machine):
        """Sets the machine the control controls."""
        if not isinstance(machine, mach.Machine) and machine is not None:
            raise TypeError("machine should be a Machine instance")
        self.machine = machine

class PosControl(Control):
    noun_pattern = re.compile("^N(OUN|P)")
    case_pattern = re.compile("N(OUN|P)[^C]*CAS<([^>]*)>")

    def __init__(self, pos, machine=None):
        Control.__init__(self, machine)
        self.pos = pos

    def __hash__(self):
        return hash(self.pos)

    def __eq__(self, other):
        return self.pos.__eq__(other.pos)

    def __cmp__(self, other):
        return self.pos < other.pos

    def is_a(self, other):
        """now only checks if self is a "type" of @other
        """

        # first call super.is_a
        Control.is_a(self, other)

        # check if "is_a" with a dumb regexp
        is_a_pattern = re.compile(other.pos)
        if is_a_pattern.search(self.pos) is not None:
            return True
        else:
            return False

    def get_case(self):
        """returns self's case if self.case_pattern has a match
        None otherwise
        """
        if PosControl.noun_pattern.search(self.pos) is not None:
            s = PosControl.case_pattern.search(self.pos)
            if s is not None:
                return s.groups()[1]
            else:
                # if NOUN/NP has no case, it should be a NOM
                return "NOM"
        else:
            return None

class FstControl(PosControl):
    def __init__(self, pos, machine=None):
        Control.__init__(self, machine)
        self.pos = pos

    def is_a(self, other):
        return PosControl.is_a(other)

class PluginControl(Control):
    """Control for plugin machines."""
    def __init__(self, plugin_url, machine=None):
        Control.__init__(self, machine)
        self.plugin_url = plugin_url

    # TODO: implement is_a, etc.

    def message(self):
        #TODO: rename
        """Compiles a message to the plugin the machine is representing. If the
        data is not yet ready (there is required argument not yet filled), this
        method returns @c None."""
        pass

class ElviraPluginControl(PluginControl):
    """Plugin control for the Elvira plugin."""
    def __init__(self, machine=None):
        PluginControl.__init__(self, 'plugin.Elvira', machine)

    def message(self):
        if self.machine is not None:
            prt = self.machine.base.partitions[1]
            before, after = None, None
            for m in prt:
                if str(m) == 'BEFORE_AT':
                    before = m.base.partitions[2][0]
                    if before in deep_cases:
                        before = None
                elif str(m) == 'AFTER_AT':
                    after = m.base.partitions[2][0]
                    if after in deep_cases:
                        after = None
            if before is not None and after is not None:
                logging.debug('Elvira message: {0} -> {1}'.format(before, after))
                return (self.plugin_url, [before, after])

