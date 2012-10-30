#!/usr/bin/env python


##@file
# Split the input fasta file in several output files
# usage: dbSplit.py [ options ]
# options:
#      -h: this help
#      -i: name of the input file (format='fasta')
#      -n: number of sequences per output file (default=1)
#      -d: record the output fasta files in a directory called 'batches'
#      -s: use the sequence header if '-n 1' (otherwise 'batch_00X')"
#      -p: use a prefix for the output files (default='batch')"
#      -v: verbose (default=0/1)


import sys
import getopt

from pyRepetUnit.commons.seq.FastaUtils import FastaUtils


## Give the list of the command-line options
#
def help():
    print
    print "usage: dbSplit.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='fasta')"
    print "     -n: number of sequences per batch file (default=1)"
    print "     -d: record the output fasta files in a directory called 'batches'"
    print "     -s: use the sequence header if '-n 1' (otherwise 'batch_00X')"
    print "     -p: use a prefix for the output files (default='batch')"
    print "     -v: verbosity level (default=0/1/2)"
    print


## Split the input fasta file in several output files
#
def main():
    inFile = ""
    nbSeqPerBatch = 1
    newDir = False
    useSeqHeader = False
    prefix = "batch"
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:n:dsp:v:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % ( str(err) ) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFile = a
        elif o == "-n":
            nbSeqPerBatch = int(a)
        elif o == "-d":
            newDir = True
        elif o == "-s":
            useSeqHeader = True
        elif o == "-p":
            prefix = a
        elif o == "-v":
            verbose = int(a)

    if inFile == "":
        msg = "ERROR: missing input file (-i)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    FastaUtils.dbSplit( inFile, nbSeqPerBatch, newDir, useSeqHeader, prefix, verbose )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
