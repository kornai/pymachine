from constants import deep_cases

class Lexicon:
    """THE machine repository."""
    def __init__(self):
        self.deep_cases = set(deep_cases)  # Set of deep cases

    def add_active(self, machines):
        """
        adds machines to active collection
        typically called to add a sentence being worked with
        """

    def add_static(self, machines):
        """
        adds machines to static collection
        typically called once to add whole background knowledge
        which is the input of the definition parser
        """

    def activate(self, already_active):
        """Finds and returns the machines that should be activated by the
        machines already active. The name is a bit misleading, since this
        method does not "activate" or instantiate the machines, only returns
        them.
        
        When exactly a machine should be activated is still up for
        consideration; however, currently this method returns a machine if
        all non-primitive machines on its partitions are active."""
        return []

