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

class Construction:
    def __init__(self, rule_left, rule_right, command):
        self.rule_left = rule_left
        self.rule_right = [Control(part) for part in rule_right]
        self.command = command

    def __match__(self, machines):
        if len(machines) != self.rule_right:
            return False
        # TODO
        # use Control class to determine if they are matching
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
        if not self.__match__(machines):
            return None

def read_constructions(f):
    constructions = set()
    for l in f:
        l = l.strip().split("\t")
        constructions.add(Construction(l[0], l[1].split(), l[2]))
    return constructions

if __name__ == "__main__":
    pass

