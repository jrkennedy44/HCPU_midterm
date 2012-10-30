#!/usr/bin/env python

import os
import sys
import getopt

try:
    from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
except:
    msg = "ERROR: can't import package 'FastaUtils'"
    sys.stderr.write( "%s\n" % ( msg ) )
    sys.exit(1)


def help():
    print
    print "usage: splitSeqPerCluster.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='fasta')"
    print "     -c: clustering method (Grouper/Recon/Piler)"
    print "     -d: create a directory for each group"
    print "     -H: simplify sequence headers"
    print "     -v: verbose (default=0/1/2)"
    print


def main():
    """
    Record all the sequences belonging to the same cluster in the same fasta file
    """

    inFileName = ""
    clusteringMethod = ""
    createDir = False
    simplifyHeader = False
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:c:dHv:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % ( str(err) ) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-c":
            clusteringMethod = a
        elif o == "-d":
            createDir = True
        elif o == "-H":
            simplifyHeader = True
        elif o == "-v":
            verbose = int(a)

    if  inFileName == "":
        msg = "ERROR: missing input file (-i)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if clusteringMethod == "":
        msg = "ERROR: missing clustering method (-c)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        msg = "ERROR: can't find file '%s'" % ( inFileName )
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    FastaUtils.splitSeqPerCluster( inFileName, clusteringMethod, simplifyHeader,
                                   createDir, "seqCluster", verbose )

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
