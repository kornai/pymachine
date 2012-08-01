"""Control class works as the control part of the machine
control does syntax-related things"""

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

    def set_machine(self, machine):
        """Sets the machine the control controls."""
        if not isinstance(machine, mach.Machine) and machine is not None:
            raise TypeError("machine should be a Machine instance")
        self.machine = machine

class PosControl(Control):
    def __init__(self, pos, machine=None):
        Control.__init__(self, machine)
        self.pos = pos

    def __hash__(self):
        return hash(self.pos)

    def __eq__(self, other):
        return self.pos.__eq__(other.pos)

    def __cmp__(self, other):
        return self.pos < other.pos

    def __str__(self):
        return self.pos

class ConceptControl(Control):
    """object controlling machines that were not in the sentence, but
    in the main lexicon"""

class PluginControl(Control):
    """Control for plugin machines."""
    def __init__(self, plugin_url, machine=None):
        Control.__init__(self, machine)
        self.plugin_url = plugin_url

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

