#!/usr/bin/env python

"""
Interface to orient sequences before making a multiple alignment.
Use hashing or suffix tree to get an idea of the appropriate strand.
Use 'orienter' by default, otherwise use 'mummer'.
"""

import sys
import os
import glob
import getopt

from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
import pyRepet.seq.fastaDB
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils


class OrientSequences( object ):
    """
    Interface to orient sequences before making a multiple alignment.
    Use hashing or suffix tree to get an idea of the appropriate strand.
    Use 'orienter' by default, otherwise use 'mummer'.
    """
    
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inFileName = ""
        self._minMatchLength = 10
        self._prgToOrient = "orienter"
        self._outFileName = ""
        self._clean = False
        self._verbose = 1
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage:",sys.argv[0].split("/")[-1],"[options]"
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file (format='fasta')"
        print "     -m: minimum match length (default=10)"
        print "     -p: program to use first (default=orienter/mummer)"
        print "     -o: name of the output file (default=inFileName+'.oriented')"
        print "     -c: clean"
        print "     -v: verbosity level (0/default=1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:m:p:o:cv:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputFileName( a )
            elif o == "-m":
                self.setMinMatchLength( a )
            elif o == "-p":
                self.setPrgToOrient( a )
            elif o == "-o":
                self.setOutputFileName( a )
            elif o == "-c":
                self.setClean()
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setInputFileName( self, inFileName ):
        self._inFileName = inFileName
        
    def setMinMatchLength( self, minMatchLength ):
        self._minMatchLength = int(minMatchLength)
        
    def setPrgToOrient( self, prgToOrient ):
        self._prgToOrient = prgToOrient
        
    def setOutputFileName( self, outFileName ):
        self._outFileName = outFileName
        
    def setClean( self ):
        self._clean = True
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
        
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._inFileName == "":
            print "ERROR: missing input file name"
            self.help(); sys.exit(1)
        if not os.path.exists( self._inFileName ):
            print "ERROR: input file '%s' doesn't exist" % ( self._inFileName )
            self.help(); sys.exit(1)
        if self._prgToOrient not in [ "orienter", "mummer" ]:
            print "ERROR: unknown program '%s'" % ( self._prgToOrient )
            self.help(); sys.exit(1)
        if self._outFileName == "":
            self._outFileName = "%s.oriented" % ( self._inFileName )
            
            
    def useOrienter( self ):
        """
        Use 'orienter'.
        @return: exit value of 'orienter'
        """
        prg = "orienter"
        cmd = prg
        cmd += " -k"
        cmd += " -v %i" % ( self._verbose )
        cmd += " %s" % ( self._inFileName )
        log = os.system( cmd )
        if log == 0 and self._outFileName.split(".")[-1] != "oriented":
            os.rename( self._inFileName + ".oriented", self._outFileName )
        return log
    
    
    def compareInputSequencesWithMummer( self, nbInSeq ):
        """
        Launch MUmmer on two single-sequence fasta files to find all maximal matches regardless of their uniqueness and record stdout.
        Only N(N-1)/2 comparisons are made.
        @param nbInSeq: number of input sequences
        @type nbInSeq: integer
        """
        if self._verbose > 0:
            print "aligning input sequences..."
            sys.stdout.flush()
        if not CheckerUtils.isExecutableInUserPath( "mummer" ):
            msg = "ERROR: 'mummer' is not in your PATH"
            sys.stderr.write( "%s\n" % ( msg ) )
            sys.exit(1)
        lInFiles = glob.glob( "batch_*.fa" )
        for i in range( 1, nbInSeq+1 ):
            for j in range( i+1, nbInSeq+1 ):
                if self._verbose > 1:
                    print "launch MUmmer on %i versus %i" % ( i, j )
                    sys.stdout.flush()
                prg = "mummer"
                cmd = prg
                cmd += " -maxmatch"
                cmd += " -l %i" % ( self._minMatchLength )
                cmd += " -b"
                cmd += " -F"
                cmd += " batch_%s.fa" % ( str(j).zfill( len( str( len(lInFiles) ) ) ) )
                cmd += " batch_%s.fa" % ( str(i).zfill( len( str( len(lInFiles) ) ) ) )
                cmd += " > mummer_%i_vs_%i.txt" % ( i, j )
                if self._verbose < 3:
                    cmd += " 2> /dev/null"
                returnStatus = os.system( cmd )
                if returnStatus != 0:
                    msg = "ERROR: '%s' returned '%i'" % ( prg, returnStatus )
                    sys.stderr.write( "%s\n" % ( msg ) )
                    sys.exit(1)
                    
                    
    def parseMummerOutput( self, mummerFileName, nameSeq1, nameSeq2 ):
        """
        Parse the output from MUmmer.
        @param mummerFileName: file with the output from MUmmer
        @type mummerFileName: string
        @param nameSeq1: name of the first sequence in the pairwise comparison
        @type nameSeq1: string
        @param nameSeq2: name of the first sequence in the pairwise comparison
        @type nameSeq2: string
        @return: dictionary whose keys are strands and values the number of maximal matches
        """
        if self._verbose > 1:
            print "parse '%s'" % ( mummerFileName )
            sys.stdout.flush()
        dStrand2NbMatches = {}
        mummerF = open( mummerFileName, "r" )
        strand = "direct"
        nbMatches = 0
        line = mummerF.readline()
        while True:
            if line == "":
                break
            if line[0] == ">":
                if nameSeq1 not in line:
                    print "ERROR"
                    print nameSeq1
                    print nameSeq2
                    sys.exit(1)
                if "Reverse" in line:
                    dStrand2NbMatches[ strand ] = nbMatches
                    strand = "reverse"
                    nbMatches = 0
            else:
                nbMatches += 1
            line = mummerF.readline()
        dStrand2NbMatches[ strand ] = nbMatches
        mummerF.close()
        if self._verbose > 1:
            print " direct: %i maximal matches" % ( dStrand2NbMatches["direct"] )
            print " reverse: %i maximal matches" % ( dStrand2NbMatches["reverse"] )
            sys.stdout.flush()
        return dStrand2NbMatches
    
    
    def getCumulativeMatchLengthsOnBothStrandForEachPairwiseComparison( self, lInHeaders, nbInSeq ):
        """
        For each pairwise comparison, retrieve the number of matches on both strand.
        @param lInHeaders: list of the sequence headers
        @type lInHeaders: list of strings
        @param nbInSeq: number of input sequences
        @type nbInSeq: integer
        @return: dictionary whose keys are pairwise comparisons and values are number of matches on both strands
        """
        dMatrix = {}
        for i in range( 1, nbInSeq+1 ):
            for j in range( i+1, nbInSeq+1 ):
                pairComp = "%i_vs_%i" % ( i, j )
                dStrand2NbMatches = self.parseMummerOutput( "mummer_%s.txt" % ( pairComp ), lInHeaders[i-1], lInHeaders[j-1] )
                dMatrix[ pairComp ] = dStrand2NbMatches
        return dMatrix
    
    
    def showResultsAsOrienter( self, nbInSeq, dMatrix ):
        """
        Not used for the moment but can be useful...
        """
        for i in range( 1, nbInSeq+1 ):
            for j in range( i+1, nbInSeq+1 ):
                pairComp = "%i_vs_%i" % ( i, j )
                string = "aligning %i with %i" % ( i, j )
                string += " %i %i" % ( dMatrix[pairComp]["direct"], dMatrix[pairComp]["reverse"] )
                string += " max=%i" % ( max( dMatrix[pairComp]["direct"], dMatrix[pairComp]["reverse"] ) )
                if dMatrix[pairComp]["reverse"] > dMatrix[pairComp]["direct"]:
                    string += " strand=-"
                    string += " nb=%i" % ( dMatrix[pairComp]["reverse"] )
                else:
                    string += " strand=+"
                    string += " nb=%i" % ( dMatrix[pairComp]["direct"] )
                print string; sys.stdout.flush()
                
                
    def getSequencesToReverseFromMatrix( self, dMatrix, lNewHeaders ):
        """
        Retrieve the sequences than need to be re-oriented.
        @param dMatrix: 
        @type dMatrix: 
        @param lInHeaders: list of the new sequence headers
        @type lInHeaders: list of strings
        @return: list of headers corresponding to sequences than need to be re-oriented
        """
        lSeqToOrient = []
        
        for i in range( 1, len(lNewHeaders)+1 ):
            for j in range( i+1, len(lNewHeaders)+1 ):
                comp = "%i_vs_%i" % ( i, j )
                nbDirectMatches = dMatrix[ comp ][ "direct" ]
                nbReverseMatches = dMatrix[ comp ][ "reverse" ]
                if self._verbose > 1:
                    print "%s: direct=%i reverse=%i" % ( comp, nbDirectMatches, nbReverseMatches )
                if nbReverseMatches > nbDirectMatches and lNewHeaders[i-1] not in lSeqToOrient:
                    if lNewHeaders[ j-1 ] not in lSeqToOrient:
                        if self._verbose > 2:
                            "need to reverse '%s'" % ( lNewHeaders[j-1] )
                        lSeqToOrient.append( lNewHeaders[ j-1 ] )
                        
        return lSeqToOrient
    
    
    def getSequencesToReverse( self ):
        """
        Return a list with the headers of the sequences to reverse. 
        """
        lSequenceHeadersToReverse = []
        
        if self._prgToOrient == "orienter":
            exitStatus = self.useOrienter()
            if exitStatus == 0:
                self.end()
                #TODO: add sys.exit(0) ?
            if exitStatus != 0:
                print "\nWARNING: 'orienter' had a problem, switch to 'mummer'"
                sys.stdout.flush()
                
        lInHeaders = pyRepet.seq.fastaDB.dbHeaders( self._inFileName )
        nbInSeq = len( lInHeaders )
        if self._verbose > 0:
            print "nb of input sequences: %i" % ( nbInSeq )
            sys.stdout.flush()
            
        pyRepet.seq.fastaDB.shortenSeqHeaders( self._inFileName, 1 )
        tmpFileName = "%s.shortH" % ( self._inFileName )
        lNewHeaders = pyRepet.seq.fastaDB.dbHeaders( tmpFileName )
        dNew2Init = pyRepet.seq.fastaDB.retrieveLinksNewInitialHeaders( "%slink" % ( tmpFileName ) )
        
        pyRepet.seq.fastaDB.dbSplit( tmpFileName, nbSeqPerBatch=1, newDir=True )
        os.chdir( "batches" )
        self.compareInputSequencesWithMummer( nbInSeq )
        dMatrix = self.getCumulativeMatchLengthsOnBothStrandForEachPairwiseComparison( lNewHeaders, nbInSeq )
        os.chdir( ".." )
        
        lNewHeadersToReverse = self.getSequencesToReverseFromMatrix( dMatrix, lNewHeaders )
        for newH in lNewHeadersToReverse:
            lSequenceHeadersToReverse.append( dNew2Init[ newH ] )
        if self._verbose > 0:
            print "nb of sequences to reverse: %i" % ( len(lNewHeadersToReverse) )
            for initH in lSequenceHeadersToReverse: print " %s" % ( initH )
            sys.stdout.flush()
            
        if self._clean:
            os.remove( tmpFileName )
            os.remove( "%slink" % ( tmpFileName ) )
            
        return lSequenceHeadersToReverse
    
    
    def orientInputSequences( self, lSequenceHeadersToReverse, tmpFileName="" ):
        """
        Save input sequences while re-orienting those needing it.
        @param lSequenceHeadersToReverse: list of headers corresponding to sequences than need to be re-oriented
        @type lSequenceHeadersToReverse: list of strings
        @param tmpFileName: name of a fasta file (inFileName by default)
        @type tmpFileName: string
        """
        if self._verbose > 0:
            print "saving oriented sequences..."
            sys.stdout.flush()
        if tmpFileName == "":
            tmpFileName = self._inFileName
        inDB = BioseqDB( tmpFileName )
        outDB = BioseqDB()
        for bs in inDB.db:
            if bs.header in lSequenceHeadersToReverse:
                bs.reverseComplement()
                bs.header += " re-oriented"
            outDB.add( bs )
        outDB.save( self._outFileName )
        
        
    def clean( self ):
        if os.path.exists( "batches" ):
            os.system( "rm -rf batches" )
        if os.path.exists( "orienter_error.log" ):
            os.remove( "orienter_error.log" )
        for f in glob.glob( "core.*" ):
            os.remove( f )
            
            
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ )
            print "input file: %s" % ( self._inFileName )
            sys.stdout.flush()
            
            
    def end( self ):
        """
        Useful commands before ending the program.
        """
        if self._clean:
            self.clean()
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ )
            sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        lSequenceHeadersToReverse = self.getSequencesToReverse()
        
        self.orientInputSequences( lSequenceHeadersToReverse )
        
        self.end()
        
        
if __name__ == "__main__":
    i = OrientSequences()
    i.setAttributesFromCmdLine()
    i.run()
