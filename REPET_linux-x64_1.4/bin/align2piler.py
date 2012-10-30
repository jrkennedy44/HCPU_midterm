#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: align2piler.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='align')"
    print "     -o: name of the output file (default=inFileName+'.gff')"
    print "     -v: verbosity level (default=0/1)"
    print
    
    
def main():
    """
    Convert the output file from Blaster ('align' format) into the input for Piler (GFF2 format).
    """
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
        outFileName = "%s.gff" % ( inFileName )
        
    if os.path.exists( os.environ["REPET_PATH"] + "/bin/align2piler" ):
        prg = os.environ["REPET_PATH"] + "/bin/align2piler"
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
        data = line.split("\t")
        qryName = data[0]
        qryStart = int(data[1])
        qryEnd = int(data[2])
        sbjName = data[3]
        sbjStart = int(data[4])
        sbjEnd = int(data[5])
        Eval = data[6]
        score = data[7]
        identity = data[8][:-1]
        if qryStart < qryEnd:
            if sbjStart < sbjEnd:
                strand = "+"
            else:
                strand = "-"
                tmp = sbjStart
                sbjStart = sbjEnd
                sbjEnd = tmp
        elif qryStart > qryEnd:
            tmp = qryStart
            qryStart = qryEnd
            qryEnd = tmp
            if sbjStart < sbjEnd:
                strand = "-"
            else:
                strand = "+"
                tmp = sbjStart
                sbjStart = sbjEnd
                sbjEnd = tmp
        percMis = (100.0 - float(identity)) / 100.0
        string = "%s\tblaster\thit\t%s\t%s \t%s\t%s\t.\tTarget %s %s %s; maxe %.4f\n" % ( qryName, qryStart, qryEnd, score, strand, sbjName, sbjStart, sbjEnd, percMis )
        outFile.write( string )
    inFile.close()
    outFile.close()
    if verbose > 0:
        print "nb of lines: %i" % ( countLines )
        
    return 0


if __name__ == "__main__":
    main()
