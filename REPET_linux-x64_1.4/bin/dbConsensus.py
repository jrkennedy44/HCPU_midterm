#!/usr/bin/env python

import os
import sys
import getopt
import exceptions

##@file
# usage: dbConsensus.py [ options ]
# options:
#      -h: this help
#      -i: name of the input file (format=aligned fasta)
#      -n: minimum number of nucleotides in a column to edit a consensus (default=1)
#      -p: minimum proportion for the major nucleotide to be used, otherwise add 'N' (default=0.0)
#      -o: name of the output file (default=inFileName+'.cons')
#      -v: verbose (default=0/1/2)

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.seq.AlignedBioseqDB


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format=aligned fasta)"
    print "     -n: minimum number of nucleotides in a column to edit a consensus (default=1)"
    print "     -p: minimum proportion for the major nucleotide to be used, otherwise add 'N' (default=0.0)"
    print "     -o: name of the output file (default=inFileName+'.cons')"
    print "     -v: verbose (default=0/1/2)"
    print


def main():

    inFileName = ""
    minNbNt = 1
    minPropNt = 0.0
    outFileName = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:n:p:o:v:")
    except getopt.GetoptError, err:
        print str(err); help(); sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
	    sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-n":
            minNbNt = int(a)
        elif o == "-p":
            minPropNt = float(a)
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file name"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    alnDB = pyRepet.seq.AlignedBioseqDB.AlignedBioseqDB( inFileName )

    if alnDB.getSize() <= minNbNt:
        print "WARNING: not enough sequences (<=%i)" % ( minNbNt )

    else:
        consensus = alnDB.getConsensus( minNbNt, minPropNt, verbose )
        if consensus != None:
            if outFileName == "":
                outFileName = "%s.cons" % ( inFileName )
            outFile = open( outFileName, "w" )
            consensus.write( outFile )
            outFile.close()

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

if __name__ == "__main__":
    main ()
