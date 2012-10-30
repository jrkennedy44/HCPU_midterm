#!/usr/bin/env python

import sys
import os
import getopt

from pyRepetUnit.commons.coord.PathUtils import PathUtils


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: input file name (format='path')"
    print "     -s: source, 2nd column of the GFF format (default='REPET')"
    print "     -o: output file name (format='gff3', default=inFileName+'.gff3')"
    print "     -v: verbosity level (default=0/1)"
    print
    
    
def main():
    inFileName = ""
    source = "REPET"
    outFileName = ""
    verbose = 0
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:s:o:v:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % str(err) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-s":
            source = a
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)
    if  inFileName == "":
        msg = "ERROR: missing input file name (-i)"
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        msg = "ERROR: can't find file '%s'" % ( inFileName )
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)
    if outFileName == "":
        outFileName = "%s.gff3" % ( inFileName )
        
    if verbose > 0:
        msg = "START %s" % ( sys.argv[0].split("/")[-1] )
        msg += "\ninput file: %s" % ( inFileName )
        msg += "\nsource: %s" % ( source )
        msg += "\noutput file: %s" % ( outFileName )
        sys.stdout.write( "%s\n" % msg )
        sys.stdout.flush()
        
    PathUtils.convertPathFileIntoGffFile( pathFile=inFileName,
                                          gffFile=outFileName,
                                          source=source,
                                          verbose=verbose )
    
    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()
        
    return 0
    
    
if __name__ == "__main__":
    main()
