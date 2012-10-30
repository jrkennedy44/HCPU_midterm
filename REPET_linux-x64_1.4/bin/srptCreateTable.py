#!/usr/bin/env python

import os
import sys
import getopt
import ConfigParser

from pyRepetUnit.commons.sql.DbMySql import DbMySql


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -f: name of the input file"
    print "     -n: name of the MySQL table"
    print "     -t: table type (fasta|align|path|set|match|map|TEclassif|cluster)"
    print "     -o: overwrite (default=False)"
    print "     -c: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -T: MySQL port (if no configuration file, default=3306)"
    print "     -v: verbose (default=0/1)"
    print


def main():
    """
    This program loads data from a file into a MySQL table.
    """
    filename = ""
    tablename = ""
    filetype = ""
    overwrite = False
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    port = 0
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hf:t:n:oc:H:U:P:D:T:v:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % str(err) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-f":
            filename = a
        elif o == "-n":
            tablename = a
        elif o == "-t":
            filetype = a
        elif o == "-o":
            overwrite = True
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

    if  filename == "" or tablename == "" or filetype == "":
        print "ERROR: missing compulsory options"
        help()
        sys.exit(1)

    if configFileName != "":
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env","repet_host")
        user = config.get("repet_env","repet_user")
        passwd = config.get("repet_env","repet_pw")
        dbname = config.get("repet_env","repet_db")
        port = config.get("repet_env","repet_port")

    if host == "" and os.environ.get( "REPET_HOST" ) != "":
        host = os.environ.get( "REPET_HOST" )
    if user == "" and os.environ.get( "REPET_USER" ) != "":
        user = os.environ.get( "REPET_USER" )
    if passwd == "" and os.environ.get( "REPET_PW" ) != "":
        passwd = os.environ.get( "REPET_PW" )
    if dbname == "" and os.environ.get( "REPET_DB" ) != "":
        dbname = os.environ.get( "REPET_DB" )
    if port == 0 and os.environ.get( "REPET_PORT" ) != "":
        port = int( os.environ.get( "REPET_PORT" ) )
        
    if host == "":
        print "ERROR: missing host"
        sys.exit(1)
    if user == "":
        print "ERROR: missing user"
        sys.exit(1)
    if passwd == "":
        print "ERROR: missing password"
        sys.exit(1)
    if dbname == "":
        print "ERROR: missing db name"
        sys.exit(1)
    if port == 0:
        print "ERROR: missing port"
        sys.exit(1)

    db = DbMySql(user, host, passwd, dbname, port )

    if not os.path.exists( filename ):
        print "ERROR: input file '%s' doesn't exist" % ( filename )
        sys.exit(1)

    db.createTable( tablename, filetype, filename, overwrite, verbose )

    db.close()

    return 0


if __name__ == "__main__":
    main()
