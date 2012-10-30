"""
Utility to handle a databank of HMM profiles.
"""

import os
import sys
from pyRepetUnit.profilesDB.Profiles import Profiles
from pyRepetUnit.profilesDB.ProfilesDatabank import ProfilesDatabank
import pyRepet.util.file.FileUtils

class ProfilesDatabankUtils:
    """
    Utility to handle a databank of HMM profiles.
    """
    
    def read( inFileName, verbose=0 ):
        """
        Read a file in Pfam format and return a L[ProfilesDatabank<pyRepetUnit.commons.ProfilesDatabank>} instance.
        @param inFileName: name of the input file
        @type inFileName: string
        @param verbose: verbosity level
        @type verbose: integer
        """ 
        if verbose > 0: print "reading file '%s'..." % ( inFileName ); sys.stdout.flush()
        fileUtilsInstance = pyRepet.util.file.FileUtils.FileUtils()     
        if fileUtilsInstance.isFileEmpty( inFileName ):
            return (None)
        profilesInstance = Profiles() 
        profilesDBInstance = ProfilesDatabank()
        f = open( inFileName , "r")
        while profilesInstance.read( f ):
            profilesDBInstance.append( profilesInstance )
            profilesInstance = Profiles()
        f.close()
        if verbose > 0: print "file '%s' is loaded" % ( inFileName ); sys.stdout.flush()
        return (profilesDBInstance)
    
    read = staticmethod( read )
