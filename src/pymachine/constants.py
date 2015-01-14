                 # TO     AT     FROM
locative_cases = ["SBL", "SUE", "DEL",  # ON
                  "ILL", "INE", "ELA",  # IN
                  "ALL", "ADE", "ABL"]  # AT
deep_cases = ['=AGT', '=PAT', '=DAT', '=FROM', '=TO', '=POSS', '=LAM']
# "ACC", "DAT", "INS", "OBL"] + ["POSS", "ROOT"]

#should be part of some langspec module, this is just a temporary hack
deep_case_to_grammatical_case = {
    '=AGT': 'NOM',
    '=PAT': 'NOM'
}

# Special prefixes, separators, etc. that occur in definitions
avm_pre = '#'
deep_pre = '='
enc_pre = '@'
id_sep = '/'
