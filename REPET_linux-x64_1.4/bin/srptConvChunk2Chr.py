#!/usr/bin/env python

import os
import sys
import getopt
import string
import ConfigParser

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

import pyRepet.sql.RepetDB
import pyRepet.sql.TableAdaptator
import pyRepet.coord.Map
import pyRepet.coord.Path
import pyRepet.coord.Match
import pyRepet.coord.Set

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:" + sys.argv[0] + " [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -m: name of the table recording the coordinates of the chunks on the chromosomes ('map' format)"
    print "     -q: name of the table recording the coordinates you want to convert ('path'/'set'/'map'/'align' format)"
    print "     -f: name of the file recording the coordinates you want to convert ('path'/'tab'/'map' format)"
    print "     -c: connect chunk overlaps (only for table input, not available for 'align' format)"
    print "     -t: format of data (match/path/map/set/align) for the target (-q or -f)"
    print "     -o: name of the output table (default=inTable+'_onchr')"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2)"
    print ""

#-----------------------------------------------------------------------------

def main():

    map_tablename = ""
    coordTable = ""
    coordFileName = ""
    dataFormat = ""
    connect = False
    outTable = ""
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hcm:q:t:f:o:C:H:U:P:D:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-m":
            map_tablename = a
        elif o == "-q":
            coordTable = a
        elif o == "-t":
            dataFormat = a
        elif o == "-f":
            coordFileName = a
        elif o == "-c":
            connect = True
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

    if map_tablename == "" or (coordTable == "" and coordFileName == "") or dataFormat == "":
        print "*** Error: missing compulsory options"
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
        print "*** Error: missing information about MySQL connection"
        sys.exit(1)

    global db
    db = pyRepet.sql.RepetDB.RepetDB( user, host, passwd, dbname )
    sql_cmd = "SELECT * FROM %s" % ( map_tablename )
    db.execute( sql_cmd )
    res = db.fetchall()
    dChunk2Link = {}
    for i in res:
        dChunk2Link[i[0]] = ( i[1], int(i[2]), int(i[3]) )

    if outTable == "":
        outTable = coordTable + "_onchr"

    if coordFileName != "" and coordTable == "":
        if verbose > 0:
            print "convert file '%s'..." % ( coordFileName )
            sys.stdout.flush()
        if dataFormat == "path":
            conv_path_file( dChunk2Link, coordFileName )
        elif dataFormat == "tab":
            conv_match_file( dChunk2Link, coordFileName )
        elif dataFormat == "map":
            conv_map_file( dChunk2Link, coordFileName )
        else:
            print "*** Error: unknown file format: %s" % ( dataFormat )
            sys.exit(1)

    elif coordTable != "" and coordFileName == "":
        if verbose > 0:
            print "convert table '%s'..." % ( coordTable )
            sys.stdout.flush()
        if dataFormat == "path":
            conv_path_table( dChunk2Link, coordTable, outTable )
            if connect:
                connect_path_chunks( dChunk2Link, outTable, db, verbose )
        elif dataFormat == "set":
            conv_set_table( dChunk2Link, coordTable, outTable )
            if connect:
                connect_set_chunks( dChunk2Link, outTable )
        elif dataFormat == "map":
            conv_map_table( dChunk2Link, coordTable, outTable )
            if connect:
                print "*** Error: cannot still connect 'map' table"
                sys.exit(1)
        elif dataFormat == "align":
            conv_align_table( dChunk2Link, coordTable, outTable )
            if connect:
                print "*** Error: not yet available"
                sys.exit(1)
        else:
            print "*** Error: unknown table format: %s" % ( dataFormat )
            sys.exit(1)

    elif coordFileName == "" and coordTable == "":
        print "*** Error: both table and file names are given"
        sys.exit(1)

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

def conv_path_file( chunk, filename ):

    """
    Convert a 'path' file format.
    """

    fout = open( filename+".on_chr", "w" )
    fin = open( filename, "r" )
    p = pyRepet.coord.Path.Path()
    while True:
        if not p.read(fin):
            break
        p.range_query.show()
        i = chunk.get(p.range_query.seqname.split()[0],None)
        if i == None:
            print "*** Error: chunk: '%s' not found" % ( p.range_query.seqname )
            sys.exit(1)
        else:
            p.range_query.seqname = i[0]
            if i[1] < i[2]:
                p.range_query.start = p.range_query.start + i[1] - 1
                p.range_query.end = p.range_query.end + i[1] - 1
            else:
                p.range_query.start = i[1] - p.range_query.start + 1
                p.range_query.end = i[1] - p.range_query.end + 1
            p.write(fout)
    fout.close()
    fin.close()

#----------------------------------------------------------------------------

def conv_match_file( chunk, filename ):

    """
    Convert a 'match' file format.
    """

    fout = open( filename+".on_chr", "w")
    fin = open( filename, "r" )
    fin.readline()
    m = pyRepet.coord.Match.Match()
    while True:
        if not m.read(fin):
            break
        m.range_query.show()
        i = chunk.get(m.range_query.seqname.split()[0],None)
        if i == None:
            print "*** Error: chunk '%s' not found" % ( m.range_query.seqname )
            sys.exit(1)
        else:
            m.range_query.seqname = i[0]
            if i[1] < i[2]:
                m.range_query.start = m.range_query.start + i[1] - 1
                m.range_query.end = m.range_query.end + i[1] - 1
            else:
                m.range_query.start = i[1] - m.range_query.start + 1
                m.range_query.end = i[1] - m.range_query.end + 1
            m.write(fout)
    fout.close()
    fin.close()

#----------------------------------------------------------------------------

def conv_map_file( chunk, filename ):

    """
    Convert a 'map' file format.
    """

    fout = open( filename+".on_chr", "w" )
    fin = open( filename, "r" )
    m = pyRepet.coord.Map.Map()
    while True:
        if not m.read(fin):
            break
        m.show()
        i = chunk.get(m.seqname.split()[0],None)
        if i == None:
            print "*** Error: chunk '%s' not found" % ( m.seqname )
            sys.exit(1)
        else:
            m.seqname = i[0]
            if i[1] < i[2]:
                m.start = m.start + i[1] - 1
                m.end = m.end + i[1] - 1
            else:
                m.start = i[1] - m.start + 1
                m.end = i[1] - m.end + 1
            m.write(fout)
    fout.close()
    fin.close()

#----------------------------------------------------------------------------

def conv_path_table( dChunk2Link, coordTable, outTable ):

    """
    Convert the coordinates recorded in a 'path' table.

    @param dChunk2Link: dictionary whose keys are the chunk names and values a list with chromosome name, start and end
    @type dChunk2Link: dictionary

    @param coordTable: name of the table recording the coordinates you want to convert
    @type coordTable: string

    @param outTable: name of the output table
    @type outTable: string
    """

    tmpFileName = "%i.on_chr" % ( os.getpid() )
    tmpFile = open( tmpFileName, "w" )
    p = pyRepet.coord.Path.Path()

    # for each chunk
    lChunks = dChunk2Link.keys()
    lChunks.sort()
    for chunkName in lChunks:
        if verbose > 1:
            print "processing %s..." % ( chunkName ); sys.stdout.flush()

        # retrieve its matches
        sql_cmd = "SELECT * FROM %s WHERE query_name LIKE \"%s %%\" or query_name=\"%s\";" \
                  % ( coordTable, chunkName, chunkName )
        db.execute( sql_cmd )
        lPaths = db.fetchall()

        # for each match
        for path in lPaths:
            p.set_from_tuple( path )

            # convert the coordinates on the query
            link = dChunk2Link[chunkName]
            p.range_query.seqname = link[0]
            if ( link[1] < link[2] ):
                p.range_query.start = p.range_query.start + link[1] - 1
                p.range_query.end = p.range_query.end + link[1] - 1
            else:
                p.range_query.start = link[1] - p.range_query.start + 1
                p.range_query.end = link[1] - p.range_query.end + 1

            # convert the coordinates on the subject (if necessary)
            link = dChunk2Link.get( p.range_subject.seqname )
            if link != None:
                if verbose > 1:
                    print "convert subject: %s" % ( p.range_subject.seqname )
                p.range_subject.seqname = link[0]
                p.range_subject.start = p.range_subject.start + link[1] - 1
                p.range_subject.end = p.range_subject.end + link[1] - 1
            p.write( tmpFile )
    tmpFile.close()

    db.create_path( outTable, tmpFileName )

    os.system( "rm -f " + tmpFileName )

#----------------------------------------------------------------------------

# convert a match table format        

def conv_match_table( chunk, table, outTable ):

    temp_file=str(os.getpid())+".on_chr"
    fout=open(temp_file,'w')
    fout.write("dummy line \n")
    m=pyRepet.coord.Match.Match()
    for chunkName in chunk.keys():
        sql_cmd='select * from %s where query_name like "%s %%" or query_name="%s" ;'\
                 %(table,chunkName,chunkName)
        db.execute(sql_cmd)
        res=db.fetchall()
        for t in res:
            m.set_from_tuple(t)
            i=chunk[chunkName]
            m.range_query.seqname=i[0]
            if(i[1]<i[2]):
                m.range_query.start=m.range_query.start+i[1]-1
                m.range_query.end=m.range_query.end+i[1]-1
            else:
                m.range_query.start=i[1]-m.range_query.start+1
                m.range_query.end=i[1]-m.range_query.end+1
            m.write(fout)
    fout.close()

    db.create_path( outTable, temp_file )

    os.system("rm -f "+temp_file)

#----------------------------------------------------------------------------

# convert a map table format        

def conv_map_table( chunk, table, outTable ):

    temp_file=str(os.getpid())+".on_chr"
    fout=open(temp_file,'w')
    m=pyRepet.coord.Map.Map()
    for chunkName in chunk.keys():
        sql_cmd='select * from %s where chr like "%s %%" or chr="%s";'\
                 %(table,chunkName,chunkName)
        db.execute(sql_cmd)
        res=db.fetchall()
        for t in res:
            m.set_from_tuple(t)
            i=chunk[chunkName]
            m.seqname=i[0]
            if(i[1]<i[2]):
                m.start=m.start+i[1]-1
                m.end=m.end+i[1]-1
            else:
                m.start=i[1]-m.start+1
                m.end=i[1]-m.end+1
            m.write(fout)
    fout.close()

    db.create_path( outTable, temp_file )

    os.system("rm -f "+temp_file)                

#----------------------------------------------------------------------------

def conv_set_table( dChunk2Link, table, outTable ):

    """
    Convert the coordinates recorded in a 'set' table.

    @param dChunk2Link: dictionary whose keys are the chunk names and values a list with chromosome name, start and end
    @type dChunk2Link: dictionary

    @param coordTable: name of the table recording the coordinates you want to convert
    @type coordTable: string

    @param outTable: name of the output table
    @type outTable: string
    """

    tmpFileName = "%i.on_chr" % ( os.getpid() )
    tmpFile = open( tmpFileName, "w" )
    s = pyRepet.coord.Set.Set()

    for chunkName in dChunk2Link.keys():
        if verbose > 1:
            print "processing %s..." % ( chunkName ); sys.stdout.flush()
        sql_cmd='select * from %s where chr like "%s %%" or chr="%s";'\
                 %(table,chunkName,chunkName)
        db.execute(sql_cmd)
        res=db.fetchall()
        for t in res:
            s.set_from_tuple(t)
            i=dChunk2Link[chunkName]
            s.seqname=i[0]
            if(i[1]<i[2]):
                s.start=s.start+i[1]-1
                s.end=s.end+i[1]-1
            else:
                s.start=i[1]-s.start+1
                s.end=i[1]-s.end+1
            s.write(tmpFile)
    tmpFile.close()

    db.create_set( outTable, tmpFileName )

    os.remove( tmpFileName )

#----------------------------------------------------------------------------

def conv_align_table( dChunk2Link, coordTable, outTable ):

    """
    Convert the coordinates recorded in an 'align' table.

    @param dChunk2Link: dictionary whose keys are the chunk names and values a list with chromosome name, start and end
    @type dChunk2Link: dictionary

    @param coordTable: name of the table recording the coordinates you want to convert
    @type coordTable: string

    @param outTable: name of the output table
    @type outTable: string
    """

    tmpFileName = "%i.on_chr" % ( os.getpid() )
    tmpFile = open( tmpFileName, "w" )
    p = pyRepet.coord.Align.Align()

    # for each chunk
    lChunks = dChunk2Link.keys()
    lChunks.sort()
    for chunkName in lChunks:
        if verbose > 1:
            print "processing %s..." % ( chunkName ); sys.stdout.flush()

        # retrieve its matches
        sql_cmd = "SELECT * FROM %s WHERE query_name LIKE \"%s %%\" or query_name=\"%s\";" \
                  % ( coordTable, chunkName, chunkName )
        db.execute( sql_cmd )
        lHSPs = db.fetchall()

        # for each HSP
        for align in lHSPs:
            p.set_from_tuple( align )

            # convert the coordinates on the query
            link = dChunk2Link[chunkName]
            p.range_query.seqname = link[0]
            if ( link[1] < link[2] ):
                p.range_query.start = p.range_query.start + link[1] - 1
                p.range_query.end = p.range_query.end + link[1] - 1
            else:
                p.range_query.start = link[1] - p.range_query.start + 1
                p.range_query.end = link[1] - p.range_query.end + 1

            # convert the coordinates on the subject (if necessary)
            link = dChunk2Link.get( p.range_subject.seqname )
            if link != None:
                if verbose > 1:
                    print "convert subject: %s" % ( p.range_subject.seqname )
                p.range_subject.seqname = link[0]
                p.range_subject.start = p.range_subject.start + link[1] - 1
                p.range_subject.end = p.range_subject.end + link[1] - 1
            p.write( tmpFile )
    tmpFile.close()

    db.create_align( outTable, tmpFileName )

    os.system( "rm -f " + tmpFileName )

#----------------------------------------------------------------------------

def connect_path_chunks( chunk, table, db, verbose ):

    if verbose > 0:
        print "connect chunks..."
        sys.stdout.flush()

    tablePathAdaptator = pyRepet.sql.TableAdaptator.TablePathAdaptator( db, table )

    nbChunks = len(chunk.keys())

    for num_chunk in xrange(1,nbChunks):
        #chunkName = "chunk"+str(num_chunk)
        chunkName = "chunk%s" % ( str(num_chunk).zfill( len(str(nbChunks)) ) )
        
        #next_chunkName="chunk"+str(num_chunk+1)
        next_chunkName = "chunk%s" % ( str(num_chunk+1).zfill( len(str(nbChunks)) ) )

        if next_chunkName not in chunk.keys():
            break
        if verbose > 1:
            print "try with %s and %s" % ( chunkName, next_chunkName )
            sys.stdout.flush()
            
        start=chunk[chunkName][2]
        end=chunk[next_chunkName][1]
        if chunk[chunkName][0] == chunk[next_chunkName][0]:
            lpath=tablePathAdaptator.getPathList_from_qcoord( chunk[chunkName][0], start, end )
            if verbose > 1:
                print "%i matches on %s (%i->%i)" % ( len(lpath), chunk[chunkName][0], start, end )
                sys.stdout.flush()
            lpath.sort()
            chg_path_id={}
            pathnum_to_ins=[]
            pathnum_to_del=[]
            dpath=[]
            rpath=[]
            for i in lpath:
                if i.range_query.isPlusStrand() and i.range_subject.isPlusStrand():
                    dpath.append(i)
                else:
                    rpath.append(i)
            x=0
            while x < len(dpath)-1:
                x=x+1
                if verbose > 1:
                    dpath[x-1].show()
                    dpath[x].show()

                if dpath[x-1].id != dpath[x].id \
                   and dpath[x-1].range_query.seqname\
                   ==dpath[x].range_query.seqname\
                   and dpath[x-1].range_subject.seqname\
                   ==dpath[x].range_subject.seqname\
                   and dpath[x-1].range_query.isPlusStrand()\
                   ==dpath[x].range_query.isPlusStrand()\
                   and dpath[x-1].range_subject.isPlusStrand()\
                   ==dpath[x].range_subject.isPlusStrand()\
                   and dpath[x-1].range_query.overlap(dpath[x].range_query)\
                   and dpath[x-1].range_subject.overlap(dpath[x].range_subject):
                    chg_path_id[dpath[x].id]=dpath[x-1].id
                    if dpath[x-1].id not in pathnum_to_ins:
                        pathnum_to_ins.append(dpath[x-1].id)
                    if dpath[x].id not in pathnum_to_del:
                        pathnum_to_del.append(dpath[x].id)
                    dpath[x-1].merge(dpath[x])
                    del dpath[x]
                    x=x-1
                    if verbose > 1:
                        print "--> merged"
            x=0
            while x < len(rpath)-1:
                x=x+1
                if verbose > 1:
                    rpath[x-1].show()
                    rpath[x].show()

                if rpath[x-1].id != rpath[x].id \
                   and rpath[x-1].range_query.seqname\
                   ==rpath[x].range_query.seqname\
                   and rpath[x-1].range_subject.seqname\
                   ==rpath[x].range_subject.seqname\
                   and rpath[x-1].range_query.isPlusStrand()\
                   ==rpath[x].range_query.isPlusStrand()\
                   and rpath[x-1].range_subject.isPlusStrand()\
                   ==rpath[x].range_subject.isPlusStrand()\
                   and rpath[x-1].range_query.overlap(rpath[x].range_query)\
                   and rpath[x-1].range_subject.overlap(rpath[x].range_subject):
                    chg_path_id[rpath[x].id]=rpath[x-1].id
                    if rpath[x-1].id not in pathnum_to_ins:
                        pathnum_to_ins.append(rpath[x-1].id)
                    if rpath[x].id not in pathnum_to_del:
                        pathnum_to_del.append(rpath[x].id)
                    rpath[x-1].merge(rpath[x])
                    del rpath[x]
                    x=x-1
                    if verbose > 1:
                        print "--> merged"
            if verbose > 1:
                print "pathnum to delete", pathnum_to_del
            tablePathAdaptator.delPath_from_listnum(pathnum_to_del)
            tablePathAdaptator.delPath_from_listnum(pathnum_to_ins)
            for i in dpath:
                if chg_path_id.has_key(i.id):
                    i.id=chg_path_id[i.id]
                if verbose > 1:
                    i.show()
                if i.id in pathnum_to_ins:
                    tablePathAdaptator.insAPath(i)
                    if verbose > 1:
                        print "--> inserted!"
            for i in rpath:
                if chg_path_id.has_key(i.id):
                    i.id=chg_path_id[i.id]
                if verbose > 1:
                    i.show()
                if i.id in pathnum_to_ins:
                    tablePathAdaptator.insAPath(i)
                    if verbose > 1:
                        print "--> inserted!"
            sys.stdout.flush()

#----------------------------------------------------------------------------

def connect_set_chunks( chunk, table ):

    if verbose > 0:
        print "connect chunks..."
        sys.stdout.flush()

    tableSetAdaptator=pyRepet.sql.TableAdaptator.TableSetAdaptator(db,table)

    nbChunks = len(chunk.keys())
    
    for num_chunk in xrange(1,nbChunks):
        #chunkName="chunk"+str(num_chunk)
        chunkName = "chunk%s" % ( str(num_chunk).zfill( len(str(nbChunks)) ) )
        if verbose > 1:
            print chunkName
        #next_chunkName="chunk"+str(num_chunk+1)
        next_chunkName = "chunk%s" % ( str(num_chunk+1).zfill( len(str(nbChunks)) ) )
        
        if next_chunkName not in chunk.keys():
            break
        start=chunk[chunkName][2]
        end=chunk[next_chunkName][1]
        if chunk[chunkName][0]==chunk[next_chunkName][0]:
            lset=tableSetAdaptator.getSetList_from_qcoord(chunk[chunkName][0],start,end)
            if verbose > 1:
                print "----------"
            lset.sort()
            chg_set_id={}
            setnum_to_ins=[]
            setnum_to_del=[]
            dset=[]
            rset=[]
            for i in lset:
                if i.isPlusStrand():
                    dset.append(i)
                else:
                    rset.append(i)
            x=0
            while x < len(dset)-1:
                x=x+1
                if verbose > 1:
                    print "++++"
                    dset[x-1].show()
                    dset[x].show()

                if dset[x-1].id != dset[x].id \
                   and dset[x-1].seqname==dset[x].seqname\
                   and dset[x-1].name==dset[x].name\
                   and dset[x-1].isPlusStrand()\
                   ==dset[x].isPlusStrand()\
                   and dset[x-1].overlap(dset[x]):
                    chg_set_id[dset[x].id]=dset[x-1].id
                    if dset[x-1].id not in setnum_to_ins:
                        setnum_to_ins.append(dset[x-1].id)
                    if dset[x].id not in setnum_to_del:
                        setnum_to_del.append(dset[x].id)
                    dset[x-1].merge(dset[x])
                    del dset[x]
                    x=x-1
                    if verbose > 1:
                        print "--> merged"
            if verbose > 1:
                print "..........."
            x=0
            while x < len(rset)-1:
                x=x+1
                if verbose > 1:
                    print "++++"
                    rset[x-1].show()
                    rset[x].show()

                if rset[x-1].id != rset[x].id \
                   and rset[x-1].seqname==rset[x].seqname\
                   and rset[x-1].name==rset[x].name\
                   and rset[x-1].isPlusStrand()\
                   ==rset[x].isPlusStrand()\
                   and rset[x-1].overlap(rset[x]):
                    chg_set_id[rset[x].id]=rset[x-1].id
                    if rset[x-1].id not in setnum_to_ins:
                        setnum_to_ins.append(rset[x-1].id)
                    if rset[x].id not in setnum_to_del:
                        setnum_to_del.append(rset[x].id)
                    rset[x-1].merge(rset[x])
                    del rset[x]
                    x=x-1
                    if verbose > 1:
                        print "--> merged"
            if verbose > 1:
                print "..........."
                print setnum_to_del
            tableSetAdaptator.delSet_from_listnum(setnum_to_del)
            if verbose > 1:
                print setnum_to_ins
            tableSetAdaptator.delSet_from_listnum(setnum_to_ins)
            for i in dset:
                if chg_set_id.has_key(i.id):
                    i.id=chg_set_id[i.id]
                if verbose > 1:
                    i.show()
                if i.id in setnum_to_ins:
                    tableSetAdaptator.insASet(i)
                    if verbose > 1:
                        print "--> inserted!"
                if verbose > 1:
                    print "=========="
            for i in rset:
                if chg_set_id.has_key(i.id):
                    i.id=chg_set_id[i.id]
                if verbose > 1:
                    i.show()
                if i.id in setnum_to_ins:
                    tableSetAdaptator.insASet(i)
                    if verbose > 1:
                        print "--> inserted!"
                if verbose > 1:
                    print "=========="

#-----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
