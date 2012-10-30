#!/usr/bin/env python

##@file
# Launch Mafft (multiple alignment).
#
# options:
#      -h: this help
#      -i: name of the input file (format='fasta')
#      -p: parameters for 'mafft' (default='--auto')
#      -o: name of the output file (format='aligned fasta', default=inFile+'.fa_aln')
#      -c: clean
#      -v: verbosity level (default=0/1)


import os
import sys
import getopt
import exceptions

from pyRepet.launcher.AbstractProgramLauncher import AbstractProgramLauncher
from pyRepet.seq.fastaDB import *
from repet_base.ChangeSequenceHeaders import ChangeSequenceHeaders
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
from pyRepetUnit.commons.seq.AlignedBioseqDB import AlignedBioseqDB


class MafftProgramLauncher( AbstractProgramLauncher ):
    """
    Launch Mafft (multiple alignment).
    """
    
    
    def __init__( self ):
        """
        Constructor.
        """
        AbstractProgramLauncher.__init__( self )
        self._prgName = "mafft"
        self._formatInFile = "fasta"
        self._prgParam = "--auto"
        self._cmdLineSpecificOptions = "p:o:"
        
        
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        string = ""
        string += "\nspecific options:"
        string += "\n     -p: parameters for '%s' (default='--auto')" % ( self.getProgramName() )
        string += "\n     -o: name of the output file (format='aligned fasta', default=inFile+'.fa_aln')"
        return string
    
    
    def setASpecificAttributeFromCmdLine( self, o, a="" ):
        """
        Set a specific attribute from the command-line arguments.
        """
        if o == "-p":
            self.setProgramParameters( a )
        elif o == "-o":
            self.setOutputFile( a )
            
            
    def checkSpecificAttributes( self ):
        """
        Check the specific attributes before running the program.
        """
        if self.getOutputFile() == "":
            self.setOutputFile( "%s.fa_aln" % ( self.getInputFile() ) )
            
            
    def setWrapperCommandLine( self ):
        """
        Set the command-line of the wrapper.
        Required for MafftClusterLauncher.
        """
        self._wrpCmdLine = self.getWrapperName()
        self._wrpCmdLine += " -i %s" % ( self.getInputFile() )
        self._wrpCmdLine += " -p '%s'" % ( self.getProgramParameters() )
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
        self._prgCmdLine += " %s" % ( self.getProgramParameters() )
        if self.getVerbosityLevel() == 0 and "--quiet" not in self._prgCmdLine:
            self._prgCmdLine += " --quiet"
        self._prgCmdLine += " %s.shortH" % ( self.getInputFile() )
        self._prgCmdLine += " > %s.shortH.fa_aln" % ( self.getInputFile() )
        if self._verbose < 2:
            self._prgCmdLine += " 2> /dev/null"
            
            
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
        self._summary += "\nparameters: %s" % ( self.getProgramParameters() )
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
        
        bsDB = BioseqDB( "%s.shortH" % ( self.getInputFile() ) )
        bsDB.upCase()
        bsDB.save( "%s.shortHtmp" % ( self.getInputFile() ) )
        del bsDB
        os.rename( "%s.shortHtmp" % ( self.getInputFile() ),
                   "%s.shortH" % ( self.getInputFile() ) )
        
        self.setProgramCommandLine()
        cmd = self.getProgramCommandLine()
        if self.getVerbosityLevel() > 0:
            print "LAUNCH: %s" % ( cmd )
            sys.stdout.flush()
        exitStatus = os.system( cmd )
        if exitStatus != 0:
            string = "ERROR: program '%s' returned exit status '%i'" % ( self.getProgramName(), exitStatus )
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
    i = MafftProgramLauncher()
    i.setAttributesFromCmdLine()
    i.run()
