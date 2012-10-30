#!/usr/bin/env python

##@file
# Launch MafftProgramLauncher on several files in parallel on a cluster.


from pyRepet.launcher.AbstractClusterLauncher import *
from repet_base.MafftProgramLauncher import MafftProgramLauncher


class MafftClusterLauncher( AbstractClusterLauncher ):
    """
    Launch Mafft on several files in parallel on a cluster.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        AbstractClusterLauncher.__init__( self )
        AbstractClusterLauncher.setAcronym( self, "Mafft" )
        
        self._cmdLineSpecificOptions = "p:"
        
        self._exeWrapper = "MafftProgramLauncher.py"
        self._prgLauncher = None
        self._prgLauncher = self.getProgramLauncherInstance()
        
        
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        string = ""
        string += "\nspecific options:"
        string += "\n     -p: parameters for 'mafft' (default='--auto')"
        return string
    
    
    def getProgramParameters( self ):
        return self._prgLauncher.getProgramParameters()
    
    
    def getProgramLauncherInstance( self ):
        if self._prgLauncher == None:
            self._prgLauncher = MafftProgramLauncher()
            self._prgLauncher.setInputFile( GENERIC_IN_FILE )
            self._prgLauncher.setOutputFile( "%s.fa_aln" % ( GENERIC_IN_FILE ) )
            self._prgLauncher.setClean()
            self._prgLauncher.setVerbosityLevel( 1 )
            self._prgLauncher.setListFilesToKeep()
            self._prgLauncher.setListFilesToRemove()
        return self._prgLauncher
    
    
if __name__ == "__main__":
    i = MafftClusterLauncher()
    i.setAttributesFromCmdLine()
    i.run()
