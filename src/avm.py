"""Attribute-value matrix."""

from matcher import Matcher

class AVM(object):
    TYPE, REQUIRED, DEFAULT, VALUE = xrange(4)

    def __init__(self):
        self.__data = {}  # {key: [type, required, default_value, value]}

    def add_field(self, key, datatype, required=False, default_value=None):
        if not isinstance(required, bool):
            raise ValueError("required must be a bool, not " + type(required))
        if not isinstance(datatype, Matcher):
            raise ValueError("datatype must be a Matcher, not " +
                             type(datatype))
        self.__data[key] = [datatype, required, default_value, default_value]
        # TODO: do we need a default_value?

    def __getitem__(self, key):
        return self.__data[key][AVM.VALUE]

    def __setitem__(self, key, value):
        self.__data[key][AVM.VALUE] = value

