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
import glob
import shutil
import sys
import re
try:
    import hashlib
except:
    pass


class FileUtils( object ):
    
    ## Return the number of lines in the given file
    #
    def getNbLinesInSingleFile( fileName ):
        fileHandler = open( fileName, "r" )
        lines = fileHandler.readlines()
        fileHandler.close()
        return len(lines)
    
    getNbLinesInSingleFile = staticmethod( getNbLinesInSingleFile )
    
    ## Return the number of lines in the files in the given list
    #
    def getNbLinesInFileList( lFileNames ):
        count = 0
        for fileName in lFileNames:
            count += FileUtils.getNbLinesInSingleFile( fileName )
        return count
    
    getNbLinesInFileList = staticmethod( getNbLinesInFileList )
    
    ## Return True if the given file exists, False otherwise
    #
    def isRessourceExists( fileName ):
        return os.path.exists( fileName )
    
    isRessourceExists = staticmethod( isRessourceExists )
    
    ## Return True if the given file is empty, False otherwise
    #
    def isEmpty( fileName ):
        return 0 == FileUtils.getNbLinesInSingleFile( fileName )
    
    isEmpty = staticmethod( isEmpty )
    
    ## Return True if both files are identical, False otherwise
    #
    def are2FilesIdentical( file1, file2 ):
        tmpFile = "diff_%s_%s" % ( os.path.basename(file1), os.path.basename(file2) )
        cmd = "diff %s %s >> %s" % ( file1, file2, tmpFile )
        returnStatus = os.system( cmd )
        if returnStatus != 0:
            msg = "ERROR: 'diff' returned '%i'" % ( returnStatus )
            sys.stderr.write( "%s\n" % msg )
            sys.stderr.flush()
            os.remove( tmpFile )
            return False
        if FileUtils.isEmpty( tmpFile ):
            os.remove( tmpFile )
            return True
        else:
            os.remove( tmpFile )
            return False
        
    are2FilesIdentical = staticmethod( are2FilesIdentical )
    
    ## Return a string with all the content of the files in the given list
    #
    def getFileContent( lFiles ):
        content = ""
        lFiles.sort()
        for fileName in lFiles:
            currentFile = open( fileName, "r" )
            content += currentFile.read()
            currentFile.close()
        return content
    
    getFileContent = staticmethod( getFileContent )
    
    ## Save content of the given file after having sorted it
    #
    def sortFileContent( inFile, outFile="" ):
        inFileHandler = open(inFile, "r" )
        lines = inFileHandler.readlines()
        inFileHandler.close()
        lines.sort()
        if outFile == "":
            outFile = inFile
        outFileHandler = open( outFile, "w" )
        outFileHandler.writelines( lines )
        outFileHandler.close()
        
    sortFileContent = staticmethod( sortFileContent )
    
    ## Add end-of-line symbol in the given file content if necessary
    #
    def addNewLineAtTheEndOfFileContent( fileContent ):
        if not fileContent.endswith('\n')  and  len(fileContent) != 0:
            fileContent += '\n'
        return fileContent
    
    addNewLineAtTheEndOfFileContent = staticmethod( addNewLineAtTheEndOfFileContent )
    
    ## Concatenate files in the given list
    #
    def catFilesFromList( lFiles, outFile, sort=True ):
        if sort:
            lFiles.sort()
        outFileHandler = open( outFile, "w" )
        for singleFile in lFiles:
            singleFileHandler = open( singleFile, "r" )
            shutil.copyfileobj( singleFileHandler, outFileHandler )
            singleFileHandler.close()
        outFileHandler.close()
        
    catFilesFromList = staticmethod( catFilesFromList )
    
    ## Concatenate files according to the given pattern
    #
    def catFilesByPattern( pattern, outFile ):
        lFiles = glob.glob( pattern )
        FileUtils.catFilesFromList( lFiles, outFile )
        
    catFilesByPattern = staticmethod( catFilesByPattern )
    
    ## Remove files listed according to the given pattern
    #
    # @example pattern="/home/tmp/dummy*.txt"
    #
    def removeFilesByPattern( pattern ):
        lFiles = glob.glob( pattern )
        for f in lFiles:
            os.remove( f )
            
    removeFilesByPattern = staticmethod( removeFilesByPattern )
    
    ## Remove files listed according to the suffixes in the given list
    #
    def removeFilesBySuffixList( targetPath, lSuffixes ):
        if targetPath[-1] == "/":
            targetPath = targetPath[:-1]
        for suffix in lSuffixes:
            pattern = "%s/*%s" % ( targetPath, suffix )
            FileUtils.removeFilesByPattern( pattern )
            
    removeFilesBySuffixList = staticmethod( removeFilesBySuffixList )
    
    ## Remove repeated blanks in the given file
    #
    def removeRepeatedBlanks( inFile, outFile="" ):
        if outFile == "":
            outFile = inFile
        tmpFile = "tr_%s_%s" % ( inFile, outFile )
        cmd = "tr -s ' ' < %s > %s" % ( inFile, tmpFile )
        os.system( cmd )
        os.rename( tmpFile, outFile )
        
    removeRepeatedBlanks = staticmethod( removeRepeatedBlanks )
    
    ## Remove files in the given list
    #
    def removeFilesFromList( lFiles ):
        for f in lFiles:
            os.remove( f )
            
    removeFilesFromList = staticmethod( removeFilesFromList )
    
    ## Append the content of a file to another file
    #
    # @param inFile string name of the input file
    # @param outFile string name of the output file
    #
    def appendFileContent( inFile, outFile ):
        outFileHandler = open( outFile, "a" )
        inFileHandler = open( inFile, "r" )
        shutil.copyfileobj( inFileHandler, outFileHandler )
        inFileHandler.close()
        outFileHandler.close()
        
    appendFileContent = staticmethod( appendFileContent )
    
    
    ## Replace Windows end-of-line by Unix end-of-line
    #
    def fromWindowsToUnixEof( inFile ):
        tmpFile = "%s.tmp" % ( inFile )
        shutil.copyfile( inFile, tmpFile )
        os.remove( inFile )
        tmpFileHandler = open( tmpFile, "r" )
        inFileHandler = open( inFile, "w" )
        while True:
            line = tmpFileHandler.readline()
            if line == "":
                break
            inFileHandler.write( line.replace("\r\n","\n") )
        tmpFileHandler.close()
        inFileHandler.close()
        os.remove( tmpFile )
        
    fromWindowsToUnixEof = staticmethod( fromWindowsToUnixEof )


    ## Remove duplicated lines in a file
    #
    # @note it preserves the initial order and handles blank lines
    #
    def removeDuplicatedLines( inFile ):
        tmpFile = "%s.tmp" % ( inFile )
        shutil.copyfile( inFile, tmpFile )
        os.remove( inFile )
        
        tmpFileHandler = open( tmpFile, "r" )
        lLines = list( tmpFileHandler.read().split("\n") )
        if lLines[-1] == "":
            del lLines[-1]
        sLines = set( lLines )
        tmpFileHandler.close()
        os.remove( tmpFile )
        
        inFileHandler = open( inFile, "w" )
        for line in lLines:
            if line in sLines:
                inFileHandler.write( "%s\n" % ( line ) )
                sLines.remove( line )
        inFileHandler.close()
        
    removeDuplicatedLines = staticmethod( removeDuplicatedLines )
    
    
    ## Write a list of lines in a given file
    #
    def writeLineListInFile( inFile, lLines ):
        inFileHandler = open( inFile, "w" )
        for line in lLines:
            inFileHandler.write( line )
        inFileHandler.close()
        
    writeLineListInFile = staticmethod( writeLineListInFile )
    
    
    ## Give the list of absolute path of each directory in the given directory
    #
    # @param rootPath string absolute path of the given directory
    #
    # @return lDirPath list of absolute directory path
    #
    def getAbsoluteDirectoryPathList(rootPath):
        lDirPath = []
        lPaths = glob.glob(rootPath + "/*")
        for ressource in lPaths:
            if os.path.isdir(ressource) :
                lDirPath.append(ressource)
        return lDirPath
    
    getAbsoluteDirectoryPathList = staticmethod(getAbsoluteDirectoryPathList)
    
    
    ## Give the list of file names found in the given directory
    #
    # @param dirPath string absolute path of the given directory
    #
    # @return lFilesInDir list of file names
    #
    def getFileNamesList( dirPath, patternFileFilter = ".*" ):
        lFilesInDir = []
        lPaths = glob.glob( dirPath + "/*" )
        for ressource in lPaths:
            if os.path.isfile( ressource ):
                fileName = os.path.basename( ressource )
                if re.match(patternFileFilter, fileName):
                    lFilesInDir.append( fileName )
        return lFilesInDir
    
    getFileNamesList = staticmethod( getFileNamesList )
    
    ## Return the MD5 sum of a file
    #
    def getMd5SecureHash( inFile ):
        if "hashlib" in sys.modules:
            md5 = hashlib.md5()
            inFileHandler = open( inFile, "r" )
            while True:
                line = inFileHandler.readline()
                if line == "":
                    break
                md5.update( line )
            inFileHandler.close()
            return md5.hexdigest()
        else:
            return ""
        
    getMd5SecureHash = staticmethod( getMd5SecureHash )
    
    ## Cat all files of a given directory
    #
    # @param dir string directory name
    # @param outFileName string output file name
    #
    def catFilesOfDir(dir, outFileName):
        lFiles = FileUtils.getFileNamesList(dir)
        lFile2 = []
        for file in lFiles:
            lFile2.append(dir + "/" + file)
        FileUtils.catFilesFromList(lFile2, outFileName)
        
    catFilesOfDir = staticmethod(catFilesOfDir)
