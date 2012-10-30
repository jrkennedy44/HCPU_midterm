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


from pyRepetUnit.commons.coord.Set import Set

## Static methods for the manipulation of Path instances
#
class SetUtils( object ):
    
    ## Change the identifier of each Set instance in the given list
    #
    # @param lSets list of Set instances
    # @param newId new identifier
    #
    def changeIdInList(lSets, newId):
        for iSet in lSets:
            iSet.id = newId
            
    changeIdInList = staticmethod( changeIdInList )
    
    ## Return the length of the overlap between two lists of Set instances
    #
    # @param lSets1 list of Set instances
    # @param lSets2 list of Set instances
    # @return length of overlap
    # @warning sequence names are supposed to be identical
    #
    def getOverlapLengthBetweenLists(lSets1, lSets2):
        lSet1Sorted = SetUtils.getSetListSortedByIncreasingMinThenMax(lSets1)
        lSet2Sorted = SetUtils.getSetListSortedByIncreasingMinThenMax(lSets2)
        osize = 0
        i = 0
        j = 0
        while i!= len(lSet1Sorted):
            while j!= len(lSet2Sorted) and lSet1Sorted[i].getMin()>lSet2Sorted[j].getMax()\
                and not(lSet1Sorted[i].isOverlapping(lSet2Sorted[j])):
                j+=1
            jj=j
            while jj!= len(lSet2Sorted) and lSet1Sorted[i].isOverlapping(lSet2Sorted[jj]):
                osize+=lSet1Sorted[i].getOverlapLength(lSet2Sorted[jj])
                jj+=1
            i+=1
        return osize
    
    getOverlapLengthBetweenLists = staticmethod( getOverlapLengthBetweenLists )
    
    ## Return True if the two lists of Set instances overlap, False otherwise    
    #
    # @param lSets1 list of Set instances
    # @param lSets2 list of Set instances
    #    
    def areSetsOverlappingBetweenLists( lSets1, lSets2 ):
        lSet1Sorted = SetUtils.getSetListSortedByIncreasingMinThenMax(lSets1)
        lSet2Sorted = SetUtils.getSetListSortedByIncreasingMinThenMax(lSets2)
        i=0
        j=0
        while i!= len(lSet1Sorted):
            while j!= len(lSet2Sorted) and lSet1Sorted[i].getMin()>lSet2Sorted[j].getMax()\
                and not(lSet1Sorted[i].isOverlapping(lSet2Sorted[j])):
                j+=1
            if j!= len(lSet2Sorted) and lSet1Sorted[i].isOverlapping(lSet2Sorted[j]):
                return True
            i+=1
        return False
    
    areSetsOverlappingBetweenLists = staticmethod( areSetsOverlappingBetweenLists )
    
    ## Merge all overlapping Set instances between two lists of Set and give the next identifier 
    #
    # @param lSets1 list of Set instances
    # @param lSets2 list of Set instances
    # @param max_id start id value for inserting new Set
    # @return a new list of the merged Set instances and the next identifier
    # 
    def getListOfMergedSetsAndNextId(lSets1, lSets2, max_id=0):
        lSets_merged = []
        list2merge = SetUtils.getListOfIdListOfOverlappingSets ( lSets1,lSets2 )
        idlist1 = SetUtils.getDictOfListsWithIdAsKey(lSets1)
        idlist2 = SetUtils.getDictOfListsWithIdAsKey(lSets2)
        if max_id == 0:
            max_id = max(idlist1.keys()) + 1
        for i in list2merge:
            if i == []:
                continue
            l = []
            min_id = max(i)
            for j in i:
                if j>0:
                    if min_id>j:
                        min_id=j
                    l.extend(idlist1[j])
                    del idlist1[j]
                else:
                    l.extend(idlist2[j*-1])
                    del idlist2[j*-1]
            l = SetUtils.mergeSetsInList(l)
            SetUtils.changeIdInList(l, min_id)
            lSets_merged.extend(l)
        for id, alist in idlist1.items():
            lSets_merged.extend(alist)
        for id,alist in idlist2.items():
            SetUtils.changeIdInList(alist,max_id)
            lSets_merged.extend(alist)
            max_id+=1
        return lSets_merged, max_id
    
    getListOfMergedSetsAndNextId = staticmethod ( getListOfMergedSetsAndNextId )
    
    ## Return the sum of the length of each Set instance in the given list
    #
    # @param lSets: list of Set instances
    #
    def getCumulLength(lSets):
        length = 0
        for i in lSets:
            length += i.getLength()
        return length
    
    getCumulLength = staticmethod( getCumulLength )
    
    ## Return a tuple with min and max coordinates of Set instances in the given list
    #
    # @param lSets list of Set instances
    # 
    def getListBoundaries(lSets):
        qmin = -1
        qmax = -1
        for iSet in lSets:
            if qmin == -1:
                qmin = iSet.start
            qmin = min(qmin, iSet.getMin())
            qmax = max(qmax, iSet.getMax())
        return (qmin, qmax)
    
    getListBoundaries = staticmethod( getListBoundaries )
    
    ## Show Set instances contained in the given list
    #
    # @param lSets list of Set instances
    # 
    def showList(lSets):
        for iSet in lSets:
            iSet.show()
            
    showList = staticmethod( showList )
    
    ## Write Set instances contained in the given list
    #
    # @param lSets list of Set instances
    # @param fileName a file name
    # @param mode the open mode of the file '"w"' or '"a"' 
    #
    def writeListInFile(lSets, fileName, mode="w"):
        fileHandler = open(fileName, mode)
        for iSet in lSets:
            iSet.write(fileHandler)
        fileHandler.close()
        
    writeListInFile = staticmethod( writeListInFile )
    
    ## Split a Set list in several Set lists according to the identifier
    #
    # @param lSets list of Set instances
    # @return a dictionary which keys are identifiers and values Set lists
    #
    def getDictOfListsWithIdAsKey(lSets):
        dId2SetList = {}
        for iSet in lSets:
            if dId2SetList.has_key(iSet.id):
                dId2SetList[iSet.id].append(iSet)
            else:
                dId2SetList[iSet.id] = [iSet]
        return dId2SetList
    
    getDictOfListsWithIdAsKey = staticmethod( getDictOfListsWithIdAsKey )
    
    
    ## Split a Set list in several Set lists according to the identifier
    #
    # @param lSets list of Set instances
    # @return a dictionary which keys are identifiers and values Set lists
    #
    def getDictOfListsWithIdAsKeyFromFile( setFile ):
        dId2SetList = {}
        setFileHandler = open( setFile, "r" )
        while True:
            line = setFileHandler.readline()
            if line == "":
                break
            iSet = Set()
            iSet.setFromTuple( line[:-1].split("\t") )
            if not dId2SetList.has_key( iSet.id ):
                dId2SetList[ iSet.id ] = []
            dId2SetList[ iSet.id ].append( iSet )
        setFileHandler.close()
        return dId2SetList
    
    getDictOfListsWithIdAsKeyFromFile = staticmethod( getDictOfListsWithIdAsKeyFromFile )
    
    
    ## Return a Map list from the given Set List
    #
    # @param lSets list of Set instances
    # 
    def getMapListFromSetList(lSets):
        lMaps = []
        for iSet in lSets:
            lMaps.append(iSet.set2map())
        return lMaps
    
    getMapListFromSetList = staticmethod( getMapListFromSetList )
    
    ## Construct a Set list from a Map list
    #
    # @param lMaps list of Map instances
    # 
    def getSetListFromMapList(lMaps):
        lSets = []
        c = 0
        for iMap in lMaps:
            c += 1
            lSets.append( Set(c, iMap.name, iMap.seqname, iMap.start, iMap.end) )
        return lSets
    
    getSetListFromMapList = staticmethod( getSetListFromMapList )
    
    ## Merge all overlapping Set instances in a list without considering the identifiers.
    #  Start by sorting Set instances by their increasing Min coordinate.
    #
    # @return: a new list of the merged Set instances
    #
    def mergeSetsInList(lSets):
        l=[]
        if len(lSets)==0:
            return l
        
        lSortedSets = SetUtils.getSetListSortedByIncreasingMinThenInvLength( lSets )
        
        prev_count = 0
        for iSet in lSortedSets[0:]:
            if prev_count != len(lSortedSets):
                for i in lSortedSets[ prev_count + 1: ]:
                    if iSet.isOverlapping( i ):
                        iSet.merge( i )
                IsAlreadyInList = False
                for newSet in l:
                    if newSet.isOverlapping( iSet ):
                        IsAlreadyInList = True
                        newSet.merge( iSet )
                        l [ l.index( newSet ) ] = newSet
                if not IsAlreadyInList:
                    l.append( iSet )
                prev_count += 1
        return l
    
    mergeSetsInList = staticmethod( mergeSetsInList )
    
    ## Unjoin a Set list according to another
    #
    # @param lToKeep: a list of Set instances to keep 
    # @param lToUnjoin: a list of Set instances to unjoin
    # @return: lToUnjoin split in several list
    #    
    def getSetListUnjoined(lToKeep, lToUnjoin):
        lSortedToKeep = SetUtils.getSetListSortedByIncreasingMinThenMax( lToKeep )
        lSortedToUnjoin = SetUtils.getSetListSortedByIncreasingMinThenMax( lToUnjoin )
        if lSortedToUnjoin == []:
            return []
        if lSortedToKeep == []:
            return [ lSortedToUnjoin ]
        
        i=0
        resultListSet=[]
        while i<len(lSortedToKeep):
            j1=0
            while j1<len(lSortedToUnjoin) and lSortedToKeep[i].getMin() > lSortedToUnjoin[j1].getMax():
                j1+=1
            if j1==len(lSortedToUnjoin):
                break
            if j1!=0:
                resultListSet.append(lSortedToUnjoin[:j1])
                del lSortedToUnjoin[:j1]
                j1=0
            if i+1==len(lSortedToKeep):
                break
            j2=j1
            if j2<len(lSortedToUnjoin) and lSortedToKeep[i+1].getMin() > lSortedToUnjoin[j2].getMax():
                while j2<len(lSortedToUnjoin) and lSortedToKeep[i+1].getMin() > lSortedToUnjoin[j2].getMax():
                    j2+=1
                resultListSet.append(lSortedToUnjoin[j1:j2])
                del lSortedToUnjoin[j1:j2]
            i+=1
    
        if resultListSet!=[] or i == 0:
            resultListSet.append(lSortedToUnjoin)
        return resultListSet
    
    getSetListUnjoined = staticmethod(getSetListUnjoined)
      
    ## Return new list of Set instances with no duplicate
    #
    # @param lSets list of Set instances
    #
    def getSetListWithoutDuplicates( lSets ):
        if len(lSets) < 2:
            return lSets
        lSortedSet = SetUtils.getSetListSortedByIncreasingMinThenMax( lSets )
        lUniqSet = [ lSortedSet[0] ]
        for iSet in lSortedSet[1:]:
            if iSet != lUniqSet[-1]:
                lUniqSet.append( iSet )
        return lUniqSet
    
    getSetListWithoutDuplicates = staticmethod( getSetListWithoutDuplicates )
    
    ## Return a list of Set instances sorted in increasing order according to the Min, then the Max, and finally their initial order
    #
    # @param lSets: list of Set instances
    #
    def getSetListSortedByIncreasingMinThenMax( lSets ):
        return sorted( lSets, key=lambda iSet: ( iSet.getMin(), iSet.getMax() ) )
    
    getSetListSortedByIncreasingMinThenMax = staticmethod( getSetListSortedByIncreasingMinThenMax )
    
    ## Return a list of Set instances sorted in increasing order according to the min, then the inverse of the length, and finally their initial order
    #
    # @param lSets: list of Set instances
    #
    def getSetListSortedByIncreasingMinThenInvLength( lSets ):
        return sorted( lSets, key=lambda iSet: ( iSet.getMin(), 1 / float(iSet.getLength()) ) )
    
    getSetListSortedByIncreasingMinThenInvLength = staticmethod( getSetListSortedByIncreasingMinThenInvLength )
 
    ## Return a list of identifier lists of overlapping Sets from the subject list, according to the reference list
    #
    # @param lRef list of Set instances
    # @param lSubject list of Set instances
    #
    def getListOfIdListOfOverlappingSets(lRef,lSubject):
        lSortedRef = SetUtils.getSetListSortedByIncreasingMinThenMax( lRef )
        lSortedSubject = SetUtils.getSetListSortedByIncreasingMinThenMax( lSubject )

        lOverlappingSet = []
        lOverlappingSetCounter = 0

        id2LOverlappingSet_pos = {}
    
        i = 0
        j = 0
        while i!= len(lSortedRef):
            while j!= len(lSortedSubject) and lSortedRef[i].getMin()>lSortedSubject[j].getMax()\
                and not(lSortedRef[i].isOverlapping(lSortedSubject[j])\
                      and lSortedRef[i].isOnDirectStrand()==lSortedSubject[j].isOnDirectStrand()):
                j+=1
            jj=j
            while jj!= len(lSortedSubject) and lSortedRef[i].isOverlapping(lSortedSubject[jj])\
                  and lSortedRef[i].isOnDirectStrand()==lSortedSubject[jj].isOnDirectStrand():
                id1=lSortedRef[i].id
                id2=lSortedSubject[jj].id*-1
                if id2LOverlappingSet_pos.has_key(id1) \
                   and not id2LOverlappingSet_pos.has_key(id2):
                    lOverlappingSet[id2LOverlappingSet_pos[id1]].append(id2)
                    id2LOverlappingSet_pos[id2]=id2LOverlappingSet_pos[id1]
                if id2LOverlappingSet_pos.has_key(id2) \
                   and not id2LOverlappingSet_pos.has_key(id1):
                    lOverlappingSet[id2LOverlappingSet_pos[id2]].append(id1)
                    id2LOverlappingSet_pos[id1]=id2LOverlappingSet_pos[id2]
                if not id2LOverlappingSet_pos.has_key(id2) \
                   and not id2LOverlappingSet_pos.has_key(id1):
                    lOverlappingSet.append([id1,id2])
                    id2LOverlappingSet_pos[id1]=lOverlappingSetCounter
                    id2LOverlappingSet_pos[id2]=lOverlappingSetCounter
                    lOverlappingSetCounter+=1
                jj+=1
            i+=1
    
        return lOverlappingSet
    
    getListOfIdListOfOverlappingSets = staticmethod (getListOfIdListOfOverlappingSets)
    
    ## Return a list of sets without overlapping between two lists of sets
    #
    # @param lSet1 and lSet2 
    #
    def getListOfSetWithoutOverlappingBetweenTwoListOfSet(lSet1, lSet2):
        for i in lSet1:
            for idx,j in enumerate(lSet2):
                n=j.diff(i)
                if not n.isEmpty() and n.getLength()>=20:
                    lSet2.append(n)
        lSet2WithoutOverlaps=[]
        for i in lSet2:
            if not i.isEmpty() and i.getLength()>=20:
                lSet2WithoutOverlaps.append(i)
        return lSet2WithoutOverlaps
        
    getListOfSetWithoutOverlappingBetweenTwoListOfSet = staticmethod (getListOfSetWithoutOverlappingBetweenTwoListOfSet)

    ## Return a Set list from a Set file
    #
    # @param setFile string name of a Set file
    # @return a list of Set instances
    #
    def getSetListFromFile( setFile ):
        lSets = []
        setFileHandler = open( setFile, "r" )
        while True:
            line = setFileHandler.readline()
            if line == "":
                break
            iSet = Set()
            iSet.setFromString( line )
            lSets.append( iSet )
        setFileHandler.close()
        return lSets
    
    getSetListFromFile = staticmethod( getSetListFromFile )
    
    
    def convertSetFileIntoMapFile( setFile, mapFile ):
        setFileHandler = open( setFile, "r" )
        mapFileHandler = open( mapFile, "w" )
        iSet = Set()
        while True:
            line = setFileHandler.readline()
            if line == "":
                break
            iSet.setFromString( line )
            iMap = iSet.getMapInstance()
            iMap.write( mapFileHandler )
        setFileHandler.close()
        mapFileHandler.close()
        
    convertSetFileIntoMapFile = staticmethod( convertSetFileIntoMapFile )


    def getDictOfListsWithSeqnameAsKey( lSets ):
        dSeqnamesToSetList = {}
        for iSet in lSets:
            if not dSeqnamesToSetList.has_key( iSet.seqname ):
                dSeqnamesToSetList[ iSet.seqname ] = []
            dSeqnamesToSetList[ iSet.seqname ].append( iSet )
        return dSeqnamesToSetList
    
    getDictOfListsWithSeqnameAsKey = staticmethod( getDictOfListsWithSeqnameAsKey )
    
    
    def filterOnLength( lSets, minLength=0, maxLength=10000000000 ):
        if minLength == 0 and maxLength == 0:
            return lSets
        lFiltered = []
        for iSet in lSets:
            if minLength <= iSet.getLength() <= maxLength:
                lFiltered.append( iSet )
        return lFiltered
    
    filterOnLength = staticmethod( filterOnLength )
    
    
    def getListOfNames( setFile ):
        lNames = []
        setFileHandler = open( setFile, "r" )
        iSet = Set()
        while True:
            line = setFileHandler.readline()
            if line == "":
                break
            iSet.setFromTuple( line[:-1].split("\t") )
            if iSet.name not in lNames:
                lNames.append( iSet.name )
        setFileHandler.close()
        return lNames
    
    getListOfNames = staticmethod( getListOfNames )


    def getDictOfDictsWithNamesThenIdAsKeyFromFile( setFile ):
        dNames2DictsId = {}
        setFileHandler = open( setFile, "r" )
        while True:
            line = setFileHandler.readline()
            if line == "":
                break
            iSet = Set()
            iSet.setFromTuple( line[:-1].split("\t") )
            if not dNames2DictsId.has_key( iSet.name ):
                dNames2DictsId[ iSet.name ] = { iSet.id: [ iSet ] }
            else:
                if not dNames2DictsId[ iSet.name ].has_key( iSet.id ):
                    dNames2DictsId[ iSet.name ][ iSet.id ] = [ iSet ]
                else:
                    dNames2DictsId[ iSet.name ][ iSet.id ].append( iSet )
        setFileHandler.close()
        return dNames2DictsId
    
    getDictOfDictsWithNamesThenIdAsKeyFromFile = staticmethod( getDictOfDictsWithNamesThenIdAsKeyFromFile )
