import logging
config_filename = "machine.cfg"

class Wrapper:
    def __init__(self, cf=config_filename):
        self.cfn = cf
        self.__read_config()
        self.__read_files()

    def __read_config(self):
        import ConfigParser
        config = ConfigParser.SafeConfigParser()
        config.read(self.cfn)
        items = dict(config.items("machine"))
        self.def_fn = items["definitions"]
        self.con_fn = items["constructions"]
        self.ocamorph = items["ocamorph"]
        self.ocamorph_bin = items["ocamorph_bin"]
        self.ocamorph_tag_sep = items["ocamorph_tag_sep"]
        self.inference_rules = items["inference_rules"]
        self.ocamorph_encoding = "LATIN1"
        self.hundisambig_bin = items["hundisambig_bin"]
        self.hundisambig_model = items["hundisambig_model"]

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
        from subprocess import Popen, PIPE
        from tempfile import NamedTemporaryFile
        command = command.encode(self.ocamorph_encoding)
        oca_output = Popen([self.ocamorph, "--bin", self.ocamorph_bin,
                        "--tag_preamble", "",
                        "--tag_sep", "{0}".format(self.ocamorph_tag_sep),
                        "--guess", "Fallback", "--blocking"], stdout=PIPE, stdin=PIPE).communicate("\n".join(command.split()))[0].strip()
        oca_output = oca_output.replace(self.ocamorph_tag_sep, "\t")
        tf = NamedTemporaryFile()
        tf_name = tf.name
        tf.write("\n".join(set(oca_output.split("\n"))))
        tf.flush()
        hundis_input = "\n".join([t.split("\t")[0] for t in oca_output.split("\n")])
        
        hundis_output = Popen([self.hundisambig_bin,
                               "--morphtable", tf_name,
                               "--tagger-model", self.hundisambig_model],
                              stdout=PIPE, stdin=PIPE, stderr=PIPE).communicate(hundis_input)[0].strip()
        hundis_output = hundis_output.decode(self.ocamorph_encoding)
        tf.close()

        tokens = [tok.split("\t")[:2] for tok in hundis_output.split("\n")]
        return tokens 

    def __run_morph_analysis_v2(self, command):
        from langtools.utils.huntools import MorphAnalyzer, Ocamorph, Hundisambig
        o = Ocamorph(self.ocamorph, self.ocamorph_bin)
        h = Hundisambig(self.hundisambig_bin, self.hundisambig_model)
        a = MorphAnalyzer(o, h)
        a = a.analyze([command.split("\n")])
        return list(a)[0] 

    def __run_infer(self, machine):
        from inference import InferenceEngine as IE
        ie = IE()
        ie.load(self.inference_rules)
        ie.infer(machine)

    def run(self, command):
        from order_parser import run as run_order
        analysed_command = self.__run_morph_analysis(command)
        logging.debug( "Analysed_command: " + str(analysed_command) )
        result = run_order(analysed_command, self.definitions, self.constructions)
        logging.debug( "After running order: " + str(result) )
        self.__run_infer(result)
        logging.debug( "After inferring: " + str(result) )
        return result

if __name__ == "__main__":
    import sys
    w = Wrapper()
    result_machine = w.run(file(sys.argv[1]).read().strip().decode("utf-8"))

