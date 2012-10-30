#!/usr/bin/env python

import os
import sys
import getopt
import math
import time
import exceptions
import logging

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )
import pyRepet.coord.MatchDB
import pyRepet.seq.BioseqDB


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: %s [ options ]" % ( sys.argv[0] )
    print "options:"
    print "     -h: this help"
    print "     -q: fasta filename of the queries"
    print "     -s: fasta filename of the subjects (same as queries if left blank)"
    print "     -m: output file from Matcher (format='tab')"
    print "     -o: name of the output query file (format=fasta, default=qryFileName+'.filtered')"
    print "     -i: identity threshold (default=0.95)"
    print "     -l: length threshold (default=0.98)"
    print "     -L: name of a 'log' file (usually from 'rmvRedundancy.py')"
    print "     -v: verbose (default=0/1)"
    print


def writeOutQuery( qryDB, outFileName, lQryToKeep ):
    """
    Write in a fasta file the queries than haven't been filtered (i.e. they are not included in any subject).
    """
    outFile = open( outFileName, "w" )
    nbRmvSeq = 0
    for bs in qryDB.db:
        if bs.header in lQryToKeep:
            bs.write( outFile )
        else:
            nbRmvSeq += 1
    outFile.close()
    if verbose > 0:
        print "%i removed queries out of %i" % ( nbRmvSeq, qryDB.getSize() ); sys.stdout.flush()


def main():
    """
    This program filters the ouput from Matcher by removing queries 'included' in subjects.
    """
    qryFileName = ""
    sbjFileName = ""
    tabFileName = ""
    outFileName = ""
    thresIdentity = 0.95   # remove the seq if it is identical to 95% of another seq
    thresLength = 0.98   # and if its length is 98% of that seq
    logFileName = ""
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:q:s:m:o:i:l:L:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-q":
            qryFileName = a 
        elif o == "-s":
            sbjFileName = a 
        elif o == "-m":
            tabFileName = a
        elif o == "-o":
            outFileName = a
        elif o == "-i":
            thresIdentity = float(a) 
        elif o == "-l":
            thresLength = float(a)
        elif o == "-L":
            logFileName = a
        elif o == "-v":
            verbose = int(a)
    if qryFileName == "" or tabFileName == "":
        print "ERROR: missing compulsory options"
        help()
        sys.exit(1)
    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    # prepare the 'log' file
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "use '%s' on '%s'" % ( sys.argv[0].split("/")[-1], tabFileName ) )

    if sbjFileName == "":
        sbjFileName = qryFileName
    if outFileName == "":
        outFileName = "%s.filtered" % ( qryFileName )

    # load the input fasta file corresponding to the queries
    qryDB = pyRepet.seq.BioseqDB.BioseqDB( qryFileName )
    if sbjFileName != qryFileName:
        string = "nb of input sequences (as query only): %i" % ( qryDB.getSize() ); sys.stdout.flush()
        logging.info( string )
        if verbose > 0: print string
    else:
        string = "nb of input sequences (as query and subject): %i" % ( qryDB.getSize() ); sys.stdout.flush()
        logging.info( string )
        if verbose > 0: print string

    # load the input 'tab' file
    matchDB = pyRepet.coord.MatchDB.MatchDB()
    tabFile = open( tabFileName, "r" )
    matchDB.read( tabFile, thresIdentity, thresLength, verbose )
    tabFile.close()
    longString = ""
    string = "nb of matches (id>=%.2f,qlgth>=%.2f): %i" % ( thresIdentity, thresLength, matchDB.getNbMatchesWithThres( thresIdentity, thresLength ) )
    longString += "\n%s" % ( string )
    if verbose > 0: print string
    string = "nb of distinct queries having matches (id>=%.2f,qlgth>=%.2f): %i" % ( thresIdentity, thresLength, matchDB.getNbDistinctQryWithThres( thresIdentity, thresLength ) )
    longString += "\n%s" % ( string )
    if verbose > 0: print string
    logging.info( longString )
    sys.stdout.flush()

    # if queries and subjects are two different files
    if sbjFileName != qryFileName:
        lQryToKeep, dQryToRmv2Matches = matchDB.filterDiffQrySbj( qryDB, thresIdentity, thresLength, verbose - 1 )

    # if queries and subjects are the same file
    else:
        lQryToKeep, dQryToRmv2Matches = matchDB.filterSameQrySbj( qryDB, thresIdentity, thresLength, verbose - 1 )

    # here, possibility to save the information about by which match a specific query has been removed

    string = "%i queries to be kept" % ( len(lQryToKeep) ); sys.stdout.flush()
    logging.info( string )
    if verbose > 0: print string

    # write the output fasta file without the included queries
    writeOutQuery( qryDB, outFileName, lQryToKeep )

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main ()
