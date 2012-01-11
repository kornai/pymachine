class Lexicon:
    """THE machine repository."""
    def __init__(self):
        pass

    def activate(self, already_active):
        """Finds and returns the machines that should be activated by the
        machines already active. The name is a bit misleading, since this
        method does not "activate" or instantiate the machines, only returns
        them.
        
        When exactly a machine should be activated is still up for
        consideration; however, currently this method returns a machine if
        all non-primitive machines on its partitions are active."""
        return []
