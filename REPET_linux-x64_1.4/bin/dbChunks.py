#!/usr/bin/env python

import os
import sys
import getopt
import exceptions

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ.get( "REPET_PATH" ) )
import pyRepet.seq.fastaDB

#------------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage: %s [ options ]" % ( sys.argv[0] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format=fasta)"
    print "     -l: chunk length (in bp, default=200000)"
    print "     -o: chunk overlap (in bp, default=10000)"
    print "     -w: N stretch word length (default=11, 0 for no detection)"
    print "     -O: prefix of the output files (default=inFileName+'_chunks' followed by '.fa' or '.map')"
    print "     -c: clean (remove 'cut' and 'Nstretch' files)"
    print "     -v: verbose (default=0/1)"
    print ""

#------------------------------------------------------------------------------

def main():

    """
    This program cuts a data bank into chunks according to the input parameters.
    If a sequence is shorter than the threshold, it is only renamed (not cut).
    """

    inFileName = ""
    chkLgth = "200000"
    chkOver = "10000"
    wordN = "11"
    outFilePrefix = ""
    clean = False
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:l:o:w:O:cv:" )
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-l":
            chkLgth = a
        elif o == "-o":
            chkOver = a
        elif o == "-w":
            wordN = a
        elif o == "-O":
            outFilePrefix = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "*** Error: missing input file"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    pyRepet.seq.fastaDB.dbChunks( inFileName, chkLgth, chkOver, wordN, outFilePrefix, clean, verbose )

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == "__main__":
    main()
