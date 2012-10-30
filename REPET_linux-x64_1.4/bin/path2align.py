#!/usr/bin/env python

import sys
import getopt

from pyRepetUnit.commons.coord.PathUtils import PathUtils


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='path')"
    print "     -o: name of the output file (format='align', default=inFileName+'.align')"
    print "     -v: verbosity level (default=0/1)"
    print


def main():

    inFileName = ""
    outFileName = ""
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:o:v:" )
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        if o == "-i":
            inFileName = a
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file name (-i)"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    if outFileName == "":
        outFileName = "%s.align" % ( inFileName )

    PathUtils.convertPathFileIntoAlignFile( inFileName, outFileName )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
