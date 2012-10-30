#!/usr/bin/env python

import user, os, sys, getopt

def setup_env():
    if os.environ.has_key( "REPET_PATH" ):
        sys.path.append( os.environ.get( "REPET_PATH" ) )
    else:
        print "*** Error: no environment variable REPET_PATH"
        sys.exit(1)
setup_env()

from pyRepet.seq.fastaDB import *

#------------------------------------------------------------------------------

def help():

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file ('fasta' format)"
    print "     -s: min size"
    print "     -n: n longest"
    print "     -o: name of the output file (default=inFileName+'.orf.map')"
    print ""

#------------------------------------------------------------------------------

def main():

    inFileName = ""
    n = 0
    s = 0
    outFileName = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:s:n:o")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-s":
            s = int(a)
        elif o == "-n":
            n = int(a)
        elif o == "-o":
            outFileName = a

    if inFileName == "":
        print "*** Error: missing input file"
        help()
        sys.exit(1)

    print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
    sys.stdout.flush()

    dbORF( inFileName, n, s, outFileName )

    print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
    sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
