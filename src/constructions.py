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
import re

class Construction:
    def __init__(self, rule_left, rule_right, command):
        self.rule_left = rule_left
        self.rule_right = [Control(part) for part in rule_right]
        self.command = command

        self.empty_rule_p = re.compile("|".join(rule_right))
        self.append_rule_p = re.compile("([^\[]*)\[([^\]]*)\]")

    def __match__(self, machines):
        if len(machines) != len(self.rule_right):
            return False

        possible_pairs = {}
        for machine in machines:
            pair_for_machine = []
            for c in self.rule_right:
                if machine.control.is_a(c):
                    pair_for_machine.append(c)
            possible_pairs[machine] = pair_for_machine
        
        pairs = {}
        for m, pp in possible_pairs.items():
            if len(pp) > 1:
                raise NotImplementedError("Now only definite matches (only 1-1) are supported")
            elif len(pp) == 0:
                return False
            else:
                """if two machines match the same rule, then it's not
                a real match"""
                if m in pairs.values():
                    return False
                pairs[pp[0]] = m

        """if there is no mapping for each part of the rule, then it's not
        a real match"""
        if len(pairs) != len(self.rule_right):
            return False

        return pairs

    def do(self, machines):
        pairs = self.__match__(machines)
        if not pairs:
            return None
        else:
            return self.run_command(pairs)

    def run_command(self, pairs):
        """
        WARNING
        there is only one command implemented: A[B]
        later there should be more, with a more sophisticated impl.
        or at least with a bunch of regexps instead of one
        """

        # Do nothing rule handling
        machines = []
        em = self.empty_rule_p.match(self.command)
        if em is not None:
            for control, machine in pairs.items():
                if Control(em.group(0)) == control:
                    machines.append(machine)
            return machines

        # Append rule handling
        am = self.append_rule_p.match(self.command)
        if am is not None:
            l = Control(am.groups()[0])
            r = Control(am.groups()[1])
            pairs[l].append(1, pairs[r])
            machines.append(pairs[l])
        else:
            raise NotImplementedError("Rule not supported")
        print machines
        return machines

def read_constructions(f):
    constructions = set()
    for l in f:
        l = l.strip().split("\t")
        constructions.add(Construction(l[0], l[1].split(), l[2]))
    return constructions

if __name__ == "__main__":
    pass

