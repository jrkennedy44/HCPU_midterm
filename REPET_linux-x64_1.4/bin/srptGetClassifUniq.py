#!/usr/bin/env python

## @file
# usage: srptGetClassifUniq.py [ options ]
# options:
#      -h: this help
#      -p: project name
#      -v: verbosity level (default=0/1/2)

import os
import sys
import getopt
from pyRepetUnit.commons.seq.BioseqDB import BioseqDB

"""
Parse the 'classif' file with all the consensus before removing the redundancy and keep only the lines of the non-redundant consensus.
"""

def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -p: project name"
    print "     -v: verbosity level (default=0/1/2)"
    print
    
    
def main():
    projectName = ""
    verbose = 0
    
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hp:v:" )
    except getopt.GetoptError, err:
        msg = str(err)
        sys.stderr.write( "%s\n" % ( msg ) )
        help(); sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help(); sys.exit(0)
        elif o == "-p":
            projectName = a
        elif o == "-v":
            verbose = int(a)
            
    if projectName == "":
        msg = "ERROR: missing project name (-p)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
    
    inClassifFileName = "%s_TEclassifier.classif" % ( projectName )
    inFastaFileName = "%s_uniq_TEclassifier.fa" % ( projectName )
    outClassifFileName = "%s_uniq_TEclassifier.classif" % ( projectName )
        
    if verbose > 0:
        msg = "START %s" % ( sys.argv[0].split("/")[-1] )
        msg += "\ninput classification file: %s" % ( inClassifFileName )
        msg += "\ninput fasta file: %s" % ( inFastaFileName )
        msg += "\noutput file: %s" % ( outClassifFileName )
        sys.stdout.write( "%s\n" % ( msg ) )
        sys.stdout.flush()
        
    uniqDB = BioseqDB( inFastaFileName )

    inClassifFile = open( inClassifFileName, "r" )
    dName2Classif = {}
    line = inClassifFile.readline()
    while True:
        if line == "":
            break
        data = line.split("\t")
        name = data[0]   # the TE classifier should be usable on any fasta file, not only consensus from TEdenovo
        if not dName2Classif.has_key( name ):
            dName2Classif[ name ] = line
        else:
            print "*ERROR: two consensus have the same name"
            sys.exit(1)
        line = inClassifFile.readline()
    inClassifFile.close()

    if os.path.exists( outClassifFileName ):
        os.remove( outClassifFileName )
    outClassifFile = open( outClassifFileName, "w" )
    for bs in uniqDB.db:
        name = bs.header.split("|")[0].split("name=")[1]
        outClassifFile.write( dName2Classif[ name ] )
    outClassifFile.close()
    
    if verbose > 0:
        msg = "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.write( "%s\n" % ( msg ) )
        sys.stdout.flush()
        
    return 0

if __name__ == '__main__':
    main()