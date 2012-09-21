"""Attribute-value matrix."""

from matcher import Matcher

class AVM(object):
    TYPE, REQUIRED, DEFAULT, VALUE = xrange(4)

    def __init__(self, name):
        self.name = name
        self.__data = {}  # {key: [type, required, default_value, value]}

    def add_attribute(self, key, datatype, required=False, default_value=None):
        """Adds a new attribute to the "matrix"."""
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

    def get_attribute(self, key):
        """Returns the whole attribute data tuple for @p key."""
        return self.__data[key]

    def get_field(self, key, field):
        """
        Returns the specified field from the data tuple for @p key. The valid
        values for @p field are @c TYPE, @c REQUIRED, @c DEFAULT and @c VALUE.
        """
        return self.__data[key][field]

    def get_dict(self):
        """Returns the attribute-value dictionary in a Python dict."""
        return dict((k, v[AVM.VALUE]) for k, v in self.__data.iteritems())

    def __getitem__(self, key):
        """Gets the current value of an attribute."""
        return self.__data[key][AVM.VALUE]

    def __setitem__(self, key, value):
        """Sets the current value of an attribute."""
        self.__data[key][AVM.VALUE] = value

    def __iter__(self):
        """Iterates through the attribute keys."""
        return self.__data.__iter__()

    def __unicode__(self):
        return u'{' + u', '.join(u'{0}: {1}'.format(key, self[key]) for key in self) + u'}'

