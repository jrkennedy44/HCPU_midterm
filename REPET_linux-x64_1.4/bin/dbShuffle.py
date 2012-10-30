#!/usr/bin/env python

# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


import os
import sys
import getopt

from pyRepetUnit.commons.seq.FastaUtils import FastaUtils


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     INPUT: use '-i' or '-I'"
    print "        -i: name of the input file (fasta format)"
    print "        -I: name of the input directory (containing fasta files)"
    print "     OUTPUT: use '-o' or '-O'"
    print "         -o: name of the output file (use only with '-i')"
    print "         -O: name of the output directory (use only with '-I')"
    print "             output file are: prefix of input fasta file + '_shuffle.fa')"
    print "     -v: verbose (default=0/1/2)"
    print


def main():
    inData = ""
    outData = ""
    verbose = 0
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:I:o:O:v:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % str(err) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inData = a
        elif o == "-I":
            inData = a
        elif o == "-o":
            outData = a
        elif o == "-O":
            outData = a
        elif o == "-v":
            verbose = int(a)

    if inData == "" or ( not os.path.isfile( inData ) \
                         and not os.path.isdir( inData ) ):
        msg = "ERROR: missing input file or directory (-i or -I)"
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)

    if outData == "":
        print "ERROR: missing name of output file or directory (-o or -O)"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()
        
    FastaUtils.dbShuffle( inData, outData, verbose )
    
    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
