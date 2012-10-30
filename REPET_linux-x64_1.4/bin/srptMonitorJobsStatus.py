#!/usr/bin/env python

import os
import sys
import getopt
import ConfigParser

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.sql.RepetDBMySQL


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -g: group id name"
    print "     -t: job table name (default=jobs)"
    print "     -c: configuration file from TEdenovo or TEannot pipeline"
    print "     -p: absolute path to project directory (if no configuration file)"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -s: status of jobs for which we want the ID in a file called 'log'"
    print


def main():

    groupid = ""
    tablename = "jobs"
    configFileName = ""
    projectDir = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    port = ""
    logStatus = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hg:t:c:p:H:U:P:D:T:s:")
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
        elif o == "-t":
            tablename = a
        elif o == "-c":
            configFileName = a
        elif o == "-p":
            projectDir = a
        elif o == "-H":
            host = a
        elif o == "-U":
            user = a 
        elif o == "-P":
            passwd = a
        elif o == "-D":
            dbname = a
        elif o == "-T":
            port = a
        elif o == "-s":
            logStatus = a

    if os.environ["REPET_JOBS"] == "files" and projectDir == "":
        print "ERROR: missing compulsory options for jobs management via files"
        help()
        sys.exit(1)

    if configFileName != "":
        if not os.path.exists( configFileName ):
            print "ERROR: can't find file '%s'" % ( configFileName )
            help()
            sys.exit(1)
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env","repet_host")
        user = config.get("repet_env","repet_user")
        passwd = config.get("repet_env","repet_pw")
        dbname = config.get("repet_env","repet_db")
        port = config.get("repet_env","repet_port")
    else:
        if host == "" or user == "" or passwd == "" or dbname == "" or port == "":
            if os.environ.has_key( "REPET_HOST" ):
                host = os.environ[ "REPET_HOST" ]
            else:
                print "ERROR: no environment variable REPET_HOST"
                sys.exit(1)
            if os.environ.has_key( "REPET_USER" ):
                user = os.environ[ "REPET_USER" ]
            else:
                print "ERROR: no environment variable REPET_USER"
                sys.exit(1)
            if os.environ.has_key( "REPET_PW" ):
                passwd = os.environ[ "REPET_PW" ]
            else:
                print "ERROR: no environment variable REPET_PW"
                sys.exit(1)
            if os.environ.has_key( "REPET_DB" ):
                dbname = os.environ[ "REPET_DB" ]
            else:
                print "ERROR: no environment variable REPET_DB"
                sys.exit(1)
            if os.environ.has_key( "REPET_PORT" ):
                port = os.environ[ "REPET_PORT" ]
            else:
                print "ERROR: no environment variable REPET_PORT"
                sys.exit(1)

    db = pyRepet.sql.RepetDBMySQL.RepetDB( user, host, passwd, dbname, port )

    if logStatus != "":
        logFile = open( "log", "w" )

    if os.environ["REPET_JOBS"] == "MySQL":
        req = "SELECT DISTINCT groupid FROM %s" % ( tablename )
        db.execute( req )
        res = db.fetchall()
        groupidPresent = False
        for i in res:
            if groupid in i:
                groupidPresent = True
        if groupid == "":
            print "WARNING: you have to choose a groupid among"
            for i in res:
                print i[0]
            sys.exit(1)
        if groupidPresent == False:
            print "ERROR: unknown groupid '%s'" % ( groupid )
            sys.exit(1)
        req = "SELECT status,count(*) FROM %s WHERE groupid=\"%s\" group by status" % ( tablename, groupid )
        db.execute( req )
        res = db.fetchall()
        for i in range(0,len(res)):
            print "%s: %i" % ( res[i][0], res[i][1] )

        if logStatus != "":
            req = "SELECT jobid,jobname FROM %s WHERE groupid=\"%s\" AND status=\"%s\"" % ( tablename, groupid, logStatus )
            db.execute( req )
            res = db.fetchall()
            for i in range(0,len(res)):
                logFile.write( str(res[i][0]) + "\t" + str(res[i][1]) + "\n" )

    elif os.environ["REPET_JOBS"] == "files":
        jobsDir = dbname + "/" + tablename + "/" + groupid
        if not os.path.exists( jobsDir ):
            print "ERROR: " + jobsDir + " doesn't exist"
            sys.exit(1)
        dStatus2Nb = {}
        dStatus2Nb[ "waiting" ] = 0
        dStatus2Nb[ "running" ] = 0
        dStatus2Nb[ "error" ] = 0
        dStatus2Nb[ "finished" ] = 0
        jobFiles = os.listdir( jobsDir )
        for f in jobFiles:
            jobFile = open( jobsDir + "/" + f, "r" )
            lines = jobFile.readlines()
            last = lines[-1].split()
            jobFile.close()
            dStatus2Nb[ last[5] ] += 1
            if logStatus != "" and last[5] == logStatus:
                logFile.write( last[0] + "\n" )
        for i in ["waiting","running","error","finished"]:
            if dStatus2Nb[i] != 0:
                print "%s: %i" % ( i, dStatus2Nb[i] )

    else:
        print "ERROR: REPET_JOBS is %s" % ( os.environ["REPET_JOBS"] )
        sys.exit(1)

    if logStatus != "":
        logFile.close()

    db.close()

    return 0


if __name__ == "__main__":
    main()
