#!/usr/bin/env python

# DEPRECATED

import user, os, sys, getopt, exceptions, logging, ConfigParser

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.sql.RepetJob
import pyRepet.launcher.Launcher

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print
    print "DEPRECATED"
    print
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -g: name of the group identifier (same for all the jobs)"
    print "     -q: name of the query directory"
    print "     -S: suffix in the query directory  (default='*.fa')"
    print "     -Q: name of the queue (on the cluster)"
    print "     -d: absolute path to the temporary directory"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -t: job table name (default=jobs)"
    print "     -p: absolute path to project directory (if jobs management via files)"
    print "     -c: clean (remove job launch files and job stdout)"
    print "     -v: verbose (default=0/1/2)"
    print

#-----------------------------------------------------------------------------

def main():

    """
    This program takes a directory as input and launches MAP on each file in it.
    """

    groupid = ""
    queryDir = ""
    patternSuffix = "*.fa"
    queue = ""
    tmpDir = ""
    configFileName = ""
    jobTable = "jobs"
    projectDir = ""
    clean = False
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hg:q:S:Q:d:C:t:p:cv:")
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
        elif o == "-S":
            patternSuffix = a
        elif o == "-Q":
            queue = a
        elif o == "-d":
            tmpDir = a
        elif o == "-C":
            configFileName = a
        elif o == "-t":
            jobTable = a
        elif o == "-p":
            projectDir = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if  groupid == "" or queryDir == "":
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

    #--------------------------------------------------------------------------

    # create the 'log' file

    logFileName = "%s_pid%s.log" % ( groupid, os.getpid() )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )


    # open a connection to the MySQL table

    if configFileName != "":
        if not os.path.exists( configFileName ):
            print "*** Error: configuration file '%s' doesn't exist" % ( configFileName )
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
        jobdb = pyRepet.sql.RepetJob.RepetJob( dbname = projectDir + "/" + os.environ["REPET_DB"] )
    elif os.environ["REPET_JOBS"] == "MySQL":
        jobdb = pyRepet.sql.RepetJob.RepetJob( user, host, passwd, dbname )
    else:
        print "*** Error: REPET_JOBS is '%s'" % ( os.environ["REPET_JOBS"] )
        sys.exit(1)


    currentDir = os.getcwd()
    if tmpDir == "":
        tmpDir = currentDir

    # launch MAP on each fasta file in queryDir
    cL = pyRepet.launcher.Launcher.MapLauncher( jobdb=jobdb, query=queryDir, cdir=currentDir, tmpdir=tmpDir, job_table=jobTable, queue=queue, groupid=groupid, acro="Map" )
    cL.run( patternSuffix )

    # clean
    if clean == True:
        cL.clean()


    logging.info( "finished" )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
