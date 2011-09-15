class NoAnalysisException(Exception):
    pass
class UnknownWordException(Exception):
    pass

class UnknownSentenceException(Exception):
    pass

class TooManyArgumentsException(Exception):
    def __init__(self, m):
        self.machines = m

class TooManySameCasesException(Exception):
    def __init__(self, m, case):
        self.ambiguate_machines = m
        self.case = case

class TooManyLocationsException(Exception):
    def __init__(self, m):
        self.ambiguate_machines = m
