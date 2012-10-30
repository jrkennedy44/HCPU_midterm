#!/usr/bin/env python

import user, os, sys, getopt, string, ConfigParser
from copy import *

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.sql.TableAdaptator
import pyRepet.coord.Map
import pyRepet.coord.Path
import pyRepet.coord.Match
import pyRepet.coord.Set
import pyRepet.sql.RepetDBMySQL

from pyRepetUnit.convCoord.ConvSetChr2Chunk import *
from pyRepetUnit.convCoord.ConvPathChr2Chunk import *

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print
    print "usage:" + sys.argv[0] + " [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -m: table name (map) recording the coordinates of the chunks on the chromosomes"
    print "     -q: table name (path/set/map) recording coordinates you want to convert"
    print "     -f: file name (path/tab/map) recording coordinates you want to convert"
    print "     -t: type of data match/path/map/set"
    print "     -o: output table name (default=inTable+'_onchr')"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2)"
    print

#-----------------------------------------------------------------------------

def main():

    chunk_tablename = ""
    coord_tablename = ""
    coord_filename = ""
    dataType = ""
    outTable = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hm:q:t:f:o:C:H:U:P:D:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(1)
        elif o == "-m":
            chunk_tablename = a
        elif o == "-q":
            coord_tablename = a
        elif o == "-t":
            dataType = a
        elif o == "-f":
            coord_filename = a
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

    if coord_tablename != "" and coord_filename != "":
        print "*** Error: missing table (-q) or file (-f)"
        help()
        sys.exit(1)

    if chunk_tablename=="" or (coord_tablename=="" and coord_filename=="") or dataType=="":
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

    db = pyRepet.sql.RepetDBMySQL.RepetDB( user, host, passwd, dbname )

    if coord_filename!="":
        if dataType=="path":
            conv_path_file(chunk_tablename,db,coord_filename)
        elif dataType=="map":
            conv_map_file(chunk_tablename,db,coord_filename)
        else:
            print "*** Error: unknown type of table: %s" % ( dataType )
            sys.exit(1)

    if outTable == "":
        outTable = path_tablename + "_onchunk"

    if coord_tablename != "":
        if dataType == "path":
            conv_path_table( chunk_tablename, db, coord_tablename, outTable )
        elif dataType == "map":
            conv_map_table( chunk_tablename, db, coord_tablename, outTable )
        elif dataType == "set":
            conv_set_table( chunk_tablename, db, coord_tablename, outTable )
        else:
            print "*** Error: unknown type of table: %s" % ( dataType )
            sys.exit(1)

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

def conv_path_file(chunk_table,db,filename):

    """
    Convert a 'path' file format.
    """

    fout = open( filename+".on_chunk", "w" )
    fin = open( filename, "r" )
    p = pyRepet.coord.Path.Path()
    old_id = -1
    while True:
        if not p.read(fin):
            break
        
        if old_id == p.get_id():
            path.append( copy(p) )
            if p.range_query.getMin() < min_r:
                min_r = p.range_query.getMin()
            if p.range_query.getMax() > max_r:
                max_r = p.range_query.getMax()
        elif old_id != -1:
            str_mask="SELECT * FROM "+\
                chunk_table+" WHERE chr='%s' AND ("+\
                "(%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
                " OR (%d BETWEEN LEAST(start,end) AND GREATEST(start,end)));"\
                 
            sql_cmd = str_mask%(path[0].range_query.seqname,min_r,max_r)
            db.execute( sql_cmd )
            res = db.fetchall()
            for i in res:
                chunk = pyRepet.coord.Map.Map(i[0],i[1],int(i[2]),int(i[3]))
                for r in path:
                    new_r = pyRepet.coord.Path.Path()
                    new_r = deepcopy( r )
                    new_r.range_query.seqname = chunk.name
                    if chunk.start < chunk.end:
                        new_r.range_query.start = r.range_query.start\
                                                  -chunk.start+1
                        new_r.range_query.end = r.range_query.end-chunk.start+1
                    else:
                        new_r.range_query.start = chunk.start\
                                                  -r.range_query.start+1
                        new_r.range_query.end = chunk.start-r.range_query.end+1
                    new_r.range_query.show()
                    new_r.write(fout)
            old_id = p.get_id()
            path = [ copy(p) ]
            min_r = p.range_query.getMin()
            max_r = p.range_query.getMax()
        elif old_id == -1:
            old_id = p.get_id()
            path = [ copy(p) ]
            min_r = p.range_query.getMin()
            max_r = p.range_query.getMax()
    fout.close()
    fin.close()

#----------------------------------------------------------------------------

def conv_map_file(chunk_table,db,filename):

    """
    Convert a 'map' file format.
    """

    fout = open( filename+".on_chr", "w" )
    fin = open( filename, "r" )
    m = pyRepet.coord.Map.Map()
    while True:
        if not m.read(fin):
            break
        str_mask="SELECT * FROM "+\
                  chunk_table+" WHERE chr='%s' AND ("+\
                  "(%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
                  " OR (%d BETWEEN LEAST(start,end) AND GREATEST(start,end)));"
        
        sql_cmd = str_mask % (m.seqname,m.start,m.end)
        db.execute( sql_cmd )
        res = db.fetchall()
        for i in res:
            chunk = pyRepet.coord.Map.Map(i[0],i[1],int(i[2]),int(i[3]))
            new_m = pyRepet.coord.Map.Map()
            new_m = deepcopy( m )
            new_m.seqname = chunk.name
            if chunk.start < chunk.end:
                new_m.start = m.start - chunk.start + 1
                new_m.end = m.end - chunk.start + 1
            else:
                new_m.start = chunk.start - m.start + 1
                new_m.end = chunk.start - m.end + 1
            new_m.show()
            new_m.write( fout )
    fout.close()
    fin.close()

#----------------------------------------------------------------------------

def conv_path_table( chunk_table, db, table, outTable ):

    """
    Convert a 'path' table format.
    """
    convPathChr2Chunk=ConvPathChr2Chunk(db,table,chunk_table,outTable)
    convPathChr2Chunk.run()

#----------------------------------------------------------------------------

def conv_map_table( chunk_table, db, table, outTable ):

    """
    Convert a 'map' table format.
    """
    convMapChr2Chunk=ConvMapChr2Chunk(db,table,chunk_table,outTable)
    convMapChr2Chunk.run()

#----------------------------------------------------------------------------

def conv_set_table( chunk_table, db, table, outTable ):

    convSetChr2Chunk=ConvSetChr2Chunk(db,table,chunk_table,outTable)
    convSetChr2Chunk.run()

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
