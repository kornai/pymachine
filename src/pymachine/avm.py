"""Attribute-value matrix."""

from matcher import Matcher
from pymachine.machine import Machine
from pyparsing import *
import logging

class AVM(object):
    TYPE, REQUIRED, DEFAULT, VALUE = xrange(4)
    RREQ, ROPT, RNEG = xrange(1, -2, -1)

    def __init__(self, name):
        self.name = name
        self.__data = {}  # {key: [type, required, default_value, value]}
        self.bool_expr = None
        self.bool_str = None

    def add_attribute(self, key, datatype, required=ROPT, default_value=None):
        """
        Adds a new attribute to the "matrix".
        @param required can take three values:
               RREQ: required,
               ROPT: optional,
               RNEG: must not to be filled.
        """
        if required not in [AVM.RREQ, AVM.ROPT, AVM.RNEG]:
            raise ValueError("required must be one of RREQ, ROPT, RNEG, not " +
                             repr(required))
        if not isinstance(datatype, Matcher):
            raise ValueError("datatype must be a Matcher, not " +
                             type(datatype))
        self.__data[key] = [datatype, required, default_value, default_value]

    def printname(self):
        return self.name

    def set_satisfaction(self, bool_str):
        self.bool_str = bool_str

        boolOperand = Word(alphas + '_') | oneOf("True False")
        self.bool_expr = operatorPrecedence( boolOperand,
            [
            ("not", 1, opAssoc.RIGHT, self.notop),
            ("or",  2, opAssoc.LEFT,  self.orop),
            ("and", 2, opAssoc.LEFT,  self.andop),
            ])

    def satisfied(self):
        """Returns @c True, if all required arguments are filled in."""
        if self.bool_expr is not None:
            return self.bool_expr.parseString(self.bool_str)[0]
        else:
            for value in self.__data.values():
                if ((value[AVM.REQUIRED] == AVM.RREQ and value[AVM.VALUE] is None)
                    or
                    (value[AVM.REQUIRED] == AVM.RNEG and value[AVM.VALUE] is not None)):
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
        ret = dict((k, v[AVM.VALUE]) for k, v in self.__data.iteritems())
        ret['__NAME__'] = self.name
        return ret

    def get_basic_dict(self):
        """
        Returns the attribute-value dictionary in a Python dict, all Machine
        values replaced by their printnames.
        """
        ret = self.get_dict()
        for k, v in ret.iteritems():
            if isinstance(v, Machine):
                ret[k] = unicode(v)
        return ret

    def clear(self):
        keys = self.__data.keys()
        for key in keys:
            datatype, required, default_value, _ = self.__data[key]
            self.__data[key] = [datatype, required, default_value, default_value]

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
    
    # -------------------------- bool functions for satisfied() ----------------

    def andop(self, t):
        args = t[0][0::2]
        for a in args:
            if isinstance(a,basestring):
                if a in set(['True', 'False']):
                    v = bool(a)
                else:
                    v = self[a] is not None
            else:
                v = bool(a)
            if not v:
                return False
        return True

    def orop(self, t):
        args = t[0][0::2]
        for a in args:
            if isinstance(a,basestring):
                if a in set(['True', 'False']):
                    v = bool(a)
                else:
                    v = self[a] is not None
            else:
                v = bool(a)
            if v:
                return True
        return False

    def notop(self, t):
        arg = t[0][1]
        if isinstance(arg,basestring):
            if arg in set(['True', 'False']):
                v = bool(arg)
            else:
                v = self[arg] is not None
        else:
            v = bool(arg)
        return not v

