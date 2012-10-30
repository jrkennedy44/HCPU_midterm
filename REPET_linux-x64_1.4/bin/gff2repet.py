#!/usr/bin/env python

import os
import sys
import getopt


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='GFF')"
    print "     -q: name of the query (otherwise, use seqID)"
    print "     -r: pattern(s) of feature(s) to retrieve (e.g. 'gene+match')"
    print "     -e: pattern(s) of feature(s) to exclude (e.g. 'chromosome+scaffold')"
    print "     -a: add attribute(s) to the sequence name in the output file"
    print "         (Label/Note/Label+Note/Name/Target/...)"
    print "     -f: output format (default='set'/'path')"
    print "     -o: name of the output file (default=inFileName+'.'+outFormat)"
    print "     -v: verbose (default=0/1/2)"
    print
    
    
def getGff3ID( attributes ):
    """
    Get the unique ID in the field 'attributes'.
    """
    gff3ID = attributes.split("ID=")[1]
    if ";" in gff3ID:
        gff3ID = gff3ID.split(";")[0]
    return gff3ID


def getParentID( attributes ):
    """
    Get the parent ID in the field 'attributes'.
    """
    parentID = attributes.split("Parent=")[1]
    if ";" in parentID:
        parentID = parentID.split(";")[0]
    return parentID


def main():
    """
    This program converts a GFF3 file into a set/path file.
    """
    inFileName = ""
    queryName = ""
    lFeaturesRetrieve = []
    lFeaturesExclude = []
    lTags = []
    outFileName = ""
    outFormat = "set"
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hi:q:r:e:a:o:f:v:" )
    except getopt.GetoptError, err:
        sys.stderr.write( "%s\n" % str(err) )
        help()
        sys.exit(1)
    for o, a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-q":
            queryName = a
        elif o == "-r":
            lFeaturesRetrieve = a.split("+")
        elif o == "-e":
            lFeaturesExclude = a.split("+")
        elif o == "-a":
            lTags = a.split("+")
        elif o == "-o":
            outFileName = a
        elif o == "-f":
            outFormat = a
        elif o == "-v":
            verbose = int(a)
    if inFileName == "":
        msg = "ERROR: missing input file (-i)"
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)
    if not os.path.exists( inFileName ):
        msg = "ERROR: can't find file '%s'" % ( inFileName )
        sys.stderr.write( "%s\n" % msg )
        help()
        sys.exit(1)
        
    if verbose > 0:
        msg = "START %s" % (sys.argv[0].split("/")[-1])
        msg += "\ninput file: %s" % ( inFileName )
        if queryName != "":
            msg += "\nquery name: %s" % ( queryName )
        if lFeaturesRetrieve != []:
            msg += "\nfeatures to retrieve: %s" % ( lFeaturesRetrieve )
        if lFeaturesExclude != []:
            msg += "\nfeatures to exclude: %s" % ( lFeaturesExclude )
        sys.stdout.write( "%s\n" % msg )
        sys.stdout.flush()
        
    # start by retrieving the ID in the GFF3 and give the appropriate path for the output
    inFile = open( inFileName, "r" )
    dId2Path = {}
    countPath = 0
    lParents = []
    dId2Attributes = {}
    while True:
        line = inFile.readline()
        if line == "" or line == "##FASTA":
            break
        if line[0] != "#":
            if verbose > 1: print "\n",line[:-1]
            tokens = line.split("\t")
            attributes = tokens[8][:-1]
            gff3ID = getGff3ID( attributes )
            if verbose > 1: print "gff3ID=%s" % ( gff3ID )
            dId2Attributes[ gff3ID ] = attributes
            if "Parent=" in attributes:
                parentID = getParentID( attributes )
                if verbose > 1: print "parentID=%s" % ( parentID )
                if parentID not in lParents:
                    lParents.append( parentID )
                if not dId2Path.has_key( parentID ):
                    countPath += 1
                    dId2Path[ parentID ] = countPath
            else:
                if not dId2Path.has_key( gff3ID ):
                    countPath += 1
                    dId2Path[ gff3ID ] = countPath
    inFile.close()
    if verbose > 0:
        print "nb of distinct IDs: %i" % ( len(dId2Path.keys()) )
        
    # parse the input file again and save the results in the 'path' format (exclude the 'parents')
    if outFileName == "":
        outFileName = "%s.%s" % ( inFileName, outFormat )
    outFile = open( outFileName, "w" )
    inFile = open( inFileName, "r" )
    countID = 0
    
    while True:
        line = inFile.readline()
        if line == "" or line == "##FASTA":
            break
        if line[0] != "#":
            tokens = line.split("\t")
            seqid = tokens[0]
            source = tokens[1]
            featType = tokens[2]
            start = tokens[3]
            end = tokens[4]
            score = tokens[5]
            strand = tokens[6]
            phase = tokens[7]
            attributes = tokens[8][:-1]
            
            if (lFeaturesRetrieve == [] and featType not in lFeaturesExclude) or (lFeaturesRetrieve != [] and featType in lFeaturesRetrieve) or (lFeaturesExclude != [] and featType not in lFeaturesExclude):
                countID += 1
                
                if queryName != "":
                    qryName = queryName
                else:
                    qryName = seqid
                if strand == "+":
                    qryStart = start
                    qryEnd = end
                else:
                    qryStart = end
                    qryEnd = start
                    
                if ";" not in attributes:
                    sbjName = attributes.split("ID=")[1]
                else:
                    if "Name=" in attributes:
                        sbjName = attributes.split("Name=")[1]
                        if ";" in sbjName:
                            sbjName = sbjName.split(";")[0]
                    else:
                        sbjName = attributes.split("ID=")[1].split(";")[0]
                sbjName = sbjName.replace(":","").replace(" ","-").replace("{}","_").replace("{","").replace("}","").replace("|","")
                
                if len(lTags) != 0:
                    for tag in lTags:
                        if tag in attributes:
                            tagValue = attributes.split(tag+"=")[1].split(";")[0].replace(" ","-").replace("Transposable-Elements","TEs")[0:65]
                            sbjName += "_%s" % ( tagValue )
                        elif tag in dId2Attributes[getParentID(attributes)]:
                            tagValue = dId2Attributes[getParentID(attributes)].split(tag+"=")[1].split(";")[0].replace(" ","-").replace("Transposable-Elements","TEs")[0:65]
                            sbjName += "_%s" % ( tagValue )
                            
                sbjStart = "0"
                sbjEnd = "0"
                evalue = "0.0"
                idPct = "0.0"
                if score == ".":
                    score = "0"
                    
                if "Parent=" in attributes:
                    parentID = getParentID( attributes )
                    path = dId2Path[ parentID ]
                else:
                    gff3ID = getGff3ID( attributes )
                    path = dId2Path[ gff3ID ]
                    
                # save the match if it is a 'match_part' or if it is 'alone'
                if featType != "match_part" or (featType == "match_part" and "Parent=" in attributes or ( "Parent=" not in attributes and gff3ID not in lParents )):
                    if outFormat == "path":
                        string = "%i\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % ( path, qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, evalue, score, idPct )
                    elif outFormat == "set":
                        string = "%i\t%s\t%s\t%s\t%s\n" % ( path, sbjName, qryName, qryStart, qryEnd )
                    outFile.write( string )
                    
    inFile.close()
    outFile.close()
    
    if verbose > 0:
        print "nb of saved IDs: %i" % ( countID )
        
    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    return 0


if __name__ == "__main__":
    main()
