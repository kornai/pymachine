from machine import Machine
from monoid import Monoid
from control import PosControl as Control

class SentenceParser:
    """
    This class will create machines from analyzed and chunked text
    """
    def __init__(self):
        pass

    def create_machines_from_chunk(self, chunk):
        """
        builds up a structure of machines that represents the whole chunk
        TODO:
            - right now we only handle 1-length chunks so this method will
              be implemented later
            - return list or Machine instance?
        """
        if len(chunk) > 1:
            raise Exception("""SentenceParser.create_machines_from_chunk()
                            is now implemented for only 1-length chunks""")
        else:
            only_token = chunk[0]
            surface, stem, analysis = only_token
            return Machine(Monoid(stem), Control(analysis))

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
            if len(token_or_chunk) == 2:
                chunk, case = token_or_chunk
                m = self.create_machines_from_chunk(chunk)
                m.append_if_not_there(case)
                machines.append(m)
            else:
                token = token_or_chunk
                surface, stem, analysis = token
                machines.append(Machine(Monoid(stem), Control(analysis)))
        return machines

if __name__ == "__main__":
    pass


