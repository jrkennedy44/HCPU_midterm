#!/usr/bin/env python

import os
import sys
import getopt


def help():
    """
    Give the list of the command-line options.
    """
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='fasta')"
    print "     -c: sequences correspond to consensus from TEdenovo"
    print "     -p: project name"
    print "     -s: field separator (default='_', seqName_classif)"
    print "     -o: name of the output file (default=inFileName+'.shortH')"
    print "     -v: verbose (default=0/1)"
    print


def main():
    """
    This program shortens the headers in a fasta file recording classified sequences after the TEclassifier.
    """
    inFileName = ""
    denovoConsensus = False
    projectName = ""
    sep = "_"
    outFileName = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:cp:s:o:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-c":
            denovoConsensus = True
        elif o == "-p":
            projectName = a
        elif o == "-s":
            sep = a
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file name"
        help()
        sys.exit(1)
        
    if projectName == "":
        print "ERROR: missing project name"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    inFile = open( inFileName, "r" )
    line = inFile.readline()

    if outFileName == "":
        outFileName = "%s.shortH" % ( inFileName )
    outFile = open( outFileName, "w" )

    while True:

        if line == "":
            break

        if line[0] == ">":
            data = line[1:-1].split( "|" )
            if verbose > 0: print data; sys.stdout.flush()
            name = line[:-1].split("name=")[1].split("|")[0]
            category = line[:-1].split("category=")[1].split("|")[0]
            order = line[:-1].split("order=")[1].split("|")[0]
            completeness = line[:-1].split("completeness=")[1].split("|")[0]
            confusedness = line[:-1].split("confusedness=")[1].split("|")[0]

            if denovoConsensus == True:
                desc = name.split(projectName)[1]
                palignMeth = desc.split("_")[1]
                clustMeth = desc.split("_")[2]
                clustID = desc.split("_")[3]
                malignMeth = desc.split("_")[4]
                malignNb = desc.split("_")[5]
                name = "%s-%s-%s%s-%s%s" % ( projectName, palignMeth[0], clustMeth[0], clustID, malignMeth, malignNb )

            newHeader = "%s" % ( name )
            if category == "NoCat":
                newHeader += "%s%s" % ( sep, "NoCat" )
            elif confusedness == "yes":
                newHeader += "%s%s" % ( sep, "confused" )
            elif category == "SSR":
                newHeader += "%s%s" % ( sep, "SSR" )
            elif category == "HostGene":
                newHeader += "%s%s" % ( sep, "HostGene" )
            else:
                newHeader += "%s%s-%s" % ( sep, category, order )
                if completeness == "comp":
                    newHeader += "-comp"
                else:
                    newHeader += "-incomp"
            outFile.write( ">%s\n" % ( newHeader ) )

        else:
            outFile.write( line )

        line = inFile.readline()

    inFile.close()
    outFile.close()

    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
