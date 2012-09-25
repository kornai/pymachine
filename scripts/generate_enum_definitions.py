"""Script that creates enumerations in definition format.

Usage: python generate_enum_definitions arg1 arg2
- arg1: file with enum members, one per line
- arg2: enum name

Output is written to stdout, and can be used as input for
definition parser
"""

import sys

def main():
    enum_file_name = sys.argv[1]
    enum_name = sys.argv[2]
    enum_file = open(enum_file_name)
    enum_members = set([l.strip().decode("utf-8")
                        for l in enum_file.read().split("\n")])
    for member in enum_members:
        print u"42 # N {0} # #: IS_A {1}".format(member,
            enum_name).encode("utf-8")

if __name__ == "__main__":
    main()
