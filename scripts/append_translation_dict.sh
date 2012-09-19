#!/bin/sh
concept_definitions=$1
langspec_definitions=$2
cut -f1,2,4 -d" " $concept_definitions | grep -v "^[[:space:]]*$" | awk '{print $1,$2,"N","#","#","#: ", $3}' - >> $langspec_definitions
