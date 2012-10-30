#!/usr/bin/env python

import os
import sys
import getopt
import glob
import logging
from pyRepetUnit.commons.utils.FileUtils import FileUtils


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage:",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -d: absolute path to the target directory"
    print "     -r: regexp to retrieve the file in the target directory (default=\"*.fa_aln\")"
    print "     -n: minimum number of nucleotides in a column to edit a consensus (default=1)"
    print "     -p: minimum proportion for the major nucleotide to be used, otherwise add 'N' (default=0.0)"
    print "     -o: output file name for the consensus (default=consensus.fa)"
    print "     -v: verbose (default=0/1/2)"
    print


def main():
    """
    This program builds a consensus for each '.fa_aln' file in the target directory and concatenate them in a fasta file.
    """

    targetDir = ""
    regexp = "*.fa_aln"
    minBase = 1
    minPropNt = 0.0
    outFileName = "consensus.fa"
    verbose = 0

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hd:r:n:p:o:cv:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit()
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit()
        elif o == "-d":
            targetDir = a
        elif o == "-r":
            regexp = a
        elif o == "-n":
            minBase = int(a)
        elif o == "-o":
            outFileName = a
        elif o == "-p":
            minPropNt = float(a)
        elif o == "-v":
            verbose = int(a)

    if targetDir == "":
        print "ERROR: target directory is missing"
        help()
        sys.exit(1)

    if glob.glob( regexp ) == []:
        print "ERROR: no files corresponding to '%s'" % ( regexp )
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    logFileName = "%s.log" % ( outFileName )
    if os.path.exists( logFileName ):
        os.remove( logFileName )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )

    currDir = os.getcwd()

    logging.info( "target directory: %s" % ( targetDir ) )
    logging.info( "min bases to edit a consensus: %i" % ( minBase ) )
    logging.info( "min proportion to add nucleotide: %.2f" % ( minPropNt ) )
    logging.info( "regexp: %s" % ( regexp ) )

    if verbose > 0:
        print "target directory: %s" % ( targetDir )
        print "retrieve files via '%s'" % ( regexp )
        sys.stdout.flush()
    os.chdir( targetDir )

    if os.path.exists( outFileName ):
        os.remove( outFileName )

    lFiles = glob.glob( regexp )
    lFiles.sort()
    if verbose > 0:
        print "initial nb of consensus: %i" % ( len(lFiles) )
    logging.info( "initial nb of consensus: %i" % ( len(lFiles) ) )
    for f in lFiles:
        if verbose > 0:
            print "processing '%s'..." % ( f ); sys.stdout.flush()
        prg = os.environ["REPET_PATH"] + "/bin/dbConsensus.py"
        cmd = prg
        cmd += " -i %s" % ( f )
        cmd += " -n %i" % ( minBase )
        cmd += " -p %F" % ( minPropNt )
        cmd += " -v %i" % ( verbose - 1 )
        log = os.system( cmd )
        if log != 0:
            print "ERROR: %s returned %i" % ( prg, log )
            sys.exit(1)

    lConsensusFiles = glob.glob( "*.cons" )
    lConsensusFiles.sort()
    if verbose > 0:
        print "final nb of consensus: %i" % ( len(lConsensusFiles) )
    logging.info( "final nb of consensus: %i" % ( len(lConsensusFiles) ) )

    FileUtils.catFilesByPattern( "*.cons", outFileName )

    os.chdir( currDir )

    logging.info( "finished" )

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

if __name__ == "__main__":
    main()
