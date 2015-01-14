from pymachine.src.machine import Machine
from pymachine.src.control import KRPosControl as Control

class SentenceParser:
    """This class will create machines from analyzed and chunked text"""

    def parse(self, sentence):
        """
        input sentence is a list of tokens and chunk in the following format:
            [(token1_tag1, token1_tag2, token1_tagX, ...),
             ([(tokeninchunk1_tag1, tokeninchunk1_tagX,...),
               ...
              ], case_of_chunk),
             (token_out_of_chunk_again_tagX,...),
             ...
            ]
        output is a list of machines
        """
        machines = []
        for token_or_chunk in sentence:
            # chunk or token?
            if type(token_or_chunk[0]) == list:
                # chunk
                chunk, _ = token_or_chunk
                machines.append([Machine(analysis.split("/")[0], Control(analysis)) 
                                 for _, analysis in chunk])
            else:
                # token
                token = token_or_chunk#[0]
                print 'token:', token
                _, analysis = token
                machines.append([Machine(analysis.split("/")[0], Control(analysis))])
        return machines

if __name__ == "__main__":
    pass


