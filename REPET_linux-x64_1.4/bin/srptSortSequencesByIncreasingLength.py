#!/usr/bin/env python

import sys, getopt
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils

#------------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input fasta file"
    print "     -o: name of the output fasta file"
    print "     -v: verbose (default=0/1)"
    print ""

#------------------------------------------------------------------------------

def main():

    inFileName = ""
    outFileName = ""
    verbose = 0

    try:
        opts, args=getopt.getopt(sys.argv[1:],"hi:o:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "beginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    log = FastaUtils.sortSequencesByIncreasingLength( inFileName, outFileName, verbose )
    if log != 0:
        print "*** Error: sortSequencesByIncreasingLength() returned %i" % ( log )
        sys.exit(1)

    if verbose > 0:
        print "%s finished successfully" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()