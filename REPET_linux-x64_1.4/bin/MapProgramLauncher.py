#!/usr/bin/env python

##@file
# Launch Map (multiple alignment).
#
# options:
#      -h: this help
#      -i: name of the input file (format='fasta')
#      -s: size above which a gap is not penalized anymore (default='50')
#      -m: penalty for a mismatch (default='-8')
#      -O: penalty for a gap openning (default='16')
#      -e: penalty for a gap extension (default='4')
#      -o: name of the output file (format='aligned fasta', default=inFile+'.fa_aln')
#      -c: clean
#      -v: verbosity level (default=0/1)


import sys
import os

from pyRepet.launcher.AbstractProgramLauncher import AbstractProgramLauncher
from repet_base.ChangeSequenceHeaders import ChangeSequenceHeaders
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
from pyRepetUnit.commons.seq.AlignedBioseqDB import AlignedBioseqDB


class MapProgramLauncher( AbstractProgramLauncher ):
    """
    Launch Map (multiple alignment).
    """
    
    
    def __init__( self ):
        """
        Constructor.
        """
        AbstractProgramLauncher.__init__( self )
        self._prgName = "rpt_map"
        self._formatInFile = "fasta"
        self._cmdLineSpecificOptions = "s:m:O:e:o:"
        self._gapSize = 50
        self._mismatchPenalty = -8
        self._gapOpenPenalty = 16
        self._gapExtendPenalty = 4
        self._outFile = ""
        
        
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        string = ""
        string += "\nspecific options:"
        string += "\n     -s: size above which a gap is not penalized anymore (default='%i')" % ( self.getGapSize() )
        string += "\n     -m: penalty for a mismatch (default='%i', match=10)" % ( self.getMismatchPenalty() )
        string += "\n     -O: penalty for a gap openning (default='%i')" % ( self.getGapOpenPenalty() )
        string += "\n     -e: penalty for a gap extension (default='%i')" % ( self.getGapExtendPenalty() )
        string += "\n     -o: name of the output file (format='aligned fasta', default=inFile+'.fa_aln')"
        return string
    
    
    def setASpecificAttributeFromCmdLine( self, o, a="" ):
        """
        Set a specific attribute from the command-line arguments.
        """
        if o == "-s":
            self.setGapSize( a )
        elif o == "-m":
            self.setMismatchPenalty( a )
        elif o == "-O":
            self.setGapOpenPenalty( a )
        elif o == "-e":
            self.setGapExtendPenalty( a )
        elif o == "-o":
            self.setOutputFile( a )
            
            
    def setGapSize( self, arg ):
        self._gapSize = int(arg)
        
        
    def setMismatchPenalty( self, arg ):
        self._mismatchPenalty = int(arg)
        
        
    def setGapOpenPenalty( self, arg ):
        self._gapOpenPenalty = int(arg)
        
        
    def setGapExtendPenalty( self, arg ):
        self._gapExtendPenalty = int(arg)
        
        
    def getGapSize( self ):
        return self._gapSize
        
        
    def getMismatchPenalty( self ):
        return self._mismatchPenalty
        
        
    def getGapOpenPenalty( self ):
        return self._gapOpenPenalty
        
        
    def getGapExtendPenalty( self ):
        return self._gapExtendPenalty
        
        
    def checkSpecificAttributes( self ):
        """
        Check the specific attributes before running the program.
        """
        if self.getGapSize() <= 0:
            string = "ERROR: gap size should be > 0"
            print string
            print self.getHelpAsString()
            sys.exit(1)
        if self.getMismatchPenalty() >= 0:
            string = "ERROR: mismatch penalty should be < 0"
            print string
            print self.getHelpAsString()
            sys.exit(1)
        if self.getGapOpenPenalty() < 0:
            string = "ERROR: gap opening penalty should be >= 0"
            print string
            print self.getHelpAsString()
            sys.exit(1)
        if self.getGapExtendPenalty() < 0:
            string = "ERROR: gap extension penalty should be >= 0"
            print string
            print self.getHelpAsString()
            sys.exit(1)
        if self.getOutputFile() == "":
            self.setOutputFile( "%s.fa_aln" % ( self.getInputFile() ) )
            
            
    def setWrapperCommandLine( self ):
        """
        Set the command-line of the wrapper.
        Required for MapClusterLauncher.
        """
        self._wrpCmdLine = self.getWrapperName()
        self._wrpCmdLine += " -i %s" % ( self.getInputFile() )
        self._wrpCmdLine += " -s %i" % ( self.getGapSize() )
        self._wrpCmdLine += " -m %i" % ( self.getMismatchPenalty() )
        self._wrpCmdLine += " -O %i" % ( self.getGapOpenPenalty() )
        self._wrpCmdLine += " -e %i" % ( self.getGapExtendPenalty() )
        if self.getOutputFile() == "":
            self.setOutputFile( "%s.fa_aln" % ( self.getInputFile() ) )
        self._wrpCmdLine += " -o %s" % ( self.getOutputFile() )
        if self.getClean():
            self._wrpCmdLine += " -c"
        self._wrpCmdLine += " -v %i" % ( self.getVerbosityLevel() )
        
        
    def setProgramCommandLine( self ):
        """
        Set the command-line of the program.
        """
        self._prgCmdLine = self.getProgramName()
        self._prgCmdLine += " %s.shortH" % ( self.getInputFile() )
        self._prgCmdLine += " %i" % ( self.getGapSize() )
        self._prgCmdLine += " %i" % ( self.getMismatchPenalty() )
        self._prgCmdLine += " %i" % ( self.getGapOpenPenalty() )
        self._prgCmdLine += " %i" % ( self.getGapExtendPenalty() )
        self._prgCmdLine += " > %s.shortH.fa_aln" % ( self.getInputFile() )
        
        
    def setListFilesToKeep( self ):
        """
        Set the list of files to keep.
        """
        if self.getOutputFile() == "":
            self.setOutputFile( "%s.fa_aln" % ( self.getInputFile() ) )
        self.appendFileToKeep( self.getOutputFile() )
        
        
    def setListFilesToRemove( self ):
        """
        Set the list of files to remove.
        """
        self.appendFileToRemove( "%s.shortH" % ( self.getInputFile() ) )
        self.appendFileToRemove( "%s.shortH.fa_aln" % ( self.getInputFile() ) )
        self.appendFileToRemove( "%s.shortHlink" % ( self.getInputFile() ) )
        
        
    def setSummary( self ):
        self._summary = "input file: %s" % ( self.getInputFile() )
        self._summary += "\ngap size: %i" % ( self.getGapSize() )
        self._summary += "\nmismatch penalty: %i" % ( self.getMismatchPenalty() )
        self._summary += "\ngap openning penalty: %i" % ( self.getGapOpenPenalty() )
        self._summary += "\ngap extension penalty: %i" % ( self.getGapExtendPenalty() )
        if self.getOutputFile() == "":
            self.setOutputFile( "%s.fa_aln" % ( self.getInputFile() ) )
        self._summary += "\noutput file: %s" % ( self.getOutputFile() )
        
        
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        lInitHeaders = FastaUtils.dbHeaders( self.getInputFile(), self.getVerbosityLevel()-1 )
        
        csh = ChangeSequenceHeaders()
        csh.setInputFile( self.getInputFile() )
        csh.setFormat( "fasta" )
        csh.setStep( 1 )
        csh.setPrefix( "seq" )
        csh.setLinkFile( "%s.shortHlink" % ( self.getInputFile() ) )
        csh.setOutputFile( "%s.shortH" % ( self.getInputFile() ) )
        csh.setVerbosityLevel( self.getVerbosityLevel() - 1 )
        csh.run()
        
        self.setProgramCommandLine()
        cmd = self.getProgramCommandLine()
        if self.getVerbosityLevel() > 0:
            print "LAUNCH: %s" % ( cmd )
            sys.stdout.flush()
        returnStatus = os.system( cmd )
        if returnStatus != 0:
            string = "ERROR: program '%s' returned status '%i'" % ( self.getProgramName(), returnStatus )
            print string
            sys.exit(1)
            
        csh.setInputFile( "%s.shortH.fa_aln" % ( self.getInputFile() ) )
        csh.setFormat( "fasta" )
        csh.setStep( 2 )
        csh.setLinkFile( "%s.shortHlink" % ( self.getInputFile() ) )
        csh.setOutputFile( "%s.shortH.fa_aln.initH" % ( self.getInputFile() ) )
        csh.setVerbosityLevel( self.getVerbosityLevel() - 1 )
        csh.run()
        
        absDB = AlignedBioseqDB( "%s.shortH.fa_aln.initH" % ( self.getInputFile() ) )
        outFileHandler = open( self.getOutputFile(), "w" )
        for header in lInitHeaders:
            bs = absDB.fetch( header )
            bs.upCase()
            bs.write( outFileHandler )
        outFileHandler.close()
        os.remove( "%s.shortH.fa_aln.initH" % ( self.getInputFile() ) )
        
        self.end()
        
        
if __name__ == "__main__":
    i = MapProgramLauncher()
    i.setAttributesFromCmdLine()
    i.run()
