#!/bin/sh

#only definitions
grep ":"

#remove authors
sed "s/MaM//g" | sed "s/ND//g" | sed "s/RG//g" | sed "s/RA//g"

#remove default symbol (<>), they are not handled right now
sed "s/<\([^>]*\)>/\1/g"

