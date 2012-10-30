#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: launchPiler.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -p: project name (default=alignFileName)"
    print "     -f: name of the file used as query by Blaster (format='fasta')"
    print "     -a: name of the file returned by Blaster (format='align')"
    print "     -s: minimum family size (default=3)" 
    print "     -c: clean"
    print "     -v: verbosity level (default=0/1)"
    print


def piler2map( inFileName, outFileName ):
    inFile = open( inFileName, "r" )
    outFile = open( outFileName, "w" )
    while True:
        line = inFile.readline()
        if line == "":
            break
        data = line.split()
        seqName = data[0]
        seqStart = data[3]
        seqEnd = data[4]
        strand = data[6]
        clusterID = data[9]
        memberID = data[12]
        if strand == "-":
            tmp = seqStart
            seqStart = seqEnd
            seqEnd = tmp
        string = "PilerCluster%sMb%s\t%s\t%s\t%s\n" % ( clusterID, memberID, seqName, seqStart, seqEnd )
        outFile.write( string )
    inFile.close()
    outFile.close()


def main():
    projectName = ""
    faFileName = ""
    alignFileName = ""
    minFamilySize = 3
    cleanDir = "no"
    verbose = 0

    try:
        options, arguments = getopt.getopt( sys.argv[1:], "hp:f:a:s:cv:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % ( str(err) ) )
        help()
        sys.exit(1)
    for o,a in options:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-p":
            projectName = a
        elif o == "-f":
            faFileName = a
        elif o == "-a":
            alignFileName = a
        elif o == "-s":
            minFamilySize = int(a)
        elif o == "-c":
            cleanDir = "yes"
        elif o == "-v":
            verbose = int(a)

    if projectName == "" or faFileName == "" or alignFileName == "":
        print "ERROR: compulsory options are missing"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()


    if verbose > 0:
        print "prepare input file"; sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/align2piler.py"
    cmd = prg
    cmd += " -i %s" % ( alignFileName )
    cmd += " -o %s.gff" % ( alignFileName )
    cmd += " -v %i" % ( verbose - 1 )
    log = os.system( cmd )
    if log != 0:
        print "*** Error: %s returned %i" % ( prg, log )
        sys.exit(1)
        
        
    if verbose > 0:
        print "Piler is running..."; sys.stdout.flush()
    prg = "piler"
    cmd = prg
    cmd += " -trs %s.gff" % ( alignFileName )
    cmd += " -out %s_Piler-trs.gff" % ( projectName )
    cmd += " -piles %s_Piler-trs_piles.gff" % ( projectName )
    cmd += " -images %s_Piler-trs_images.gff" % ( projectName )
    cmd += " -famsize %i" % ( minFamilySize )
    returnStatus = os.system( cmd )
    if returnStatus != 0:
        msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
        sys.stderr.write( "%s\n" % ( msg ) )
        sys.exit(1)


    if verbose > 0:
        print "convert results into 'map' format"; sys.stdout.flush()
    piler2map( projectName + "_Piler-trs.gff", projectName + "_Piler.map" )

    if cleanDir == "yes":
        os.system( "rm -f *trs_*.gff" )


    if verbose > 0:
        print "generate fasta from map"; sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/map2db"
    cmd = prg
    cmd += " " + projectName + "_Piler.map"
    cmd += " " + faFileName
    log = os.system( cmd )
    if log != 0:
        print "*** Error: %s returned %i" % ( prg, log )
        sys.exit(1)

    os.system( "mv " + projectName + "_Piler.map.flank_size0.fa " +  projectName + "_Piler.fa" )


    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
