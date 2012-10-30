#!/usr/bin/env python

"""
This program removes redundancy among queries compared to subjects.
"""

import os
import sys
import getopt
import logging
import time
import shutil

from pyRepet.launcher.programLauncher import programLauncher
from pyRepetUnit.commons.launcher.Launcher import Launcher
from pyRepetUnit.commons.sql.RepetJob import RepetJob
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
import ConfigParser


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
    print "     -o: output queries fasta filename (default=qryFileName+'.uniq')"
    print "     -i: identity threshold (default=0.95)"
    print "     -l: length threshold (default=0.98)"
    print "     -e: E-value threshold (default=1e-10)"
    print "     -f: length filter for Blaster (default=100)"
    print "     -Q: queue name to run in parallel"
    print "     -C: name of the configuration file"
    print "     -n: max. number of jobs (default=100,given a min. of 1 query per job)"
    print "     -c: clean"
    print "     -v: verbose (default=0/1/2)"
    print


def main():
    """
    This program removes redundancy among queries compared to subjects.
    """
    qryFileName = ""
    sbjFileName = ""
    outFileName = ""
    thresIdentity = 0.95   # remove the seq if it is identical to 95% of another seq
    thresLength = 0.98   # and if its length is 98% of that seq
    threshEvalue = "1e-10"
    lengthFilter = 100
    useCluster = False
    queue = ""
    configFileName = ""
    maxNbJobs = 100
    clean = False
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hq:s:o:L:i:l:e:w:f:Q:C:n:cv:")
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
        elif o == "-o":
            outFileName = a
        elif o == "-i":
            thresIdentity = float(a) 
        elif o == "-l":
            thresLength = float(a)
        elif o == "-e":
            threshEvalue = a
        elif o == "-f":
            lengthFilter = int(a)
        elif o == "-Q":
            useCluster = True
            queue = a
        elif o == "-C":
            configFileName = a
        elif o == "-n":
            maxNbJobs = int(a)
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)
            
    if thresIdentity > 1.0 or thresLength > 1.0:
        print "ERROR: thresholds must be <= 1.0"
        sys.exit(1)
    if qryFileName == "":
        print "ERROR: missing input file (-q)"
        help()
        sys.exit(1)
    if configFileName == "":
        print "ERROR: missing configuration file (-C)"
        sys.exit(1)
    if not os.path.exists( configFileName ):
        print "ERROR: configuration file doesn't exist"
        sys.exit(1)

    #--------------------------------------------------------------------------

    if verbose > 0:
        print "START %s (%s)" % ( sys.argv[0].split("/")[-1],
                                  time.strftime("%m/%d/%Y %H:%M:%S") )
        sys.stdout.flush()

    if outFileName == "":
        outFileName = "%s.uniq" % ( qryFileName )
        
    uniqId = "%s-%s" % ( time.strftime("%Y%m%d%H%M%S"), os.getpid() )

    # create the 'log' file
    logFileName = "%s_rmvRedundancy_%s.log" % ( outFileName, uniqId )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )

    if not os.path.exists( qryFileName ):
        string = "query file '%s' doesn't exist" % ( qryFileName )
        logging.error( string )
        print "ERROR: %s" % ( string )
        sys.exit(1)
    if sbjFileName != "":
        if not os.path.exists( sbjFileName ):
            string = "subject file '%s' doesn't exist" % ( sbjFileName )
            logging.error( string )
            print "ERROR: %s" % ( string )
            sys.exit(1)
    else:
        sbjFileName = qryFileName

    logging.info( "remove redundancy among '%s' (queries) compare to '%s' (subjects)" % ( qryFileName, sbjFileName ) )

    #--------------------------------------------------------------------------

    # check the input files are not empty, otherwise exit

    nbSeqQry = FastaUtils.dbSize( qryFileName )
    if nbSeqQry == 0:
        string = "query file is empty"
        logging.info( string )
        print "WARNING: %s" % ( string )
        logging.info( "finished" )
        sys.exit(0)

    nbSeqSbj = FastaUtils.dbSize( sbjFileName )
    if sbjFileName != qryFileName:
        nbSeqSbj = FastaUtils.dbSize( sbjFileName )
        if nbSeqSbj == 0:
            string = "subject file is empty"
            logging.info( string )
            print "WARNING: %s" % ( string )
            logging.info( "finished" )
            sys.exit(0)

    #--------------------------------------------------------------------------

    pL = programLauncher()
    uniqTmpDir = "tmp%s" % ( uniqId )
    if os.path.exists( uniqTmpDir ):
        shutil.rmtree( uniqTmpDir )
    os.mkdir( uniqTmpDir )
    os.chdir( uniqTmpDir )
    os.system( "ln -s ../%s ." % ( qryFileName ) )
    if sbjFileName != qryFileName:
        os.system( "ln -s ../%s ." % ( sbjFileName ) )
    os.system( "ln -s ../%s ." % ( logFileName ) )
    if useCluster:
        os.system( "ln -s ../%s ." % ( configFileName ) )
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        queue = config.get("classif_consensus", "resources")
        cDir = os.getcwd()
        if config.get("classif_consensus", "tmpDir" ) != "":
            tmpDir = config.get("classif_consensus", "tmpDir")
        else:
            tmpDir = cDir

    lCmds=[]
    # shorten sequence headers
    if sbjFileName == qryFileName:
        # sort sequences by increasing length
    
        os.system( "mv %s %s.initOrder" % ( qryFileName, qryFileName ) )
            
        prg = os.environ["REPET_PATH"] + "/bin/srptSortSequencesByIncreasingLength.py"
        cmd = prg
        cmd += " -i %s.initOrder" % ( qryFileName )
        cmd += " -o %s" % ( qryFileName )
        cmd += " -v %d" % ( verbose-1 )
        lCmds.append(cmd)

        prg = os.environ["REPET_PATH"] + "/bin/shortenSeqHeader.py"
        cmd = prg
        cmd += " -i %s" % ( qryFileName )
        lCmds.append(cmd)
        if not useCluster:
            for c in lCmds:
                pL.launch( prg, c )
        else:
            groupid = "%s_SubjectEqualQuery_sortSequencesAndShortenSeqHeader" % ( "rmvRedundancy" )
            acronym = "sortSequencesAndShortenSeqHeader"
            jobdb = RepetJob( cfgFileName = configFileName )
            cLauncher = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
            cLauncher.beginRun()
            cLauncher.job.jobname = acronym
            cmd_start = ""
            cmd_start += "os.system( \"ln -s %s/%s.initOrder .\" )\n" % ( cDir, qryFileName )
            for c in lCmds:
                cmd_start += "log = os.system( \""
                cmd_start += c
                cmd_start += "\" )\n"
            cmd_finish = "if not os.path.exists( \"%s/%s.shortH\" ):\n" % ( cDir, qryFileName )
            cmd_finish += "\tos.system( \"mv %s.shortH %s/.\" )\n" % ( qryFileName, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.shortHlink\" ):\n" % ( cDir, qryFileName )
            cmd_finish += "\tos.system( \"mv %s.shortHlink %s/.\" )\n" % ( qryFileName, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.initOrder\" ):\n" % ( cDir, qryFileName )
            cmd_finish += "\tos.system( \"mv %s.initOrder %s/.\" )\n" % ( qryFileName, cDir )
            cLauncher.runSingleJob( cmd_start, cmd_finish )
            cLauncher.endRun()
            if config.get("classif_consensus","clean") == "yes":
                cLauncher.clean( acronym )
            jobdb.close()
    else:
        prg = os.environ["REPET_PATH"] + "/bin/shortenSeqHeader.py"
        cmd = prg
        cmd += " -i %s" % ( qryFileName )
        cmd += " -p %s" % ( "qry" )
        lCmds.append(cmd)
    
        cmd = prg
        cmd += " -i %s" % ( sbjFileName )
        cmd += " -p %s" % ( "sbj" )
        lCmds.append(cmd)
        if not useCluster:
            for c in lCmds:
                pL.launch( prg, c )
        else:
            acronym = "shortenSeqHeader"
            groupid = "rmvRedundancy_SubjectNotEqualQuery_shortenSeqHeader"
            jobdb = RepetJob( cfgFileName = configFileName )
            cLauncher = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
            cLauncher.beginRun()
            cLauncher.job.jobname = acronym
            cmd_start = ""
            cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, qryFileName )
            cmd_start += "os.system( \"ln -s %s/%s .\" )\n" % ( cDir, sbjFileName )
            for c in lCmds:
                cmd_start += "log = os.system( \""
                cmd_start += c
                cmd_start += "\" )\n"
            cmd_finish = "if not os.path.exists( \"%s/%s.shortH\" ):\n" % ( cDir, qryFileName )
            cmd_finish += "\tos.system( \"mv %s.shortH %s/.\" )\n" % ( qryFileName, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.shortHlink\" ):\n" % ( cDir, qryFileName )
            cmd_finish += "\tos.system( \"mv %s.shortHlink %s/.\" )\n" % ( qryFileName, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.shortH\" ):\n" % ( cDir, sbjFileName )
            cmd_finish += "\tos.system( \"mv %s.shortH %s/.\" )\n" % ( sbjFileName, cDir )
            cmd_finish += "if not os.path.exists( \"%s/%s.shortHlink\" ):\n" % ( cDir, sbjFileName )
            cmd_finish += "\tos.system( \"mv %s.shortHlink %s/.\" )\n" % ( sbjFileName, cDir )
            cLauncher.runSingleJob( cmd_start, cmd_finish )
            cLauncher.endRun()
            if config.get("classif_consensus", "clean") == "yes":
                cLauncher.clean( acronym )
            jobdb.close()
            
    #--------------------------------------------------------------------------
    # case not in parallel
    if useCluster == False:

        # run Blaster
        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -q %s.shortH" % ( qryFileName )
        cmd += " -s %s.shortH" % ( sbjFileName )
        cmd += " -a"
        cmd += " -I %i" % ( int(100*thresIdentity) )
        cmd += " -L %i" % ( lengthFilter )
        cmd += " -E %s" % ( threshEvalue )
        cmd += " -B %s.shortH_vs_%s.shortH" % ( qryFileName, sbjFileName )
        pL.launch( prg, cmd )

        # run Matcher
        prg = os.environ["REPET_PATH"] + "/bin/matcher"
        cmd = prg
        cmd += " -m %s.shortH_vs_%s.shortH.align" % ( qryFileName, sbjFileName )
        cmd += " -q %s.shortH" % ( qryFileName )
        cmd += " -s %s.shortH" % ( sbjFileName )
        cmd += " -j"
        cmd += " -a"
        pL.launch( prg, cmd )

    #--------------------------------------------------------------------------
    
    # case in parallel
    elif useCluster == True:
        # run Blaster + Matcher
        prg = os.environ["REPET_PATH"] + "/bin/launchBlasterMatcherPerQuery.py"
        cmd = prg
        cmd += " -q %s.shortH" % ( qryFileName )
        cmd += " -s %s.shortH" % ( sbjFileName )
        cmd += " -Q '%s'" % ( queue )
        cmd += " -d %s" % ( os.getcwd() )
        cmd += " -C %s" % ( configFileName )
        cmd += " -n %i" % ( maxNbJobs )
        cmd += " -B \"-a -I %s -L %s -E %s\"" % ( int(100*thresIdentity), lengthFilter, threshEvalue )
        cmd += " -M \"%s\"" % ( "-j -a" )
        cmd += " -Z tab"
        if clean == True:
            cmd += " -c"
        cmd += " -v %i" % ( verbose - 1 )
        pL.launch( prg, cmd )

    #--------------------------------------------------------------------------

    # filter the resulting 'tab' file
    prg = os.environ["REPET_PATH"] + "/bin/filterOutMatcher.py"
    cmd = prg
    cmd += " -q %s.shortH" % ( qryFileName )
    if sbjFileName != qryFileName:
        cmd += " -s %s.shortH" % ( sbjFileName )
    cmd += " -m %s.shortH_vs_%s.shortH.align.match.tab" % ( qryFileName, sbjFileName )
    cmd += " -o %s.shortH.filtered" % ( qryFileName )
    cmd += " -i %f" % ( thresIdentity )
    cmd += " -l %f" % ( thresLength )
    cmd += " -L %s" % ( logFileName )
    cmd += " -v %i" % ( verbose )
    
    if not useCluster:
        pL.launch( prg, cmd )
    else:
        groupid = "rmvRedundancy_filterOutMatcher"
        acronym = "filterOutMatcher"
        jobdb = RepetJob( cfgFileName = configFileName )
        cLauncher = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s.shortH .\" )\n" % ( cDir, qryFileName )
        if sbjFileName != qryFileName:
            cmd_start += "os.system( \"ln -s %s/%s.shortH .\" )\n" % ( cDir, sbjFileName )
        cmd_start += "os.system( \"ln -s %s/%s.shortH_vs_%s.shortH.align.match.tab .\" )\n" % ( cDir, qryFileName, sbjFileName )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/%s.shortH.filtered\" ):\n" % ( cDir, qryFileName )
        cmd_finish += "\tos.system( \"mv %s.shortH.filtered %s/.\" )\n" % ( qryFileName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s.shortH_vs_%s.shortH.align.match.tab\" ):\n" % ( cDir, qryFileName, sbjFileName )
        cmd_finish += "\tos.system( \"mv %s.shortH_vs_%s.shortH.align.match.tab %s/.\" )\n" % ( qryFileName, sbjFileName, cDir )
        cmd_finish += "if not os.path.exists( \"%s/%s\" ):\n" % ( cDir, logFileName )
        cmd_finish += "\tos.system( \"mv %s %s/.\" )\n" % ( logFileName, cDir )
        cLauncher.runSingleJob( cmd_start, cmd_finish )
        cLauncher.endRun()
        if config.get("classif_consensus", "clean") == "yes":
            cLauncher.clean( acronym )
        jobdb.close()
        
    # retrieve initial headers
    prg = os.environ["REPET_PATH"] + "/bin/ChangeSequenceHeaders.py"
    cmd = prg
    cmd += " -i %s.shortH.filtered" % ( qryFileName )
    cmd += " -f fasta"
    cmd += " -s 2"
    cmd += " -l %s.shortHlink" % ( qryFileName )
    cmd += " -o %s" % ( outFileName )
    
    if not useCluster:
        pL.launch( prg, cmd )
    else:
        groupid = "rmvRedundancy_ChangeSequenceHeaders"
        acronym = "ChangeSequenceHeaders"
        jobdb = RepetJob( cfgFileName = configFileName )
        cLauncher = Launcher( jobdb, os.getcwd(), "", "", cDir, tmpDir, "jobs", queue, groupid, acronym )
        cLauncher.beginRun()
        cLauncher.job.jobname = acronym
        cmd_start = ""
        cmd_start += "os.system( \"ln -s %s/%s.shortH.filtered .\" )\n" % ( cDir, qryFileName )
        cmd_start += "os.system( \"ln -s %s/%s.shortHlink .\" )\n" % ( cDir, qryFileName )
        cmd_start += "log = os.system( \""
        cmd_start += cmd
        cmd_start += "\" )\n"
        cmd_finish = "if not os.path.exists( \"%s/%s\" ):\n" % ( cDir, outFileName )
        cmd_finish += "\tos.system( \"mv %s %s/.\" )\n" % ( outFileName, cDir )
        cLauncher.runSingleJob( cmd_start, cmd_finish )
        cLauncher.endRun()
        if config.get("classif_consensus", "clean") == "yes":
            cLauncher.clean( acronym )
        jobdb.close()

    # future improvement: give file '.shortHlink' to 'filterOutMatcher.py' so that it saves the information about which match removed which query, with the true headers

    os.system( "mv %s .." % ( outFileName ) )
    os.chdir( ".." )
    if clean == True:
        shutil.rmtree( uniqTmpDir )

    logging.info( "finished" )

    if verbose > 0:
        print "END %s (%s)" % ( sys.argv[0].split("/")[-1],
                                time.strftime("%m/%d/%Y %H:%M:%S") )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
