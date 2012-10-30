#!/usr/bin/env python

import os
import sys
import getopt
import exceptions
from string import *


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage:",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input fasta file"
    print "     -o: name of the output fasta file (default=inFileName+'.shortH')"
    print "     -p: project name"
    print "     -s: self-alignment program (Blaster/Pals)"
    print "     -c: clustering method (Grouper/Recon/Piler)"
    print "     -m: MSA program (Map/Mafft/Muscle/Clustal/Tcoffee/Prank/...)"
    print "    -v: verbose (default=0/1)"
    print


def main():
    """
    This program shortens the headers of consensus obtained with REPET tools.
    Specific formatting for consensus from the TEdenovo pipeline.
    """

    project = ""
    smplAlign = ""
    clustHsp = ""
    multAlign = ""
    inFileName = ""
    outFileName = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hp:s:c:m:i:o:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-p":
            project = a
        elif o == "-s":
            smplAlign = a
        elif o == "-c":
            clustHsp = a
        elif o == "-m":
            multAlign = a
        elif o == "-i":
            inFileName = a
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file name"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    if outFileName == "":
        outFileName = "%s.shortH" % ( inFileName )

    outFile = open( outFileName, "w" )
    inFile = open( inFileName, "r" )
    lines = inFile.readlines()

    countSeq = 0

    for line in lines:
        if ">" in line:
            countSeq += 1
            data = line.split()
            cons_name = data[0].split("=")[1]
            cons_lgth = data[1].split("=")[1]
            cons_nbAlign = data[2].split("=")[1]
            if project != "":
                cluster_id = cons_name.split("Cluster")[1]
                cluster_id = cluster_id.split(".fa")[0]
                header = cluster_id + "_" + cons_nbAlign
                outFile.write( ">%s_%s_%s_%s_%s_%s\n" % ( project, smplAlign, clustHsp, cluster_id, multAlign, cons_nbAlign ) )
            else:
                outFile.write( ">%s_nbAlign%s\n" % ( cons_name, cons_nbAlign ) )
        else:
            seq = line.split("\n")
            outFile.write(seq[0]+"\n")

    inFile.close()
    outFile.close()

    if verbose > 0:
        print "nb of consensus: %i" % ( countSeq )

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
