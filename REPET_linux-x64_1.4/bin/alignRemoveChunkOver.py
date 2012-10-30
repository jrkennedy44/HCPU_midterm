#!/usr/bin/env python

import user, os, sys, getopt, string

def setup_env():
    if os.environ.has_key( "REPET_PATH" ):
        sys.path.append( os.environ.get( "REPET_PATH" ) )
    else:
        print "*** Error: no environment variable REPET_PATH"
        sys.exit(1)
setup_env()

from pyRepet.coord.Align import *

#------------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage: %s [ options ]" % ( sys.argv[0] )
    print "option:"
    print "    -h: this help"
    print "    -i: output file from Blaster ('.align')"
    print "    -l: chunk length (in bp)"
    print "    -o: chunk overlap (in bp)"
    print "    -O: name of the output file (default=inFileName+'.not_over')"
    print "    -v: verbose (default=0/1)"
    print ""

#------------------------------------------------------------------------------

def main():

    """
    This program removes the HSPs (high-scoring segment pairs) due to the overlaps created when building the chunks library.
    """

    inFileName = ""
    chkLgth = -1
    chkOver = -1
    outFileName = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:i:l:o:O:v:")
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
            chkLgth = int(a)
        elif o == "-o":
            chkOver = int(a) 
        elif o == "-O":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "" or chkLgth == -1 or chkOver == -1 :
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    inFile = open( inFileName )

    if outFileName == "":
        outFileName = inFileName + ".not_over"
    outFile = open( outFileName, "w" )

    a = Align()
    nbRmvHSPs = 0
    rlim = chkLgth - chkOver

    while True:

        if not a.read( inFile ):
            break

        qchunk = int(a.range_query.seqname.replace("chunk",""))
        schunk = int(a.range_subject.seqname.replace("chunk",""))

        if qchunk == schunk + 1:
            if a.range_subject.start - a.range_query.start != rlim \
                   and a.range_subject.end - a.range_query.end != rlim:
                a.write( outFile )
            else:
                #a.show()
                nbRmvHSPs += 1

        elif qchunk + 1 == schunk:
            if a.range_query.start - a.range_subject.start != rlim \
                   and a.range_query.end - a.range_subject.end != rlim:
                a.write( outFile )
            else:
                #a.show()
                nbRmvHSPs += 1

        else:
            a.write( outFile )

    inFile.close()
    outFile.close()

    if verbose > 0:
        print "nb of removed HSPs: %i" % ( nbRmvHSPs )
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main ()
