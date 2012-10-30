#!/usr/bin/env python

## @file
# usage: srptCollectResults.py [ options ]
# options:
#      -h: this help
#      -p: project name
#      -c: configuration file name
#      -v: verbosity level (default=0/1/2)


import sys
import os
import glob
import getopt
import ConfigParser
from ConfigParser import MissingSectionHeaderError
from pyRepetUnit.commons.coord.AlignUtils import AlignUtils
from pyRepet.util.Stat import Stat


def help():
    print
    print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
    print "options:"
    print "     -h: this help"
    print "     -p: project name"
    print "     -c: configuration file name"
    print "     -v: verbosity level (default=0/1/2)"
    print
    
    
def main():
    projectName = ""
    configFileName = ""
    verbose = 0
    thres = {}    
    
    try:
        opts, args = getopt.getopt( sys.argv[1:], "hp:c:v:" )
    except getopt.GetoptError, err:
        msg = str(err)
        sys.stderr.write( "%s\n" % ( msg ) )
        help(); sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help(); sys.exit(0)
        elif o == "-p":
            projectName = a
        elif o == "-c":
            configFileName = a  
        elif o == "-v":
            verbose = int(a)
        
    if projectName == "":
        msg = "ERROR: missing project name (-p)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
        
    if configFileName == "":
        msg = "ERROR: missing configuration file name (-c)"
        sys.stderr.write( "%s\n" % ( msg ) )
        help()
        sys.exit(1)
        
    if verbose > 0:
        msg = "START %s" % ( sys.argv[0].split("/")[-1] )
        msg += "\nproject name: %s" % ( projectName )
        msg += "\nconfiguration file name: %s" % ( configFileName )
        sys.stdout.write( "%s\n" % ( msg ) )
        sys.stdout.flush()
    
    config = ConfigParser.ConfigParser()
    try:
        config.readfp( open(configFileName) )
    except MissingSectionHeaderError:
        print "ERROR: your config file " + configFileName + " must begin with a section name"
        sys.exit(1)
        
    os.chdir( projectName + "_TEdetect_rnd")
    if verbose > 0:
        print "\n* retrieve for each program ran on the random chunks the highest score from all 'align' files"
        sys.stdout.flush()
    scoresFile = "maxScores.txt"
    scoresFileHandler = open(scoresFile, "w")
    scoresFileHandler.write("algo\tfile\tmaxScore\n")
    scoresFileHandler.flush()
    for alignProgram in ["BLR", "RM", "CEN"]:
        if not os.path.exists(alignProgram):
            if verbose > 0:
                print "WARNING: %s doesn't exist, did you run the previous step ?" % ( alignProgram )
                sys.stdout.flush()
        else:
            lFiles = glob.glob("%s/*.align" % (alignProgram))
            if verbose > 0:
                    print "parse %i files from %s..." % ( len(lFiles), alignProgram )
                    sys.stdout.flush()
            lFiles.sort()
            lHighestScores = []
            for fileName in lFiles:
                if verbose > 1:
                    print "file '%s'" % ( fileName )
                    sys.stdout.flush()
                lScores = AlignUtils.getScoreListFromFile( fileName )
                if verbose > 1:
                    print "nb of matches: %i" % ( len(lScores) )
                    sys.stdout.flush()
                if lScores != []:
                    lHighestScores.append(max(lScores))
                    scoresFileHandler.write("%s\t%s\t%i\n" % (alignProgram, os.path.basename(fileName), max(lScores)))
                else:
                    lHighestScores.append(0)
                    scoresFileHandler.write("%s\t%s\t0\n" % (alignProgram, os.path.basename(fileName)))
                del lScores
                scoresFileHandler.flush()
                
            iStat = Stat(lHighestScores)
            if verbose > 0:
                iStat.viewQuantiles()
            thres[alignProgram] = str(iStat.quantile(0.95))
            if thres[alignProgram] != "":
                if verbose > 0:
                    print "threshold %s: %s" % (alignProgram, thres[alignProgram])
                    sys.stdout.flush()
            else:
                thres[alignProgram] = configFileName.get("filter", alignProgram)
                if verbose > 0:
                    print "WARNING: no threshold found for %s. Default value is %s." % (alignProgram, thres[alignProgram])
                    sys.stdout.flush()
    scoresFileHandler.close() 
      
    thresFile = "threshold.tmp"
    thresFileHandler = open(thresFile, "w")
    for threshold in thres:
        thresFileHandler.write(threshold + "\t" + thres[threshold] + "\n")
    thresFileHandler.close()
    
    os.chdir("../")
        
    if verbose > 0:
        msg = "END %s" % ( sys.argv[0].split("/")[-1] )
        sys.stdout.write( "%s\n" % ( msg ) )
        sys.stdout.flush()
        
    return 0

if __name__ == "__main__":
    main()
