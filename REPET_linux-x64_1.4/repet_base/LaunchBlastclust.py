#!/usr/bin/env python

"""
Launch Blastclust on nucleotide sequences and return a fasta file.
"""

import os
import sys
import getopt

from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
from pyRepet.launcher.programLauncher import programLauncher
from pyRepet.seq.fastaDB import shortenSeqHeaders


class LaunchBlastclust( object ):
    """
    Launch Blastclust on nucleotide sequences and return a fasta file.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inFileName = ""
        self._identityThreshold = 95
        self._coverageThreshold = 0.9
        self._bothSeq = "T"
        self._filterUnclusteredSeq = False
        self._outFilePrefix = ""
        self._clean = False
        self._verbose = 0
        self._pL = programLauncher()
        self._tmpFileName = ""
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage:",sys.argv[0]," [ options ]"
        print "option:"
        print "    -h: this help"
        print "    -i: name of the input fasta file (nucleotides)"
        print "    -L: length coverage threshold (default=0.9)"
        print "    -S: identity coverage threshold (default=95)"
        print "    -b: require coverage on both neighbours (default=T/F)"
        print "    -f: filter unclustered sequences"
        print "    -o: prefix of the output files (default=inFileName)"
        print "    -c: clean temporary files"
        print "    -v: verbosity level (default=0/1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:L:S:b:fo:cv:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputFileName( a )
            elif o == "-L":
                self.setCoverageThreshold( a )
            elif o == "-S":
                self.setIdentityThreshold( a )
            elif o == "-b":
                self.setBothSequences( a )
            elif o == "-f":
                self.setFilterUnclusteredSequences()
            elif o == "-o":
                self.setOutputFilePrefix( a )
            elif o == "-c":
                self.setClean()
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setInputFileName( self , inFileName ):
        self._inFileName = inFileName
        
    def setCoverageThreshold( self, lengthThresh ):
        self._coverageThreshold = float(lengthThresh)
                
    def setIdentityThreshold( self, identityThresh ):
        self._identityThreshold = int(identityThresh)
        
    def setBothSequences( self, bothSeq ):
        self._bothSeq = bothSeq
        
    def setFilterUnclusteredSequences( self ):
        self._filterUnclusteredSeq = True
        
    def setOutputFilePrefix( self, outFilePrefix ):
        self._outFilePrefix = outFilePrefix
        
    def setClean( self ):
        self._clean = True
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
        
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._inFileName == "":
            print "ERROR: missing input file name (-i)"
            self.help(); sys.exit(1)
        if self._outFilePrefix == "":
            self._outFilePrefix = self._inFileName
        self._tmpFileName = "%s_blastclust.txt" % ( self._outFilePrefix )
        
        
    def launchBlastclust( self, inFile ):
        """
        Launch Blastclust in command-line.
        """
        if os.path.exists(os.path.basename(inFile)):
            inFile = os.path.basename(inFile)
        prg = "blastclust"
        cmd = prg
        cmd += " -i %s" % ( inFile )
        cmd += " -o %s" % ( self._tmpFileName )
        cmd += " -S %i" % ( self._identityThreshold )
        cmd += " -L %f" % ( self._coverageThreshold )
        cmd += " -b %s" % ( self._bothSeq )
        cmd += " -p F"
        if self._verbose > 0:
            print cmd; sys.stdout.flush()
        self._pL.launch( prg, cmd )
        if self._clean and os.path.exists("error.log"):
            os.remove( "error.log" )
            
            
    def getClustersFromTxtFile( self ):
        """
        Return a dictionary with cluster IDs as keys and sequence headers as values.
        """
        dClusterId2SeqHeaders = {}
        inF = open( self._tmpFileName, "r" )
        line = inF.readline()
        clusterId = 1
        while True:
            if line == "":
                break
            tokens = line[:-1].split(" ")
            dClusterId2SeqHeaders[ clusterId ] = []
            for seqHeader in tokens:
                if seqHeader != "":
                    dClusterId2SeqHeaders[ clusterId ].append( seqHeader )
            line = inF.readline()
            clusterId += 1
        inF.close()
        if self._verbose > 0:
            print "nb of clusters: %i" % ( len(dClusterId2SeqHeaders.keys()) )
            sys.stdout.flush()
        return dClusterId2SeqHeaders
    
    
    def filterUnclusteredSequences( self, dClusterId2SeqHeaders ):
        """
        Filter clusters having only one sequence.
        """
        for clusterId in dClusterId2SeqHeaders.keys():
            if len( dClusterId2SeqHeaders[ clusterId ] ) == 1:
                del dClusterId2SeqHeaders[ clusterId ]
        if self._verbose > 0:
            print "nb of clusters (>1seq): %i" % ( len(dClusterId2SeqHeaders.keys()) )
            sys.stdout.flush()
        return dClusterId2SeqHeaders
    
    
    def getClusteringResultsInFasta( self, inFile ):
        """
        Write a fasta file whose sequence headers contain the clustering IDs.
        """
        dClusterId2SeqHeaders = self.getClustersFromTxtFile()
        if self._filterUnclusteredSeq:
            dClusterId2SeqHeaders = self.filterUnclusteredSequences( dClusterId2SeqHeaders )
        inDB = BioseqDB( inFile )
        outFileName = "%s_blastclust.fa" % ( inFile )
        outF = open( outFileName, "w" )
        for clusterId in dClusterId2SeqHeaders.keys():
            memberId = 1
            for seqHeader in dClusterId2SeqHeaders[ clusterId ]:
                bs = inDB.fetch( seqHeader )
                bs.header = "BlastclustCluster%iMb%i_%s" % ( clusterId, memberId, seqHeader )
                bs.write( outF )
                memberId += 1
        outF.close()
        
        
    def getLinkInitNewHeaders( self ):
        dNew2Init = {}
        linkFileName = "%s.shortHlink" % ( self._inFileName )
        linkFile = open( linkFileName,"r" )
        line = linkFile.readline()
        while True:
            if line == "":
                break
            data = line.split("\t")
            dNew2Init[ data[0] ] = data[1]
            line = linkFile.readline()
        linkFile.close()
        return dNew2Init
    
    
    def retrieveInitHeaders( self, dNewH2InitH ):
        tmpTxtFileHandler = open( self._tmpFileName, "r" )
        outTxtFile = "%s_blastclust.txt" % ( self._outFilePrefix )
        outTxtFileHandler = open( outTxtFile, "w" )
        while True:
            line = tmpTxtFileHandler.readline()
            if line == "":
                break
            tokens = line[:-1].split(" ")
            string = ""
            for newHeader in tokens:
                if newHeader != "":
                    string += "%s " % ( dNewH2InitH[ newHeader ] )
            outTxtFileHandler.write( "%s\n" % ( string ) )
        tmpTxtFileHandler.close()
        outTxtFileHandler.close()
        os.remove( self._tmpFileName )
        
        tmpFaFile = "%s.shortH_blastclust.fa" % ( self._inFileName )
        tmpFaFileHandler = open( tmpFaFile, "r" )
        outFaFile = "%s_blastclust.fa" % ( self._outFilePrefix )
        outFaFileHandler = open( outFaFile, "w" )
        while True:
            line = tmpFaFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                tokens = line[1:-1].split("_")
                newHeader = "%s_%s" % ( tokens[0], dNewH2InitH[ tokens[1] ] )
                outFaFileHandler.write( ">%s\n" % ( newHeader ) )
            else:
                outFaFileHandler.write( line )
        tmpFaFileHandler.close()
        outFaFileHandler.close()
        os.remove( tmpFaFile )
        
        
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ )
            
            
    def end( self ):
        """
        Useful commands before ending the program.
        """
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ )
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        shortenSeqHeaders( self._inFileName, "2" )
        
        self.launchBlastclust( "%s.shortH" % ( self._inFileName ) )
        
        self.getClusteringResultsInFasta( "%s.shortH" % ( self._inFileName ) )
        
        dNewH2InitH = self.getLinkInitNewHeaders()
        self.retrieveInitHeaders( dNewH2InitH )
        
        os.remove( "%s.shortH" % ( self._inFileName ) )
        os.remove( "%s.shortHlink" % ( self._inFileName ) )
        
        self.end()
        
        
if __name__ == "__main__":
    i = LaunchBlastclust()
    i.setAttributesFromCmdLine()
    i.run()
