import logging

from machine import Machine
from monoid import Monoid
from control import PosControl as Control

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
            if len(token_or_chunk) == 2:
                # chunk
                chunk, case = token_or_chunk
                for token in chunk:
                    surface, stem, analysis = token
                    machines.append(Machine(Monoid(stem), Control(analysis)))
            else:
                # token
                token = token_or_chunk
                surface, stem, analysis = token
                machines.append(Machine(Monoid(stem), Control(analysis)))
        return machines

if __name__ == "__main__":
    pass


