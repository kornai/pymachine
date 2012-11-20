"""Control class works as the control part of the machine
control does syntax-related things"""

import logging

import machine as mach
from langtools.utils.readkr import kr_to_dictionary as kr2dict

class Control(object):
    def __init__(self, machine=None):
        self.set_machine(machine)

    def set_machine(self, machine):
        """Sets the machine the control controls."""
        if not isinstance(machine, mach.Machine) and machine is not None:
            raise TypeError("machine should be a Machine instance")
        self.machine = machine

class PosControl(Control):
    def __init__(self, pos, machine=None):
        Control.__init__(self, machine)
        self.pos = pos

class KRPosControl(Control):
    def __init__(self, pos, machine=None):
        Control.__init__(self, machine)
        self.kr = kr2dict(pos)

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
                if m.printname() == 'BEFORE_AT':
                    before = m.base.partitions[2][0]
                elif m.printname() == 'AFTER_AT':
                    after = m.base.partitions[2][0]
            if before is not None and after is not None:
                logging.debug('Elvira message: {0} -> {1}'.format(before, after))
                return (self.plugin_url, [unicode(before), unicode(after)])

