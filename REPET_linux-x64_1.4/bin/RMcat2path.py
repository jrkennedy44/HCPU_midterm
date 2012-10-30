#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: RMcat2path.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: input file name (cat format, output from RepeatMasker)"
    print "     -o: output file name (path format, default=inFileName+'.path')"
    print "     -v: verbosity level (default=0/1)"
    print


def main():
    """
    Convert the output file from RepeatMasker ('cat' format) into the 'path' format.
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
        outFileName = "%s.path" % ( inFileName )

    inFileHandler = open( inFileName, "r" )
    outFileHandler = open( outFileName, "w" )
    countLines = 0

    while True:
        line = inFileHandler.readline()
        if line == "":
            break
        countLines += 1

        tokens = line.split()
        try:
            test = int(line[0])
        except ValueError:
            break

        scoreSW = tokens[0]
        percDiv = tokens[1]
        percId = 100.0 - float(percDiv)
        percDel = tokens[2]
        percIns = tokens[3]

        # query coordinates are always direct (start<end)
        qryName = tokens[4]
        qryStart = int(tokens[5])
        qryEnd = int(tokens[6])
        qryAfterMatch = tokens[7]
        
        # if subject on direct strand
        if len(tokens) == 13:
            sbjName = tokens[8]
            sbjStart = int(tokens[9])
            sbjEnd = int(tokens[10])
            sbjAfterMatch = tokens[11]
            
        # if subject on reverse strand
        elif tokens[8] == "C":
            sbjName = tokens[9]
            sbjAfterMatch = tokens[10]
            sbjStart = int(tokens[11])
            sbjEnd = int(tokens[12])
            
        # compute a new score: match length on query times identity
        matchLengthOnQuery = qryEnd - qryStart + 1
        newScore = int( matchLengthOnQuery * float(percId) / 100.0 )
        
        string = "%i\t%s\t%i\t%i\t%s\t%i\t%i\t0.0\t%i\t%s\n" % ( countLines, qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, newScore, percId )
        
        outFileHandler.write( string )
        
    inFileHandler.close()
    outFileHandler.close()
    if verbose > 0:
        print "nb of lines: %i" % ( countLines )
        
    return 0


if __name__ == "__main__":
    main()
