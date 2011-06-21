import sys

def read_order_file(f):
    sentence = []
    for line in f:
        le = line.strip().split("\t")
        if len(le) == 0:
            break
        else:
            sentence.append(tuple(le))
    return sentence

if __name__ == "__main__":
    pass

