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

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "option:"
    print "    -h: this help"
    print "    -p: absolute path to project directory (if jobs management via files)"
    print "    -t: job table name"
    print "    -g: group id name"
    print "    -q: query directory name"
    print "    -s: subject database name"
    print "    -Q: queue name"
    print "    -d: temporary directory (absolute path)"
    print "    -P: RepeatMasker parameters"
    print "    -c: clean (remove job launch files and job stdout)"
    print ""

#-----------------------------------------------------------------------------

def main():

    projectDir = ""
    job_table = "jobs"
    groupid = ""
    query_dir = ""
    subject_db = ""
    paramRM = ""
    queue = ""
    tmpdir = ""
    clean = "no"

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hp:t:g:q:s:Q:d:P:c")
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
        elif o == "-s":
            subject_db = a
        elif o == "-P":
            paramRM = a
        elif o == "-Q":
            queue = a
        elif o == "-d":
            tmpdir = a
        elif o == "-c":
            clean = "yes"

    if  job_table == "" or subject_db == "" or query_dir == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if os.environ["REPET_JOBS"] == "files" and projectDir == "":
        print "*** Error: missing compulsory options for jobs management via files"
        help()
        sys.exit(1)

    print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
    sys.stdout.flush()

    cdir = os.getcwd()
    #print "cdir ", cdir

    logfilename = cdir + "/" + groupid + "-" + str(os.getpid()) + ".log"
    handler = logging.FileHandler( logfilename )
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter( formatter )

    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.DEBUG)

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

    # launch RepeatMasker on each chunk in query_dir
    launcher = Launcher.RMLauncher( jobdb, query_dir, subject_db, paramRM, cdir, tmpdir, job_table, queue, groupid )
    launcher.run()

    # clean
    if clean == "yes":
        launcher.clean()

    logging.info( "finished" )

    print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
    sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
