#! /usr/bin/env python
import sys
import sourmash

tree = sourmash.load_sbt_index(sys.argv[1])
tree.print_dot()
