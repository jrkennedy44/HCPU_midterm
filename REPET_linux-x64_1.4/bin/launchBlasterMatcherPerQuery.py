#!/usr/bin/env python

"""
This program splits the input fasta file in a given number of files, launch Blaster and/or Matcher on them in parallel and collect the results afterwards.
"""

import os
import sys
import getopt
import exceptions
import logging
import ConfigParser

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.launcher.programLauncher
import pyRepet.seq.fastaDB

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -q: fasta filename of the queries"
    print "     -s: fasta filename of the subjects (same as queries if not specified)"
    print "     -Q: queue name on the cluster"
    print "     -d: absolute path to the temporary directory"
    print "     -C: configuration file"
    print "     -n: max. number of jobs (default=10,given a min. of 1 query per job)"
    print "     -m: mix of Blaster and/or Matcher"
    print "         1: launch Blaster only"
    print "         2: launch Matcher only (on '*.align' query files)"
    print "         3: launch Blaster+Matcher in the same job (default)"
    print "     -B: parameters for Blaster (e.g. \"-a -n tblastx\")"
    print "     -M: parameters for Matcher (e.g. \"-j\")"
    print "     -Z: collect all the results into a single file (format 'align', 'path' or 'tab')"
    print "     -c: clean"
    print "     -v: verbose (default=0/1/2)"
    print

#-----------------------------------------------------------------------------

def main():

    """
    This program splits the input fasta file in a given number of files, launch Blaster and/or Matcher on them in parallel and collect the results afterwards.
    """

    qryFileName = ""
    sbjFileName = ""
    queue = ""
    tmpDir = ""
    configFileName = ""
    maxNbJobs = 10
    minQryPerJob = 1
    mix = "3"
    paramBlaster = ""
    paramMatcher = ""
    collectFormat = ""
    clean = False
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hq:s:Q:d:C:n:m:B:M:Z:cv:")
    except getopt.GetoptError, err:
        print str(err)
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
        elif o == "-Q":
            queue = a
        elif o == "-d":
            tmpDir = a
        elif o == "-C":
            configFileName = a
        elif o == "-n":
            maxNbJobs = int(a)
        elif o == "-m":
            mix = a
        elif o == "-B":
            paramBlaster = a
        elif o == "-M":
            paramMatcher = a
        elif o == "-Z":
            collectFormat = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if qryFileName == "" or configFileName == "" or collectFormat == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if not os.path.exists( qryFileName ):
        print "*** Error: query file '%s' doesn't exist" % ( qryFileName )
        sys.exit(1)
    if sbjFileName != "":
        if not os.path.exists( sbjFileName ):
            print "*** Error: subject file '%s' doesn't exist" % ( sbjFileName )
            sys.exit(1)
    else:
        sbjFileName = qryFileName

    pL = pyRepet.launcher.programLauncher.programLauncher()

    nbSeqQry = pyRepet.seq.fastaDB.dbSize( qryFileName )
    qryPerJob = nbSeqQry / float(maxNbJobs)

    # split the input query file in single files into a new directory
    prg = os.environ["REPET_PATH"] + "/bin/dbSplit.py"
    cmd = prg
    cmd += " -i %s" % ( qryFileName )
    if qryPerJob <= 1.0:
        cmd += " -n %i" % ( minQryPerJob )
    else:
        cmd += " -n %i" % ( qryPerJob + 1 )
    cmd += " -d"
    pL.launch( prg, cmd )

    # prepare the subject databank
    if sbjFileName != qryFileName:
        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -q %s" % ( sbjFileName )
        cmd += " -P"
        pL.launch( prg, cmd )

    # launch Blaster+Matcher in parallel
    prg = os.environ["REPET_PATH"] + "/bin/srptBlasterMatcher.py"
    cmd = prg
    cmd += " -g %s_vs_%s" % ( qryFileName, sbjFileName )
    cmd += " -q %s/batches" % ( os.getcwd() )
    cmd += " -s %s/%s" % ( os.getcwd(), sbjFileName )
    cmd += " -Q '%s'" % ( queue )
    if tmpDir != "":
        cmd += " -d %s" % ( tmpDir )
    cmd += " -m %s" % ( mix )
    if paramBlaster != "":
        cmd += " -B \"%s\"" % ( paramBlaster )
    if paramMatcher != "":
        cmd += " -M \"%s\"" % ( paramMatcher )
    cmd += " -Z %s" % ( collectFormat )
    cmd += " -C %s" % ( configFileName )
    if clean == True:
        cmd += " -c"
    cmd += " -v %i" % ( verbose - 1 )
    pL.launch( prg, cmd )

    suffix = ""
    if mix in ["2","3"]:
        if "-a" in paramMatcher:
            suffix = "match.%s" % ( collectFormat )
        else:
            suffix = "clean_match.%s" % ( collectFormat )
        os.system( "mv %s_vs_%s.%s %s_vs_%s.align.%s" % ( qryFileName, sbjFileName, collectFormat, qryFileName, sbjFileName, suffix ) )

    # clean
    if clean == True:
        prg = "rm"
        cmd = prg
        cmd += " -rf batches formatdb.log %s_cut* %s.Nstretch.map" % ( sbjFileName, sbjFileName )
        pL.launch( prg, cmd )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
