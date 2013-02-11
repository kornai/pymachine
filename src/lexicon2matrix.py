# TODO add lines for triplet to matrix
# TODO distinguish the partiion of a unary machine from the first partition of a binary machine?


from collections import defaultdict
from definition_parser import read
import sys

try: 
    lexfile = open(sys.argv[1])
    mxfile = open(sys.argv[2], mode='w')
    indexfile = open(sys.argv[3], mode='w')
except:
    raise(Exception('Usage: '+sys.argv[0]+' mxfile indexfile'))

lex_dict = read(lexfile,2) # 2: English printnames
mx_dict = defaultdict(lambda: defaultdict(int))
lines = set()


def add_mach(definiendum, machine, visited):
    if machine in visited:
        return
    visited.add(machine)
    lines.add(machine.printname())
    for part_ind in xrange(len(machine.partitions)):
        for sub in machine.partitions[part_ind]:
            if machine.printname() == definiendum:
                triplet = sub.printname()
            else:
                if part_ind == 0:
                    triplet = sub.printname() + ' ' + machine.printname()

                else:
                    triplet = machine.printname() + ' ' + sub.printname()
                mx_dict[triplet]['partition' +str(part_ind + 1)] = 1
                for column in [sub.printname(), machine.printname()]:
                    mx_dict[triplet][column] = 1
            mx_dict[definiendum][triplet] += 1
            lines.add(triplet)
            lines.add(machine.printname())
            add_mach(definiendum,sub, visited)
    for  part_ind in xrange(2):
        lines.add('partition' +str(part_ind + 1))

if __name__ == "__main__":
    for printname, machine in lex_dict.items():
        visited = set()
        add_mach(printname, machine, visited)
    
    for index, definiendum in enumerate(lines):
        indexfile.write(str(index+1)+'\t'+definiendum+'\n')
        for defining in lines:
            mxfile.write(str(mx_dict[definiendum][defining])+' ')
        mxfile.write('\n')
    
