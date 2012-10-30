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
    print "     -i: name of the input file (format='classif')"
    print "     -o: name of the output file (default=inFileName+'_stats.txt')"
    print "     -v: verbose (default=0/1)"
    print
    
    
def main():
    """
    Give a summary from a 'classif' file, output of the TEclassifier.
    """
    inFileName = ""
    outFileName = ""
    verbose = 0
    
    try:
        opts, args = getopt.getopt( sys.argv[1:],"hi:o:v:" )
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
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "ERROR: missing input file"
        help()
        sys.exit(1)

    if verbose > 0:
        print "START %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()
        
        
    dClassif2count = {}
    total = 0

    inFile = open( inFileName, "r" )
    line = inFile.readline()

    while True:
        if line == "":
            break
        total += 1
        data = line.split( "\t" )
        seqname = data[0]
        seqlength = data[1]
        strand = data[2]
        confusedness = data[3]
        category = data[4].replace(" ","")
        order = data[5]
        if len(data) == 8:
            completeness = data[6]
            comments=data[7]
        else:
            superfam = data[6]
            completeness = data[7]
            comments=data[8]

        if confusedness == "confused":
            if dClassif2count.has_key( "confused" ):
                dClassif2count[ "confused" ] += 1
            else:
                dClassif2count[ "confused" ] = 1
            if category == "?":
                if dClassif2count.has_key( "confused_?_?" ):
                    dClassif2count[ "confused_?_?" ] += 1
                else:
                    dClassif2count[ "confused_?_?" ] = 1
            else:
                if order == "?":
                    if dClassif2count.has_key( "confused_OK_?" ):
                        dClassif2count[ "confused_OK_?" ] += 1
                    else:
                        dClassif2count[ "confused_OK_?" ] = 1
                else:
                    if "length=" in comments:
                        if dClassif2count.has_key( "confused_length" ):
                            dClassif2count[ "confused_length" ] += 1
                        else:
                            dClassif2count[ "confused_length" ] = 1

        else:
            if category in [ "SSR", "HostGene", "NoCat" ]:
                if dClassif2count.has_key( category ):
                    dClassif2count[ category ] += 1
                else:
                    dClassif2count[ category ] = 1
                if category == "NoCat":
                    if "profiles=" in comments and "match=" in comments:
                        if dClassif2count.has_key( "NoCat_profiles-matches" ):
                            dClassif2count[ "NoCat_profiles-matches" ] += 1
                        else:
                            dClassif2count[ "NoCat_profiles-matches" ] = 1
                    else:
                        if "profiles=" in comments and "match=" not in comments:
                            if dClassif2count.has_key( "NoCat_profiles" ):
                                dClassif2count[ "NoCat_profiles" ] += 1
                            else:
                                dClassif2count[ "NoCat_profiles" ] = 1
                        else:
                            if "profiles=" not in comments and "match=" in comments:
                                if dClassif2count.has_key( "NoCat_matches" ):
                                    dClassif2count[ "NoCat_matches" ] += 1
                                else:
                                    dClassif2count[ "NoCat_matches" ] = 1
                            else:
                                if "profiles=" not in comments and "match=" not in comments:
                                    if dClassif2count.has_key( "NoCat_nothing" ):
                                        dClassif2count[ "NoCat_nothing" ] += 1
                                    else:
                                        dClassif2count[ "NoCat_nothing" ] = 1
                                        
            elif category in [ "classI", "classII" ]:
                if order not in [ "Helitron", "Polinton", "LARD", "SINE", "MITE" ]:
                    if dClassif2count.has_key( "%s_%s_%s" % ( category, order, completeness ) ):
                        dClassif2count[ "%s_%s_%s" % ( category, order, completeness ) ] += 1
                    else:
                        dClassif2count[ "%s_%s_%s" % ( category, order, completeness ) ] = 1
                    if completeness == "incomp":
                        if "struct" in comments:
                            if dClassif2count.has_key( "%s_%s_%s_struct" % ( category, order, completeness ) ):
                                dClassif2count[ "%s_%s_%s_struct" % ( category, order, completeness ) ] += 1
                            else:
                                dClassif2count[ "%s_%s_%s_struct" % ( category, order, completeness ) ] = 1
                        elif "match" in comments and ("TE_BLRtx" in comments or "TE_BLRx" in comments):
                            if dClassif2count.has_key( "%s_%s_%s_coding" % ( category, order, completeness ) ):
                                dClassif2count[ "%s_%s_%s_coding" % ( category, order, completeness ) ] += 1
                            else:
                                dClassif2count[ "%s_%s_%s_coding" % ( category, order, completeness ) ] = 1
                else:
                    if dClassif2count.has_key( "%s_%s" % ( category, order ) ):
                        dClassif2count[ "%s_%s" % ( category, order ) ] += 1
                    else:
                        dClassif2count[ "%s_%s" % ( category, order ) ] = 1

        line = inFile.readline()

    inFile.close()


    if outFileName == "":
        outFileName = "%s_stats.txt" % ( inFileName )
    outFile = open( outFileName, "w" )

    lClassif = [ "classI_LTR_comp", "classI_LTR_incomp", "classI_LTR_incomp_struct", "classI_LTR_incomp_coding", "classI_LARD",
                 "classI_LINE_comp", "classI_LINE_incomp", "classI_LINE_incomp_struct", "classI_LINE_incomp_coding", "classI_SINE",
                 "classII_TIR_comp", "classII_TIR_incomp", "classII_TIR_incomp_struct", "classII_TIR_incomp_coding", "classII_MITE",
                 "classII_Helitron", "classII_Polinton" , "SSR", "HostGene",
                 "NoCat", "NoCat_profiles-matches", "NoCat_profiles", "NoCat_matches", "NoCat_nothing",
                 "confused", "confused_length" ]

    for classif in lClassif:
        if dClassif2count.has_key( classif ):
            string = "%s: %i (%.2f%%)" % ( classif, dClassif2count[ classif ], 100 * dClassif2count[ classif ] / float(total) )
            outFile.write( "%s\n" % ( string ) )
            if verbose > 0:
                print string
        else:
            string = "%s: %i (%.2f%%)" % ( classif, 0, 0.0 )
            outFile.write( "%s\n" % ( string ) )
            if verbose > 0:
                print string

    string = "TOTAL: %i (%.2f%%)" % ( total, 100*total/float(total) )
    outFile.write( "%s\n" % ( string ) )
    if verbose > 0:
        print string


    if verbose > 0:
        print "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    main()
