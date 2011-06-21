def read_constructions(f):
    constructions = set()
    for l in f:
        l = l.strip().split("\t")
        constructions.add(tuple(l))
    return constructions

if __name__ == "__main__":
    pass

