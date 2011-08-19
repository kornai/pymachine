"""
Construction class and related functions are to represent constructions
given in a grammar-like syntax. With them, one can
- change/set relations between machines
- ???

TODO:
- matching based on Control class
- do() function to make the changes implied by @command
- unique S construction whose rule is distinguished from any others
  - lookup the Verb in construction in definition collection
  - use Nouns and their deep cases in construction to insert them into
    the verb machine
"""
from control import PosControl as Control

class Command:
    """
    Abstract class for commands in constructions
    """

    def run(self, pairs):
        """
        @pairs if a mapping between Control and Machine instances
        keys of @pairs are Control instances,
        values of @pairs are Machine instances.

        runs the command over the machines
        returns None if there is nothing to be changed,
        otherwise a new machine list
        """
        pass

    @staticmethod
    def get_instance(type_str, terminals, definitions):
        """
        Factory method
        """
        import re
        append_regex_pattern = re.compile("([^\[]*)\[([^\]]*)\]")
        m = append_regex_pattern.match(type_str)
        if m is not None:
            return AppendRegexCommand(m.groups()[0], m.groups()[1])

        one_rule_pattern = re.compile("|".join(terminals))
        m = one_rule_pattern.match(type_str)
        if m is not None:
            return OneCommand(m.group(0))

        if type_str == "*":
            return VerbCommand(definitions)

        if type_str == "?":
            return QuestionCommand()


class AppendRegexCommand(Command):
    """
    Appends one of the machines at a partition of the other one
    used for cube[yellow]-like expressions
    """
    def __init__(self, into, what):
        self.into = Control(into)
        self.what = Control(what)

    def run(self, pairs):
        into = [m for i,c,m in pairs if c == self.into][0]
        what = [m for i,c,m in pairs if c == self.what][0]
        into.append(1, what)
        return [into]

class OneCommand(Command):
    """
    Removes one from the machines. The other is kept.
    used for DETs for example
    """
    def __init__(self, stay):
        self.stay = Control(stay)

    def run(self, pairs):
        filterer = lambda a: a[1] == self.stay
        return [m for _, _, m in filter(filterer, pairs)]

class FinalCommand(Command):
    pass

class VerbCommand(FinalCommand):
    """
    The machine of the verb is looked up in the defining dictionary,
    and any deep cases found in that machine get matched with NP cases
    """
    def __init__(self, definitions):
        self.definitions = dict([((k[0],k[1]), v) for k,v in definitions.items()])
    
    @classmethod
    def is_imp(m):
        return m.is_a(Control("VERB<SUBJUNC-IMP>"))

    def run(self, pairs):
        verb_machine = [m for _,c,m in pairs if c == Control("VERB")][0]

        done = [verb_machine]

        # if we make a change in the verb_machine, the original machine can't be changed
        # so copy it first
        from copy import deepcopy as copy
        defined_machine = copy(self.definitions[(str(verb_machine), "V")])

        # discover known cases to be used when filling slots
        known_cases = [(m.control.get_case(),m) for _, _, m in pairs if m != verb_machine]
        known_cases = dict(filter(lambda x: x[0] is not None, known_cases))

        # filling known cases
        for c, m in known_cases.items():
            # TODO insert m into defined_machine somehow
            # WARNING HACK: ACC machine position is hacked into the code ritht now
            if c == defined_machine.base.partitions[1][0].base.partitions[2][0].base.partitions[1][0].base.partitions[0]:
                defined_machine.base.partitions[1][0].base.partitions[2][0].base.partitions[1][0] = m
                done.append(m)

        # if we have done everything, then we have done everything
        if len(done) == len(pairs):
            return [defined_machine]

        # if there is one unknown, it can be guessed
        if len(pairs) - len(done) == 1:
            # search for an empty place for the one left
            left = [m for _,_,m in pairs if m not in done][0]
            # TODO how to search for empty places
            # WARNING: this is just hacked right now
            defined_machine.base.partitions[1][0].base.partitions[2][0].base.partitions[2].append(left)

        # else we do not know what to do
        else:
            from machine_exceptions import UnknownSentenceException
            raise UnknownSentenceException("empty slots cannot be filled without guessing")

        # TODO think it through
        # now CAUSE is at first partition of put, but it should be instead of it?
        return [defined_machine.base.partitions[1][0]]

class QuestionCommand(FinalCommand):
    def run(self, pairs):
        from machine import Machine
        from monoid import Monoid
        final_machine = Machine(Monoid("AT"))
        final_machine.append(1, pairs[-1][2])
        final_machine.append(2, pairs[0][2])
        return [final_machine]

class Construction:
    """
    instructions about how to perform transformations in machines
    """

    def __init__(self, rule_left, rule_right, command, definitions):
        """
        @rule_left: now this is used for changing control of resulting machine
          if some change has been made
        @rule_right: on what machines to perform operations, based on their Control
        @command: what to do
        """
        self.rule_left = rule_left
        self.rule_right = [Control(part) for part in rule_right]
        self.command = Command.get_instance(command, rule_right, definitions)

    def __match__(self, machines):
        """
        checks if the given @machines are possible inputs for this construction
        uses only @self.rule_right

        returns False if not matched
        returns a dictionary with (control, machine) pairs
        """
        if len(machines) != len(self.rule_right):
            return False

        pairs = []
        for control_index, machine in zip(xrange(len(self.rule_right)), machines):
            c = self.rule_right[control_index]
            if machine.control.is_a(c):
                pairs.append((control_index, c, machine))
            else:
                return False
        return pairs

    def change_main_control(self, machines):
        """
        hack function
        put self.rule_left into the control of the first machine
        """
        if machines[0].control is None:
            return
        old_pos = machines[0].control.pos
        if old_pos.startswith("NOUN") and len(old_pos) >= 6:
            machines[0].control = Control(self.rule_left + "<" + old_pos.split("<", 1)[1])
        else:
            machines[0].control = Control(self.rule_left)


    def do(self, machines):
        """
        run construction over the machines and return None if nothing is changed
        otherwise return transformed machine
        """
        pairs = self.__match__(machines)
        if not pairs:
            return None
        else:
            transformed = self.command.run(pairs)
            self.change_main_control(transformed)
            return transformed

def read_constructions(f, definitions=None):
    """
    TODO maybe a factory?
    """
    constructions = set()
    for l in f:
        l = l.strip().split("\t")
        constructions.add(Construction(l[0], l[1].split(), l[2], definitions))
    return constructions

if __name__ == "__main__":
    pass

