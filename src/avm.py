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

    def satisfied(self):
        """Returns @c True, if all required arguments are filled in."""
        for value in self.__data.values():
            if value[AVM.REQUIRED] and value[AVM.VALUE] is None:
                return False
        else:
            return True

    def __getitem__(self, key):
        """Gets the current value of an attribute."""
        return self.__data[key][AVM.VALUE]

    def __setitem__(self, key, value):
        """Sets the current value of an attribute."""
        self.__data[key][AVM.VALUE] = value

    def __iter__(self):
        return self.__data.__iter__()
