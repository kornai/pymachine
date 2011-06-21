from monoid import Monoid

class Machine:
    def __init__(self, base):
        
        # control will be an FST representation later
        self.control = None
        
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
    
    def to_dot(self, toplevel=False):
        s = "subgraph"
        if toplevel:
            s = "graph"
        
        s += " cluster_{0}_{1} {{\n".format(self.base.partitions[0], id(self))
        s += "label={0};\n".format(self.base.partitions[0])
        
        if len(self.base.partitions) > 1:
            s += "color=black;\n"
            for p in reversed(self.base.partitions[1:]):
                s += "subgraph cluster_{0}_{1} {{\n".format(self.base.partitions[0], id(p))
                s += "label=\"\"\n"
                s += "color=lightgrey;\n"
                for m in reversed(p):
                    s += m.to_dot()
                s += "}\n"
        else:
            #s += "color=white;\n"
            s += "{0}[color=white, fontcolor=white];\n".format(self.base.partitions[0])
        s += "}\n"
        
        return s
