#! /usr/bin/env python
import sys
import sourmash

with open(sys.argv[2], 'rt') as fp:
    unsig = sourmash.load_one_signature(fp)

tree = sourmash.load_sbt_index(sys.argv[1])
tree.print(unsig)

