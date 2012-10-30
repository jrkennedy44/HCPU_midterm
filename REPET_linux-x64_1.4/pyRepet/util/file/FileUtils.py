import os
import difflib
import re
from filecmp import cmp
import glob
import shutil

# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!
# !!!!!!!! DEPRECATED !!!!!!!!

class FileUtils( object ):
    
    def _addNewLineAtTheEndOfFileContent(self, fileContent):
        if ( not fileContent.endswith('\n')  and  (len(fileContent)) != 0 ):
            fileContent = fileContent + '\n'
        return fileContent
    
    def _extractFilesContentInAList(self, listFileNames):
        filesContentList = []
        for fileName in listFileNames:
            currentFile = open(fileName, "r")
            filesContentList.append(currentFile.read())
            currentFile.close()
        return filesContentList
    
    def countLinesInAFile(self, fileName):
        f = open(fileName, "r")
        lines = f.readlines()
        f.close()
        return len(lines)    
    
    def countLinesInFiles(self, listFileNames):
        count=0
        for fileName in listFileNames:
            count+=self.countLinesInAFile(fileName)
        return count
        
    def concatFiles(self, listFileNames, concatFileName):
        fileContentList = self._extractFilesContentInAList(listFileNames)
        concatFile = open(concatFileName, "w")
        for fileContent in fileContentList:
            fileContent = self._addNewLineAtTheEndOfFileContent(fileContent)
            concatFile.write(fileContent);
        concatFile.close()
        
    def isFileEmpty(self, fileName):
        return 0 == self.countLinesInAFile(fileName)
    
    def isRessourceExists(self, fileName):
        return os.path.exists(fileName)             
            
    def listDir (self, dirName, patternFileFilter = ".*"):
        alignFileList = []
        try:
            lfile = os.listdir(dirName)
            for file in lfile:
                if re.match(patternFileFilter, file):
                    alignFileList.append(dirName + "/" + file)
        except OSError, e:
            raise e
        return alignFileList
    
    def listFilesInDir (self, dirName, patternFileFilter = ".*"):
        alignFileList = []
        for file in os.listdir(dirName):
            if os.path.isfile( dirName + "/" + file):
                if re.match(patternFileFilter, file):
                    alignFileList.append(dirName + "/" + file)
        return alignFileList
    
    def are2FilesIdentical(self, file1, file2):
        emptyResFile = False
        returnValue = os.system("diff " + file1 + " " + file2 + ">> res")
        if self.isFileEmpty("res") and returnValue == 0:
            emptyResFile = True
        os.remove("res")
        return emptyResFile
        
    def removeSuffix (self, inFileName, suffixList):
        inFilePath, file = os.path.split( inFileName )
        if inFilePath != "": 
            inFilePath = inFilePath + "/"
        for suffix in suffixList:
            #os.system("rm " + inFilePath + file + suffix)
            os.remove( inFilePath + file + suffix )
                  
    def sort(self, fileName):
        f = open(fileName)
        lines = f.readlines()
        f.close
        lines.sort()
        f = open(fileName, "w")
        f.writelines(lines)
        f.close()       

    def removeFile (self, fileName):
        cmd = "rm -f %s " % (fileName)
        os.system(cmd)   
        #removeFile_static= staticmethod (removeFile_static)
          
    def removeEmptyLine (self, inFileName, outFileName=""):
        if outFileName == "":
            outFileName= inFileName
        tempFileName = "dummySed"
        cmd = "sed /^$/d %s > %s"% (inFileName, tempFileName)
        os.system(cmd)
        cmd = "mv " + tempFileName + " " + outFileName
        os.system(cmd)        
        #removeEmptyLineInAFile_static = staticmethod (removeEmptyLineInAFile_static )
                   
    def removeRepeatedBlanks (self, inFileName, outFileName=""):
        if outFileName=="":
            outFileName=inFileName
        tempFileName = "dummyTr"
        cmd = "tr -s ' ' <%s > %s" % (inFileName, tempFileName)
        os.system(cmd)
        cmd = "mv " + tempFileName + " " + outFileName
        os.system(cmd)
        #removeRepeatedBlanks_static = staticmethod( removeRepeatedBlanks_static )
    
#--------------------------------------------------------------        

    def countLinesInAFile_static( fileName ):
        f = open( fileName, "r")
        lines = f.readlines()
        f.close()
        return len(lines)
    countLinesInAFile_static = staticmethod( countLinesInAFile_static )
    
    def isFileEmpty_static( fileName ):
        return 0 == FileUtils.countLinesInAFile_static( fileName )
    isFileEmpty_static = staticmethod( isFileEmpty_static )
    
    def are2FilesIdentical_static( file1, file2 ):
        emptyResFile = False
        returnValue = os.system( "diff " + file1 + " " + file2 + ">> res" )
        if FileUtils.isFileEmpty_static("res") and returnValue == 0:
            emptyResFile = True
        os.remove( "res" )
        return emptyResFile
    are2FilesIdentical_static = staticmethod( are2FilesIdentical_static )
    
    def isRessourceExists_static(fileName):
        return os.path.exists(fileName)  
    isRessourceExists_static = staticmethod( isRessourceExists_static )           
    
    def concatFiles_static( listFileNames, concatFileName ):
        fileContentList = FileUtils.extractFilesContentInAList_static( listFileNames )
        concatFile = open( concatFileName, "w" )
        for fileContent in fileContentList:
            fileContent = FileUtils.addNewLineAtTheEndOfFileContent_static( fileContent )
            concatFile.write( fileContent )
        concatFile.close()
    concatFiles_static = staticmethod( concatFiles_static )
    
    def extractFilesContentInAList_static( listFileNames ):
        filesContentList = []
        for fileName in listFileNames:
            currentFile = open( fileName, "r" )
            filesContentList.append( currentFile.read() )
            currentFile.close()
        return filesContentList
    extractFilesContentInAList_static = staticmethod( extractFilesContentInAList_static )

    def addNewLineAtTheEndOfFileContent_static( fileContent ):
        if not fileContent.endswith('\n')  and  len(fileContent) != 0:
            fileContent += '\n'
        return fileContent
    addNewLineAtTheEndOfFileContent_static = staticmethod( addNewLineAtTheEndOfFileContent_static )

    def catFilesUsingPattern( pattern, outFile ):
        outFileHandler = open( outFile, "w" )
        lFiles = glob.glob( pattern )
        lFiles.sort()
        for singleFile in lFiles:
            singleFileHandler = open( singleFile, "r" )
            shutil.copyfileobj( singleFileHandler, outFileHandler )
            singleFileHandler.close()
        outFileHandler.close()
    catFilesUsingPattern = staticmethod( catFilesUsingPattern )
