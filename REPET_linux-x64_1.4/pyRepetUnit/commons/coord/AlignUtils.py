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
import shutil
from pyRepetUnit.commons.coord.Align import Align


## Static methods manipulating Align instances
#
class AlignUtils( object ):
    
    ## Return a list with Align instances from the given file
    #
    # @param inFile name of a file in the Align format
    #
    def getAlignListFromFile( inFile ):
        lAlignInstances = []
        inFileHandler = open( inFile, "r" )
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            a = Align()
            a.setFromString( line )
            lAlignInstances.append( a )
        inFileHandler.close()
        return lAlignInstances

    getAlignListFromFile = staticmethod( getAlignListFromFile )
    
    
    ## Return a list with all the scores
    #
    # @param lAlignInstances: list of Align instances
    #
    def getListOfScores( lAlignInstances ):
        lScores = []
        for iAlign in lAlignInstances:
            lScores.append( iAlign.score )
        return lScores
    
    getListOfScores = staticmethod( getListOfScores )

    
    ## Return a list with all the scores from the given file
    #
    # @param inFile name of a file in the Align format
    #
    def getScoreListFromFile( inFile ):
        lScores = []
        inFileHandler = open( inFile, "r" )
        iAlign = Align()
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            iAlign.reset()
            iAlign.setFromString( line )
            lScores.append( iAlign.score )
        inFileHandler.close()
        return lScores
    
    getScoreListFromFile = staticmethod( getScoreListFromFile )
    
    
    ## for each line of a given Align file, write the coordinates on the query and the subject as two distinct lines in a Map file
    #
    # @param alignFile: name of the input Align file
    # @param mapFile: name of the output Map file
    #
    def convertAlignFileIntoMapFileWithQueriesAndSubjects( alignFile, mapFile ):
        alignFileHandler = open( alignFile, "r" )
        mapFileHandler = open( mapFile, "w" )
        iAlign = Align()
        while True:
            line = alignFileHandler.readline()
            if line == "":
                break
            iAlign.setFromString( line )
            iMapQ, iMapS = iAlign.getMapsOfQueryAndSubject()
            iMapQ.write( mapFileHandler )
            iMapS.write( mapFileHandler )
        alignFileHandler.close()
        mapFileHandler.close()
        
    convertAlignFileIntoMapFileWithQueriesAndSubjects = staticmethod( convertAlignFileIntoMapFileWithQueriesAndSubjects )
    
    
    ## for each line of a given Align file, write the coordinates of the subject on the query as one line in a Map file
    #
    # @param alignFile: name of the input Align file
    # @param mapFile: name of the output Map file
    #
    def convertAlignFileIntoMapFileWithSubjectsOnQueries( alignFile, mapFile ):
        alignFileHandler = open( alignFile, "r" )
        mapFileHandler = open( mapFile, "w" )
        iAlign = Align()
        while True:
            line = alignFileHandler.readline()
            if line == "":
                break
            iAlign.setFromString( line )
            iMapQ = iAlign.getSubjectAsMapOfQuery()
            iMapQ.write( mapFileHandler )
        alignFileHandler.close()
        mapFileHandler.close()
        
    convertAlignFileIntoMapFileWithSubjectsOnQueries = staticmethod( convertAlignFileIntoMapFileWithSubjectsOnQueries )
    
    
    ## return a list of Align instances sorted in decreasing order according to their score, then their length on the query and finally their initial order
    #
    # @param lAligns: list of Align instances
    #
    def getAlignListSortedByDecreasingScoreThenLength( lAligns ):
        return sorted( lAligns, key=lambda iAlign: ( 1 / float(iAlign.getScore()), 1 / float(iAlign.getLengthOnQuery()) ) )
    
    getAlignListSortedByDecreasingScoreThenLength = staticmethod( getAlignListSortedByDecreasingScoreThenLength )
    
    
    ## Convert an Align file into a Path file
    #
    # @param alignFile string name of the input Align file
    # @param pathFile string name of the output Path file
    #
    def convertAlignFileIntoPathFile( alignFile, pathFile ):
        alignFileHandler = open( alignFile, "r" )
        pathFileHandler = open( pathFile, "w" )
        iAlign = Align()
        countAlign = 0
        while True:
            line = alignFileHandler.readline()
            if line == "":
                break
            countAlign += 1
            iAlign.setFromString( line, "\t" )
            pathFileHandler.write( "%i\t%s\n" % ( countAlign, iAlign.toString() ) )
        alignFileHandler.close()
        pathFileHandler.close()
        
    convertAlignFileIntoPathFile = staticmethod( convertAlignFileIntoPathFile )
    
    
    ## Sort an Align file
    #
    def sortAlignFile( inFile, outFile="" ):
        if outFile == "":
            outFile = "%s.sort" % ( inFile )
        prg = "sort"
        cmd = prg
        cmd += " -k 1,1 -k 4,4 -k 2,2n -k 3,3n -k 5,5n -k 6,6n -k 8,8n"
        cmd += " %s" % ( inFile )
        cmd += " > %s" % ( outFile )
        exitStatus = os.system( cmd )
        if exitStatus != 0:
            msg = "ERROR: '%s' returned '%i'" % ( prg, exitStatus )
            sys.stderr.write( "%s\n" % ( msg ) )
            sys.exit( exitStatus )
            
    sortAlignFile = staticmethod( sortAlignFile )
    
    
    ## Write Align instances contained in the given list
    #
    # @param lAlign a list of Align instances
    # @param fileName name of the file to write the Align instances
    # @param mode the open mode of the file ""w"" or ""a"" 
    #
    def writeListInFile( lAlign, fileName, mode="w" ):
        fileHandler = open( fileName, mode )
        for iAlign in lAlign:
            iAlign.write( fileHandler )
        fileHandler.close()
        
    writeListInFile = staticmethod( writeListInFile )

        
    ## Split a list of Align instances according to the name of the query
    #
    # @param lInAlign list of align instances
    # @return lOutAlignList list of align instances lists 
    #
    def splitAlignListByQueryName( lInAlign ):
        lSortedAlign = sorted(lInAlign, key=lambda o: o.range_query.seqname)
        lOutAlignList = []
        if len(lSortedAlign) != 0 :
            lAlignForCurrentQuery = [] 
            previousQuery = lSortedAlign[0].range_query.seqname
            for align in lSortedAlign :
                currentQuery = align.range_query.seqname
                if previousQuery != currentQuery :
                    lOutAlignList.append(lAlignForCurrentQuery)
                    previousQuery = currentQuery 
                    lAlignForCurrentQuery = []
                lAlignForCurrentQuery.append(align)
                    
            lOutAlignList.append(lAlignForCurrentQuery)         
                
        return lOutAlignList
    
    splitAlignListByQueryName = staticmethod( splitAlignListByQueryName )
    
    
    ## Create an Align file from each list of Align instances in the input list
    #
    # @param lAlignList list of lists with Align instances
    # @param pattern string
    # @param dirName string 
    #
    def createAlignFiles( lAlignList, pattern, dirName="" ):
        nbFiles = len(lAlignList)
        countFile = 1
        if dirName != "" :
            if dirName[-1] != "/":
                dirName = dirName + '/'
            if os.path.exists( dirName ):
                shutil.rmtree( dirName )
            os.mkdir( dirName ) 
            
        for lAlign in lAlignList:
            fileName = dirName + pattern  + "_%s.align" % ( str(countFile).zfill( len(str(nbFiles)) ) )
            AlignUtils.writeListInFile( lAlign, fileName )
            countFile += 1
            
    createAlignFiles = staticmethod( createAlignFiles )
    
    
    ## Return a list with Align instances sorted by query name, subject name, query start, query end and score
    #
    def sortList( lAligns ):
        return sorted( lAligns, key=lambda iAlign: ( iAlign.getQueryName(),
                                                     iAlign.getSubjectName(),
                                                     iAlign.getQueryStart(),
                                                     iAlign.getQueryEnd(),
                                                     iAlign.getScore() ) )
        
    sortList = staticmethod( sortList )
    
    
    ## Return a list after merging all overlapping Align instances
    #
    def mergeList( lAligns ):
        lMerged = []
        
        lSorted = AlignUtils.sortList( lAligns )
        
        prev_count = 0
        for iAlign in lSorted:
            if prev_count != len(lSorted):
                for i in lSorted[ prev_count + 1: ]:
                    if iAlign.isOverlapping( i ):
                        iAlign.merge( i )
                IsAlreadyInList = False
                for newAlign in lMerged:
                    if newAlign.isOverlapping( iAlign ):
                        IsAlreadyInList = True
                        newAlign.merge( iAlign )
                        lMerged [ lMerged.index( newAlign ) ] = newAlign
                if not IsAlreadyInList:
                    lMerged.append( iAlign )
                prev_count += 1
                
        return lMerged
    
    mergeList = staticmethod( mergeList )
    
    
    ## Merge all Align instance in a given Align file
    #
    def mergeFile( inFile, outFile="" ):
        if outFile == "":
            outFile = "%s.merged" % ( inFile )
        if os.path.exists( outFile ):
            os.remove( outFile )
            
        tmpFile = "%s.sorted" % ( inFile )
        AlignUtils.sortAlignFile( inFile, tmpFile )
        
        tmpF = open( tmpFile, "r" )
        dQrySbj2Aligns = {}
        prevPairQrySbj = ""
        while True:
            line = tmpF.readline()
            if line == "":
                break
            iAlign = Align()
            iAlign.setFromString( line )
            pairQrySbj = "%s_%s" % ( iAlign.getQueryName(), iAlign.getSubjectName() )
            if not dQrySbj2Aligns.has_key( pairQrySbj ):
                if prevPairQrySbj != "":
                    lMerged = AlignUtils.mergeList( dQrySbj2Aligns[ prevPairQrySbj ] )
                    AlignUtils.writeListInFile( lMerged, outFile, "a" )
                    del dQrySbj2Aligns[ prevPairQrySbj ]
                    prevPairQrySbj = pairQrySbj
                else:
                    prevPairQrySbj = pairQrySbj
                dQrySbj2Aligns[ pairQrySbj ] = []
            dQrySbj2Aligns[ pairQrySbj ].append( iAlign )
        lMerged = []
        if len(dQrySbj2Aligns.keys()) > 0:
            lMerged = AlignUtils.mergeList( dQrySbj2Aligns[ prevPairQrySbj ] )
        AlignUtils.writeListInFile( lMerged, outFile, "a" )
        tmpF.close()
        os.remove( tmpFile )
        
    mergeFile = staticmethod( mergeFile )


    ## Update the scores of each match in the input file
    #
    # @note the new score is the length on the query times the percentage of identity
    #
    def updateScoresInFile( inFile, outFile ):
        inHandler = open( inFile, "r" )
        outHandler = open( outFile, "w" )
        iAlign = Align()
        
        while True:
            line = inHandler.readline()
            if line == "":
                break
            iAlign.reset()
            iAlign.setFromString( line, "\t" )
            iAlign.updateScore()
            iAlign.write( outHandler )
            
        inHandler.close()
        outHandler.close()
        
    updateScoresInFile = staticmethod( updateScoresInFile )
