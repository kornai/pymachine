class UnknownWordException(Exception):
    pass

class UnknownSentenceException(Exception):
    pass

class TooManyArgumentsException(Exception):
    def __init__(self, m):
        self._machines = m

class CaseAmbiguityException(Exception):
    def __init__(self, m):
        self._ambiguate_machines = m

class LocationAmbiguityException(Exception):
    def __init__(self, m):
        self._ambiguate_machines = m
