#!/usr/bin/env python

##@file FilterClassifiedSequences.py


import sys
import os
import getopt
from pyRepetUnit.commons.seq.Bioseq import Bioseq


## Filter classified sequences (output data-bank from TEclassifier.py)
#
class FilterClassifiedSequences( object ):
    
    def __init__( self ):
        self._inFaFile = ""
        self._filterSSRs = False
        self._maxLengthToFilterSSRs = 0
        self._filterHostGenes = False
        self._filterConfused = False
        self._filterNoCat = "0"
        self._nbAlignSeqNoCat = 0
        self._classifFile = ""
        self._filterIncomplete = False
        self._outFaFile = ""
        self._verbose = 0
        
        
    def help( self ):
        print
        print "usage: FilterClassifiedSequences.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file (format='fasta')"
        print "     -S: filter the consensus classified as 'SSR'"
        print "     -s: length below which a SSR is filtered (e.g. 300, default=0 : all SSR are filtered)"
        print "     -g: filter the consensus classified as 'HostGene'"
        print "     -c: filter the consensus classified as 'confused'"
        print "     -N: filter the consensus classified as 'NoCat'"
        print "         '-N 1': filter all NoCat"
        print "         '-N 2': filter NoCat when formed from less than 'n' sequences (see option '-n')"
        print "         '-N 3': filter NoCat when having no TE feature at all"
        print "         '-N 23': filter NoCat when in cases 2 and/or 3"
        print "     -n: minimum number of sequences in the MSA from which the NoCat consensus has been built"
        print "     -C: name of the file with the detailed classification (format='classif')"
        print "     -u: filter the consensus classified as 'incomplete'"
        print "     -o: name of the output fasta file (default=inFileName+'.filtered')"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt( sys.argv[1:], "hi:Ss:gcN:n:C:uo:v:" )
        except getopt.GetoptError, err:
            print str(err)
            self.help()
            sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help()
                sys.exit(0)
            elif o == "-i":
                self._inFaFile = a
            elif o == "-S":
                self._filterSSRs = True
            elif o == "-s":
                self._maxLengthToFilterSSRs = int(a)
            elif o == "-g":
                self._filterHostGenes = True
            elif o == "-c":
                self._filterConfused = True
            elif o == "-N":
                self._filterNoCat = a
            elif o == "-n":
                self._nbAlignSeqNoCat = int(a)
            elif o == "-C":
                self._classifFile = a
            elif o == "-u":
                self._filterIncomplete = True
            elif o == "-o":
                self._outFaFile = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        if self._inFaFile == "":
            msg = "ERROR: missing input file (-i)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if not os.path.exists( self._inFaFile ):
            msg = "ERROR: can't find input file '%s'" % ( self._inFaFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if "2" in self._filterNoCat and self._nbAlignSeqNoCat <= 0:
            msg = "ERROR: missing nb aligned sequences for NoCat (-n)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if "3" in self._filterNoCat and self._classifFile == "":
            msg = "ERROR: missing 'classif' file (-C)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if "3" in self._filterNoCat and not os.path.exists( self._classifFile ):
            msg = "ERROR: can't find 'classif' file '%s'" % ( self._classifFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if self._outFaFile == "":
            self._outFaFile = "%s.filtered" % ( self._inFaFile )
            
            
    def getClassifPerHeaderOfUnclassifiedConsensus( self ):
        dHeader2Classif = {}
        classifF = open( self._classifFile, "r" )
        while True:
            line = classifF.readline()
            if line == "":
                break
            if "NoCat" in line:
                tokens = line[:-1].split("\t")
                dHeader2Classif[ tokens[0] ] = tokens[1:]
        classifF.close()
        return dHeader2Classif
    
    
    def filterClassifiedConsensus( self ):
        inFile = open( self._inFaFile, "r" )
        outFile = open( self._outFaFile, "w" )
        bs = Bioseq()
        nbInSeq = 0
        nbRmv = 0
        
        if self._classifFile != "":
            dHeader2Classif = self.getClassifPerHeaderOfUnclassifiedConsensus()
            
        while True:
            bs.read( inFile )
            if bs.header == None:
                break
            nbInSeq += 1
            if self._verbose > 1:
                print bs.header
                
            if self._filterSSRs and "SSR" in bs.header and ( self._maxLengthToFilterSSRs == 0 or bs.getLength() <= self._maxLengthToFilterSSRs ):
                nbRmv += 1
                if self._verbose > 1: print "filtered SSR !"
                
            elif self._filterHostGenes and "HostGene" in bs.header:
                nbRmv += 1
                if self._verbose > 1: print "filtered HostGene !"
                
            elif self._filterConfused and "confused" in bs.header and "confusedness=no" not in bs.header:
                nbRmv += 1
                if self._verbose > 1: print "filtered confused !"
                
            elif self._filterNoCat != "0" and "NoCat" in bs.header:
                keep = False
                if "2" in self._filterNoCat:
                    algoMSA = ""
                    for i in ["Map","MAP","Malign","Mafft","Prank","Clustalw","Muscle","Tcoffee"]:
                        if i in bs.header:
                            algoMSA = i
                    nbAlignSeq = int( bs.header.split(algoMSA+"_")[1].split("|")[0] )
                    if nbAlignSeq > self._nbAlignSeqNoCat:
                        keep = True
                if "3" in self._filterNoCat:
                    for header in dHeader2Classif.keys():
                        if header in bs.header:
                            if "no structural features" not in dHeader2Classif[header][6]:
                                keep = True
                if keep:
                    bs.write( outFile )
                else:
                    nbRmv += 1
                    if self._verbose > 1: print "filtered NoCat !"
                    
            elif self._filterIncomplete and "completeness=incomp" in bs.header:
                nbRmv += 1
                if self._verbose > 1: print "filtered incomplete !"
                
            else:
                bs.write( outFile )
                
        inFile.close()
        outFile.close()
        
        if self._verbose > 0:
            print "nb of input seq: %i" % ( nbInSeq )
            print "nb of filtered seq: %i" % ( nbRmv )
            sys.stdout.flush()
            
            
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            msg = "START FilterClassifiedSequences.py"
            sys.stdout.write( "%s\n" % ( msg ) )
            print "input file: %s" % ( self._inFaFile )
            print "output file: %s" % ( self._outFaFile )
            if self._filterSSRs:
                if self._maxLengthToFilterSSRs == 0:
                    print "filter SSRs"
                else:
                    print "filter SSRs (<%ibp)" % ( self._maxLengthToFilterSSRs )
            if self._filterHostGenes:
                print "filter host's genes"
            if self._filterNoCat != "0":
                print "filter NoCat"
            if self._filterConfused:
                print "filter confused"
            sys.stdout.flush()
            
            
    def end( self ):
        if self._verbose > 0:
            msg = "END FilterClassifiedSequences.py"
            sys.stdout.write( "%s\n" % ( msg ) )
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        
        self.filterClassifiedConsensus()
        
        self.end()
        
        
if __name__ == "__main__":
    i = FilterClassifiedSequences()
    i.setAttributesFromCmdLine()
    i.run()
