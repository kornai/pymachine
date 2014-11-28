import logging

def jaccard(seq1, seq2, log=False):
    set1, set2 = map(set, (seq1, seq2))
    union = set1 | set2
    intersection = set1 & set2
    if not intersection:
        return 0
    else:
        sim = float(len(intersection)) / len(union)
        if log:
            logging.info(u'set1: {0}, set2: {1}'.format(set1, set2))
            logging.info(u'shared: {0}'.format(intersection))
            logging.info('sim: {0}'.format(sim))
        return sim
