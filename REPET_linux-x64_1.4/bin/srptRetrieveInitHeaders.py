#!/usr/bin/env python

import os
import sys
import getopt
import ConfigParser
from pyRepetUnit.commons.sql.DbMySql import DbMySql

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -n: name of the MySQL table"
    print "     -t: table type (default=path)"
    print "     -l: name of the entity (file or table) recording the link initial header - temporary header"
    print "     -q: replace the name of the queries"
    print "     -s: replace the name of the subjects"
    print "     -o: name of the output MySQL table (if not, the table is replaced)"
    print "     -c: clean (i.e. remove the input table)"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1)"
    print ""

#-----------------------------------------------------------------------------

def getLinkTmp2Init( link ):

    """
    Retrieve the relationships initial headers - temporary headers.

    @param link: name of file or table
    @type link: string

    @return: dictionary whose keys are temporary headers and value initial headers
    @rtype: dictionary
    """

    dTmpH2InitH = {}
    linkFileName = ""
    linkTable = ""

    if os.path.isfile( link ):
        linkFileName = link
        linkFile = open( linkFileName, "r" )
        line = linkFile.readline()
        while True:
            if line == "":
                break
            data = line[:-1].split("\t")
            dTmpH2InitH[ data[0] ] = data[1]
            line = linkFile.readline()
        linkFile.close()

    else:
        linkTable = link
        if not db.doesTableExist( linkTable ):
            print "*** Error: table '%s' doesn't exist" % ( linkTable )
            sys.exit(1)
        qry = "SELECT name,chr FROM %s" % ( linkTable )
        db.execute( qry )
        lRes = db.fetchall()
        for i in lRes:
            dTmpH2InitH[ i[0] ] = i[1]

    return dTmpH2InitH

#-----------------------------------------------------------------------------

def main():

    """
    This program replaces the temporary headers from queries (or subjects) by the initial ones.
    """

    inTable = ""
    inTableType = "path"
    link = ""
    replaceQ = None
    replaceS = None
    outTable = ""
    clean = False
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hn:t:l:qso:cC:H:U:P:D:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-n":
            inTable = a
        elif o == "-t":
            inTableType = a
        elif o == "-l":
            link = a
        elif o == "-q":
            replaceQ = True
        elif o == "-s":
            replaceS = True
        elif o == "-o":
            outTable = a
        elif o == "-c":
            clean = True
        elif o == "-C":
            configFileName = a
        elif o == "-H":
            host = a
        elif o == "-U":
            user = a 
        elif o == "-P":
            passwd = a
        elif o == "-D":
            dbname = a
        elif o == "-v":
            verbose = int(a)

    if  inTable == "" or inTableType == "" or link == "" or (replaceQ == None and replaceS == None):
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if configFileName != "":
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env","repet_host")
        user = config.get("repet_env","repet_user")
        passwd = config.get("repet_env","repet_pw")
        dbname = config.get("repet_env","repet_db")

    if host == "" and os.environ.get( "REPET_HOST" ) != "":
        host = os.environ.get( "REPET_HOST" )
    if user == "" and os.environ.get( "REPET_USER" ) != "":
        user = os.environ.get( "REPET_USER" )
    if passwd == "" and os.environ.get( "REPET_PW" ) != "":
        passwd = os.environ.get( "REPET_PW" )
    if dbname == "" and os.environ.get( "REPET_DB" ) != "":
        dbname = os.environ.get( "REPET_DB" )

    if host == "" or user == "" or passwd == "" or dbname == "":
        print "*** Error: missing information about MySQL connection"
        sys.exit(1)

    global db
    db = DbMySql( user, host, passwd, dbname )

    dTmpH2InitH = getLinkTmp2Init( link )
    if verbose > 0:
        print "nb of relationships: %i" % ( len(dTmpH2InitH.keys()) )

    tmpTable = "%s_tmp" % ( inTable )
    db.copyTable( inTable, tmpTable )

    if replaceQ == True:
        for tmpH in dTmpH2InitH.keys():
            qry = "UPDATE %s SET query_name=\"%s\" WHERE query_name=\"%s\"" % ( tmpTable, dTmpH2InitH[ tmpH ], tmpH )
            db.execute( qry )

    if replaceS == True:
        for tmpH in dTmpH2InitH.keys():
            qry = "UPDATE %s SET subject_name=\"%s\" WHERE subject_name=\"%s\"" % ( tmpTable, dTmpH2InitH[ tmpH ], tmpH )
            db.execute( qry )

    if outTable == "":
        outTable = inTable
    db.copyTable( tmpTable, outTable )
    db.dropTable( tmpTable )

    if clean == True:
        db.dropTable( inTable )

    db.close()

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
