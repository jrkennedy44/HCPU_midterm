#!/usr/bin/env python

"""
Save annotations from a REPET table into a GFF3 file.
"""

import os
import sys
import getopt
import ConfigParser
import glob

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepet.sql.RepetDB import *


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage:",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -f: 'fasta' file or 'seq' table recording the input sequences (required to generate new '.gff3' files)"
    print "     -g: gff3 file or pattern (e.g. '*.gff3')"
    print "     -t: file of table name to use to create the gff3 files (tier name 'tab' format 'tab' table name)"
    print "     -c: Chado compliance"
    print "     -C: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2/3)"
    print


def createGff3Files( seqData ):
    """
    Create as many GFF3 files as sequences given in parameter.

    @param seqData: 'fasta' file or 'seq' table recording the input sequences
    @type seqData: string
    """

    if os.path.exists( seqData ):
        if verbose > 0:
            print "create GFF3 file(s) from file '%s'..." % ( seqData )
            sys.stdout.flush()
        inDB = pyRepet.seq.BioseqDB( seqData )
        for bs in inDB.db:
            outFile = open( "%s.gff3" % ( bs.header ), "w" )
            outFile.write( "##gff-version 3\n" )
            outFile.write( "##sequence-region %s 1 %s\n" %( bs.header, bs.getLength() ) )
            outFile.write( "##FASTA\n" )
            outFile.write( ">%s\n" % ( bs.header ) )
            i = 0
            while i < bs.getLength():
                outFile.write( bs.sequence[i:i+60] + "\n" )
                i += 60
            outFile.close()

    elif db.exist( seqData ):
        if verbose > 0:
            print "create GFF3 file(s) from table '%s'..." % ( seqData )
            sys.stdout.flush()
        qry = "SELECT DISTINCT accession,length,sequence FROM %s" % ( seqData )
        db.execute( qry )
        lSequences = db.fetchall()
        for seq in lSequences:
            outFile = open( "%s.gff3" % ( seq[0] ), "w" )
            outFile.write( "##gff-version 3\n" )
            outFile.write( "##sequence-region %s 1 %s\n" %( seq[0], seq[1] ) )
            outFile.write( "##FASTA\n" )
            outFile.write( ">%s\n" % ( seq[0] ) )
            i = 0
            while i < int(seq[1]):
                outFile.write( seq[2][i:i+60] + "\n" )
                i += 60
            outFile.close()

    else:
        print "ERROR: no file or table '%s' exists" % ( seqData )
        sys.exit(1)


def saveAnnotPath( key, table, tierName, chado ):
    """
    Save the annotations from the table corresponding to the given sequence.

    @param key: name of the sequence
    @type key: string

    @param table: name of the 'path' table
    @type table: string

    @param tierName: name of the tier in the GFF3 file
    @type tierName: string

    @param chado: Chado compliance
    @type chado: boolean
    """

    if verbose > 1:
        print "processing '%s' for tier '%s'..." % ( key, tierName )
        sys.stdout.flush()

    log = os.system( "mv %s.gff3 %s.gff3_tmp" % ( key, key ) )
    if log != 0:
        print "ERROR in saveAnnotPath()"
        sys.exit(1)
    tmpFile = open( "%s.gff3_tmp" % ( key ), "r" )
    line = tmpFile.readline()
    outFile = open( "%s.gff3" % ( key ), "w" )
    while True:
        if line == "":
            break
        if line != "##FASTA\n":
            outFile.write( line )
            line = tmpFile.readline()
        else:
            source = tierName
            feature = "region"
            frame = "."
            cmd = getPathFeatures( table, key, source, feature, frame, chado )
            outFile.write( cmd )
            break
    if line == "##FASTA\n":
        while True:
            if line == "":
                break
            outFile.write( line )
            line = tmpFile.readline()
    tmpFile.close()
    outFile.close()
    os.system( "rm %s.gff3_tmp" % ( key ) )


def getPathFeatures( pathTable, seqName, source, feature, frame, chado ):
    """
    Retrieve the features to write in the GFF3 file.

    @param pathTable: name of the MySQL table recording the annotations (i.e. the features)
    @type pathTable: string

    @param seqName: name of the sequence (the source feature) on which we want to visualize the matches (the features)
    @type seqName: string

    @param source: the program that generated the feature (i.e. REPET)
    @type source: string

    @param frame: '.' by default
    @type frame: string

    @param chado: Chado compliance
    @type chado: boolean
    """

    string = ""

    # retrieve all the data about the matches
    qry = "SELECT DISTINCT path, query_start, query_end, subject_name, subject_start, subject_end, E_value FROM %s WHERE query_name=\"%s\"" % ( pathTable, seqName )
    db.execute( qry )
    data = db.fetchall()

    # organise them into 'match' and 'match_part'
    dPathID2Data = gatherSamePathFeatures( data )

    # build the output string
    for pathID in dPathID2Data:
        string += organizeEachPathFeature( pathID, dPathID2Data[ pathID ], seqName, source, frame, chado )

    return string


def gatherSamePathFeatures( data ):
    """
    Gather matches with the same path ID.

    @param data: results of a MySQL request
    @type data: list of lists of strings

    @return: dictionary whose keys are path IDs and values are matches data
    """

    dPathID2Matchs = {}

    for i in data:

        pathID = i[0]
        query_start = i[1]
        query_end = i[2]
        subject_name = i[3].replace(";"," ").replace(","," ").replace("  "," ")
        subject_start = i[4]
        subject_end = i[5]
        E_value = i[6]

        # save the annotations with the subject always on the '+' strand
        if subject_start > subject_end:
            tmp = subject_start
            subject_start = subject_end
            subject_end = tmp
            tmp = query_start
            query_start = query_end
            query_end = tmp

        matchStart = min( query_start, query_end )
        matchEnd = max( query_start, query_end )
        strand = getStrand( query_start, query_end )

        if dPathID2Matchs.has_key( pathID ):
            dPathID2Matchs[ pathID ].append( [ matchStart, matchEnd, strand, subject_name, subject_start, subject_end, E_value ] )

        else:
            dPathID2Matchs[ pathID ] = [ [ matchStart, matchEnd, strand, subject_name, subject_start, subject_end, E_value ] ]

    return dPathID2Matchs


def organizeEachPathFeature( pathID, lMatches, seqName, source, frame, chado ):
    """
    For a specific path ID, organize match data according to the GFF3 format.

    @param pathID: path ID
    @type pathID: string

    @param lMatches: list of matches ( [ matchStart, matchEnd, strand, subject_name, subject_start, subject_end, E_value ] )
    @type lMatches: list of list(s) of strings

    @param seqName: name of the source feature
    @type seqName: string

    @param source: 'source' field for GFF3 format
    @type source: string

    @param frame: 'frame' field for GFF3 format
    @type frame: string

    @param chado: Chado compliance
    @type chado: boolean

    @return: lines to write in the GFF3 file
    @rtype: string
    """

    string = ""

    minStart = lMatches[0][0]
    maxEnd = lMatches[0][1]
    minStartSubject = lMatches[0][4]
    maxEndSubject = lMatches[0][5]
    strand = lMatches[0][2]

    # for each match
    for i in lMatches:

        if i[0] < minStart:
            minStart = i[0]

        if i[1] > maxEnd:
            maxEnd = i[1]

        if i[4] < minStartSubject:
            minStartSubject = i[4]

        if i[5] > maxEndSubject:
            maxEndSubject = i[5]

    target = lMatches[0][3]

    attributes = "ID=ms%s_%s_%s" % ( pathID, seqName, target )
    if chado == True:
        attributes += ";Target=%s+%s+%s" % ( target, minStartSubject, maxEndSubject )
    else:
        attributes += ";Target=%s %s %s" % ( target, minStartSubject, maxEndSubject )
    string += "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( seqName, source, "match", minStart, maxEnd, "0.0", strand, frame, attributes )

    if len(lMatches) > 1:
        count = 1
        for i in lMatches:
            attributes = "ID=mp%s-%i_%s_%s" % ( pathID, count, seqName, target )
            attributes += ";Parent=ms%s%s%s%s%s" % ( pathID, "_", seqName, "_", target )
            if chado == True:
                attributes += ";Target=%s+%s+%s" % ( target, i[4], i[5] )
            else:
                attributes += ";Target=%s %s %s" % ( target, i[4], i[5] )
            string += "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( seqName, source, "match_part", i[0], i[1], i[6], i[2], frame, attributes )
            count += 1

    return string


def saveAnnotSet( key, table, tierName, chado ):
    """
    Save the annotations from the table corresponding to the given sequence.

    @param key: name of the sequence
    @type key: string

    @param table: name of the 'set' table
    @type table: string

    @param tierName: name of the tier in the GFF3 file
    @type tierName: string
    """

    if verbose > 1:
        print "processing '%s' for tier '%s'..." % ( key, tierName )
        sys.stdout.flush()

    log = os.system( "mv %s.gff3 %s.gff3_tmp" % ( key, key ) )
    if log != 0:
        print "ERROR in saveAnnotSet()"
        sys.exit(1)
    tmpFile = open( "%s.gff3_tmp" % ( key ), "r" )
    line = tmpFile.readline()
    outFile = open( "%s.gff3" % ( key ), "w" )
    while True:
        if line == "":
            break
        if line != "##FASTA\n":
            outFile.write( line )
            line = tmpFile.readline()
        else:
            source = tierName
            feature = "region"
            frame = "."
            cmd = getSetFeatures( table, key, source, feature, frame, chado )
            outFile.write( cmd )
            break
    if line == "##FASTA\n":
        while True:
            if line == "":
                break
            outFile.write( line )
            line = tmpFile.readline()
    tmpFile.close()
    outFile.close()
    os.system( "rm %s.gff3_tmp" % ( key ) )


def getSetFeatures( table, key, source, feature, frame, chado ):
    """
    Retrieve the features to write in the GFF3 file.

    @param table: name of the MySQL table recording the annotations (i.e. the features)
    @type table: string

    @param key: name of the sequence (the source feature) on which we want to visualize the matches (the features)
    @type key: string

    @param source: the program that generated the feature (i.e. REPET)
    @type source: string

    @param frame: '.' by default
    @type frame: string

    @param chado: Chado compliance
    @type chado: boolean
    """

    string = ""

    # retrieve all the data about the matches
    qry = "SELECT DISTINCT path,name,start,end FROM %s WHERE chr=\"%s\"" % ( table, key )
    db.execute( qry )
    data = db.fetchall()

    # organise them into 'match' and 'match_part'
    dPathID2Data = gatherSameSetFeatures( data )

    # build the output string
    for pathID in dPathID2Data:
        string += organizeEachSetFeature( pathID, dPathID2Data[ pathID ], key, source, frame, chado )

    return string


def gatherSameSetFeatures( data ):
    """
    Gather matches with the same path ID.

    @param data: results of a MySQL request
    @type data: list of lists of strings

    @return: dictionary whose keys are path IDs and values are matches data
    """

    dPathID2Matchs = {}

    for i in data:

        pathID = i[0]
        name = i[1]
        start = i[2]
        end = i[3]

        matchStart = min( start, end )
        matchEnd = max( start, end )
        strand = getStrand( start, end )

        if dPathID2Matchs.has_key( pathID ):
            dPathID2Matchs[ pathID ].append( [ name, matchStart, matchEnd, strand ] )

        else:
            dPathID2Matchs[ pathID ] = [ [ name, matchStart, matchEnd, strand ] ]

    return dPathID2Matchs


def organizeEachSetFeature( pathID, lMatches, seqName, source, frame, chado ):
    """
    For a specific path ID, organize match data according to the GFF3 format.

    @param pathID: path ID
    @type pathID: string

    @param lMatches: list of matches ( [ name, start, end, strand ] )
    @type lMatches: list of list(s) of strings

    @param seqName: name of the source feature
    @type seqName: string

    @param source: 'source' field for GFF3 format
    @type source: string

    @param frame: 'frame' field for GFF3 format
    @type frame: string

    @param chado: Chado compliance
    @type chado: boolean

    @return: lines to write in the GFF3 file
    @rtype: string
    """

    string = ""

    minStart = lMatches[0][1]
    maxEnd = lMatches[0][2]
    strand = lMatches[0][3]

    # for each match
    for i in lMatches:

        if i[0] < minStart:
            minStart = i[0]

        if i[1] > maxEnd:
            maxEnd = i[1]

    target = lMatches[0][0].replace("(","").replace(")","").replace("#","")

    attributes = "ID=ms%s_%s_%s" % ( pathID, seqName, target )
    if chado == True:
        attributes += ";Target=%s+%s+%s" % ( target, "1", abs(minStart-maxEnd)+1 )
    else:
        attributes += ";Target=%s %s %s" % ( target, "1", abs(minStart-maxEnd)+1 )
    string += "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( seqName, source, "match", minStart, maxEnd, "0.0", strand, frame, attributes )

    if len(lMatches) > 1:
        count = 1
        for i in lMatches:
            attributes = "ID=mp%s-%i_%s_%s" % ( pathID, count, seqName, target )
            attributes += ";Parent=ms%s%s%s%s%s" % ( pathID, "_", seqName, "_", target )
            if chado == True:
                attributes += ";Target=%s+%s+%s" % ( target, "1", abs(i[1]-i[2])+1 )
            else:
                attributes += ";Target=%s %s %s" % ( target, "1", abs(i[1]-i[2])+1 )
            string += "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( seqName, source, "match_part", i[1], i[2], "0.0", i[3], frame, attributes )
            count += 1

    return string


def getStrand( start, end ):
    """
    Return the strand ('+' if start < end, '-' otherwise).

    @param start: start coordinate
    @type start: integer

    @param end: end coordinate
    @type end: integer
    """

    if start < end:
        return "+"
    else:
        return "-"


def main():
    """
    This program exports annotations from a 'path' table into a GFF3 file.
    """

    seqData = ""
    gff3FileName = ""
    tablesFileName = ""
    chado = False
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    global verbose
    verbose = 0

    try:
        options,arguments=getopt.getopt(sys.argv[1:],"hf:g:t:cC:H:U:P:D:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(0)
    if options == []:
        help()
        sys.exit(1)
    for o,a in options:
        if o == "-h" or o == "--help":
            help()
            sys.exit(0)
        elif o == "-f":
            seqData = a
        elif o == "-g":
            gff3FileName = a
        elif o == "-t":
            tablesFileName = a
        elif o == "-c":
            chado = True
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

    if seqData == "" and gff3FileName == "":
        print "ERROR: options -f or -g required"
        help()
        sys.exit(1)

    if configFileName == "" and host == "" and os.environ.get( "REPET_HOST" ) == "":
        print "ERROR: missing data about MySQL connection"
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
    else:
        if user == "":
            user = os.environ.get( "REPET_USER" )
        if host == "":
            host = os.environ.get( "REPET_HOST" )
        if passwd == "":
            passwd = os.environ.get( "REPET_PW" )
        if dbname == "":
            dbname = os.environ.get( "REPET_DB" )

    global db
    if os.environ["REPET_PATH"] != "":
        db = RepetDB( user, host, passwd, dbname )
    else:
        print "ERROR: no environment variable REPET_PATH"
        sys.exit(1)

    # create all the ".gff3" files (option '-f')
    if seqData != "":
        createGff3Files( seqData )

    # save the annotations in the gff3 file
    if tablesFileName != "":
        if os.path.exists( gff3FileName ):
            lGff3Files = [ gff3FileName ]
        else:
            lGff3Files = glob.glob( gff3FileName )
            if len(lGff3Files) == 0:
                print "ERROR: '%s' is neither a file nor a pattern" % ( gff3FileName )
                sys.exit(1)
        for gff3File in lGff3Files:
            if verbose > 0:
                print "handle file '%s'" % ( gff3File )
                sys.stdout.flush()
            key = gff3File.split(".gff3")[0]
            tablesFile = open( tablesFileName, "r" )
            lines = tablesFile.readlines()
            for l in lines:
                if l[0] == "#":
                    continue
                tok = l.split()
                if len(tok) == 0:
                    break
                tierName = tok[0]
                format = tok[1]
                table = tok[2]
                if verbose > 0:
                    print "save annotations from table '%s' (format %s)" % ( table, format)
                    sys.stdout.flush()
                if format == "path":
                    saveAnnotPath( key, table, tierName, chado )
                elif format == "set":
                    saveAnnotSet( key, table, tierName, chado )
            tablesFile.close()

    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
