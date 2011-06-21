class Monoid:
    """
    Our monoid class
    """
    
    def __init__(self, name):
        self.partitions = []
        self.partitions.append(name)
        
        self.operations = None
        self.unit = None
        self.distinguished_partition = None
    
    def __str__(self):
        return self.partitions[0]
    
    def __eq__(self, other):
        return (self.partitions == other.partitions and
                self.operations == other.operations and
                self.unit == other.unit and
                self.distinguished_partition == other.distinguished_partition)