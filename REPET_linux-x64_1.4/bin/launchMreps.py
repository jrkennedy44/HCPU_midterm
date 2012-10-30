#!/usr/bin/env python

"""
Launch Mreps.
"""

import os
import sys
import getopt
import exceptions

if not "REPET_PATH" in os.environ.keys():
    print "*** Error: no environment variable REPET_PATH"
sys.path.append( os.environ["REPET_PATH"] )

from pyRepet.launcher.programLauncher import *
from pyRepet.parser.Parser import *


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='fasta')"
    print "     -o: name of the output file (default=inFileName+'.Mreps.set')"
    print "     -f: error filter (default=1.0)"
    print "     -c: clean"
    print "     -v: verbosity level (default=0/1)"
    print


def main():
    """
    Launch Mreps.
    """

    inFileName = ""
    outFileName = ""
    errorFilter = 1.0
    clean = False
    verbose = 0

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hi:o:f:cv:")
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
        elif o == "-f":
            errorFilter = float(a)
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "beginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    # Mreps 2.5 doesn't fully support IUPAC nomenclature
    if verbose > 0:
        print "* check IUPAC symbols"; sys.stdout.flush()
    tmpInFileName = "%s.tmp%i" % ( inFileName, os.getpid() )
    if os.path.exists( tmpInFileName ):
        os.system( "rm -f %s" % ( tmpInFileName ) )
    bsDB = BioseqDB( inFileName )
    for bs in bsDB.db:
        if verbose > 0:
            print bs.header; sys.stdout.flush()
        bs.partialIUPAC()
        onlyN = True
        for nt in ["A","T","G","C"]:
            if nt in bs.sequence:
                onlyN = False
        if onlyN == True:
            if verbose > 0:
                print "** Warning: only Ns"; sys.stdout.flush()
        else:
            bsDB.save( tmpInFileName )

    if not os.path.exists( tmpInFileName ):
        sys.exit(0)

    if verbose > 0:
        print "* remove N stretches"; sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/cutterDB"
    cmd = prg
    cmd += " -l 200000"
    cmd += " -o 0"
    cmd += " -w 11"
    cmd += " %s" % ( tmpInFileName )
    if verbose > 0:
        print cmd; sys.stdout.flush()
    log = os.system( cmd )
    if log != 0:
        print "ERROR: %s returned %i" % ( prg, log )
        sys.exit(1)

    # launch Mreps on the input file
    pL = programLauncher( tmpInFileName + "_cut" )
    MrepsOutFileName = "%s.Mreps.xml" % ( tmpInFileName )
    pL.launchMreps( MrepsOutFileName, verbose="yes" )

    if outFileName == "":
        outFileName = inFileName + ".Mreps.set"

    # parse Mreps results in xml format
    parser = MrepsParser( inFileName, MrepsOutFileName, outFileName, errorFilter )
    parser.xml2set()
    if clean:
        parser.clean()

    # remove temporary input filename
    os.system( "rm -f %s %s_cut %s.Nstretch.map" % ( tmpInFileName, tmpInFileName, tmpInFileName ) )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == '__main__':
    main()
