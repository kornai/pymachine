import re

                 # TO     AT     FROM
locative_cases = ["SBL", "SUE", "DEL", # ON
                  "ILL", "INE", "ELA", # IN
                  "ALL", "ADE", "ABL"] # AT
deep_cases = locative_cases + ["NOM", "ACC", "DAT", "INS", "OBL"] + ["POSS", "ROOT"]
unary_pattern = re.compile("^[a-z_#\-/0-9]+$")
binary_pattern = re.compile("^[A-Z_0-9]+$")
