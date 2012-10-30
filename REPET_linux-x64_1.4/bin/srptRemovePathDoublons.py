#!/usr/bin/env python

##@file
# Remove duplicates within a path table.

import os
import sys
import getopt
import string
import ConfigParser
import logging

from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input table (format=path)"
    print "     -o: name of the output table (default=inTable+'_nr')"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbosity level (default=0/1/2)"
    print
    
    
def main():
    """
    Remove duplicates within a path table.
    """
    
    inTable = ""
    outTable = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    verbose = 0
    
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:o:C:H:U:P:D:v:" )
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inTable = a
        elif o == "-o":
            outTable = a
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
            
    if inTable == "":
        print "ERROR: missing name of input table (-i)"
        help()
        sys.exit(1)
        
    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
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
        print "ERROR: missing information about MySQL connection"
        sys.exit(1)
        
    logFileName = "%s_RemovePathDoublons.log" % ( inTable )
    if os.path.exists( logFileName ):
        os.remove( logFileName )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )
    
    db = DbMySql( user, host, passwd, dbname )
    if not db.doesTableExist( inTable ):
        print "ERROR: table '%s' doesn't exist" % ( inTable )
        logging.error( "table '%s' doesn't exist" % ( inTable ) )
        sys.exit(1)
        
    # create a temporary file
    tmpFileName = inTable + ".tmp" + str(os.getpid()) + "-nr"
    
    # retrieve the name of the queries
    tpA = TablePathAdaptator( db, inTable )
    lContigs = tpA.getQueryList()
    
    # for each query
    for c in lContigs:
        
        string = "processing query '%s'..." % ( c )
        
        # retrieve its paths
        clist = tpA.getPathListFromQuery( c )
        string += "\ninitial nb of paths: %i" % ( len(clist) )
        
        # remove doublons
        clist = PathUtils.getPathListWithoutDuplicates( clist, True )
        string += "\nnb of paths without duplicates: %i" % ( len(clist) )
        
        logging.info( string )
        if verbose > 1:
            print string; sys.stdout.flush()
            
        # write the non-redundant paths into the temporary file
        PathUtils.writeListInFile( clist, tmpFileName, "a" )
        
    if outTable == "":
        outTable = "%s_nr" % ( inTable )
    string = "create destination table '%s'" % ( outTable )
    logging.info( string )
    if verbose > 1:
        print string
        
    # load the temporary file in a MySQL table
    db.dropTable( outTable, verbose - 1 )
    db.createPathTable( outTable, tmpFileName )
    os.remove( tmpFileName )   
    
    db.close()
    
    logging.info( "finished" )
    
    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    return 0


if __name__ == "__main__":
    main()
