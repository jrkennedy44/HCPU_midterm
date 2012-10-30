#!/usr/bin/env python

import user, os, sys, getopt, exceptions, logging, glob

def setup_env():
    if "REPET_PATH" in os.environ.keys():
        sys.path.append( os.environ["REPET_PATH"] )
    else:
        print "*** Error: no environment variable REPET_PATH ***"
        sys.exit(1)
setup_env()

from pyRepet.sql.RepetJob import *
from pyRepet.launcher import Launcher

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "option:"
    print "    -h: this help"
    print "    -p: absolute path to project directory (if jobs management via files)"
    print "    -t: job table name"
    print "    -g: group id name" 
    print "    -q: absolute path to query directory"
    print "    -d: absolute path to temporary directory"
    print "    -Q: resources"
    print "    -P: parameters for RepeatMasker"
    print "    -C: collect all the results into a single file"
    print "    -c: clean (remove job launch files, job stdout and individual job results if '-C' is given)"
    print "    -v: verbose (default=0/1/2)"
    print ""

#-----------------------------------------------------------------------------

def runCollect( groupid, clean ):

    if verbose > 1:
        print "concatenate the results of each job"; sys.stdout.flush()

    if os.path.exists( "%s.path_tmp" % ( groupid ) ):
        os.system( "rm -f %s.path_tmp" % ( groupid ) )

    lPathFiles = glob.glob( "*.RMSSR.path" )

    # concatenate all the individual path files
    for pathFile in lPathFiles:
        prg = "cat"
        cmd = prg
        cmd += " %s >> %s.path_tmp" % ( pathFile, groupid )
        log = os.system( cmd )
        if log != 0:
            print "*** Error: %s returned %i" % ( prg, log )
            sys.exit(1)
        if clean == "yes":
            prg = "rm"
            cmd = prg
            cmd += " -f " + pathFile
            log = os.system( cmd )
            if log != 0:
                print "*** Error: %s returned %i" % ( prg, log )
                sys.exit(1)

    if os.path.exists( "%s.path" % ( groupid ) ):
        os.system( "rm -f %s.path" % ( groupid ) )

    # adapt the path IDs
    if os.path.exists( os.environ["REPET_PATH"] + "/bin/pathnum2id" ):
        prg = os.environ["REPET_PATH"] + "/bin/pathnum2id"
        cmd = prg
        cmd += " -i %s.path_tmp" % ( groupid )
        cmd += " -o %s.path" % ( groupid )
        cmd += " -v %i" % ( verbose - 1 )
    else:
        prg = os.environ["REPET_PATH"] + "/bin/pathnum2id.py"
        cmd = prg
        cmd += " -i %s.path_tmp" % ( groupid )
        cmd += " -o %s.path" % ( groupid )
    log = os.system( cmd )
    if log != 0:
        print "*** Error: %s returned %i" % ( prg, log )
        sys.exit(1)

    os.system( "rm -f %s.path_tmp" % ( groupid ) )

#-----------------------------------------------------------------------------

def main():

    projectDir = ""
    job_table = "jobs"
    groupid = ""
    query_dir = ""
    paramRM = ""
    queue = ""
    tmpdir = ""
    collect = "no"
    clean = "no"
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hp:t:g:q:Q:d:P:Ccv:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-p":
            projectDir = a
        elif o == "-t":
            job_table = a
        elif o == "-g":
            groupid = a
        elif o == "-q":
            query_dir = a
        elif o == "-Q":
            queue = a
        elif o == "-d":
            tmpdir = a
        elif o == "-P":
            paramRM = a
        elif o == "-C":
            collect = "yes"
        elif o == "-c":
            clean = "yes"
        elif o == "-v":
            verbose = int(a)

    if  job_table == "" or query_dir == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if os.environ["REPET_JOBS"] == "files" and projectDir == "":
        print "*** Error: missing compulsory options for jobs management via files"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    cdir = os.getcwd()
    #print "cdir ", cdir

    logfilename = cdir + "/" + groupid + "-" + str(os.getpid()) + ".log"
    handler = logging.FileHandler( logfilename )
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter( formatter )

    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )

    logging.info( "started" )

    if tmpdir == "":
        tmpdir = cdir

    if os.environ["REPET_JOBS"] == "files":
        jobdb = RepetJob( dbname = projectDir + "/" + os.environ["REPET_DB"] )
    elif os.environ["REPET_JOBS"] == "MySQL":
        jobdb = RepetJob()
    else:
        print "*** Error: REPET_JOBS is " + os.environ["REPET_JOBS"]
        sys.exit(1)

    # launch RMSSR in parallel on all the fasta files in 'query_dir'
    launcher = Launcher.RMSSRLauncher( jobdb, query_dir, paramRM, cdir, tmpdir, job_table, queue, groupid )
    launcher.run()

    # clean
    if clean == "yes":
        launcher.clean()

    # collect the results
    if collect == "yes":
        runCollect( groupid, clean )

    logging.info( "finished" )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
