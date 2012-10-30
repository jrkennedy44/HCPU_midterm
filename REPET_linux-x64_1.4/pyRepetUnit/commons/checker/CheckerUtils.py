# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


import os
import sys
import re
import glob
import ConfigParser
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
from pyRepetUnit.commons.checker.CheckerException import CheckerException


## A set of static methods used to perform checks.
#
#
class CheckerUtils( object ):
    
    ## Check if blastName param is in ["blastn", "blastp", "blastx", "tblastn", "tblastx"]
    # 
    # @param blastName name to check
    # @return True if name is in list False otherwise
    #
    def isBlastNameNotInBlastValues( blastName ):
        blastValuesSet = set( ["blastn", "blastp", "blastx", "tblastn", "tblastx"] )
        blastNameSet = set( [ blastName ] )
        return not blastNameSet.issubset( blastValuesSet )
    
    isBlastNameNotInBlastValues = staticmethod( isBlastNameNotInBlastValues )
    
    
    ## Check if param is NOT "TRUE" and NOT false "FALSE"
    #
    # @param param str to check
    # @return True if param is not eq to "TRUE" AND not eq to "FALSE", false otherwise 
    #
    def isNotTRUEisNotFALSE( param ):
        return param != "TRUE" and param != "FALSE"
    
    isNotTRUEisNotFALSE = staticmethod( isNotTRUEisNotFALSE )
    
    
    ## Check if resource (file or dir) do NOT exists
    #  
    # @param resource file or dir to check
    # @return True if resource exists False otherwise
    #
    def isRessourceNotExits( resource ):
        return not os.path.exists( resource )
    
    isRessourceNotExits = staticmethod( isRessourceNotExits )
    
    
    ## Check a specific E-value format: de-dd 
    #
    # @param param E-value to check
    # @return True if format is de-dd False otherwise
    #
    def isNotAeValueWithOneDigit2DecimalsAtLeast( param ):
        # \d\d stands for 2 digits and more ???
        return not re.match( "\de\-\d\d", param )
    
    isNotAeValueWithOneDigit2DecimalsAtLeast = staticmethod( isNotAeValueWithOneDigit2DecimalsAtLeast )
    
    
    ## Check a number format
    #
    # @param param value to check
    # @return True if param is a number (d+) False otherwise
    #
    def isNotANumber( param ):
        return not re.match( "\d+", param )
    
    isNotANumber = staticmethod( isNotANumber )
    

    ## Check if an executable is in the user's PATH
    #
    # @param exeName name of the executable
    # @return True if executable in user's PATH, False otherwise
    #
    def isExecutableInUserPath( exeName ):
        dirPathList = os.environ["PATH"].split(":")
        for dirPath in dirPathList:
            if os.path.isdir( dirPath ):
                try:
                    binPathList = glob.glob( dirPath + "/*" )
                except OSError, e:
                    continue
                for binPath in binPathList:
                    bin = os.path.basename( binPath )
                    if bin == exeName:
                        return True
        return False
    
    isExecutableInUserPath = staticmethod( isExecutableInUserPath )
    
    
    ## Return the full path of a given executable
    #
    def getFullPathFromExecutable( exeName ):
        lDirFromUserPath = os.environ["PATH"].split(":")
        for dir in lDirFromUserPath:
            if os.path.isdir( dir ):
                try:
                    lExecutables = glob.glob( "%s/*" % ( dir ) )
                except OSError, e:
                    continue
                for exe in lExecutables:
                    path, exe = os.path.split( exe )
                    if exe == exeName:
                        return path
        return ""
    
    getFullPathFromExecutable = staticmethod( getFullPathFromExecutable )
    
    
    #TODO: to remove ?
    ## Check if a queue Name is valid. Warning: Only with the queue manager SGE
    #
    # @param fullQueueName name of the queue to test (with or without parameters)
    # @return True if queue name is valid, False otherwise
    #
    def isQueueNameValid( fullQueueName ):
        queueName = fullQueueName.split()[0]
        if queueName == "none":
            return True
        queueFile = "queueName.txt"
        if not CheckerUtils.isExecutableInUserPath( "qconf" ):
            msg = "executable 'qconf' can't be found"
            sys.stderr.write( "%s\n" % ( msg ) )
            return False
        cmd = "qconf -sql > " + queueFile
        os.system( cmd )
        queueFileHandler = open( queueFile, "r" )
        lQueueNames = queueFileHandler.readlines()
        queueFileHandler.close()
        os.remove( queueFile )
        queueNameValid = False
        for qName in lQueueNames:
            qName = qName.strip()
            if qName == queueName:
                queueNameValid = True
                break
        return queueNameValid
    
    isQueueNameValid = staticmethod( isQueueNameValid )
    
    
    ## Check if a string length is lower or equal than 15
    #
    # @param strName any string
    # @return True if string length is <= 15, False otherwise
    #
    def isMax15Char( strName ):
        return (len(strName) <= 15 )
    
    isMax15Char = staticmethod( isMax15Char )
    
    
    ## Check if a string is made with only alphanumeric or underscore character
    #
    # @param strName any string
    # @return True if string is with alphanumeric or underscore, False otherwise
    #
    def isCharAlphanumOrUnderscore( strName ):
        # authorized ALPHABET [a-z,A-Z,0-9,_]
        p = re.compile('\W')
        errList=p.findall(strName)
        if len( errList ) > 0 :
            return False
        else:
            return True
        
    isCharAlphanumOrUnderscore = staticmethod( isCharAlphanumOrUnderscore )
    
    
    ## Check if sectionName is in the configuration file
    #
    # @param config filehandle of configuration file
    # @param sectionName string of section name to check
    # @exception NoSectionError: if section not found raise a NoSectionError 
    # 
    def checkSectionInConfigFile( config, sectionName ):
        if not (config.has_section(sectionName)):
            raise NoSectionError(sectionName)
        
    checkSectionInConfigFile = staticmethod( checkSectionInConfigFile )
    
    
    ## Check if an option is in a specified section in the configuration file
    #
    # @param config filehandle of configuration file
    # @param sectionName string of section name
    # @param optionName string of option name to check
    # @exception NoOptionError: if option not found raise a NoOptionError
    #
    def checkOptionInSectionInConfigFile( config, sectionName, optionName ):
        config.get( sectionName, optionName )
    
    checkOptionInSectionInConfigFile = staticmethod( checkOptionInSectionInConfigFile )
    
    
    ## Check version number coherency between configFile and CHANGELOG
    #
    # @param config ConfigParser Instance of configuration file
    # @param changeLogFileHandle CHANGELOG file handle
    # @exception NoOptionError: if option not found raise a NoOptionError
    #
    def checkConfigVersion( changeLogFileHandle, config ):
        line = changeLogFileHandle.readline()
        while not line.startswith("REPET release "):
            line = changeLogFileHandle.readline()
        numVersionChangeLog = line.split()[2]
        
        numVersionConfig = config.get("repet_env", "repet_version")
        
        if not numVersionChangeLog == numVersionConfig:
            message = "*** Error: wrong config file version. Expected version num is " + numVersionChangeLog + " but actual in config file is " + numVersionConfig
            raise CheckerException(message)
    
    checkConfigVersion = staticmethod( checkConfigVersion )
    
    
    ## Check if headers of an input file contain only alpha numeric characters and "_ : . -"
    #
    # @param fileHandler file handle
    # @exception CheckerException if bad header raise a CheckerException
    #
    def checkHeaders( fileHandler ):
        lHeaders = CheckerUtils._getHeaderFromFastaFile(fileHandler)
        #TODO: regexp don't work with | and =
        p = re.compile('[^a-zA-Z0-9_:\.\-]', re.IGNORECASE)
        lWrongHeaders = []
        for header in lHeaders:
            errList=p.findall(header)
            if len( errList ) > 0 :
                lWrongHeaders.append(header)
        if lWrongHeaders != []:
            exception = CheckerException()
            exception.setMessages(lWrongHeaders)
            raise exception
        
    checkHeaders = staticmethod( checkHeaders )  
    
    
    def _getHeaderFromFastaFile( inFile ):
        lHeaders = []
        while True:
            line = inFile.readline()
            if line == "":
                break
            if line[0] == ">":
                lHeaders.append( line[1:-1] )
        return lHeaders
    
    _getHeaderFromFastaFile = staticmethod( _getHeaderFromFastaFile ) 


    ## Return True if an option is in a specified section in the configuration file, False otherwise
    #
    # @param config handler of configuration file
    # @param sectionName string of section name
    # @param optionName string of option name to check
    #
    def isOptionInSectionInConfig( configHandler, section, option ):
        try:
            CheckerUtils.checkOptionInSectionInConfigFile( configHandler, section, option ) 
        except NoOptionError:
            return False
        return True
    
    isOptionInSectionInConfig = staticmethod( isOptionInSectionInConfig )
