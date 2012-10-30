#!/usr/bin/env python

##@file
# Launch MapProgramLauncher.py on several files in parallel on a cluster.


import os
import sys
import getopt
import exceptions

from pyRepet.launcher.AbstractClusterLauncher import *
from repet_base.MapProgramLauncher import MapProgramLauncher


class MapClusterLauncher( AbstractClusterLauncher ):
    """
    Launch Map on several files in parallel on a cluster.
    """
    
    
    def __init__( self ):
        """
        Constructor.
        """
        AbstractClusterLauncher.__init__( self )
        AbstractClusterLauncher.setAcronym( self, "Map" )
        
        self._cmdLineSpecificOptions = "s:m:O:e:"
        
        self._exeWrapper = "MapProgramLauncher.py"
        self._prgLauncher = None
        self._prgLauncher = self.getProgramLauncherInstance()
        
        
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        string = ""
        string += "\nspecific options:"
        string += "\n     -s: size above which a gap is not penalized anymore (default='%i')" % ( self.getGapSize() )
        string += "\n     -m: penalty for a mismatch (default='%i')" % ( self.getMismatchPenalty() )
        string += "\n     -O: penalty for a gap openning (default='%i')" % ( self.getGapOpenPenalty() )
        string += "\n     -e: penalty for a gap extension (default='%i')" % ( self.getGapExtendPenalty() )
        return string
    
    
    def getGapSize( self ):
        return self._prgLauncher.getGapSize()
        
        
    def getMismatchPenalty( self ):
        return self._prgLauncher.getMismatchPenalty()
        
        
    def getGapOpenPenalty( self ):
        return self._prgLauncher.getGapOpenPenalty()
        
        
    def getGapExtendPenalty( self ):
        return self._prgLauncher.getGapExtendPenalty()
    
    
    def getProgramLauncherInstance( self ):
        if self._prgLauncher == None:
            self._prgLauncher = MapProgramLauncher()
            self._prgLauncher.setInputFile( GENERIC_IN_FILE )
            self._prgLauncher.setOutputFile( "%s.fa_aln" % ( GENERIC_IN_FILE ) )
            self._prgLauncher.setClean()
            self._prgLauncher.setVerbosityLevel( 1 )
            self._prgLauncher.setListFilesToKeep()
            self._prgLauncher.setListFilesToRemove()
        return self._prgLauncher
    
    
if __name__ == "__main__":
    i = MapClusterLauncher()
    i.setAttributesFromCmdLine()
    i.run()
