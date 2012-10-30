#!/usr/bin/env python

##@file
# Abstract class to launch a program.


import os
import sys
import getopt
import time

from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils


class AbstractProgramLauncher( object ):  #( IProgramLauncher )
    """
    Abstract class to launch a program.
    """
    
    
    def __init__( self ):
        """
        Constructor.
        """
        self._wrpName = "%s.py" % ( type(self).__name__ )
        self._prgName = ""
        self._inFile = ""
        self._formatInFile = ""
        self._prgParam = ""
        self._outFile = ""
        self._clean = False
        self._verbose = 0
        self._wrpCmdLine = ""
        self._prgCmdLine = ""
        self._lFilesToKeep = []
        self._lFilesToRemove = []
        self._summary = ""
        self._cmdLineGenericOptions = "hi:cv:"
        self._cmdLineSpecificOptions = ""
        
    def getGenericHelpAsString( self ):
        """
        Return the generic help as a string.
        """
        string = ""
        string += "usage: %s.py [options]" % ( type(self).__name__ )
        string += "\ngeneric options:"
        string += "\n     -h: this help"
        string += "\n     -i: name of the input file (format='%s')" % ( self.getFormatInputFile() )
        string += "\n     -c: clean"
        string += "\n     -v: verbosity level (default=0/1)"
        return string
    
    
    def getSpecificHelpAsString( self ):
        """
        Return the specific help as a string.
        """
        pass
    
    
    def getHelpAsString( self ):
        """
        Return the help as a string.
        """
        string = self.getGenericHelpAsString()
        string += self.getSpecificHelpAsString()
        return string
    
    
    def setAGenericAttributeFromCmdLine( self, o, a="" ):
        """
        Set a generic attribute from the command-line arguments.
        """
        if o == "-h":
            print self.getHelpAsString()
            sys.exit(0)
        elif o == "-i":
            self.setInputFile( a )
        elif o == "-c":
            self.setClean()
        elif o == "-v":
            self.setVerbosityLevel( a )
            
            
    def setASpecificAttributeFromCmdLine( self, o, a="" ):
        """
        Set a specific attribute from the command-line arguments.
        """
        pass
    
    
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line arguments.
        """
        try:
            opts, args = getopt.getopt( sys.argv[1:], "%s%s" % ( self._cmdLineGenericOptions, self._cmdLineSpecificOptions ) )
        except getopt.GetoptError, err:
            print str(err);
            print self.getHelpAsString()
            sys.exit(1)
        for o, a in opts:
            self.setAGenericAttributeFromCmdLine( o, a )
            self.setASpecificAttributeFromCmdLine( o, a )
            
            
    def setInputFile( self, arg ):
        self._inFile = arg
        
        
    def setProgramParameters( self, arg ):
        if arg != "":
            self._prgParam = arg
            
            
    def setOutputFile( self, arg ):
        self._outFile = arg
        
        
    def setClean( self ):
        self._clean = True
        
        
    def setVerbosityLevel( self, arg ):
        self._verbose = int(arg)
        
        
    def setWrapperCommandLine( self ):
        pass
    
    
    def setProgramCommandLine( self ):
        pass
    
    
    def setListFilesToKeep( self ):
        pass
    
    
    def setListFilesToRemove( self ):
        pass
    
    
    def appendFileToKeep( self, arg ):
        self._lFilesToKeep.append( arg )
        
        
    def appendFileToRemove( self, arg ):
        self._lFilesToRemove.append( arg )


    def setSummary( self ):
        """
        Set a few sentences summaryzing the program parameters.
        To be writtent in the log file and/or sent to stdout.
        """
        pass
    
    
    def getWrapperName( self ):
        return self._wrpName
    
    
    def getProgramName( self ):
        return self._prgName
    
    
    def getInputFile( self ):
        return self._inFile
    
    
    def getFormatInputFile( self ):
        return self._formatInFile
    
    
    def getProgramParameters( self ):
        return self._prgParam
    
    
    def getOutputFile( self ):
        return self._outFile
    
    
    def getClean( self ):
        return self._clean
    
    
    def getVerbosityLevel( self ):
        return self._verbose
    
    
    def getWrapperCommandLine( self ):
        """
        Return the command-line of the wrapper.
        """
        return self._wrpCmdLine
    
    
    def getProgramCommandLine( self ):
        """
        Return the command-line of the program.
        """
        return self._prgCmdLine
    
    
    def getListFilesToKeep( self ):
        """
        Return a list of the files to keep.
        """
        return self._lFilesToKeep
    
    
    def getListFilesToRemove( self ):
        """
        Return a list of the files to remove.
        """
        return self._lFilesToRemove
    
    
    def getSummary( self ):
        """
        Return the few sentences summarizing the program parameters.
        """
        return self._summary


    def check( self ):
        """
        Check all required resources are present.
        """
        self.checkGenericAttributes()
        self.checkSpecificAttributes()
        
        
    def checkGenericAttributes( self ):
        """
        Check the generic attributes before running the program.
        """
        string = self._checkProgramName()
        if self.getInputFile() == "":
            string = "ERROR: missing input file"
            print string
            print self.getHelpAsString()
            sys.exit(1)
        if not os.path.exists( self.getInputFile() ):
            string = "ERROR: input file '%s' doesn't exist" % ( self.getInputFile() )
            print string
            print self.getHelpAsString()
            sys.exit(1)
            
            
    def checkSpecificAttributes( self ):
        """
        Check the specific attributes before running the program.
        """
        pass
    
    
    def _checkProgramName( self ):
        if not CheckerUtils.isExecutableInUserPath( self.getProgramName() ):
            msg = "ERROR: '%s' not in your PATH" % ( self.getProgramName() )
            sys.stderr.write( "%s\n"  %( msg ) )
            sys.exit(1)
            
            
    def preprocess( self ):
        """
        Pre-processing, in run(), after start()
        """
        pass
    
    
    def postprocess( self ):
        """
        Post-processing, in run(), before end()
        """
        pass
    
    
    def clean( self ):
        """
        Remove the files in 'getListFilesToRemove()'.
        """
        self.setListFilesToRemove()
        for f in self.getListFilesToRemove():
            if os.path.exists( f ):
                os.remove( f )
                
                
    def start( self ):
        """
        Useful commands before running the program (check, open database connector...).
        """
        self.check()
        if self._verbose > 0:
            string = "START %s (%s)" % ( type(self).__name__, time.strftime("%m/%d/%Y %H:%M:%S") )
            print string
        self.setSummary()
        if self._verbose > 0:
            print self.getSummary()
        sys.stdout.flush()
        
        
    def end( self ):
        """
        Useful commands after the program was run (clean, close database connector...).
        """
        if self.getClean():
            self.clean()
            
        if self._verbose > 0:
            string = "END %s (%s)" % ( type(self).__name__, time.strftime("%m/%d/%Y %H:%M:%S") )
            print string
        sys.stdout.flush()
        
        
    def run( self ):
        """
        Run the program.
        """
        pass
