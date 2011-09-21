import socket
import os
import logging
config_filename = "machine.cfg"

class Wrapper:
    def __init__(self, cf=config_filename):
        self.cfn = cf
        self.__read_config()
        self.__read_files()

    def __read_config(self):
        import ConfigParser
        try:
            machinepath = os.environ['MACHINEPATH']
        except KeyError:
            logging.critical('MACHINEPATH environment variable not set!')
            sys.exit(-1)
        config = ConfigParser.SafeConfigParser({'machinepath':machinepath})
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_fn = items["definitions"]
        self.con_fn = items["constructions"]
        self.known_words = self.getKnownWords(items["known_words"])
        self.known_words.update(self.getKnownWords(items["morph_override"]))
        self.ocamorph_tag_sep = items["ocamorph_tag_sep"]
        self.inference_rules = items["inference_rules"]
        self.ocamorph_encoding = "LATIN2"
        self.hunmorph_host = items["hunmorph_host"]
        self.hunmorph_port = int(items["hunmorph_port"])

    def getKnownWords(self, file):
        return dict([line.decode('utf-8').strip().split()[:2] for line in open(file) if line!='\n'])
    
    def __read_files(self):
        self.__read_definitions()
        self.__read_constructions()

    def __read_definitions(self):
        from definition_parser import read
        self.definitions = read(file(self.def_fn))

    def __read_constructions(self):
       from constructions import read_constructions
       self.constructions = read_constructions(file(self.con_fn), self.definitions)

    def __run_morph_analysis(self, command):
        """
        calls ocamorph and hundisambig based on config
        """
        from subprocess import Popen, PIPE
        from tempfile import NamedTemporaryFile
        
        try:
            tokens = [[w, self.known_words[w]] for w in command.split()]
            return tokens
        except KeyError:
            pass
        logging.warning('not all words are known, falling back to ocamorph')
        command = command.encode(self.ocamorph_encoding)
        hunmorph_input = "\n".join(command.split())
        try:
            s = socket.socket()
            s.connect((self.hunmorph_host, self.hunmorph_port))
            logging.debug('connected to hunmorph at %s:%d' % (self.hunmorph_host, self.hunmorph_port))
            logging.debug('sending...')#: \n'+hunmorph_input)
            s.send(hunmorph_input)
            logging.debug('sent')
            logging.debug('receiving...')
            hunmorph_output = s.recv(4096)
            logging.debug('received')
            hunmorph_output = hunmorph_output.decode(self.ocamorph_encoding)
            tokens = [tok.split("\t")[:2] for tok in hunmorph_output.split("\n") if tok!='']
            return tokens 
        except:
            logging.error("unable to connect to ocamorph")
            from machine_exceptions import NoAnalysisException
            raise NoAnalysisException
            
    def __run_morph_analysis_v2(self, command):
        """
        improved version of __run_morph_analysis, uses langtools

        maybe this will be the place of using sockets and communicating with daemons
        instead of using local ocamorph (and others) directly
        """
        from langtools.utils.huntools import MorphAnalyzer, Ocamorph, Hundisambig
        o = Ocamorph(self.ocamorph, self.ocamorph_bin)
        h = Hundisambig(self.hundisambig_bin, self.hundisambig_model)
        a = MorphAnalyzer(o, h)
        a = a.analyze([command.split("\n")])
        return list(a)[0] 

    def __run_infer(self, machine):
        """
        run inference engine over the machines
        (usually called after constructions has been run)
        """
        from inference import InferenceEngine as IE
        ie = IE()
        ie.load(self.inference_rules)
        ie.infer(machine)

    def run(self, command):
        from order_parser import OrderParser

        # morph analysis
        analysed_command = self.__run_morph_analysis(command)
        logging.debug( u"Analysed_command: {0}".format(unicode(analysed_command)).encode("utf-8") )

        # transforming command/order based on constructions and definitions
        op = OrderParser(self.constructions, self.definitions)
        result = op.run(analysed_command)
        logging.debug( u"After running order: {0}".format(unicode(result)).encode("utf-8") )

        # running inference engine
        self.__run_infer(result)
        logging.debug( u"After inferring: {0}".format(unicode(result)).encode("utf-8") )
        return result

if __name__ == "__main__":
    import sys
    w = Wrapper()
    result_machine = w.run(file(sys.argv[1]).read().strip().decode("utf-8"))
    
