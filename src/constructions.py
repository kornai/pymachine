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
from control import Control
import re

class Construction:
    def __init__(self, rule_left, rule_right, command):
        self.rule_left = rule_left
        self.rule_right = [Control(part) for part in rule_right]
        self.command = command

        self.append_rule_p = re.compile("([^\[]*)\[([^\]]*)\]")

    def __match__(self, machines):
        if len(machines) != self.rule_right:
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
            if len(pp) != 1:
                raise NotImplementedError("Now only definite matches (only 1-1) are supported")
            else:
                pairs[pp[0]] = m
        return pairs

    def do(self, machines):
        pairs = self.__match__(machines)
        if not pairs:
            return None
        else:
            self.run_command(pairs)

    def run_command(self, pairs):
        """
        WARNING
        there is only one command implemented: A[B]
        later there should be more, with a more sophisticated impl.
        or at least with a bunch of regexps instead of one
        """
        m = self.append_rule_p.match(self.command)
        if m is not None:
            l = m.groups()[0]
            r = m.groups()[1]
            pairs[l].base.partitions[1].append(pairs[r])
        else:
            raise NotImplementedError("Rule not supported")

def read_constructions(f):
    constructions = set()
    for l in f:
        l = l.strip().split("\t")
        constructions.add(Construction(l[0], l[1].split(), l[2]))
    return constructions

if __name__ == "__main__":
    pass

