from monoid import Monoid
from control import Control

class Machine:
    def __init__(self, base, control=None):
        
        # control will be an FST representation later
        if not isinstance(control, Control) and control is not None:
            raise TypeError("control should be a Control instance")
        self.control = control
        
        # base is a monoid
        if not isinstance(base, Monoid):
            raise TypeError("base should be a Monoid instance")
        self.base = base
    
    def __str__(self):
        """
        Returns machine's "printname"
        """
        return str(self.base)
    
    def __eq__(self, other):
        return self.control == other.control and self.base == other.base
    
    def __hash__(self):
        return hash(id(self))

    def append(self, which_partition, what):
        self.base.append(which_partition, what)
    
    def to_dot(self, toplevel=False):
        s = u"subgraph"
        if toplevel:
            s = u"graph"
        
        s += u" cluster_{0}_{1} {{\n".format(self.base.partitions[0], id(self))
        s += u"label={0};\n".format(self.base.partitions[0])
        
        if len(self.base.partitions) > 1:
            s += "color=black;\n"
            for p in reversed(self.base.partitions[1:]):
                s += u"subgraph cluster_{0}_{1} {{\n".format(self.base.partitions[0], id(p))
                s += "label=\"\"\n"
                s += "color=lightgrey;\n"
                for m in reversed(p):
                    if isinstance(m, Machine):
                        s += m.to_dot()
                s += "}\n"
        else:
            #s += "color=white;\n"
            s += u"{0}[color=white, fontcolor=white];\n".format(self.base.partitions[0])
        s += "}\n"
        
        return s
