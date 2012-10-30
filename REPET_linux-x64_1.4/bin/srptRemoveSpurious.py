#!/usr/bin/env python

import os
import sys
import getopt
import ConfigParser
import logging

from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.sql.TableBinPathAdaptator import TableBinPathAdaptator
from pyRepetUnit.commons.sql.TableSetAdaptator import TableSetAdaptator
from pyRepetUnit.commons.sql.TableBinSetAdaptator import TableBinSetAdaptator
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -q: input table name"
    print "     -s: simple repeats table"
    print "     -r: min remaining size of chain of matches (default=20)"
    print "     -t: table types ([path,set]/[path,set])"
    print "     -o: output table name (default=inTable+'_noSSR')"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2)"
    print


def main ():
    """
    Remove TE fragments overlapping too much with SSRs.
    """
    qtable = ""
    stable = ""
    qtype = ""
    stype = ""
    remain_thres_size = 20
    outTable = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hq:s:t:r:o:C:H:U:P:D:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(0)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-q":
            qtable = a
        elif o == "-s":
            stable = a
        elif o == "-t":
            qtype = a.split("/")[0]
            stype = a.split("/")[1]
        elif o == "-r":
            remain_thres_size = int(a)
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

    if qtable == "" or stable == "" or qtype == "" or stype == "":
        print "ERROR: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    logFileName = "%s_RemoveSpurious.log" % ( qtable )
    if os.path.exists( logFileName ):
        os.remove( logFileName )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )

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

    db = DbMySql( user, host, passwd, dbname )

    if outTable == "":
        outTable = "%s_noSSR" % ( qtable )
    db.copyTable( qtable, outTable )
    qtable = outTable

    # prepare the query table
    if qtype == "path":
        db.createPathIndex( qtable )
        qtablePathAdaptator = TablePathAdaptator( db, qtable )
        lPathId = qtablePathAdaptator.getIdList()
    elif qtype == "set":
        db.createSetIndex( qtable )
        qtableSetAdaptator = TableSetAdaptator( db, qtable )
        lPathId = qtableSetAdaptator.getIdList()
    else:
        print "ERROR: unknown query table type: %s" % ( qtype )
        sys.exit(1)

    string = "total number of paths: %i" % ( len(lPathId) )
    logging.info( string )
    if verbose > 0:
        print string

    # prepare the subject table
    if stype == "path":
        stablePathAdaptator = TableBinPathAdaptator( db, stable )
    elif stype == "set":
        stableSetAdaptator = TableBinSetAdaptator( db, stable )
    else:
        print "ERROR: unknown subject table type: %s" % ( stype )
        sys.exit(1)


    lSetIdToRemovePaths = []
    count = 0

    # for each path ID
    for id in lPathId:

        string = "processing path '%i'..." % ( id )

        if qtype == "path":
            lPaths = qtablePathAdaptator.getPathListFromId( id )
            lQuerySets = PathUtils.getSetListFromQueries( lPaths )
        elif qtype == "set":
            lQuerySets = qtableSetAdaptator.getSetListFromId( id )

        lQuerySets.sort()
        qmin, qmax = SetUtils.getListBoundaries( lQuerySets )

        qmin = qmin - 1
        qmax = qmax + 1
        if stype == "path":
            lPaths = stablePathAdaptator.getPathListOverlappingQueryCoord( lQuerySets[0].seqname.split()[0], qmin, qmax )
            lSubjectSets = PathUtils.getSetListFromQueries( lPaths )
        elif stype == "set":
            lSubjectSets = stableSetAdaptator.getSetListFromQueryCoord( lQuerySets[0].seqname.split()[0], qmin, qmax )

        if verbose > 1:
            print "----------------------------------------"

        if len(lSubjectSets) > 0:
            if verbose > 1:
                print "annot:"
                SetUtils.showList( lQuerySets )
            lQuerySets = SetUtils.mergeSetsInList( lQuerySets )
            qsize = SetUtils.getCumulLength( lQuerySets )
            string += "\nannot size: %i" % ( qsize )
            if verbose > 1:
                print "annot size=", qsize

            if verbose > 1:
                print "simple repeats list:"
                SetUtils.showList( lSubjectSets )
            lSubjectSets = SetUtils.mergeSetsInList( lSubjectSets )
            ssize = SetUtils.getCumulLength( lSubjectSets )
            string += "\nsimple repeats size: %i" % ( ssize )
            osize = SetUtils.getOverlapLengthBetweenLists( lQuerySets, lSubjectSets )
            string += "\noverlap size: %i" % ( osize )
            string += "\nremains %i" % ( qsize - osize )

            if verbose > 1:
                print "merged simple repeats list:"
                SetUtils.showList( lSubjectSets )
                print "simple repeats size=",ssize
                print "overlap size=", osize, "--> remains=", qsize - osize

            if qsize - osize < remain_thres_size:
                string += "\nremove path %i" % ( lQuerySets[0].id )
                if verbose > 1:
                    print "remove path %d" % ( lQuerySets[0].id )
                lSetIdToRemovePaths.append( lQuerySets[0].id )
                count = count + 1
                
                
        else:
            string += "\nno overlapping simple repeats"
            pathLength = (qmax-1) - (qmin+1) + 1
            if pathLength < remain_thres_size:
                string += "\nfilter (length=%ibp < %ibp)" % ( pathLength, remain_thres_size )
                lSetIdToRemovePaths.append( id )
                count += 1
                if verbose > 1:
                    print string
                    
        logging.info( string )
        
    string = "number of path(s) to remove: %i" % ( count )
    logging.info( string )
    if verbose > 0:
        print string
    lSetIdToRemovePaths.sort()
    if verbose > 1:
        print lSetIdToRemovePaths; sys.stdout.flush()

    for i in xrange(0,len(lSetIdToRemovePaths),20):
        lPathIdToRemove = lSetIdToRemovePaths[i:i+20]
        if qtype == "path":
            qtablePathAdaptator.deleteFromIdList( lPathIdToRemove )
        elif qtype == "set":
            qtableSetAdaptator.deleteFromIdList( lPathIdToRemove )
            
    db.dropTable( "%s_bin" % ( stable ) )

    db.close()

    logging.info( "finished" )

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0
    
    
if __name__ == "__main__":
    main()
