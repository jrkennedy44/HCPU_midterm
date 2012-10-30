#!/usr/bin/env python

##@file
# usage: filterOutGrouper.py [ options ]
# options:
#      -h: this help
#      -i: name of the input file (output from Grouper, format='fasta')
#      -m: minimum number of sequences per group (default=3)
#      -M: maximum number of sequences (the longest) per group (default=20)
#      -L: maximum length of a HSP, with join or not (in bp, default=20000, -1 to avoid)
#      -J: maximum length of a join (in bp, default=30000, -1 to avoid)
#      -O: chunk overlap (default=10000; skip chunk filtering if negative, e.g. -1)
#      -o: name of the output file (format='fasta', default=inFileName+'.filtered')
#      -v: verbose (default=0/1/2)

import os
import sys
import getopt
import logging

if not os.environ.has_key( "REPET_PATH" ):
    print "ERROR: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

from pyRepet.util.Stat import Stat
from pyRepetUnit.commons.coord.Map import Map


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (output from Grouper, format='fasta')"
    print "     -m: minimum number of sequences per group (default=3)"
    print "     -M: maximum number of sequences (the longest) per group (default=20)"
    print "     -L: maximum length of a HSP, with join or not (in bp, default=20000, -1 to avoid)"
    print "     -J: maximum length of a join (in bp, default=30000, -1 to avoid)"
    print "     -O: chunk overlap (default=10000; skip chunk filtering if negative, e.g. -1)"
    print "     -o: name of the output file (format='fasta', default=inFileName+'.filtered')"
    print "     -v: verbose (default=0/1/2)"
    print


def getStatsGroupSize( dGr2Mb ):
    """
    Get some descriptive statistics on the groups.
    """
    string = ""
    iStat.reset()

    lGroups = dGr2Mb.keys()
    lGroups.sort()
    nbGroups = len(lGroups)
    string += "%i groups" % ( nbGroups )

    countGroup = 0
    for groupID in lGroups:
        countGroup += 1
        iStat.add( len(dGr2Mb[groupID]) )
        if verbose > 1:
            msg = "group %s (%s/%i): %i member" % ( groupID, str(countGroup).zfill(len(str(nbGroups))), nbGroups, len(dGr2Mb[groupID]) )
            if len(dGr2Mb[groupID]) > 1:
                msg += "s"
            print msg
            sys.stdout.flush()

    string += "\ngroup size: mean=%.3f sd=%.3f" % ( iStat.mean(), iStat.sd() )
    string += "\n%s" % ( iStat.stringQuantiles() )

    logging.info( string )
    if verbose > 0:
        print string; sys.stdout.flush()


def getStatsMemberLength( dGr2Mb, dMb2Length ):
    """
    Get some descriptive statistics on the members.
    """
    string = ""
    iStat.reset()
    iStatForCoefVar = Stat()

    for groupID in dGr2Mb.keys():
        tmpStat = Stat()
        for memberID in dGr2Mb[groupID]:
            iStat.add( dMb2Length[memberID] )
            tmpStat.add( dMb2Length[memberID] )
        iStatForCoefVar.add( tmpStat.cv() )

    string += "%i members" % ( iStat.n )
    string += "\nmember length: mean=%.3f sd=%.3f" % ( iStat.mean(), iStat.sd() )
    string += "\n%s" % ( iStat.stringQuantiles() )
    string += "\ncoef var of member length: mean=%.3f sd=%.3f" % ( iStatForCoefVar.mean(), iStatForCoefVar.sd() )

    logging.info( string )
    if verbose > 0:
        print string; sys.stdout.flush()


def getStatsJoinLengths( lJoinLengths ):
    """
    Get some descriptive statistics on the joins (pairs of connected HSPs).
    """
    string = ""
    iStat.reset()

    for i in lJoinLengths:
        iStat.add( i )

    string += "mean length of the joins (connection between 2 HSPs): %.3f bp" % ( iStat.mean() )
    string += "\n%s" % ( iStat.stringQuantiles() )

    logging.info( string )
    if verbose > 0:
        print string; sys.stdout.flush()


def removeRedundantMembersDueToChunkOverlaps( dGroupId2MemberHeaders, dGr2Mb, chunkOverlap ):
    # for each group
    for groupID in dGroupId2MemberHeaders.keys():
        if verbose > 1:
            print "group %s:" % ( groupID )
        if groupID not in [ "3446" ]:
            #continue
            pass

        # get members into Map object, per chunk name
        dChunkName2Map = {}
        for memberH in dGroupId2MemberHeaders[ groupID ]:
            if verbose > 1: print memberH
            tokens = memberH.split(" ")
            if "," not in tokens[3]:
                m = Map()
                m.name = tokens[0]
                m.seqname = tokens[1]
                m.start = int( tokens[3].split("..")[0] )
                m.end = int( tokens[3].split("..")[1] )
                dChunkName2Map[ m.seqname ] = [ m ]
            else:
                dChunkName2Map[ tokens[1] ] = []
                for i in tokens[3].split(","):
                    m = Map()
                    m.name = tokens[0]
                    m.seqname = tokens[1]
                    m.start = int( i.split("..")[0] )
                    m.end = int( i.split("..")[1] )
                    dChunkName2Map[ m.seqname ].append( m )

        # remove chunks without previous or next chunks
        for chunkName in dChunkName2Map.keys():
            chunkId = int( chunkName.split("chunk")[1] )
            if not ( dChunkName2Map.has_key( "chunk%i" % ( chunkId + 1 ) ) \
                     or dChunkName2Map.has_key( "chunk%i" % ( chunkId - 1 ) ) ):
                del dChunkName2Map[ chunkName ]
                continue

        # for each pair of chunk overlap, remove one chunk
        lChunkNames = dChunkName2Map.keys()
        lChunkNames.sort()
        out = []
        for i in range(0,len(lChunkNames), 2):
            del dChunkName2Map[ lChunkNames[i] ]

        # remove members outside chunk overlap (~< 10000 bp)
        for chunkName in dChunkName2Map.keys():
            out = []
            for index, m in enumerate( dChunkName2Map[ chunkName ][:] ):
                if m.getMax() <= 1.1 * chunkOverlap:
                    out.append( dChunkName2Map[ chunkName ][ index ] )
            dChunkName2Map[ chunkName ] = out
            if len(dChunkName2Map[ chunkName ]) == 0:
                del dChunkName2Map[ chunkName ]

        if verbose > 1:
            print "all members:", dGr2Mb[ groupID ]
            print "chunks to clean:", dChunkName2Map.keys()
        lMembersToRemove = []
        for i in dChunkName2Map.keys():
            for j in dChunkName2Map[ i ]:
                mbId = j.name.split("Gr")[0]
                if "Q" in mbId:
                    mbId = mbId.split("Q")[1]
                elif "S" in mbId:
                    mbId = mbId.split("S")[1]
                lMembersToRemove.append( mbId )
        out = []
        for index, k in enumerate( dGr2Mb[ groupID ][:] ):
            if k not in lMembersToRemove:
                out.append( dGr2Mb[ groupID ][index] )
        dGr2Mb[ groupID ] = out
        if verbose > 1:
            print "members to keep:", dGr2Mb[ groupID ]
            sys.stdout.flush()

    return dGr2Mb


def main():
    """
    This program filters the groups made by Grouper.
    """
    inFaFileName = ""
    minSeq = 3
    maxSeq = 20
    maxHspLength = 20000
    maxJoinLength = 30000
    outFaFileName = ""
    chunkOverlap = 10000
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:m:M:L:J:O:o:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o, a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFaFileName = a
        elif o == "-m":
            minSeq = int(a)
        elif o == "-M":
            maxSeq = int(a)
        elif o == "-L":
            maxHspLength = int(a)
        elif o == "-J":
            maxJoinLength = int(a)
        elif o == "-O":
            chunkOverlap = int(a)
        elif o == "-o":
            outFaFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFaFileName == "":
        print "ERROR: missing compulsory options"
        help()
        sys.exit(1)

    if minSeq < 0 or maxSeq < 0 or maxSeq < minSeq:
        print "ERROR with options '-m' or '-M'"
        help()
        sys.exit(1)

    if outFaFileName == "":
        outFaFileName = "%s.filtered" % ( inFaFileName )

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    logFileName = "%s_filtered.log" % ( inFaFileName )
    if os.path.exists( logFileName ):
        os.remove( logFileName )
    global logging
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )

    if minSeq > 0:
        logging.info( "keep groups with more than %i members" % ( minSeq ) )
    if maxSeq > 0:
        logging.info( "keep the %i longest sequences of each group" % ( maxSeq ) )

    # create the object recording the statistics
    global iStat
    iStat = Stat()


    # retrieve the data about the groups and check the length of the members

    string = "parse input file '%s'" % ( inFaFileName )
    logging.info( string )
    if verbose > 0:
        print "\n* %s" % ( string ); sys.stdout.flush()

    keep = True
    nbHspTooLong = 0
    nbJoinTooLong = 0
    dGr2Mb = {}
    dMb2Length = {}
    lJoinLengths = []
    dGroupId2MemberHeaders = {}

    inFaFile = open( inFaFileName, "r" )
    line = inFaFile.readline()

    while True:

        if line == "":
            break

        if line[0] == ">":
            data = line[:-1].split(" ")
            if verbose > 2:
                print data

            memberName = data[0]
            clusterID = memberName.split("Cl")[1]
            groupID = memberName.split("Cl")[0].split("Gr")[1]
            if "Q" in memberName.split("Gr")[0]:
                memberID = memberName.split("Gr")[0].split("MbQ")[1]
            elif "S" in memberName:
                memberID = memberName.split("Gr")[0].split("MbS")[1]

            coord = data[-1]

            # if the member was joined (concatenation of several HSPs)
            if "," in coord:
                length = 0
                for i in coord.split(","):
                    start = int( i.split("..")[0] )
                    end = int( i.split("..")[1] )
                    length += abs( end - start ) + 1
                if maxHspLength > 0 and length > maxHspLength:
                    keep = False
                    nbHspTooLong += 1
                else:
                    if maxJoinLength > 0:
                        for i in coord.split("..")[1:-1]:
                            joinLength = abs( int(i.split(",")[1]) - int(i.split(",")[0]) ) + 1
                            lJoinLengths.append( joinLength )
                            if joinLength > maxJoinLength:
                                keep = False
                                nbJoinTooLong += 1

            # if not (the member is one HSP)
            else:
                start = int( coord.split("..")[0] )
                end = int( coord.split("..")[1] )
                length = abs( end - start ) + 1
                if maxHspLength > 0 and length > maxHspLength:
                    keep = False
                    nbHspTooLong += 1

            if keep == True:
                if dGr2Mb.has_key( groupID ):
                    dGr2Mb[ groupID ].append( memberID )
                    dGroupId2MemberHeaders[ groupID ].append( line[0:-1] )
                else:
                    dGr2Mb[ groupID ] = [ memberID ]
                    dGroupId2MemberHeaders[ groupID ] = [ line[0:-1] ]
                if dMb2Length.has_key( memberID ):
                    print "ERROR: memberID '%s' is duplicated" % ( memberID )
                else:
                    dMb2Length[ memberID ] = length

        line = inFaFile.readline()
        keep = True

    inFaFile.close()

    if len(dMb2Length.keys()) == 0:
        string = "WARNING: input fasta file '%s' is empty" % ( inFaFileName )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()
        os.system( "touch %s" % ( outFaFileName ) )
        logging.info( "finished" )
        if verbose > 0:
            print "END %s" % ( sys.argv[0].split("/")[-1] )
            sys.stdout.flush()
        sys.exit(0)

    if maxHspLength > 0:
        string = "nb of HSPs longer than %i bp: %i" % ( maxHspLength, nbHspTooLong )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()
    if maxJoinLength > 0:
        string = "nb of joins longer than %i bp: %i" % ( maxJoinLength, nbJoinTooLong )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()
    getStatsGroupSize( dGr2Mb )
    getStatsMemberLength( dGr2Mb, dMb2Length )
    getStatsJoinLengths( lJoinLengths )

    if chunkOverlap > 0:
        removeRedundantMembersDueToChunkOverlaps( dGroupId2MemberHeaders, dGr2Mb, chunkOverlap )


    # delete dictionary entries corresponding to groups having less than 'minSeq' members

    nbTooSmallGroup = 0

    if minSeq > 0:

        string = "filter groups having less than %i members" % ( minSeq )
        logging.info( string )
        if verbose > 0:
            print "\n* %s" % ( string ); sys.stdout.flush()

        for groupID in dGr2Mb.keys():
            if len( dGr2Mb[groupID] ) < minSeq:
                del dGr2Mb[groupID]
                nbTooSmallGroup += 1

        string = "nb of groups with less than %i members: %i" % ( minSeq, nbTooSmallGroup )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()


    # select the 'maxSeq' longest sequences of each group

    if maxSeq >= minSeq:

        string = "keep the %i longest sequences of each group" % ( maxSeq )
        logging.info( string )
        if verbose > 0:
            print "\n* %s" % ( string ); sys.stdout.flush()

        lMbToKeep = []
        groupsWithManyMb = 0

        for groupID in dGr2Mb.keys():
            lMbFromThisGroup = []

            if len( dGr2Mb[groupID] ) > maxSeq:
                groupsWithManyMb += 1
                for mb in dGr2Mb[groupID]:
                    lMbFromThisGroup.append( "%i_|_%s" % ( dMb2Length[mb], mb ) )
                    lMbFromThisGroup.sort()
                    lMbFromThisGroup.reverse()
                tmp_lFilteredMb = []
                for i in xrange( 0, min(len(lMbFromThisGroup),maxSeq) ):
                    lMbToKeep.append( lMbFromThisGroup[i].split("_|_")[1] )
                    tmp_lFilteredMb.append( lMbFromThisGroup[i].split("_|_")[1] )
                dGr2Mb[groupID] = tmp_lFilteredMb

            else:
                for mb in dGr2Mb[groupID]:
                    lMbToKeep.append( mb )

        string = "nb of groups with more than %i members: %i" % ( maxSeq, groupsWithManyMb )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()

    getStatsGroupSize( dGr2Mb )
    getStatsMemberLength( dGr2Mb, dMb2Length )


    # write the remaining sequences into the output fasta file

    inFaFile = open( inFaFileName, "r" )
    line = inFaFile.readline()
    outFaFile = open( outFaFileName, "w" )

    string = "write output file '%s'" % ( outFaFileName )
    logging.info( string )
    if verbose > 0:
        print "\n* %s" % ( string ); sys.stdout.flush()

    keepMember = False

    while True:

        if line == "":
            break

        if line[0] == ">":
            data = line[:-1].split(" ")

            memberName = data[0]
            clusterID = memberName.split("Cl")[1]
            groupID = memberName.split("Cl")[0].split("Gr")[1]
            if "Q" in memberName.split("Gr")[0]:
                memberID = memberName.split("Gr")[0].split("MbQ")[1]
            elif "S" in memberName:
                memberID = memberName.split("Gr")[0].split("MbS")[1]

            if memberID in lMbToKeep:
                keepMember = True
                outFaFile.write( line )
            else:
                keepMember = False

        else:
            if keepMember == True:
                outFaFile.write( line )

        line = inFaFile.readline()

    inFaFile.close()
    outFaFile.close()

    logging.info( "finished" )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
