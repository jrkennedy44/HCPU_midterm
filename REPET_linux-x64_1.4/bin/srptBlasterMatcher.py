#!/usr/bin/env python

"""
This program takes a query directory as input,
then launches Blaster and/or Matcher on each file in it,
finally results are optionally gathered in a single file.
"""

import os
import sys
import getopt
import logging
import glob
import ConfigParser

from pyRepet.launcher.programLauncher import programLauncher
from pyRepet.launcher import Launcher
from pyRepet.sql.RepetJob import RepetJob
from pyRepetUnit.commons.coord.Align import Align


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -g: name of the group identifier (same for all the jobs)"
    print "     -q: name of the query directory"
    print "     -S: suffix in the query directory (default='*.fa' for Blaster, '*.align' for Matcher)"
    print "     -s: absolute path to the subject databank"
    print "     -Q: resources needed on the cluster)"
    print "     -d: absolute path to the temporary directory"
    print "     -m: mix of Blaster and/or Matcher"
    print "         1: launch Blaster only"
    print "         2: launch Matcher only (on '*.align' query files)"
    print "         3: launch Blaster+Matcher in the same job"
    print "     -B: parameters for Blaster (e.g. \"-a -n tblastx\")"
    print "     -M: parameters for Matcher (e.g. \"-j\")"
    print "     -Z: collect all the results into a single file"
    print "         align (after Blaster)"
    print "         path/tab (after Matcher)"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -t: name of the table recording the jobs (default=jobs)"
    print "     -p: absolute path to project directory (if jobs management via files)"
    print "     -c: clean (remove job launch files and job stdout)"
    print "     -v: verbose (default=0/1/2)"
    print


def filterRedundantMatches( inFile, outFile ):
    """
    When a pairwise alignment is launched ~ all-by-all (ie one batch against all chunks),
    one filters the redundant matches. For instance we keep 'chunk3-1-100-chunk7-11-110-...'
    and we discards 'chunk7-11-110-chunk3-1-100-...'.
    Also we keep 'chunk5-1-100-chunk5-11-110-...' and we discards
    'chunk5-11-110-chunk5-1-100-...'.
    For this of course the results need to be sorted by query, on plus strand,
    and in ascending coordinates (always the case with Blaster).
    """
    inFileHandler = open( inFile, "r" )
    outFileHandler = open( outFile, "w" )
    iAlign = Align()
    countMatches = 0
    tick = 100000
    while True:
        line = inFileHandler.readline()
        if line == "":
            break
        countMatches += 1
        iAlign.setFromString( line )
        if "chunk" not in iAlign.range_query.seqname \
               or "chunk" not in iAlign.range_subject.seqname:
            print "ERROR: 'chunk' not in seqname"
            sys.exit(1)
        if int(iAlign.range_query.seqname.split("chunk")[1]) < int(iAlign.range_subject.seqname.split("chunk")[1]):
            iAlign.write( outFileHandler )
        elif int(iAlign.range_query.seqname.split("chunk")[1]) == int(iAlign.range_subject.seqname.split("chunk")[1]):
            if iAlign.range_query.getMin() < iAlign.range_subject.getMin():
                iAlign.write( outFileHandler )
        if countMatches % tick == 0:   # need to free buffer frequently as file can be big
            outFileHandler.flush()
            os.fsync( outFileHandler.fileno() )
    inFileHandler.close()
    outFileHandler.close()


def runCollect( groupid, collect, allByAll ):
    """
    Gather the results of each job in a single job and adapt path ID if necessary.
    """
    if verbose > 0:
        print "concatenate the results of each job"; sys.stdout.flush()

    # retrieve the list of the files
    lFiles = glob.glob( "*.%s" % ( collect ) )
    lFiles.sort()

    # concatenate all the individual files
    if os.path.exists( "%s.%s_tmp" % ( groupid, collect ) ):
        os.remove( "%s.%s_tmp" % ( groupid, collect ) )
    for resFile in lFiles:
        prg = "cat"
        cmd = prg
        cmd += " %s >> %s.%s_tmp" % ( resFile, groupid, collect )
        pL.launch( prg, cmd )
        if clean == True:
            prg = "rm"
            cmd = prg
            cmd += " -f %s" % ( resFile )
            pL.launch( prg, cmd )

    if os.path.exists( "%s.%s" % ( groupid, collect ) ):
        os.remove( "%s.%s" % ( groupid, collect ) )

    if collect == "align":
        if not allByAll:
            os.system( "mv %s.%s_tmp %s.%s" % ( groupid, collect, groupid, collect ) )
        else:
            filterRedundantMatches( "%s.%s_tmp" % ( groupid, collect ),
                                    "%s.%s" % ( groupid, collect ) )

    # adapt the path IDs if necessary
    elif collect == "path":
        prg = os.environ["REPET_PATH"] + "/bin/"
        if os.path.exists( prg + "pathnum2id" ):
            prg += "pathnum2id"
            cmd = prg
            cmd += " -i %s.path_tmp" % ( groupid )
            cmd += " -o %s.path" % ( groupid )
            cmd += " -v %i" % ( verbose - 1 )
            pL.launch( prg, cmd )
        else:
            prg += "pathnum2id.py"
            cmd = prg
            cmd += " -i %s.path_tmp" % ( groupid )
            cmd += " -o %s.path" % ( groupid )
            pL.launch( prg, cmd )

    elif collect == "tab":
        prg = os.environ["REPET_PATH"] + "/bin/"
        if os.path.exists( prg + "tabnum2id" ):
            prg += "tabnum2id"
            cmd = prg
            cmd += " -i %s.tab_tmp" % ( groupid )
            cmd += " -o %s.tab" % ( groupid )
            cmd += " -v %i" % ( verbose - 1 )
            pL.launch( prg, cmd )
        else:
            prg += "tabnum2id.py"
            cmd = prg
            cmd += " -i %s.tab_tmp" % ( groupid )
            cmd += " -o %s.tab" % ( groupid )
            pL.launch( prg, cmd )

    if clean == True:
        os.remove( "%s.%s_tmp" % ( groupid, collect ) )


def main():
    """
    This program takes a query directory as input,
    then launches Blaster and/or Matcher on each file in it,
    finally results are optionally gathered in a single file.
    """

    groupid = ""
    queryDir = ""
    patternSuffix = ""
    subjectBank = ""
    queue = ""
    tmpDir = ""
    mix = ""
    paramBlaster = ""
    paramMatcher = ""
    collect = ""
    configFileName = ""
    jobTable = "jobs"
    projectDir = ""
    global clean
    clean = False
    global verbose
    verbose = 0
    allByAll = False

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hg:q:S:s:Q:d:m:B:M:Z:C:t:p:cv:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-g":
            groupid = a
        elif o == "-q":
            queryDir = a
            if queryDir[-1] == "/":
                queryDir = queryDir[:-1]
        elif o == "-S":
            patternSuffix = a
        elif o == "-s":
            subjectBank = a
        elif o == "-Q":
            queue = a
        elif o == "-d":
            tmpDir = a
            if tmpDir[-1] == "/":
                tmpDir = tmpDir[:-1]
        elif o == "-m":
            mix = a
        elif o == "-B":
            paramBlaster = a
        elif o == "-M":
            paramMatcher = a
        elif o == "-C":
            configFileName = a
        elif o == "-Z":
            collect = a
        elif o == "-t":
            jobTable = a
        elif o == "-p":
            projectDir = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if groupid == "":
        print "ERROR: missing group identifier (-g)"
        help()
        sys.exit(1)

    if queryDir == "":
        print "ERROR: missing query directory (-q)"
        help()
        sys.exit(1)

    if mix in [ "1", "3" ] and subjectBank == "":
        print "ERROR: missing subject bank for Blaster"
        sys.exit(1)

    if os.environ["REPET_JOBS"] == "files" and projectDir == "":
        print "ERROR: missing compulsory options for jobs management via files"
        help()
        sys.exit(1)

    if not os.path.exists( queryDir ):
        print "ERROR: can't find query directory '%s'" % ( queryDir )
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()


    logFileName = "%s_pid%s.log" % ( groupid, os.getpid() )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )


    if configFileName != "":
        if not os.path.exists( configFileName ):
            print "ERROR: configuration file '%s' doesn't exist" % ( configFileName )
            sys.exit(1)
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env","repet_host")
        user = config.get("repet_env","repet_user")
        passwd = config.get("repet_env","repet_pw")
        dbname = config.get("repet_env","repet_db")
    else:
        host = os.environ["REPET_HOST"]
        user = os.environ["REPET_USER"]
        passwd = os.environ["REPET_PW"]
        dbname = os.environ["REPET_DB"]

    if os.environ["REPET_JOBS"] == "files":
        jobdb = RepetJob( dbname = projectDir + "/" + os.environ["REPET_DB"] )
    elif os.environ["REPET_JOBS"] == "MySQL":
        jobdb = RepetJob( user, host, passwd, dbname )
    else:
        print "ERROR: REPET_JOBS is '%s'" % ( os.environ["REPET_JOBS"] )
        sys.exit(1)


    currentDir = os.getcwd()
    if tmpDir == "":
        tmpDir = currentDir

    global pL
    pL = programLauncher()

    if "-a" in paramBlaster:
        allByAll = True


    # if Blaster will be launched, prepare the subject data if necessary
    if mix != "2" and not os.path.exists( "%s_cut" % ( subjectBank ) ):
        if verbose > 0:
            print "prepare subject bank '%s'..." % ( subjectBank.split("/")[-1] )
            sys.stdout.flush()
        prg = os.environ["REPET_PATH"] + "/bin/blaster"
        cmd = prg
        cmd += " -q %s" % ( subjectBank )
        cmd += " %s" % ( paramBlaster )
        cmd += " -P"
        pL.launch( prg, cmd )


    # launch Blaster only (on '*.fa' in queryDir)
    if mix == "1":
        launcher = Launcher.BlasterLauncher( jobdb, queryDir, subjectBank, paramBlaster, currentDir, tmpDir, jobTable, queue, groupid, "Blaster" )
        if patternSuffix == "":
            patternSuffix = "*.fa"
        launcher.run( patternSuffix, verbose )
        if clean == True:
            launcher.clean()

    # launch Matcher only (on '*.align' in queryDir; don't use '-q' or '-s', only '-m')
    elif mix == "2":
        launcher = Launcher.MatcherLauncher( jobdb, queryDir, subjectBank, paramMatcher, currentDir, tmpDir, jobTable, queue, groupid, "Matcher" )
        if patternSuffix == "":
            patternSuffix = "*.align"
        launcher.run( patternSuffix, verbose  )
        if clean == True:
            launcher.clean()

    # launch Blaster+Matcher (on '*.fa' in queryDir)
    elif mix == "3":
        launcher = Launcher.Launcher( jobdb, queryDir, subjectBank, paramBlaster, currentDir, tmpDir, jobTable, queue, groupid, "BlasterMatcher" )
        launcher.beginRun()
        if patternSuffix == "":
            patternSuffix = "*.fa"
        lFaFiles = glob.glob( queryDir + "/" + patternSuffix )
        if len(lFaFiles) == 0:
            print "ERROR: query directory '%s' is empty of suffix '%s'" % ( queryDir, patternSuffix )
            sys.exit(1)
        count = 0
        for inFaName in lFaFiles:
            count += 1
            launcher.acronyme = "BlasterMatcher_%i" % ( count )
            launcher.job.jobname = launcher.acronyme
            prefix = os.path.basename( inFaName )
            cmd_start = ""
            cmd_start += "if not os.path.exists( \"" + prefix + "\" ):\n"
            cmd_start += "\tos.system( \"cp " + inFaName + " .\" )\n"
            launchB = ""
            launchB += os.environ["REPET_PATH"] + "/bin/blaster"
            launchB += " -q %s" % ( prefix )
            launchB += " -s %s" % ( subjectBank )
            launchB += " -B %s" % ( prefix )
            if paramBlaster != "":
                launchB += " %s" % ( paramBlaster )
            cleanB = ""
            cleanB += "if not os.path.exists( \"%s/%s.param\" ):\n" % ( currentDir, prefix )
            cleanB += "\tos.system( \"mv %s.param %s\" )\n" % ( prefix, currentDir )
            cleanB += "if os.path.exists( \"" + prefix + ".Nstretch.map\" ):\n"
            cleanB += "\tos.remove( \"" + prefix + ".Nstretch.map\" )\n"
            cleanB += "if os.path.exists( \"" + prefix + "_cut\" ):\n"
            cleanB += "\tos.system( \"rm -f " + prefix + "_cut*\" )\n"
            cleanB += "if os.path.exists( \"" + prefix + ".raw\" ):\n"
            cleanB += "\tos.remove( \"" + prefix + ".raw\" )\n"
            cleanB += "if os.path.exists( \"" + prefix + ".seq_treated\" ):\n"
            cleanB += "\tos.remove( \"" + prefix + ".seq_treated\" )\n"
            launchM = ""
            launchM += os.environ["REPET_PATH"] + "/bin/matcher"
            launchM += " -m %s.align" % ( prefix )
            launchM += " -q %s" % ( prefix )
            launchM += " -s %s" % ( subjectBank )
            if paramMatcher != "":
                launchM += " %s" % ( paramMatcher )
            cleanM = ""
            s = ""
            if "-a" in paramMatcher:
                s = "match"
            else:
                s = "clean_match"
            if collect == "path":
                cleanM += "if not os.path.exists( \"%s/%s.align.%s.path\" ):\n" % ( currentDir, prefix, s )
                cleanM += "\tos.system( \"mv %s.align.%s.path %s\" )\n" % ( prefix, s, currentDir )
                cleanM += "if os.path.exists( \"" + prefix + ".align."+s+".tab\" ):\n"
                cleanM += "\tos.remove( \"" + prefix + ".align."+s+".tab\" )\n"
            elif collect == "tab":
                cleanM += "if not os.path.exists( \"%s/%s.align.%s.tab\" ):\n" % ( currentDir, prefix, s )
                cleanM += "\tos.system( \"mv %s.align.%s.tab %s\" )\n" % ( prefix, s, currentDir )
                cleanM += "if os.path.exists( \"" + prefix + ".align."+s+".path\" ):\n"
                cleanM += "\tos.remove( \"" + prefix + ".align."+s+".path\" )\n"
            cleanM += "if not os.path.exists( \"%s/%s.align.%s.param\" ):\n" % ( currentDir, prefix, s )
            cleanM += "\tos.system( \"mv %s.align.%s.param %s\" )\n" % ( prefix, s, currentDir )
            if tmpDir != currentDir:
                cleanM += "if os.path.exists( \"%s\" ):\n" % ( prefix )
                cleanM += "\tos.remove( \"%s\" )\n" % ( prefix )
            if clean == True:
                cleanM += "if os.path.exists( \"" + prefix + ".align\" ):\n"
                cleanM += "\tos.remove( \"" + prefix + ".align\" )\n"
            else:
                cleanM += "if not os.path.exists( \"%s/%s.align\" ):\n" % ( currentDir, prefix )
                cleanM += "\tos.system( \"mv %s.align %s\" )\n" % ( prefix, currentDir )
            cleanM += "if os.path.exists( \"" + prefix + ".align."+s+".fa\" ):\n"
            cleanM += "\tos.remove( \"" + prefix + ".align."+s+".fa\" )\n"
            cleanM += "if os.path.exists( \"" + prefix + ".align."+s+".map\" ):\n"
            cleanM += "\tos.remove( \"" + prefix + ".align."+s+".map\" )\n"
            cmd_start += "print \"" + launchB + "\"; sys.stdout.flush()\n"
            cmd_start += "log = os.system( \"" + launchB + "\" )\n"
            cmd_start += "if log != 0:\n"
            cmd_start += launcher.cmd_test( launcher.job, "error", loop=1 )
            cmd_start += "\tsys.exit(1)\n"
            cmd_start += cleanB
            cmd_start += "print \"" + launchM + "\"; sys.stdout.flush()\n"
            cmd_start += "log = os.system( \"" + launchM + "\" )\n"
            cmd_start += cleanM
            launcher.runSingleJob( cmd_start )
        launcher.acronyme = "BlasterMatcher"
        launcher._nbJobs = count
        launcher.endRun()
        if clean == True:
            launcher.clean( "BlasterMatcher_*" )

    else:
        print "ERROR: option '-m %s' not recognized" % ( mix )
        sys.exit(1)


    if collect != "":
        if collect in [ "align", "path", "tab" ]:
            runCollect( groupid, collect, allByAll )
        else:
            print "ERROR: collect '%s' not implemented" % ( collect )
            sys.exit(1)


    logging.info( "finished" )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
