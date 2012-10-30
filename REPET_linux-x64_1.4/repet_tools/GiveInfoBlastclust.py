#!/usr/bin/env python

"""
Give some information about the clustering done by Blastclust.
"""

import os
import sys
import getopt
from pyRepetUnit.commons.LoggerFactory import LoggerFactory


class GiveInfoBlastclust( object ):
    """
    Give some information about the clustering done by Blastclust.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inFileName = ""
        self._format = ""
        self._verbose = 0
        self._logger = None
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage:",sys.argv[0]," [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file"
        print "     -f: format (blastclust/fasta)"
        print "     -v: verbosity level (default=0/1)"
        print
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:f:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputFileName( a )
            elif o == "-f":
                self.setFormat( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setInputFileName( self, inFileName  ):
        self._inFileName = inFileName
        
    def setFormat( self, format ):
        self._format = format
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if  self._inFileName == "":
            print "ERROR: missing input file name (-i)"
            self.help(); sys.exit(1)
        if not os.path.exists( self._inFileName ):
            print "ERROR: input file '%s' doesn't exist" % ( self._inFileName )
            self.help(); sys.exit(1)
        if self._format not in [ "blastclust", "fasta" ]:
            print "ERROR: format '%S' not recognized"
            self.help(); sys.exit(1)
            
    def parseBlastclustOutput( self ):
        """
        Parse the output file from Blastclust in its native format.
        """
        dClusterId2SeqHeaders = {}
        clusterID = 1
        inF = open( self._inFileName, "r" )
        line = inF.readline()
        while True:
            if line == "": break
            tokens = line[:-2].split(" ")
            dClusterId2SeqHeaders[ clusterID ] = tokens
            clusterID += 1
            line = inF.readline()
        inF.close()
        return dClusterId2SeqHeaders
    
    def parseBlastclustForRepetOutput( self ):
        """
        Parse the output file from Blastclust in the fasta format.
        See the program 'LaunchBlastclust.py'.
        """
        dClusterId2SeqHeaders = {}
        inF = open( self._inFileName, "r" )
        line = inF.readline()
        while True:
            if line == "": break
            if ">" not in line:
                line = inF.readline()
                continue
            lElements = line[:-1].split("_")
            clusterID = int(lElements[0].split("Cluster")[1].split("Mb")[0])
            seqName = "_".join(lElements[1:])
            if not dClusterId2SeqHeaders.has_key( clusterID ):
                dClusterId2SeqHeaders[ clusterID ] = []
            dClusterId2SeqHeaders[ clusterID ].append( seqName )
            line = inF.readline()
        inF.close()
        return dClusterId2SeqHeaders
    
    def giveInfoOnBlastclustResults( self, dClusterId2SeqHeaders ):
        """
        Give information on Blastclust results.
        """
        nbInputSequences = 0
        nbClustersWithSingleSeq = 0
        nbClustersWithAtLeastTwoSeq = 0
        nbSequencesIn2SeqClusters = 0
        for clusterID in dClusterId2SeqHeaders.keys():
            nbInputSequences += len( dClusterId2SeqHeaders[ clusterID ] )
            if len( dClusterId2SeqHeaders[ clusterID ] ) == 1:
                nbClustersWithSingleSeq += 1
            else:
                nbClustersWithAtLeastTwoSeq += 1
                nbSequencesIn2SeqClusters += len( dClusterId2SeqHeaders[ clusterID ] )
        string = "information on file '%s'" % ( self._inFileName )
        string +=  "\nnumber of sequences: %i" % ( nbInputSequences )
        string += "\nnumber of clusters: %i" % ( len(dClusterId2SeqHeaders.keys()) )
        string += "\nnumber of clusters with only one sequence: %i"  % ( nbClustersWithSingleSeq )
        string += "\nnumber of clusters with at least two sequences: %i (%i sequences)"  % ( nbClustersWithAtLeastTwoSeq, nbSequencesIn2SeqClusters )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ )
        logFileName = "%s_%s.log" % ( type(self).__name__, os.path.basename( self._inFileName ) )
        if os.path.exists( logFileName ): os.remove( logFileName )
        self._logger = LoggerFactory.createLogger( logFileName )
        self._logger.info( "START %s" % ( type(self).__name__ ) )
        
    def end( self ):
        """
        Useful commands before ending the program.
        """
        self._logger.info( "END %s" % ( type(self).__name__ ) )
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ )
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        if self._format == "blastclust":
            dClusterId2SeqHeaders = self.parseBlastclustOutput()
        elif self._format == "fasta":
            dClusterId2SeqHeaders = self.parseBlastclustForRepetOutput()
        self.giveInfoOnBlastclustResults( dClusterId2SeqHeaders )
        self.end()
        
        
if __name__ == '__main__':
    i = GiveInfoBlastclust()
    i.setAttributesFromCmdLine()
    i.run()
