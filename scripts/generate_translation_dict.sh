#!/bin/sh
# generates a language specific definition file from
# concepts (based on concept printnames), and a hand-written
# language-specific file with concatenation

# WARNING: now only hungarian printnames will work, because
# index is hard-coded. See cut -f
concept_definitions=$1
langspec_definitions=$2
out=$3
cp $langspec_definitions $out
cut -f1,2,4 -d" " $concept_definitions | grep -v "^[[:space:]]*$" | awk '{print $1,$2,"N","#","#","#: ", $3}' - >> $out
