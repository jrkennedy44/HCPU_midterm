#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: CENmap2align.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: input file name (map format, output from Censor)"
    print "     -o: output file name (align format, default=inFileName+'.align')"
    print "     -v: verbosity level (default=0/1)"
    print


def main():
    """
    Convert the output file from Censor ('map' format) into the 'align' format.
    """
    inFileName = ""
    outFileName = ""
    verbose = 0
    
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:o:v:" )
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
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)
            
    if inFileName == "":
        msg = "ERROR: missing input file (-i)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        msg = "ERROR: can't find input file '%s'" % ( inFileName )
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if outFileName == "":
        outFileName = "%s.align" % ( inFileName )

    inFileHandler = open( inFileName, "r" )
    outFileHandler = open( outFileName, "w" )
    countLines = 0
    
    while True:
        line = inFileHandler.readline()
        if line == "":
            break
        countLines += 1
        
        tokens = line.split()
        qryName = tokens[0]
        qryStart = int(tokens[1])
        qryEnd = int(tokens[2])
        sbjName = tokens[3]
        strand = tokens[6]
        if strand == "d":   # if match with direct subject
            sbjStart = int(tokens[4])
            sbjEnd = int(tokens[5])
        elif strand == "c":   # if match with complement subject
            sbjStart = int(tokens[5])
            sbjEnd = int(tokens[4])
            
        similarity = float(tokens[7])
        BLASTscore = int(tokens[9])
        newScore = int( BLASTscore * similarity )
        percId = 100 * similarity
        
        string = "%s\t%i\t%i\t%s\t%i\t%i\t0.0\t%i\t%s\n" % ( qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, newScore, percId )
        
        outFileHandler.write( string )
        
    inFileHandler.close()
    outFileHandler.close()
    if verbose > 0:
        print "nb of lines: %i" % ( countLines )
        
    return 0


if __name__ == "__main__":
    main()
