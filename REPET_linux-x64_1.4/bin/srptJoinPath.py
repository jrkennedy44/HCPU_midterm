#!/usr/bin/env python

import user, os, sys, getopt, exceptions, logging, copy, math, ConfigParser

def setup_env():
    if "REPET_PATH" in os.environ.keys():
        sys.path.append( os.environ["REPET_PATH"] )
    else:
        print "*** Error: no environment variable REPET_PATH"
        sys.exit(1)
setup_env()

import pyRepet.sql.RepetDB
from pyRepet.sql.TableAdaptator import *
from pyRepet.coord.Path import *

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:",sys.argv[0],"[options]"
    print "options:"
    print "     -h: this help"
    print "     -t: path table name"
    print "     -a: alias"
    print "     -g: max gap size (default=5000)"
    print "     -m: max mismatch size (default=500)"
    print "     -i: identity tolerance (default=2)"
    print "     -c: TE insertion coverage (default=0.95)"
    print "     -o: overlap (default=15)"
    print "     -O: output table name (default=inTable+'_join')"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2)"
    print ""

#-----------------------------------------------------------------------------

def main():

    """
    This program performs a long join procedure on a set of matches.
    """

    table_path = ""
    alias = ""
    gap_thres = 5000
    mismh_thres = 500
    overlap_size = 15
    idtol = 2.0
    insTEcov = 0.95
    outTable = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"ht:a:g:m:o:i:c:O:C:H:U:P:D:v:")
    except getopt.GetoptError:
        help()
        sys.exit(0)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-t":
            table_path = a
        elif o == "-a":
            alias = a
        elif o == "-o":
            overlap_size = int(a)
        elif o == "-g":
            gap_thres = int(a)
        elif o == "-m":
            mismh_thres = int(a)
        elif o == "-i":
            idtol = float(a)
        elif o == "-c":
            insTEcov = float(a)
        elif o == "-O":
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

    if table_path == "":
        print "*** Error: missing input table name (-t)"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s\n" % (sys.argv[0].split("/")[-1])
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

    logfilename = table_path + "_joined.log"
    if os.path.exists( logfilename ):
        os.system( "rm -f %s" % ( logfilename ) )
    handler = logging.FileHandler( logfilename )
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter( formatter )

    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )

    logging.info( "started" )

    string = "Analyze table '%s'." % table_path
    logging.info( string )
    if verbose == 1:
        print "%s" % ( string ); sys.stdout.flush()

    db = pyRepet.sql.RepetDB.RepetDB( user, host, passwd, dbname )

    if not db.exist( table_path ):
        print "*** Error: input table doesn't exist"
        logging.error("table %s not known!!"%table_path)
        sys.exit(1)

    sqlCmd = "SELECT COUNT(DISTINCT path) FROM %s" % ( table_path )
    db.execute( sqlCmd )
    res = db.fetchall()
    string = "nb of distinct path identifiers: %i" % ( res[0][0] )
    logging.info( string )
    if verbose == 1:
        print "%s" % ( string ); sys.stdout.flush()

    if outTable == "":
        outTable = table_path + "_join"
    db.copy_table( table_path, outTable )
    table_path = outTable
    db.create_path_index( table_path )

    join( db, table_path, alias, gap_thres, mismh_thres, overlap_size, idtol, insTEcov )
    split( db, table_path )
    db.remove_if_exist( table_path + "_bin" )

    string = "output table: %s" % ( outTable )
    logging.info( string )
    if verbose == 1:
        print "%s" % ( string ); sys.stdout.flush()
    sqlCmd = "SELECT COUNT(DISTINCT path) FROM %s" % ( outTable )
    db.execute( sqlCmd )
    res = db.fetchall()
    string = "nb of distinct path identifiers: %i" % ( res[0][0] )
    logging.info( string )
    if verbose == 1:
        print "%s" % ( string ); sys.stdout.flush()

    db.close()

    logging.info( "finished" )

    if verbose > 0:
        print "\n%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#-----------------------------------------------------------------------------

def load_path_from_table( db, table, alias="" ):

        id2name = {}

        if alias != "":
            db.execute( "SELECT id,name FROM %s;" % (alias) )
            result = db.fetchall()
            if result == ():
                logging.error("no alias table: %s"%alias)
            for i in result:
                id2name[i[0]] = i[1]

        db.path2path_range( table, "tmp" + str(os.getpid()) )

        table = table + "_range_tmp" + str(os.getpid())

        db.execute( 'SELECT * FROM %s WHERE query_start<query_end and subject_start<subject_end ORDER BY query_name and subject_name and LEAST(query_start,query_end);' % (table) )
        results_1 = db.fetchall()

        db.execute('SELECT * FROM %s WHERE query_start>query_end xor subject_start>subject_end ORDER BY query_name and subject_name and LEAST(query_start,query_end);'%(table))
        results_2 = db.fetchall()

        results = results_1 + results_2
        if results == ():
            logging.error( "no key: %s in table: %s" % ( key, table ) )
        logging.info( "nb of paths tested for join: %i" % ( len(results) ) )

        path = pyRepet.coord.Path.Path()
        dQry2Paths = {}
        for i in results:
            path.set_from_tuple( i )
            if alias != "":
                path.range_subject.seqname = id2name[ path.range_subject.seqname.split("|")[-1] ]
            if not dQry2Paths.has_key( path.range_query.seqname ):
                dQry2Paths[ path.range_query.seqname ] = []
            dQry2Paths[ path.range_query.seqname ].append( copy.deepcopy(path) )

        return dQry2Paths

#----------------------------------------------------------------------------

def join( db, table_path, alias, gap_thres, mismh_thres, overlap_size, idtol, insTEcov ):

    string = "* Join fragmented paths."
    logging.info( "=================================================" )
    logging.info( string )
    if verbose == 1:
        print "\n%s" % ( string ); sys.stdout.flush()

    string = "overlap = %d" % ( overlap_size )
    logging.info( string )
    if verbose == 1:
        print string; sys.stdout.flush()

    string = "max gap = %d" % ( gap_thres )
    logging.info( string )
    if verbose == 1:
        print string; sys.stdout.flush()

    string = "max mismatch = %d" % ( mismh_thres )
    logging.info( string )
    if verbose == 1:
        print string; sys.stdout.flush()

    #tablePathAdaptator=TablePathAdaptator(db,table_path)
    tablePathAdaptator = TableBinPathAdaptator( db, table_path )
    dQry2Paths = load_path_from_table( db, table_path, alias )

    miss = []

    # for each query name in the input 'path' table
    for chk_name in dQry2Paths.keys():
        string = "Processing query '%s'" % ( chk_name )
        logging.info( string )
        if verbose == 1:
            print string; sys.stdout.flush()
        chk = dQry2Paths[ chk_name ]

        # for each of its matches
        for i in xrange(1,len(chk)):

            # 
            if chk[i].range_subject.seqname == chk[i-1].range_subject.seqname and \
                   chk[i].range_query.start != chk[i-1].range_query.start and \
                   chk[i].range_query.end != chk[i-1].range_query.end and \
                   chk[i].range_query.isPlusStrand() == chk[i-1].range_query.isPlusStrand() and \
                   chk[i].range_subject.isPlusStrand() == chk[i-1].range_subject.isPlusStrand() and \
                   chk[i].range_subject.start > chk[i-1].range_subject.end:

                if not chk[i].range_subject.isPlusStrand():
                    chk[i].reverse()

                if chk[i].range_query.isPlusStrand():
                    dist_q = chk[i].range_query.start - chk[i-1].range_query.end
                    dist_s = chk[i].range_subject.start - chk[i-1].range_subject.end
                else:
                    dist_q = chk[i].range_query.end - chk[i-1].range_query.start
                    dist_s = chk[i-1].range_subject.start - chk[i].range_subject.end

                logging.info( "---------------------------------------------" )
                logging.debug( "%s %d %d %s %d %d ID=%d"%\
                      (chk[i-1].range_query.seqname,\
                       chk[i-1].range_query.start,\
                       chk[i-1].range_query.end,\
                       chk[i-1].range_subject.seqname,\
                       chk[i-1].range_subject.start,\
                       chk[i-1].range_subject.end,chk[i-1].get_id()))
                logging.debug( "%s %d %d %s %d %d ID=%d"%\
                      (chk[i].range_query.seqname,\
                       chk[i].range_query.start,\
                       chk[i].range_query.end,\
                       chk[i].range_subject.seqname,\
                       chk[i].range_subject.start,\
                       chk[i].range_subject.end,chk[i].get_id()))
                logging.debug( "query dist=%d subject dist=%d"%(dist_q,dist_s))

                if dist_q >= (overlap_size*-1) and dist_s >= (overlap_size*-1):

                    key = chk_name

                    if chk[i].range_subject.isPlusStrand() and chk[i].range_query.isPlusStrand():
                        diag1 = chk[i-1].range_subject.end - chk[i-1].range_query.end
                        diag2 = chk[i].range_subject.start - chk[i].range_query.start
                        gap = diag1 - diag2
                        if gap > 0: # gap on query
                            mismh = dist_s
                        else:
                            mismh = dist_q
                    elif chk[i].range_subject.isPlusStrand() and not chk[i].range_query.isPlusStrand():
                        adiag1 = chk[i-1].range_subject.start + chk[i-1].range_query.start
                        adiag2 = chk[i].range_subject.end + chk[i].range_query.end
                        gap = adiag2 - adiag1
                        if gap > 0: # gap on query
                            mismh = dist_s
                        else:
                            mismh = dist_q

                    logging.debug( "gap=%d mismatch=%d"%(gap,mismh) )

                    # check identity of fragments to join
                    if abs(chk[i].identity-chk[i-1].identity)>idtol:
                        logging.debug( "deny long join: different identity (%.3f vs %.3f)" %\
                                       ( chk[i-1].identity, chk[i].identity ) )
                        continue

                    #check gap and mismatches
                    if gap <= gap_thres and mismh <= mismh_thres:
                        new_id = tablePathAdaptator.joinPath( chk[i-1].get_id(), chk[i].get_id() )
                        miss.append( ( key, chk[i-1], chk[i], dist_q, dist_s ) )
                        chk[i].id = new_id
                        logging.debug( "simple join: identity %.3f and %.3f" %\
                                       ( chk[i-1].identity, chk[i].identity ) )

                    elif mismh <= mismh_thres:
                        #check long gap
                        qmin = min( chk[i-1].range_query.getMax() + 1, chk[i].range_query.getMin() - 1 )
                        qmax = max( chk[i-1].range_query.getMax() + 1, chk[i].range_query.getMin() - 1 )
                        if qmax - qmin > 100000:
                            logging.debug( "too long join" ) 
                            continue
                        lnest = tablePathAdaptator.getInPathList_from_qcoord(\
                            chk[i].range_query.seqname,\
                            qmin, qmax )

                        if lnest != []:

                            # check that nested TE are younger
                            min_identity = 200
                            for p in lnest:
                                if p.identity < min_identity:
                                    min_identity = p.identity
                            if ( min_identity < chk[i].identity \
                                 or min_identity < chk[i-1].identity)\
                                 and abs(min_identity\
                                         -max(chk[i].identity,\
                                              chk[i-1].identity))>idtol:
                                logging.debug( "deny nest join: different identity (%.3f vs %.3f)" %\
                                               ( chk[i-1].identity, chk[i].identity ) )
                                continue
                            lnest_set = pyRepet.coord.Path.path_list_rangeQ2Set( lnest )
                            lnest_set = pyRepet.coord.Set.set_list_merge( lnest_set )

                            size = pyRepet.coord.Set.set_list_size( lnest_set )

                            # check that insertion is made by TE at x%
                            if float(size)/dist_q > insTEcov:
                                pyRepet.coord.Set.set_list_show( lnest_set )
                                new_id = tablePathAdaptator.joinTwoPaths( chk[i-1].get_id(), chk[i].get_id() )
                                miss.append( ( key, chk[i-1], chk[i], dist_q, dist_s ) )
                                chk[i].id = new_id
                                logging.debug( "nest join: identity %.3f and %.3f, nested %.3f"%\
                                               ( chk[i-1].identity, chk[i].identity, float(size)/dist_q) )
                            else:
                                logging.debug( "deny nest join: low TE coverage (%.3f)" % ( float(size)/dist_q ) )

    if verbose == 1:
        print "number of 'join': %i" % ( len(miss) )
    if verbose == 2:
        miss.sort()
        for l in miss:
            print "--------------------------------"
            print "%s %d %d %s %d %d ID=%d"%\
                  (l[1].range_query.seqname,\
                   l[1].range_query.start,\
                   l[1].range_query.end,\
                   l[1].range_subject.seqname,\
                   l[1].range_subject.start,\
                   l[1].range_subject.end,l[1].get_id())
            print "%s %d %d %s %d %d ID=%d"%\
                  (l[2].range_query.seqname,\
                   l[2].range_query.start,\
                   l[2].range_query.end,\
                   l[2].range_subject.seqname,\
                   l[2].range_subject.start,\
                   l[2].range_subject.end,l[2].get_id())
            print "query dist=",l[3],"subject dist=",l[4]
    sys.stdout.flush()

#----------------------------------------------------------------------------

def split( db, table_path ):

    string = "* Split overlapping paths."
    logging.info( "=================================================" )
    logging.info( string )
    if verbose == 1:
        print "\n%s" % ( string ); sys.stdout.flush()

    nbSplits = 0

    tablePathAdaptator = TableBinPathAdaptator( db, table_path )
    db.execute('SELECT path,query_name,query_start,query_end  FROM %s ORDER BY abs(query_start-query_end+1) DESC;'\
               % ( table_path ) )
    result = db.fetchall()

    if result == ():
        logging.error("no key: %s in table: %s"%(key,table_path))
        return
    found = []
    new_id = tablePathAdaptator.getNewId()

    for i in result:

        logging.debug( "test split on %s from %s to %s" % ( i[1], i[2], i[3] ) )

        plist1 = tablePathAdaptator.getPathList_from_num( i[0] )
        if len(plist1) == 1:
            continue
        if i[0] not in found:
            found.append( i[0] )
        plist2 = tablePathAdaptator.getPathList_from_qcoord( i[1], i[2], i[3] )

        plist2 = path_list_split( plist2 )
        for n,pl2 in plist2.items():
            if n == i[0] or n in found: continue
            pl2 = path_list_unjoin( plist1, pl2 )
            if pl2 != []:
                logging.info( "split id %d because of id %d" % ( n, i[0] ) )
                tablePathAdaptator.delPath_from_num( n )
                for l in pl2:
                    logging.debug( "----" )
                    for k in l:
                        logging.debug( "%s %d %d %s %d %d ID=%d"%\
                                       (k.range_query.seqname,\
                                        k.range_query.start,\
                                        k.range_query.end,\
                                        k.range_subject.seqname,\
                                        k.range_subject.start,\
                                        k.range_subject.end,k.get_id()))
                    new_id += 1
                    logging.info( "change id %d -> %d" % ( n, new_id) )
                    path_list_changeId( l, new_id )
                    tablePathAdaptator.insPathList( l )
                    nbSplits += 1

    if verbose == 1:
        print "number of 'split': %i" % ( nbSplits )

#-----------------------------------------------------------------------------
    
if __name__ == '__main__':
    main()
