#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: align2recon.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='align')"
    print "     -o: name of the output file (default=inFileName+'.msp')"
    print "     -v: verbosity level (default=0/1)"
    print


def main():
    inFileName = ""
    outFileName = ""
    verbose = 0
    
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:o:v:" )
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
        outFileName = "%s.msp" % ( inFileName )
        
    if os.path.exists( os.environ["REPET_PATH"] + "/bin/align2recon" ):
        prg = os.environ["REPET_PATH"] + "/bin/align2recon"
        cmd = prg
        cmd += " -i %s" % ( inFileName )
        cmd += " -o %s" % ( outFileName )
        cmd += " -v %i" % ( verbose )
        return os.system( cmd )
    
    inFile = open( inFileName, "r" )
    outFile = open( outFileName, "w" )
    countLines = 0
    while True:
        line = inFile.readline()
        if line == "":
            break
        countLines += 1
        tokens = line.split()
        qryName = tokens[0]
        qryStart = tokens[1]
        qryEnd = tokens[2]
        sbjName = tokens[3]
        sbjStart = tokens[4]
        sbjEnd = tokens[5]
        Eval = tokens[6]
        score = tokens[7]
        percId = tokens[8]
        out = score + " " + percId + " " + qryStart + " " + qryEnd + " " \
        + qryName + " " + sbjStart + " " + sbjEnd + " " + sbjName
        outFile.write( out + "\n" )
    inFile.close()
    outFile.close()
    if verbose > 0:
        print "nb of lines: %i" % ( countLines )
        
    return 0


if __name__ == "__main__":
    main()
