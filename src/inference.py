import re
import itertools

from machine import Machine
from monoid import Monoid
from itertools import chain

## -------------------------------- Conditions --------------------------------

class Condition(object):
    def __init__(self, attr_path, value):
        """Requires the attribute path as Attribute objects."""
        self.attr_path = attr_path
        self.value = value

    def holds(self, obj):
        """Checks if the attribute has the prescribed value in obj. Returns
        a pair. If the condition holds, the first element will be True and the
        second will be the machine at the bottom of the attribute path."""
        return self._holds(obj, self.attr_path, 0, obj)

    def _cmp(self, obj_value, true_value):
        """Compares the value the object has, and should have for the
        condition to hold. Subclasses must override this method. For the return
        value, see holds()."""
        raise NotImplementedError()

    def _holds(self, val, attrs, depth, curr_machine):
        """Recursively checks the condition in the graph. Required because we
        want to handle wildcard searches."""
        if len(attrs) == 0:
            return (self._cmp(val, self.value), curr_machine)
        else:
            new_vals = attrs[0].get(val)
            if new_vals is not None:
                for new_val in new_vals:
                    try:
                        next_machine = new_val if isinstance(new_val, Machine)\
                                               else curr_machine
                        ret_tup = self._holds(new_val, attrs[1:], depth + 1,
                                              next_machine)
                        if ret_tup[0]:
                            return ret_tup
                    except AttributeError:
                        # print "error"
                        pass
            return (False, None)

    @staticmethod
    def getInstance(type, attr_path, value):
        """Returns a condition object based on its string 'type' (=, ~, etc.)"""
        if type == '=':
            return EqualsCondition(attr_path, value)
        elif type == '~':
            return SubstringCondition(attr_path, value)
        else:
            return None

class EqualsCondition(Condition):
    """Checks the equality of values."""
    def _cmp(self, obj_value, true_value):
        return obj_value == true_value

class SubstringCondition(Condition):
    """Checks if the attribute contains the condition value as a substring."""
    def _cmp(self, obj_value, true_value):
        return obj_value.find(true_value) >= 0

## ------------------------------- AttributeElems ------------------------------

class AttributeElem(object):
    ARR_PATTERN  = re.compile(r"^(\w*)[[]([\d?]+)[]]$")

    """To make reflection easier... and perhaps slower."""
    def __init__(self, name):
        """Name: the name of the attribute."""
        self.name = name

    def get(self, obj):
        """Returns the value of the attribute in obj."""
        raise NotImplementedError()

    @staticmethod
    def analysePath(path):
        """Splits a path to a list of AttributeElems."""
        str_elems = [elem.strip() for elem in path.split('.')]
        attr_elems = []
        for elem in str_elems:
            m = AttributeElem.ARR_PATTERN.match(elem)
            if m is None:
                attr_elems.append(PrimitiveAttributeElem(elem))
            else:
                if m.group(2) == '?':
                    attr_elems.append(WildCardListAttributeElem(m.group(1)))
                else:
                    attr_elems.append(ListAttributeElem(m.group(1), m.group(2)))
        return attr_elems

class PrimitiveAttributeElem(AttributeElem):
    """obj.attr"""
    def get(self, obj):
        attr = getattr(obj, self.name)
        return [attr] if attr is not None else None

class ListAttributeElem(AttributeElem):
    """obj.attr[index]"""
    def __init__(self, name, index):
        """Name: the name of the attribute."""
        AttributeElem.__init__(self, name)
        self.index = int(index)

    def get(self, obj):
        attr = None
        if len(self.name) > 0:
            attr = getattr(obj, self.name)[self.index]
        else:
            attr = obj[self.index]
        return [attr] if attr is not None else None

class WildCardListAttributeElem(AttributeElem):
    """obj.attr[index]"""
    def __init__(self, name):
        """Name: the name of the attribute."""
        AttributeElem.__init__(self, name)

    def get(self, obj):
        attr = None
        if len(self.name) > 0:
            attr = getattr(obj, self.name)
        else:
            attr = obj
        return attr

## ---------------------------------- Actions ---------------------------------

class Action(object):
    """Action ancestor and factory. The format is action_name:param1,param2,
    ..."""
    ACT_PATTERN = re.compile(r"^(\w+?):(.+)$")

    def act(self, current, parent, machines):
        """Acts on the current object."""
        pass

    @staticmethod
    def getInstance(action):
        res = Action.ACT_PATTERN.match(action)
        if res is not None:
            if res.group(1) == 'rename':
                return RenameAction(res.group(2).split(',')[0])
        return None

## TODO: refactor and rename to ReplaceAction
class RenameAction(Action):
    """Renames the object to a pre-defined name. NOTE: this is a hack, it
    should really replace the machine with another and copy its properties.
    However, that only makes sense once we can look up machines in the
    lexicon."""
    def __init__(self, name):
        """Name: the new name of the object."""
        self.name = name

    def act(self, current, parent, machines):
        """Renames the current object."""
        current.base.partitions[0] = self.name

class ReplaceAction(Action):
    """Replaces a machine parameter with another in the graph; the indices are
    passed in the constructor. Cannot replace the root object."""
    # TODO: the root object should be replaceable as well.
    def __init__(self, old, new):
        self.old = old
        self.new = new

    def act(self, current, parent, machines):
        if max(self.old, self.new) < machines.length:
            self._replace(current, machines[self.old], machines[self.new])

    def _replace(self, current, m_from, m_to):
        for p in xrange(1, 3):
            for index, machine in enumerate(current.partitions[p]):
                if machine == m_from:
                    current.partitions[p][index] = m_to
                else:
                    self._replace(machine, m_from, m_to)

## -------------------------------- The engine --------------------------------

class FormatError(Exception):
    pass

class InferenceEngine(object):
    RULE_PATTERN = re.compile(r"^(.+) => (.+)$")
    COND_PATTERN = re.compile(r"^(.+) (=|~) (\w+)")

    def __init__(self):
        """Just to see that what members we have."""
        self.rules = []
    
    @staticmethod
    def _parse_premise(premise):
        """Parses the premise (condition) part of a rule and returns its
        representation."""
        pres = [pre.strip() for pre in premise.split(';')]
        conds = []
        for pre in pres:
            cresult = InferenceEngine.COND_PATTERN.match(pre)
            if cresult is None:
                raise FormatError, "Invalid premise: " + pre
            conds.append(Condition.getInstance(
                cresult.group(2),
                AttributeElem.analysePath(cresult.group(1)),
                cresult.group(3)))
        return conds

    def add_rule(self, premise, action):
        """Adds a rule to the engine. @premise is the string representation
        of the premise; @action is an object that implements the Action
        interface."""
        conds = InferenceEngine._parse_premise(premise)
        self.rules.append((conds, action))


    def load(self, rule_file):
        """Loads a set of rules to the engine from rule_file."""
        with open(rule_file, 'r') as rule_stream:
            for rule in rule_stream:
                rule = InferenceEngine.strip(rule)
                result = InferenceEngine.RULE_PATTERN.match(rule)
                if result is None:
                    continue
                action = Action.getInstance(result.group(2))
                self.add_rule(result.group(1), action)

    def infer(self, root):
        """Runs the inference on the object graph whose root is root."""
        self._visit(root, None)

    def _visit(self, current, parent):
        """Recursively visits all machines in the graph."""
        self.apply(current, parent)
        for machine in itertools.chain(*current.base.partitions[1:]):
            if machine is not None:
                self._visit(machine, current)

    def apply(self, current, parent):
        """Applies all possible rules to the current object."""
        print (u"Before: " + current.base.partitions[0]).encode('utf-8')
        for rule in self.rules:
            matches = True
            cond_res = []  # The results of the condition checks
            for cond in rule[0]:
                cond_res.append(cond.holds(current))
                if not cond_res[-1][0]:
                    matches = False
                    break
            if matches:
                rule[1].act(current, parent, [cond[1] for cond in cond_res])
        print (u"After: " + current.base.partitions[0]).encode('utf-8')

    @staticmethod
    def strip(line):
        """Strips all whitespaces from around the content and removes
        comments as well."""
        ## TODO: encoding
        hashmark = line.find("#")
        if hashmark >= 0:
            line = line[hashmark:]
        return line.strip()

## ----------------------------------- Test -----------------------------------

if __name__ == '__main__':
    from control import PosControl

    i = InferenceEngine()
    import sys
    i.load(sys.argv[1])
#    class C(object):
#        def __init__(self):
#            self.x = "3"
#            self.y = []
#            self.y.append("11")
#            self.y.append("22")
#            self.y.append("33")
#
#    class D(object):
#        def __init__(self, c):
#            self.x = c
#
#    c = C()
#    d = D(c)
#
#    i = InferenceEngine()
#    import sys
#    i.load(sys.argv[1])
#    i.apply(d)

    # a sa1rga printnevu3 ge1p
    sarga = Machine(Monoid("sa1rga"))
    # sarga.control == None, me1g nincs szo1faj
    # sarga.base == Monoid("sarga"), az a pe1lda1ny
    
    # ke1k ge1p ugyani1gy
    kek = Machine(Monoid("ke1k"))
    
    kocka = Machine(Monoid("kocka"))
    # a 0. parti1cio1 a printname, kell egy elso3 parti1cio1
    kocka.base.partitions.append([])
    kocka.base.partitions[1].append(sarga)
    # legyen egy szofaja is, ez most string, ke1so3bb FSx
    kocka.control = PosControl("NOUN<ACC>")
    
    gomb = Machine(Monoid("go2mb"))
    gomb.base.partitions.append([])
    gomb.base.partitions[1].append(kek)
    gomb.control = PosControl("NOUN<SBL>")
    
    on = Machine(Monoid("AT"))
    on.base.partitions.append([])
    on.base.partitions.append([])
    on.base.partitions[1].append(kocka)
    on.base.partitions[2].append(gomb)
    
    put = Machine(Monoid("CAUSE/AFTER"))
    put.base.partitions.append([])
    put.base.partitions.append([])
    put.base.partitions[1].append(None) # NOM
    put.base.partitions[2].append(on)
    
    i.infer(put)

    behind = Machine(Monoid("behind"))
    behind.base.partitions.append([])
    behind.base.partitions.append([])
    behind.base.partitions[1].append(kocka)

    at = Machine(Monoid("AT"))
    at.base.partitions.append([])
    at.base.partitions.append([])
    at.base.partitions[1].append(kocka)
    at.base.partitions[2].append(behind)
    
    i.infer(put)
    print "-----------------"
    i.infer(at)
