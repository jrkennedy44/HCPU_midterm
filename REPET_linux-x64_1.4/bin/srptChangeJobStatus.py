#!/usr/bin/env python

import os
import sys
import getopt
import ConfigParser

from pyRepetUnit.commons.sql.RepetJob import RepetJob
from pyRepetUnit.commons.sql.Job import Job

def help():
    print
    print "usage: ",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -t: job table name (default='jobs')"
    print "     -j: job ID"
    print "     -n: job name"
    print "     -g: group ID"
    print "     -q: needed resources (not mandatory)"
    print "     -s: new job status (waiting/running/error/finished)"
    print "     -m: method (file/db)"
    print "     -c: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -T: MySQL port (if no configuration file, default=3306)"
    print "     -v: verbosity level (default=0/1)"
    print
    
    
def main():

    tablename = "jobs"
    jobid = 0
    jobname = ""
    groupid = ""
    queue = ""
    newStatus = ""
    method = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    port = 0
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"ht:j:n:g:q:s:m:c:H:U:P:D:T:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
        elif o == "-t":
            tablename = a
        elif o == "-j":
            jobid = a
        elif o == "-n":
            jobname = a
        elif o == "-g":
            groupid = a
        elif o == "-q":
            queue = a
        elif o == "-s":
            newStatus = a
        elif o == "-m":
            method = a
        elif o == "-c":
            configFileName = a
        elif o == "-H":
            host = a
        elif o == "-U":
            user = a 
        elif o == "-P":
            passwd = a
        elif o == "-D":
            dbname = a
        elif o == "-T":
            port = int(a)
        elif o == "-v":
            verbose = int(a)

    if  tablename == "" or ( jobid == "" and jobname == "" ) or groupid == "" or newStatus == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)
        
    if configFileName == "" and host == "" and user == "" and passwd == "" and dbname == "" and port == 0:
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)
        
    if configFileName != "":
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env", "repet_host")
        user = config.get("repet_env", "repet_user")
        passwd = config.get("repet_env", "repet_pw")
        dbname = config.get("repet_env", "repet_db")
        port = config.get("repet_env", "repet_port")
        
    jobdb = RepetJob( user, host, passwd, dbname, port )
    
    node = os.getenv( "HOSTNAME" )
    job = Job( tablename = tablename,
               jobid = jobid,
               jobname = jobname,
               groupid = groupid,
               queue = queue,
               node = node )
    
    if verbose > 0:
        print "current status: " + jobdb.getJobStatus( job )
        sys.stdout.flush()
        
    jobdb.changeJobStatus( job, newStatus, method )
    
    if verbose > 0:
        print "updated status: " + jobdb.getJobStatus( job )
        sys.stdout.flush()
        
    jobdb.close()
        
    return 0


if __name__ == "__main__":
    main()
