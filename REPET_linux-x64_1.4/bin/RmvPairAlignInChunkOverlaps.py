#!/usr/bin/env python

"""
Remove hits due to chunk overlaps.
"""

import os
import sys
import getopt
import exceptions
import copy
from pyRepetUnit.commons.coord.Align import *


class RmvPairAlignInChunkOverlaps( object ):
    """
    Remove hits due to chunk overlaps.
    """
    
    
    def __init__( self, inFileName="", chunkLength=200000, chunkOverlap=10000, margin=10, outFileName="", verbose=0 ):
        """
        Constructor.
        """
        self._inFileName = inFileName
        self._chunkLength = chunkLength
        self._chunkOverlap = chunkOverlap
        self._margin = margin
        self._outFileName = outFileName
        self._verbose = verbose

    def help( self ):
        """
        Display the help.
        """
        print
        print "usage: %s [ options ]" % ( sys.argv[0] )
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file (format='align')"
        print "     -l: chunk length (in bp)"
        print "     -o: chunk overlap (in bp)"
        print "     -m: margin to remove match included into a chunk overlap (default=10)"
        print "     -O: name of the output file (default=inFileName+'.not_over')"
        print "     -v: verbose (default=0/1)"
        print

    def setAttributesFromCmdLine( self ):
        """
        Set attributes from the command-line arguments.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"h:i:l:o:m:O:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputFileName( a )
            elif o == "-l":
                self.setChunkLength( a )
            elif o == "-o":
                self.setChunkOverlap( a )
            elif o == "-m":
                self.setMargin( a )
            elif o == "-O":
                self.setOutputFileName( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setInputFileName( self, inFileName ):
        self._inFileName = inFileName
        
    def setChunkLength( self, chunkLength ):
        self._chunkLength = int(chunkLength)
        
    def setChunkOverlap( self, chunkOverlap ):
        self._chunkOverlap = int(chunkOverlap)
        
    def setMargin( self, margin ):
        self._margin = int(margin)
        
    def setOutputFileName( self, outFileName ):
        self._outFileName = outFileName
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
    def checkAttributes( self ):
        """
        Before running, check the required attributes are properly filled.
        """
        if self._inFileName == "":
            print "ERROR: missing input file"; self.help(); sys.exit(1)
        if not os.path.exists(self._inFileName ):
            print "ERROR: input file '%s' doesn't exist"  %( self._inFileName )
        if self._outFileName == "":
            self._outFileName = "%s.not_over" % ( self._inFileName )
            
            
    def isPairAlignAChunkOverlap( self, a, chunkQuery, chunkSubject ):
        """
        Return True if the pairwise alignment exactly corresponds to a 2-chunk overlap, False otherwise.
        Take into account cases specific to BLASTER or PALS.
        """
        
        if a.range_query.isOnDirectStrand() != a.range_subject.isOnDirectStrand():
            if self._verbose > 1: print "on different strand"
            return False
        
        if chunkQuery == chunkSubject + 1:
            if self._verbose > 1: print "query > subject"
            if a.range_query.start == 1 and a.range_subject.end == self._chunkLength \
                   and ( a.range_query.getLength() == self._chunkOverlap \
                         or a.range_query.getLength() == self._chunkOverlap + 1 ) \
                         and ( a.range_subject.getLength() == self._chunkOverlap \
                               or a.range_subject.getLength() == self._chunkOverlap + 1 ):
                if self._verbose > 1: print "chunk overlap"
                return True
            
        elif chunkQuery == chunkSubject - 1:
            if self._verbose > 1: print "query < subject"
            if a.range_query.end == self._chunkLength and a.range_subject.start == 1 \
                   and ( a.range_query.getLength() == self._chunkOverlap \
                         or a.range_query.getLength() == self._chunkOverlap + 1 ) \
                         and ( a.range_subject.getLength() == self._chunkOverlap \
                               or a.range_subject.getLength() == self._chunkOverlap + 1 ):
                if self._verbose > 1: print "chunk overlap"
                return True
            
        if self._verbose > 1: print "not a chunk overlap"
        return False
    
    
    def isInInterval( self, coord, midpoint ):
        """
        Check if a given coordinate is inside the interval [midpoint-margin;midpoint+margin].
        """
        if coord >= midpoint - self._margin and coord <= midpoint + self._margin:
            return True
        return False
    
    
    def isPairAlignWithinAndDueToAChunkOverlap( self, a, chunkQuery, chunkSubject ):
        """
        Return True if the pairwise alignment lies within an overlap between two contiguous chunks and is due to it, False otherwise.
        """
        uniqLength = self._chunkLength - self._chunkOverlap
        
        if a.range_query.isOnDirectStrand() != a.range_subject.isOnDirectStrand():
            if self._verbose > 1: print "on different strand"
            return False
        
        if chunkQuery == chunkSubject + 1:
            if self._verbose > 1: print "query > subject"
            if a.range_query.getMin() >= 1 and a.range_query.getMax() <= self._chunkOverlap \
                   and a.range_subject.getMin() >= self._chunkLength - self._chunkOverlap + 1 \
                   and a.range_subject.getMax() <= self._chunkLength:
                if self._verbose > 1: print "included"
                if self.isInInterval( a.range_query.getMin(), a.range_subject.getMin() - uniqLength ) \
                       and self.isInInterval( self._chunkOverlap - a.range_query.getMax(), self._chunkLength - a.range_subject.getMax() ):
                    if self._verbose > 1: print "due to overlap"
                    return True
                else:
                    if self._verbose > 1: print "not due to overlap"
                    return False
                
        elif chunkQuery == chunkSubject - 1:
            if self._verbose > 1: print "query < subject"
            if a.range_query.getMin() >= self._chunkLength - self._chunkOverlap + 1 \
                   and a.range_query.getMax() <= self._chunkLength \
                   and a.range_subject.getMin() >= 1 \
                   and a.range_subject.getMax() <= self._chunkOverlap:
                if self._verbose > 1: print "included"
                if self.isInInterval( a.range_subject.getMin(), a.range_query.getMin() - uniqLength ) \
                       and self.isInInterval( self._chunkOverlap - a.range_subject.getMax(), self._chunkLength - a.range_query.getMax() ):
                    if self._verbose > 1: print "due to overlap"
                    return True
                else:
                    if self._verbose > 1: print "not due to overlap"
                    return False
                
        else:
            if self._verbose > 1: print "not contiguous chunks"
            return False
        
        if self._verbose > 1: print "not included"
        return False
    
    
    def removeChunkOverlaps( self ):
        """
        Remove pairwise alignments exactly corresponding to chunk overlaps or those included within such overlaps.
        """
        totalNbPairAlign = 0
        nbChunkOverlaps = 0
        d = {}
        nbPairAlignWithinChunkOverlaps = 0
        
        inF = open( self._inFileName, "r" )
        outF = open( self._outFileName, "w" )
        alignInstance = Align()
        
        while True:
            if not alignInstance.read( inF ): break
            totalNbPairAlign += 1
            if self._verbose > 1: alignInstance.show()
            
            if "chunk" not in alignInstance.range_query.seqname or "chunk" not in alignInstance.range_subject.seqname:
                print "WARNING: no 'chunk' in query or subject name"; return False
                
            chunkQuery = int(alignInstance.range_query.seqname.replace("chunk",""))
            chunkSubject = int(alignInstance.range_subject.seqname.replace("chunk",""))
            
            if abs( chunkSubject - chunkQuery ) > 1:
                if self._verbose > 1: print "non contiguous chunks -> keep"
                alignInstance.write( outF )
                continue
            
            if alignInstance.range_query.isOnDirectStrand() != alignInstance.range_subject.isOnDirectStrand():
                if self._verbose > 1: print "on different strand"
                alignInstance.write( outF )
                continue
            
            if abs( chunkSubject - chunkQuery ) == 0:
                if alignInstance.range_query.start == 1 \
                       and alignInstance.range_query.end == self._chunkLength \
                       and alignInstance.range_subject.start == 1 \
                       and alignInstance.range_subject.end == self._chunkLength:
                    if self._verbose > 1: print "self-alignment on whole chunk -> remove"
                    continue
                
            if self.isPairAlignAChunkOverlap( alignInstance, chunkQuery, chunkSubject ):
                if self._verbose > 1: print "chunk overlap -> remove"
                nbChunkOverlaps += 1
                
            elif self.isPairAlignWithinAndDueToAChunkOverlap( alignInstance, chunkQuery, chunkSubject ):
                if self._verbose > 1: print "within chunk overlap -> remove"
                nbPairAlignWithinChunkOverlaps += 1
                
            else:
                if self._verbose > 1: print "keep"
                alignInstance.write( outF )
                
        inF.close()
        if self._verbose > 0: print "nb of pairwise alignments in input file: %i" % ( totalNbPairAlign )
        if self._verbose > 0: print "nb of chunk overlaps: %i" % ( nbChunkOverlaps )
        if self._verbose > 0: print "nb of pairwise alignments within chunk overlaps: %i" % ( nbPairAlignWithinChunkOverlaps )
        
        for names,lAligns in d.items():
            for alignInstance in lAligns:
                alignInstance.write( outF )
        outF.close()
        
        
    def start( self ):
        """
        Useful commands before running the program.
        """
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ ); sys.stdout.flush()
        self.checkAttributes()
        
        
    def end( self ):
        """
        Useful commands before ending the program.
        """
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ ); sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        self.removeChunkOverlaps()
        self.end()
        
        
if __name__ == '__main__':
    i = RmvPairAlignInChunkOverlaps()
    i.setAttributesFromCmdLine()
    i.run()
