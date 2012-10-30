#!/usr/bin/env python

##@file
# usage: ",sys.argv[0],"[ options ]
# options:
#      -h: this help
#      -i: input file name (output from the clustering method, format=map)
#      -o: output file (format=map, default=inFileName+'.filtered')
#      -c: clustering method used to produce the clusters (Recon/Piler, not Grouper!)
#      -L: maximum length of a HSP (in bp, default=20000, -1 to avoid)
#      -m: minimum number of sequences per group (default=3, '-1' to avoid this filter)
#      -M: maximum number of sequences (longest) per group (default=20, '-1' to avoid this filter)
#      -d: give stats per cluster, in a file inFileName+'.distribC'
#      -e: give stats per sequence, in a file inFileName+'distribS'
#      -v: verbose (default=0/1/2)


import os
import sys
import getopt
import string
import logging

from pyRepet.coord.Map import Map
from pyRepet.util.Stat import Stat


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: input file name (output from the clustering method, format=map)"
    print "     -o: output file (format=map, default=inFileName+'.filtered')"
    print "     -c: clustering method used to produce the clusters (Recon/Piler, not Grouper!)"
    print "     -L: maximum length of a HSP (in bp, default=20000, -1 to avoid)"
    print "     -m: minimum number of sequences per group (default=3, '-1' to avoid this filter)"
    print "     -M: maximum number of sequences (longest) per group (default=20, '-1' to avoid this filter)"
    print "     -d: give stats per cluster, in a file inFileName+'.distribC'"
    print "     -e: give stats per sequence, in a file inFileName+'distribS'"
    print "     -v: verbose (default=0/1/2)"
    print


def showStatsClusterSize( dCl2Mb ):
    """
    Show some descriptive statistics on the clusters.
    """

    string = ""
    iStat.reset()

    string += "%i clusters" % ( len(dCl2Mb.keys()) )

    for clusterID in dCl2Mb.keys():
        iStat.add( len(dCl2Mb[clusterID]) )
        if verbose > 2:
            print "cluster %s: %i members" % ( clusterID, len(dCl2Mb[clusterID]) ); sys.stdout.flush()

    string += "\ncluster size: mean=%.3f sd=%.3f" % ( iStat.mean(), iStat.sd() )
    string += "\n%s" % ( iStat.stringQuantiles() )

    logging.info( string )
    if verbose > 1:
        print string; sys.stdout.flush()


def showStatsMemberLength( dCl2Mb ):
    """
    Show some descriptive statistics on the members.
    """

    string = ""
    iStat.reset()
    iStatForCoefVar = Stat()

    for clusterID in dCl2Mb.keys():
        tmpStat = Stat()
        for iMap in dCl2Mb[clusterID]:
            iStat.add( iMap.length() )
            tmpStat.add( iMap.length() )
        iStatForCoefVar.add( tmpStat.cv() )

    string += "%i members" % ( iStat.n )
    string += "\nmember length: mean=%.3f sd=%.3f" % ( iStat.mean(), iStat.sd() )
    string += "\n%s" % ( iStat.stringQuantiles() )
    string += "\ncoef var of member length: mean=%.3f sd=%.3f" % ( iStatForCoefVar.mean(), iStatForCoefVar.sd() )

    logging.info( string )
    if verbose > 1:
        print string; sys.stdout.flush()


def writeDistribPerCluster( inFileName, dCl2Mb ):
    """
    Write some statistics on each cluster.
    """

    distribFileName = "%s.distribC" % ( inFileName )
    distribFile = open( distribFileName, "w" )
    distribFile.write( "cluster\tsize\tmeanMbLength\tvarMbLength\tsdMbLength\tcvMbLength\n" )

    for clusterID in dCl2Mb.keys():
        tmpStat = Stat()
        for iMap in dCl2Mb[clusterID]:
            tmpStat.add( iMap.length() )
        distribFile.write( "%s\t%i\t%f\t%f\t%f\t%f\n" % ( clusterID, len(dCl2Mb[clusterID]), tmpStat.mean(), tmpStat.var(), tmpStat.sd(), tmpStat.cv() ) )

    distribFile.close()


def writeDistribPerSeq( inFileName, dSeq2Cl ):
    """
    Write some statistics on each input sequence (not member).
    """

    distribFileName = "%s.distribS" % ( inFileName )
    distribFile = open( distribFileName, "w" )
    distribFile.write( "sequence\tclusters\tmeanMbLength\tvarMbLength\tsdMbLength\tcvMbLength\n" )

    for seqName in dSeq2Cl.keys():
        tmpStat = Stat()
        for iMap in dSeq2Cl[ seqName ]:
            tmpStat.add( iMap.length() )
        distribFile.write( "%s\t%i\t%f\t%f\t%f\t%f\n" % ( seqName, len(dSeq2Cl[seqName]), tmpStat.mean(), tmpStat.var(), tmpStat.sd(), tmpStat.cv() ) )

    distribFile.close()


def main():
    """
    This programs filters clusters of sequences to have a minimum size of to take the longest sequences.
    """

    inFileName = ""
    outFileName = ""
    clustMethod = ""
    maxHspLength = 20000
    minSeq = 3
    maxSeq = 20
    getDistribPerCluster = False
    getDistribPerSeq = False
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:c:L:m:M:dev:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o, a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-o":
            outFileName = a
        elif o == "-c":
            clustMethod = a
        elif o == "-L":
            maxHspLength = int(a)
        elif o == "-m":
            minSeq = int(a)
        elif o == "-M":
            maxSeq = int(a)
        elif o == "-d":
            getDistribPerCluster = True
        elif o == "-e":
            getDistribPerSeq = True
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file (-i)"
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        print "ERROR: can't find file '%s'" % ( inFileName )
        help()
        sys.exit(1)

    if clustMethod == "":
        print "ERROR: missing clustering method (-c)"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    # create the 'log' file
    logFileName = "%s_filtered.log" % ( inFileName )
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
        logging.info( "keep clusters with more than %i members" % ( minSeq ) )
    if maxSeq > 0:
        logging.info( "keep the %i longest sequences of each cluster" % ( maxSeq ) )

    # create the object recording the statistics
    global iStat
    iStat = Stat()

    nbClWithLessThanMinSeq = 0
    nbClWithMoreThanMaxSeq = 0


    # fill a dictionary whose keys are groupIDs and values the members belonging to the same group

    string = "parse input file '%s'" % ( inFileName )
    logging.info( string )
    if verbose > 0:
        print "\n* %s" % ( string ); sys.stdout.flush()

    inFile = open( inFileName, "r" )
    line = inFile.readline()
    count = 1
    dCl2Mb = {}
    dSeq2Cl = {}
    keep = True

    # for each member in the input file
    while True:
        if line == "":
            break

        newMap = Map()
        data = line.split("\t")
        name = data[0]
        seqname = data[1]
        start = data[2]
        end = data[3][:-1]

        # parse the data
        if clustMethod == "Grouper":
            name = name.split("Cl")[0]
            clusterID = name.split("Gr")[1]   # in Grouper's terminology, 'cluster' corresponds to 'group'
            if "Q" in name:
                memberID = name.split("Gr")[0].split("MbQ")[1]
            elif "S" in name:
                memberID = name.split("Gr")[0].split("MbS")[1]
            name = "%sCluster%sMb%s" % ( clustMethod, clusterID, memberID )   # rename to be coherent with Recon and Piler
        elif clustMethod in ["Recon","Piler"]:
            if "Fam" in name:   # old style name
                clusterID = name.split("Fam")[1]
                memberID = name.split("Pile")[1].split("Fam")[0]
            else:
                clusterID = name.split("Cluster")[1].split("Mb")[0]

        t = ( name, seqname, start, end )
        newMap.set_from_tuple( t, count )

        if newMap.length() > maxHspLength:
            keep = False

        if keep == True:

            # record the data per cluster
            if dCl2Mb.has_key( clusterID ):
                dCl2Mb[ clusterID ].append( newMap )
            else:
                dCl2Mb[ clusterID ] = [ newMap ]

            # record the data per sequence
            if dSeq2Cl.has_key( seqname ):
                dSeq2Cl[ seqname ].append( newMap )
            else:
                dSeq2Cl[ seqname ] = [ newMap ]

        line = inFile.readline()
        count += 1
        keep = True

    inFile.close()

    showStatsClusterSize( dCl2Mb )
    showStatsMemberLength( dCl2Mb )

    if getDistribPerCluster == True:
        writeDistribPerCluster( inFileName, dCl2Mb )
    if getDistribPerSeq == True:
        writeDistribPerSeq( inFileName, dSeq2Cl )


    # delete dictionary entries corresponding to groups having less than 'minSeq' members

    if minSeq > 0:

        string = "filter clusters having less than %i members" % ( minSeq )
        logging.info( string )
        if verbose > 0:
            print "\n* %s" % ( string ); sys.stdout.flush()

        for clusterID in dCl2Mb.keys():
            if len(dCl2Mb[clusterID]) < minSeq:
                nbClWithLessThanMinSeq += 1
                del dCl2Mb[clusterID]

        string = "%i cluster(s) with < %i members" % ( nbClWithLessThanMinSeq, minSeq )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()


    # select the 'maxSeq' longest sequences of each group

    if maxSeq > 0:

        string = "keep the %i longest sequences of each cluster" % ( maxSeq )
        logging.info( string )
        if verbose > 0:
            print "\n* %s" % ( string ); sys.stdout.flush()

        for clusterID in dCl2Mb.keys():
            if len(dCl2Mb[clusterID]) > maxSeq:
                nbClWithMoreThanMaxSeq += 1
                lOrdMb = []
                for iMap in dCl2Mb[clusterID]:
                    lOrdMb.append( "%i_|_%s" % ( iMap.length(), iMap.name ) )
                lOrdMb.sort()
                lOrdMb.reverse()
                tmpList = []
                for index in range(0,maxSeq):
                    mbToKeep = lOrdMb[index].split("_|_")[1]
                    count = 0
                    while dCl2Mb[clusterID][count].name != mbToKeep:
                        count += 1
                    tmpList.append( dCl2Mb[clusterID][count] )
                    del dCl2Mb[clusterID][count]
                dCl2Mb[clusterID] = tmpList

        string = "%i cluster(s) with > %i members" % ( nbClWithMoreThanMaxSeq, maxSeq )
        logging.info( string )
        if verbose > 0:
            print string; sys.stdout.flush()

    showStatsClusterSize( dCl2Mb )
    showStatsMemberLength( dCl2Mb )


    # write the remaining sequences into the output fasta file

    if outFileName == "":
        outFileName = "%s.filtered-%i-%i" % ( inFileName, minSeq, maxSeq )

    string = "write output file '%s'" % ( outFileName )
    logging.info( string )
    if verbose > 0:
        print "\n* %s" % ( string ); sys.stdout.flush()

    outFile = open( outFileName, "w" )
    for clusterID in dCl2Mb.keys():
        for iMap in dCl2Mb[clusterID]:
            outFile.write( "%s\t%s\t%i\t%i\n" % ( iMap.name, iMap.seqname, iMap.start, iMap.end ) )
    outFile.close()


    logging.info( "finished" )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
