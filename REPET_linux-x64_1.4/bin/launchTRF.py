#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='fasta')"
    print "     -o: name of the output file (default=inFileName+'.TRF.set')"
    print "     -c: clean"
    print "     -v: verbosity level (default=0/1)"
    print


def main():
    """
    Launch TRF to detect micro-satellites in sequences.
    """
    inFileName = ""
    outFileName = ""
    clean = False
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:o:cv:" )
    except getopt.GetoptError, err:
        print str(err)
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
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)
            
    if inFileName == "":
        print "ERROR: missing input file (-i)"
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        print "ERROR: can't find input file '%s'" % ( inFileName )
        help()
        sys.exit(1)
        
    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()
        
    if verbose > 0:
        print "launch TRF..."
        sys.stdout.flush()
    cmd = "trf"
    cmd += " %s 2 3 5 80 10 20 15 -h -d" % ( inFileName )
    returnValue = os.system( cmd )
    # CAUTION: even when 'trf' ends properly, it does not return '0'...
#    if returnValue != 0:
#        print "ERROR: 'trf' returned %i" % ( returnValue )
#        sys.exit(1)
        
    if verbose > 0:
        print "parse the results..."
        sys.stdout.flush()
    if outFileName == "":
        outFileName = "%s.TRF.set" % ( inFileName )
    outFile = open( outFileName, "w" )
    inFile = open( "%s.2.3.5.80.10.20.15.dat" % ( inFileName ), "r" )
    nbPatterns = 0
    nbInSeq = 0
    while True:
        line = inFile.readline()
        if line == "":
            break
        data = line.split(" ")
        if len(data) > 1 and "Sequence:" in data[0]:
            nbInSeq += 1
            seqName = data[1][:-1]
        if len(data) < 14:
            continue
        nbPatterns += 1
        consensus = data[13]
        copyNb = int( float(data[3]) + 0.5 )
        start = data[0]
        end = data[1]
        outFile.write( "%i\t(%s)%i\t%s\t%s\t%s\n" % ( nbPatterns, consensus, copyNb, seqName, start, end ) )
    outFile.close()
    
    if clean:
        if verbose > 0:
            print "clean the temporary files..."
            sys.stdout.flush()
        cmd = "rm -f %s.*.dat" % ( inFileName )
        returnValue = os.system( cmd )
        if returnValue != 0:
            print "ERROR while cleaning"
            sys.exit(1)
            
    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()
        
    return 0


if __name__ == "__main__":
    main()
