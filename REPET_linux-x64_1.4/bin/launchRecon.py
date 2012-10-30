#!/usr/bin/env python

import os
import sys
import getopt

try:
    from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
except:
    msg = "ERROR: can't import package 'FastaUtils'"
    sys.stderr.write( "%s\n" % ( msg ) )
    sys.exit(1)


def help():
    print
    print "usage: launchRecon.py [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -p: project name (default=alignFileName)"
    print "     -f: name of the file used as query by Blaster (format='fasta')"
    print "     -a: name of the file returned by Blaster (format='align')"
    print "     -c: clean"
    print "     -v: verbosity level (default=0/1)"
    print
    
    
def recon2map( inFileName, outFileName ):
    inFile = open( inFileName, "r" )
    outFile = open( outFileName, "w" )
    line = inFile.readline()   # to avoid the 1st line of comments
    while True:
        line = inFile.readline()
        if line == "":
            break
        data = line.split()
        clusterID = data[0]
        memberID = data[1]
        strand = data[2]
        seqName = data[3]
        seqStart = data[4]
        seqEnd = data[5]
        if strand == "-1":
            tmp = seqStart
            seqStart = seqEnd
            seqEnd = tmp
        string = "ReconCluster%sMb%s\t%s\t%s\t%s\n" % ( clusterID, memberID, seqName, seqStart, seqEnd )
        outFile.write( string )
    inFile.close()
    outFile.close()


def main():
    projectName = ""
    faFileName = ""
    alignFileName = ""
    clean = False
    verbose = 0

    try:
        opts, args = getopt.getopt( sys.argv[1:], "hp:f:a:cv:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % ( str(err) ) )
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-p":
            projectName = a
        elif o == "-f":
            faFileName = a
        elif o == "-a":
            alignFileName = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)

    if faFileName == "":
        msg = "ERROR: missing 'fasta' file (-f)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if  alignFileName == "":
        msg = "ERROR: missing 'align' file (-a)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if not os.path.exists( faFileName ):
        msg = "ERROR: can't find file '%s'" % ( faFileName )
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    if not os.path.exists( alignFileName ):
        msg = "ERROR: can't find file '%s'" % ( alignFileName )
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if projectName == "":
        projectName = alignFileName


    if verbose > 0:
        print "prepare MSP file"; sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/align2recon.py"
    cmd = prg
    cmd += " -i %s" % ( alignFileName )
    cmd += " -o %s_MSP_file" % ( projectName )
    cmd += " -v %i" % ( verbose - 1 )
    returnStatus = os.system( cmd )
    if returnStatus != 0:
        msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
        sys.stderr.write( "%s\n" % ( msg ) )
        sys.exit(1)


    if verbose > 0:
        print "prepare seq file"; sys.stdout.flush()
    lSeqNames = FastaUtils.dbHeaders( faFileName, verbose - 1 )
    lSeqNames.sort()
    seqListFile = open( projectName + "_seq_list", "w" )
    seqListFile.write( str(len(lSeqNames)) + "\n" )
    for seqName in lSeqNames:
        seqListFile.write( ">%s\n" % ( seqName ) )
    seqListFile.close()


    if verbose > 0:
        print "Recon is running..."; sys.stdout.flush()
    prg = "recon.pl"
    cmd = prg
    cmd += " %s_seq_list" % ( projectName )
    cmd += " %s_MSP_file" % ( projectName )
    cmd += " 1"
    returnStatus = os.system( cmd )
    if returnStatus != 0:
        msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
        sys.stderr.write( "%s\n" % ( msg ) )
        sys.exit(1)
        
    if clean == True:
        os.system( "rm -rf edge_redef_res ele_def_res ele_redef_res" )


    if verbose > 0:
        print "convert results into 'map' format"; sys.stdout.flush()
    recon2map( "summary/eles", projectName + "_Recon.map" )

    if clean == True:
        os.system( "rm -rf summary images" )


    if verbose > 0:
        print "generate fasta from map"; sys.stdout.flush()
    prg = os.environ["REPET_PATH"] + "/bin/map2db"
    cmd = prg
    cmd += " -v %i" % ( verbose - 1 )
    cmd += " %s_Recon.map" % ( projectName )
    cmd += " %s" % ( faFileName )
    returnStatus = os.system( cmd )
    if returnStatus != 0:
        msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
        sys.stderr.write( "%s\n" % ( msg ) )
        sys.exit(1)

    os.system( "mv " + projectName + "_Recon.map.flank_size0.fa " + projectName + "_Recon.fa" )


    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
