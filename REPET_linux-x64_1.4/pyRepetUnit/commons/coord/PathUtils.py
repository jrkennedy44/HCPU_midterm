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
import copy
from pyRepetUnit.commons.coord.Path import Path
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.coord.Map import Map
from pyRepetUnit.commons.coord.AlignUtils import AlignUtils

## Static methods for the manipulation of Path instances
#
class PathUtils ( object ):
    
    ## Change the identifier of each Set instance in the given list
    #
    # @param lPaths list of Path instances
    # @param newId new identifier
    #
    def changeIdInList(lPaths, newId):
        for iPath in lPaths:
            iPath.id = newId
            
    changeIdInList = staticmethod( changeIdInList )
    
    
    ## Return a list of Set instances containing the query range from a list of Path instances
    # 
    # @param lPaths a list of Path instances
    #  
    def getSetListFromQueries(lPaths):
        lSets = []
        for iPath in lPaths:
            lSets.append( iPath.getSubjectAsSetOfQuery() )
        return lSets
    
    getSetListFromQueries = staticmethod( getSetListFromQueries )
    
    
    ## Return a sorted list of Range instances containing the subjects from a list of Path instances
    # 
    # @param lPaths a list of Path instances
    # @note meaningful only if all Path instances have same identifier
    #
    def getRangeListFromSubjects( lPaths ):
        lRanges = []
        for iPath in lPaths:
            lRanges.append( iPath.range_subject )
        if lRanges[0].isOnDirectStrand():
            return sorted( lRanges, key=lambda iRange: ( iRange.getMin(), iRange.getMax() ) )
        else:
            return sorted( lRanges, key=lambda iRange: ( iRange.getMax(), iRange.getMin() ) )
        
    getRangeListFromSubjects = staticmethod( getRangeListFromSubjects )
    
    
    ## Return a tuple with min and max of query coordinates from Path instances in the given list
    #
    # @param lPaths a list of Path instances
    #
    def getQueryMinMaxFromPathList(lPaths):
        qmin = -1
        qmax = -1
        for iPath in lPaths:
            if qmin == -1:
                qmin = iPath.range_query.start
            qmin = min(qmin, iPath.range_query.getMin())
            qmax = max(qmax, iPath.range_query.getMax())
        return (qmin, qmax)
    
    getQueryMinMaxFromPathList = staticmethod( getQueryMinMaxFromPathList )
    
    
    ## Return a tuple with min and max of subject coordinates from Path instances in the given list
    #
    # @param lPaths lists of Path instances
    #
    def getSubjectMinMaxFromPathList(lPaths):
        smin = -1
        smax = -1
        for iPath in lPaths:
            if smin == -1:
                smin = iPath.range_subject.start
            smin = min(smin, iPath.range_subject.getMin())
            smax = max(smax, iPath.range_subject.getMax())
        return (smin, smax)
    
    getSubjectMinMaxFromPathList = staticmethod( getSubjectMinMaxFromPathList )
    
    
    ## Return True if the query range of any Path instance from the first list overlaps with the query range of any Path instance from the second list
    #
    #  @param lPaths1: list of Path instances
    #  @param lPaths2: list of Path instances
    #  @return boolean
    #  
    def areQueriesOverlappingBetweenPathLists( lPaths1, lPaths2 ):
        lSortedPaths1 = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQuery( lPaths1 )
        lSortedPaths2 = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQuery( lPaths2 )
        i = 0
        j = 0
        while i != len(lSortedPaths1):
            while j != len(lSortedPaths2):
                if not lSortedPaths1[i].range_query.isOverlapping( lSortedPaths2[j].range_query ):
                    j += 1
                else:
                    return True
            i += 1
        return False
    
    areQueriesOverlappingBetweenPathLists = staticmethod( areQueriesOverlappingBetweenPathLists )
    

    ## Show Path instances contained in the given list
    #
    # @param lPaths a list of Path instances
    #      
    def showList(lPaths):
        for iPath in lPaths:
            iPath.show()
            
    showList = staticmethod( showList )
    
    
    ## Write Path instances contained in the given list
    #
    # @param lPaths a list of Path instances
    # @param fileName name of the file to write the Path instances
    # @param mode the open mode of the file ""w"" or ""a"" 
    #
    def writeListInFile(lPaths, fileName, mode="w"):
        AlignUtils.writeListInFile(lPaths, fileName, mode)
        
    writeListInFile = staticmethod( writeListInFile )
    
    
    ## Return new list of Path instances with no duplicate
    #
    # @param lPaths a list of Path instances
    # @param useOnlyCoord boolean if True, check only coordinates and sequence names
    # @return lUniqPaths a path instances list
    #
    def getPathListWithoutDuplicates(lPaths, useOnlyCoord = False):
        if len(lPaths) < 2:
            return lPaths
        lSortedPaths = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQueryThenIdentifier( lPaths )
        lUniqPaths = [ lSortedPaths[0] ]
        if useOnlyCoord:
            for iPath in lSortedPaths[1:]:
                if iPath.range_query.start != lUniqPaths[-1].range_query.start \
                or iPath.range_query.end != lUniqPaths[-1].range_query.end \
                or iPath.range_query.seqname != lUniqPaths[-1].range_query.seqname \
                or iPath.range_subject.start != lUniqPaths[-1].range_subject.start \
                or iPath.range_subject.end != lUniqPaths[-1].range_subject.end \
                or iPath.range_subject.seqname != lUniqPaths[-1].range_subject.seqname:
                    lUniqPaths.append( iPath )
        else:
            for iPath in lSortedPaths[1:]:
                if iPath != lUniqPaths[-1]:
                    lUniqPaths.append( iPath )
        return lUniqPaths
    
    getPathListWithoutDuplicates = staticmethod( getPathListWithoutDuplicates )
    
    
    ##  Split a Path list in several Path lists according to the identifier
    #
    #  @param lPaths a list of Path instances
    #  @return a dictionary which keys are identifiers and values Path lists
    #
    def getDictOfListsWithIdAsKey( lPaths ):
        dId2PathList = {}
        for iPath in lPaths:
            if dId2PathList.has_key( iPath.id ):
                dId2PathList[ iPath.id ].append( iPath )
            else:
                dId2PathList[ iPath.id ] = [ iPath ]
        return dId2PathList
    
    getDictOfListsWithIdAsKey = staticmethod( getDictOfListsWithIdAsKey )
    
    
    ##  Split a Path file in several Path lists according to the identifier
    #
    #  @param pathFile name of the input Path file
    #  @return a dictionary which keys are identifiers and values Path lists
    #
    def getDictOfListsWithIdAsKeyFromFile( pathFile ):
        dId2PathList = {}
        pathFileHandler = open( pathFile, "r" )
        while True:
            line = pathFileHandler.readline()
            if line == "":
                break
            iPath = Path()
            iPath.setFromString( line )
            if dId2PathList.has_key( iPath.id ):
                dId2PathList[ iPath.id ].append( iPath )
            else:
                dId2PathList[ iPath.id ] = [ iPath ]
        pathFileHandler.close()
        return dId2PathList
    
    getDictOfListsWithIdAsKeyFromFile = staticmethod( getDictOfListsWithIdAsKeyFromFile )
    
    
    ## Return a list of Path list(s) obtained while splitting a list of connected Path instances according to another based on query coordinates
    #  
    # @param lToKeep: a list of Path instances to keep (reference)
    # @param lToUnjoin: a list of Path instances to unjoin
    # @return: list of Path list(s) (can be empty if one of the input lists is empty)
    # @warning: all the path instances in a given list MUST be connected (i.e. same identifier)
    # @warning: all the path instances in a given list MUST NOT overlap neither within each other nor with the Path instances of the other list
    #
    def getPathListUnjoinedBasedOnQuery( lToKeep, lToUnjoin ):
        lSortedToKeep = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQuery( lToKeep )
        lSortedToUnjoin = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQuery( lToUnjoin )
        if lToUnjoin == []:
            return []
        if lToKeep == []:
            return [ lToUnjoin ]
        
        lLists = []
        k = 0
        while k < len(lSortedToKeep):
            j1 = 0
            while j1 < len(lSortedToUnjoin) and lSortedToKeep[k].range_query.getMin() > lSortedToUnjoin[j1].range_query.getMax():
                j1 += 1
            if j1 == len(lSortedToUnjoin):
                break
            if j1 != 0:
                lLists.append( lSortedToUnjoin[:j1] )
                del lSortedToUnjoin[:j1]
                j1 = 0
            if k+1 == len(lSortedToKeep):
                break
            j2 = j1
            if j2 < len(lSortedToUnjoin) and lSortedToKeep[k+1].range_query.getMin() > lSortedToUnjoin[j2].range_query.getMax():
                while j2 < len(lSortedToUnjoin) and lSortedToKeep[k+1].range_query.getMin() > lSortedToUnjoin[j2].range_query.getMax():
                    j2 += 1
                lLists.append( lSortedToUnjoin[j1:j2] )
                del lSortedToUnjoin[j1:j2]
            k += 1
            
        if lLists != [] or k == 0:
            lLists.append( lSortedToUnjoin )
        return lLists
    
    getPathListUnjoinedBasedOnQuery = staticmethod( getPathListUnjoinedBasedOnQuery )
    
    
    ## Return the identity of the Path list, the identity of each instance being weighted by the length of each query range
    #  All Paths should have the same query and subject.
    #  The Paths are merged using query coordinates only.
    #
    # @param lPaths list of Path instances
    #
    def getIdentityFromPathList( lPaths, checkSubjects=True ):
        if len( PathUtils.getListOfDistinctQueryNames( lPaths ) ) > 1:
            msg = "ERROR: try to compute identity from Paths with different queries"
            sys.stderr.write( "%s\n" % msg ); sys.stderr.flush()
            raise Exception
        if checkSubjects and len( PathUtils.getListOfDistinctSubjectNames( lPaths ) ) > 1:
            msg = "ERROR: try to compute identity from Paths with different subjects"
            sys.stderr.write( "%s\n" % msg ); sys.stderr.flush()
            raise Exception
        identity = 0
        lMergedPaths = PathUtils.mergePathsInListUsingQueryCoordsOnly( lPaths )
        lQuerySets = PathUtils.getSetListFromQueries( lMergedPaths )
        lMergedQuerySets = SetUtils.mergeSetsInList( lQuerySets )
        totalLengthOnQry = SetUtils.getCumulLength( lMergedQuerySets )
        for iPath in lMergedPaths:
            identity += iPath.identity * iPath.getLengthOnQuery()
        weightedIdentity = identity / float(totalLengthOnQry)
        if weightedIdentity < 0 or weightedIdentity > 100:
            msg = "ERROR: weighted identity '%.2f' outside range" % ( weightedIdentity )
            sys.stderr.write( "%s\n" % msg ); sys.stderr.flush()
            raise Exception
        return weightedIdentity
    
    getIdentityFromPathList = staticmethod( getIdentityFromPathList )
    
    
    ## Return a list of Path instances sorted in increasing order according to the min of the query, then the max of the query, and finally their initial order.
    #
    # @param lPaths list of Path instances
    #
    def getPathListSortedByIncreasingMinQueryThenMaxQuery(lPaths):
        return sorted( lPaths, key=lambda iPath: ( iPath.getQueryMin(), iPath.getQueryMax() ) )
    
    getPathListSortedByIncreasingMinQueryThenMaxQuery = staticmethod( getPathListSortedByIncreasingMinQueryThenMaxQuery )
    
    
    ## Return a list of Path instances sorted in increasing order according to the min of the query, then the max of the query, then their identifier, and finally their initial order.
    #
    # @param lPaths list of Path instances
    #
    def getPathListSortedByIncreasingMinQueryThenMaxQueryThenIdentifier(lPaths):
        return sorted( lPaths, key=lambda iPath: ( iPath.getQueryMin(), iPath.getQueryMax(), iPath.getIdentifier() ) )
    
    getPathListSortedByIncreasingMinQueryThenMaxQueryThenIdentifier = staticmethod( getPathListSortedByIncreasingMinQueryThenMaxQueryThenIdentifier )
    
    
    ## Return a list of the distinct identifiers
    #
    # @param lPaths list of Path instances
    #
    def getListOfDistinctIdentifiers( lPaths ):
        lDistinctIdentifiers = []
        for iPath in lPaths:
            if iPath.id not in lDistinctIdentifiers:
                lDistinctIdentifiers.append( iPath.id )
        return lDistinctIdentifiers
    
    getListOfDistinctIdentifiers = staticmethod( getListOfDistinctIdentifiers )
    
    
    ## Return a list of the distinct query names present in the collection
    #
    # @param lPaths list of Path instances
    #
    def getListOfDistinctQueryNames( lPaths ):
        lDistinctQueryNames = []
        for iPath in lPaths:
            if iPath.range_query.seqname not in lDistinctQueryNames:
                lDistinctQueryNames.append( iPath.range_query.seqname )
        return lDistinctQueryNames
    
    getListOfDistinctQueryNames = staticmethod( getListOfDistinctQueryNames )
    
    
    ## Return a list of the distinct subject names present in the collection
    #
    # @param lPaths list of Path instances
    #
    def getListOfDistinctSubjectNames( lPaths ):
        lDistinctSubjectNames = []
        for iPath in lPaths:
            if iPath.range_subject.seqname not in lDistinctSubjectNames:
                lDistinctSubjectNames.append( iPath.range_subject.seqname )
        return lDistinctSubjectNames
    
    getListOfDistinctSubjectNames = staticmethod( getListOfDistinctSubjectNames )
    
    
    ## Return a list of lists containing query coordinates of the connections sorted in increasing order.
    #
    # @param lConnectedPaths: list of Path instances having the same identifier
    # @param minLength: threshold below which connections are not reported (default= 0 bp)
    # @note: return only connections longer than threshold
    # @note: if coordinate on query ends at 100, return 101
    # @warning: Path instances MUST be sorted in increasing order according to query coordinates
    # @warning: Path instances MUST be on direct query strand (and maybe on reverse subject strand)
    #
    def getListOfJoinCoordinatesOnQuery(lConnectedPaths, minLength=0):
        lJoinCoordinates = []
        for i in xrange(1,len(lConnectedPaths)):
            startJoin = lConnectedPaths[i-1].range_query.end
            endJoin = lConnectedPaths[i].range_query.start
            if endJoin - startJoin + 1 > minLength:
                lJoinCoordinates.append( [ startJoin + 1, endJoin - 1 ] )
        return lJoinCoordinates

    getListOfJoinCoordinatesOnQuery = staticmethod( getListOfJoinCoordinatesOnQuery )
    
    
    ## Return the length on the query of all Path instance in the given list
    #
    # @param lPaths list of Path instances
    # @note overlapping ranges are not summed but truncated.
    #
    def getLengthOnQueryFromPathList( lPaths ):
        lSets = PathUtils.getSetListFromQueries( lPaths )
        lMergedSets = SetUtils.mergeSetsInList( lSets )
        length = SetUtils.getCumulLength( lMergedSets )
        return length

    getLengthOnQueryFromPathList = staticmethod( getLengthOnQueryFromPathList )
    
    
    ## Convert a Path file into an Align file
    #
    # @param pathFile: name of the input Path file
    # @param alignFile: name of the output Align file
    #
    def convertPathFileIntoAlignFile(pathFile, alignFile):
        pathFileHandler = open( pathFile, "r" )
        alignFileHandler = open( alignFile, "w" )
        iPath = Path()
        while True:
            line = pathFileHandler.readline()
            if line == "":
                break
            iPath.setFromString( line )
            iAlign = iPath.getAlignInstance()
            iAlign.write( alignFileHandler )
        pathFileHandler.close()
        alignFileHandler.close()
        
    convertPathFileIntoAlignFile = staticmethod( convertPathFileIntoAlignFile )
    
    
    ## Convert a Path File into a Map file with query coordinates only
    #
    # @param pathFile: name of the input Path file
    # @param mapFile: name of the output Map file
    #
    def convertPathFileIntoMapFileWithQueryCoordsOnly( pathFile, mapFile ):
        pathFileHandler = open( pathFile, "r" )
        mapFileHandler = open( mapFile, "w" )
        p = Path()
        while True:
            line = pathFileHandler.readline()
            if line == "":
                break
            p.reset()
            p.setFromTuple( line.split("\t") )
            p.writeSubjectAsMapOfQuery( mapFileHandler )
        pathFileHandler.close()
        mapFileHandler.close()
        
    convertPathFileIntoMapFileWithQueryCoordsOnly = staticmethod( convertPathFileIntoMapFileWithQueryCoordsOnly )
    
    
    ## for each line of a given Path file, write the coordinates of the subject on the query as one line in a Map file
    #
    # @param pathFile: name of the input Path file
    # @param mapFile: name of the output Map file
    #
    def convertPathFileIntoMapFileWithSubjectsOnQueries( pathFile, mapFile ):
        PathUtils.convertPathFileIntoMapFileWithQueryCoordsOnly( pathFile, mapFile )
    convertPathFileIntoMapFileWithSubjectsOnQueries = staticmethod( convertPathFileIntoMapFileWithSubjectsOnQueries )
    
    
    ## Merge matches on queries
    #
    # @param inFile: name of the input Path file
    # @param outFile: name of the output Path file
    #
    def mergeMatchesOnQueries(inFile, outFile):
        mapFile = "%s.map" % ( inFile )
        PathUtils.convertPathFileIntoMapFileWithQueryCoordsOnly( inFile, mapFile )
        cmd = "mapOp"
        cmd += " -q %s" % ( mapFile )
        cmd += " -m"
        cmd += " 2>&1 > /dev/null"
        exitStatus = os.system( cmd )
        if exitStatus != 0:
            print "ERROR: mapOp returned %i" % ( exitStatus )
            sys.exit(1)
        os.remove( mapFile )
        mergeFile = "%s.merge" % ( mapFile )
        mergeFileHandler = open( mergeFile, "r" )
        outFileHandler = open( outFile, "w" )
        m = Map()
        while True:
            line = mergeFileHandler.readline()
            if line == "":
                break
            m.reset()
            m.setFromString( line, "\t" )
            m.writeAsQueryOfPath( outFileHandler )
        mergeFileHandler.close()
        os.remove( mergeFile )
        outFileHandler.close()
        
    mergeMatchesOnQueries = staticmethod( mergeMatchesOnQueries )
    
    
    ## Filter chains of Path(s) which length is below a given threshold
    #
    # @param lPaths: list of Path instances
    # @param minLengthChain: minimum length of a chain to be kept
    # @note: a chain may contain a single Path instance
    # @return: a list of Path instances
    #
    def filterPathListOnChainLength( lPaths, minLengthChain ):
        lFilteredPaths = []
        dPathnum2Paths = PathUtils.getDictOfListsWithIdAsKey( lPaths )
        for pathnum in dPathnum2Paths.keys():
            length = PathUtils.getLengthOnQueryFromPathList( dPathnum2Paths[ pathnum ] )
            if length >= minLengthChain:
                lFilteredPaths += dPathnum2Paths[ pathnum ]
        return lFilteredPaths
    
    filterPathListOnChainLength = staticmethod( filterPathListOnChainLength )
    
    
    ## Return a Path list from a Path file
    #
    # @param pathFile string name of a Path file
    # @return a list of Path instances
    #
    def getPathListFromFile( pathFile ):
        lPaths = []
        pathFileHandler = open( pathFile, "r" )
        while True:
            line = pathFileHandler.readline()
            if line == "":
                break
            iPath = Path()
            iPath.setFromString( line )
            lPaths.append( iPath )
        pathFileHandler.close()
        return lPaths
    
    getPathListFromFile = staticmethod( getPathListFromFile )
    
    
    ## Convert a chain into a 'pathrange'
    #
    # @param lPaths a list of Path instances with the same identifier
    # @note: the min and max of each Path is used
    #
    def convertPathListToPathrange( lPaths ):
        if len(lPaths) == 0:
            return
        if len(lPaths) == 1:
            return lPaths[0]
        iPathrange = copy.deepcopy( lPaths[0] )
        iPathrange.identity = lPaths[0].identity * lPaths[0].getLengthOnQuery()
        cumulQueryLength = iPathrange.getLengthOnQuery()
        for iPath in lPaths[1:]:
            if iPath.id != iPathrange.id:
                msg = "ERROR: two Path instances in the chain have different identifiers"
                sys.stderr.write( "%s\n" % ( msg ) )
                sys.exit(1)
            if iPathrange.range_subject.isOnDirectStrand() != iPath.range_subject.isOnDirectStrand():
                msg = "ERROR: two Path instances in the chain are on different strands"
                sys.stderr.write( "%s\n" % ( msg ) )
                sys.exit(1)
            iPathrange.range_query.start = min( iPathrange.range_query.start, iPath.range_query.start )
            iPathrange.range_query.end = max( iPathrange.range_query.end, iPath.range_query.end )
            if iPathrange.range_subject.isOnDirectStrand():
                iPathrange.range_subject.start = min( iPathrange.range_subject.start, iPath.range_subject.start )
                iPathrange.range_subject.end = max( iPathrange.range_subject.end, iPath.range_subject.end )
            else:
                iPathrange.range_subject.start = max( iPathrange.range_subject.start, iPath.range_subject.start )
                iPathrange.range_subject.end = min( iPathrange.range_subject.end, iPath.range_subject.end )
            iPathrange.e_value = min( iPathrange.e_value, iPath.e_value )
            iPathrange.score += iPath.score
            iPathrange.identity += iPath.identity * iPath.getLengthOnQuery()
            cumulQueryLength += iPath.getLengthOnQuery()
        iPathrange.identity = iPathrange.identity / float(cumulQueryLength)
        return iPathrange
    
    convertPathListToPathrange = staticmethod( convertPathListToPathrange )
    
    
    ## Convert a Path file into an Align file via 'pathrange'
    #
    # @param pathFile: name of the input Path file
    # @param alignFile: name of the output Align file
    # @param verbose integer verbosity level
    # @note: the min and max of each Path is used
    #
    def convertPathFileIntoAlignFileViaPathrange( pathFile, alignFile, verbose=0 ):
        lPaths = PathUtils.getPathListFromFile( pathFile )
        dId2PathList = PathUtils.getDictOfListsWithIdAsKey( lPaths )
        lIds = dId2PathList.keys()
        lIds.sort()
        if verbose > 0:
            msg = "number of chains: %i" % ( len(lIds) )
            sys.stdout.write( "%s\n" % ( msg ) )
            sys.stdout.flush()
        alignFileHandler = open( alignFile, "w" )
        for identifier in lIds:
            iPath = PathUtils.convertPathListToPathrange( dId2PathList[ identifier ] )
            iAlign = iPath.getAlignInstance()
            iAlign.write( alignFileHandler )
        alignFileHandler.close()
        
    convertPathFileIntoAlignFileViaPathrange = staticmethod( convertPathFileIntoAlignFileViaPathrange )
    
    
    ## Split a list of Path instances according to the name of the query
    #
    # @param lInPaths list of align instances
    # @return lOutPathLists list of align instances lists 
    #
    def splitPathListByQueryName( lInPaths ):
        lInSortedPaths = sorted( lInPaths, key=lambda o: o.range_query.seqname )
        lOutPathLists = []
        if len(lInSortedPaths) != 0 :
            lPathsForCurrentQuery = [] 
            previousQuery = lInSortedPaths[0].range_query.seqname
            for iPath in lInSortedPaths :
                currentQuery = iPath.range_query.seqname
                if previousQuery != currentQuery :
                    lOutPathLists.append( lPathsForCurrentQuery )
                    previousQuery = currentQuery
                    lPathsForCurrentQuery = []
                lPathsForCurrentQuery.append( iPath )
                
            lOutPathLists.append(lPathsForCurrentQuery)         
            
        return lOutPathLists
    
    splitPathListByQueryName = staticmethod( splitPathListByQueryName )
    
    
    ## Create an Path file from each list of Path instances in the input list
    #
    # @param lPathList list of lists with Path instances
    # @param pattern string
    # @param dirName string 
    #
    def createPathFiles( lPathList, pattern, dirName="" ):
        nbFiles = len(lPathList)
        countFile = 1
        if dirName != "" :
            if dirName[-1] != "/":
                dirName = dirName + '/'
            os.mkdir( dirName ) 
            
        for lPath in lPathList:
            fileName = dirName + pattern  + "_%s.path" % ( str(countFile).zfill( len(str(nbFiles)) ) )
            PathUtils.writeListInFile( lPath, fileName )
            countFile += 1
            
    createPathFiles = staticmethod( createPathFiles )
    
    
    ## Return a list of Path instances sorted in increasing order according to the min, then the inverse of the query length, and finally their initial order
    #
    # @param lPaths: list of Path instances
    #
    def getPathListSortedByIncreasingQueryMinThenInvQueryLength( lPaths ):
        return sorted( lPaths, key=lambda iPath: ( iPath.getQueryMin(), 1 / float(iPath.getLengthOnQuery()) ) )
    
    getPathListSortedByIncreasingQueryMinThenInvQueryLength = staticmethod( getPathListSortedByIncreasingQueryMinThenInvQueryLength )
    
    
    ## Merge all overlapping Path instances in a list without considering the identifiers
    #  Start by sorting the Path instances by their increasing min coordinate
    #
    # @return: a new list with the merged Path instances
    #
    def mergePathsInList( lPaths ):
        lMergedPaths = []
        if len(lPaths)==0:
            return lMergedPaths
        
        lSortedPaths = PathUtils.getPathListSortedByIncreasingQueryMinThenInvQueryLength( lPaths )
        
        prev_count = 0
        for iPath in lSortedPaths[0:]:
            if prev_count != len(lSortedPaths):
                for i in lSortedPaths[ prev_count + 1: ]:
                    if iPath.isOverlapping( i ):
                        iPath.merge( i )
                isAlreadyInList = False
                for newPath in lMergedPaths:
                    if newPath.isOverlapping( iPath ):
                        isAlreadyInList = True
                        newPath.merge( iPath )
                        lMergedPaths [ lMergedPaths.index( newPath ) ] = newPath
                if not isAlreadyInList:
                    lMergedPaths.append( iPath )
                prev_count += 1
        return lMergedPaths
    
    mergePathsInList = staticmethod( mergePathsInList )
    
    
    ## Merge all overlapping Path instances in a list without considering if subjects are overlapping.
    #  Start by sorting the Path instances by their increasing min coordinate.
    #
    # @return: a new list with the merged Path instances
    #
    def mergePathsInListUsingQueryCoordsOnly( lPaths ):
        lMergedPaths = []
        if len(lPaths)==0:
            return lMergedPaths
        
        lSortedPaths = PathUtils.getPathListSortedByIncreasingQueryMinThenInvQueryLength( lPaths )
        
        prev_count = 0
        for iPath in lSortedPaths[0:]:
            if prev_count != len(lSortedPaths):
                for i in lSortedPaths[ prev_count + 1: ]:
                    if iPath.isQueryOverlapping( i ):
                        iPath.merge( i )
                isAlreadyInList = False
                for newPath in lMergedPaths:
                    if newPath.isQueryOverlapping( iPath ):
                        isAlreadyInList = True
                        newPath.merge( iPath )
                        lMergedPaths [ lMergedPaths.index( newPath ) ] = newPath
                if not isAlreadyInList:
                    lMergedPaths.append( iPath )
                prev_count += 1
        return lMergedPaths
    
    mergePathsInListUsingQueryCoordsOnly = staticmethod( mergePathsInListUsingQueryCoordsOnly )
    
    
    ## Convert a Path file into a GFF file
    #
    # @param pathFile: name of the input Path file
    # @param gffFile: name of the output GFF file
    # @param source: source to write in the GFF file (column 2)
    #
    # @note the 'path' query is supposed to correspond to the 'gff' first column
    #
    def convertPathFileIntoGffFile( pathFile, gffFile, source="REPET", verbose=0 ):
        dId2PathList = PathUtils.getDictOfListsWithIdAsKeyFromFile( pathFile )
        if verbose > 0:
            msg = "number of chains: %i" % ( len(dId2PathList.keys()) )
            sys.stdout.write( "%s\n" % msg )
            sys.stdout.flush()
        gffFileHandler = open( gffFile, "w" )
        for id in dId2PathList.keys():
            if len( dId2PathList[ id ] ) == 1:
                iPath = dId2PathList[ id ][0]
                string = iPath.toStringAsGff( ID="%i" % iPath.getIdentifier(),
                                              source=source )
                gffFileHandler.write( "%s\n" % string )
            else:
                iPathrange = PathUtils.convertPathListToPathrange( dId2PathList[ id ] )
                string = iPathrange.toStringAsGff( ID="ms%i" % iPathrange.getIdentifier(),
                                                   source=source )
                gffFileHandler.write( "%s\n" % string )
                count = 0
                for iPath in dId2PathList[ id ]:
                    count += 1
                    string = iPath.toStringAsGff( type="match_part",
                                                  ID="mp%i-%i" % ( iPath.getIdentifier(), count ),
                                                  Parent="ms%i" % iPathrange.getIdentifier(),
                                                  source=source )
                    gffFileHandler.write( "%s\n" % string )
        gffFileHandler.close()
        
    convertPathFileIntoGffFile = staticmethod( convertPathFileIntoGffFile )
    
    
    ## Convert a Path file into a Set file
    #
    # @param pathFile: name of the input Path file
    # @param setFile: name of the output Set file
    #
    def convertPathFileIntoSetFile( pathFile, setFile ):
        pathFileHandler = open( pathFile, "r" )
        setFileHandler = open( setFile, "w" )
        iPath = Path()
        while True:
            line = pathFileHandler.readline()
            if line == "":
                break
            iPath.setFromString( line )
            iSet = iPath.getSubjectAsSetOfQuery()
            iSet.write( setFileHandler )
        pathFileHandler.close()
        setFileHandler.close()
        
    convertPathFileIntoSetFile = staticmethod( convertPathFileIntoSetFile )
