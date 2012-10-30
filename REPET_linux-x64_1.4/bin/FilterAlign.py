#!/usr/bin/env python

import sys
import getopt
import os


def help():
    print
    print "usage: ",sys.argv[0].split("/")[-1],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='align')"
    print "     -E: maximum E-value (default=100)"
    print "     -S: minimum score (default=0)"
    print "     -I: minimum identity (default=0)"
    print "     -l: minimum length (default=0)"
    print "     -L: maximum length (default=1000000000)"
    print "     -o: name of the output file (default=inFileName+'.filtered')"
    print "     -v: verbose (default=0/1)"
    print
    
    
def main():
    """
    This program filters the output from BLASTER ('align' file recording HSPs).
    """
    
    inFileName = ""
    outFileName = ""
    maxEValue = 100
    minIdentity = 0
    minLength = 0
    maxLength = 1000000000
    minScore = 0
    verbose = 0
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:E:S:I:l:L:o:v:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit()
        elif o == "-i":
            inFileName = a
        elif o == "-E":
            maxEValue = float(a)
        elif o == "-S":
            minScore = int(float(a))
        elif o == "-I":
            minIdentity = int(float(a))
        elif o == "-l":
            minLength = int(a)
        elif o == "-L":
            maxLength = int(a)
        elif o == "-o":
            outFileName = a
        elif o == "-v":
            verbose = int(a)
            
    if inFileName == "":
        print "ERROR: missing input file name"
        help()
        sys.exit(1)
        
    if outFileName == "":
        outFileName = "%s.filtered" % ( inFileName )
        
    if os.path.exists( os.environ["REPET_PATH"] + "/bin/filterAlign" ):
        prg = os.environ["REPET_PATH"] + "/bin/filterAlign"
        cmd = prg
        cmd += " -i %s" % ( inFileName )
        cmd += " -E %g" % ( maxEValue )
        cmd += " -S %i" % ( minScore )
        cmd += " -I %f" % ( minIdentity )
        cmd += " -l %i" % ( minLength )
        cmd += " -L %i" % ( maxLength )
        cmd += " -o %s" % ( outFileName )
        cmd += " -v %i" % ( verbose )
        return os.system( cmd )
    
    if verbose > 0:
        print "START %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    inFile = open( inFileName, "r" )
    outFile = open( outFileName, "w" )
    
    nbMatches = 0
    nbFiltered = 0
    
    line = inFile.readline()
    while True:
        if line == "":
            break
        nbMatches += 1
        data = line.split("\t")
        qryName = data[0]
        qryStart = data[1]
        qryEnd = data[2]
        sbjName = data[3]
        sbjStart = data[4]
        sbjEnd = data[5]
        Evalue = data[6]
        score = data[7]
        identity = data[8]
        
        if int(qryStart) < int(qryEnd):
            matchLength = int(qryEnd) - int(qryStart) + 1
        elif int(qryStart) > int(qryEnd):
            matchLength = int(qryStart) - int(qryEnd) + 1

        if float(Evalue) <= maxEValue and matchLength >= minLength and \
               float(identity) >= minIdentity and matchLength <= maxLength and \
               int(score) >= minScore:
            string = qryName + "\t" + qryStart + "\t" + qryEnd + "\t" +\
                     sbjName + "\t" + sbjStart + "\t" + sbjEnd + "\t" +\
                     Evalue + "\t" + score + "\t" + identity
            outFile.write( string )
        else:
            nbFiltered += 1
            string = "qry %s (%s-%s) vs subj %s (%s-%s): Eval=%s identity=%s matchLength=%s score=%s" %\
            ( qryName, qryStart, qryEnd, sbjName, sbjStart, sbjEnd, Evalue, identity.split("\n")[0], matchLength, score )
            if verbose > 1:
                print string; sys.stdout.flush()
                
        line = inFile.readline()
        
    inFile.close()
    outFile.close()
    
    if verbose > 0:
        msg = "total number of matches: %i" % ( nbMatches )
        msg += "\nnumber of filtered matches: %i" % ( nbFiltered )
        print msg; sys.stdout.flush()
        
    if verbose > 0:
        print "END %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()
        
    return 0


if __name__ == "__main__":
    main()
