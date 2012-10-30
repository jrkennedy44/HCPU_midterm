import os
import pyRepetUnit.commons.coord.Align
import pyRepetUnit.align.AlignList
from pyRepetUnit.commons.utils.FileUtils import FileUtils

class AlignListUtils:  
  
    ##read a file in align format and return a AlignList
    #
    # @param inFileName string name of file
    # @return listAlignInstance list list of align instance
    #
    def read( inFileName ):
        alignInstance = pyRepetUnit.commons.coord.Align.Align() 
        listAlignInstance = pyRepetUnit.align.AlignList.AlignList()
        f = open( inFileName , "r")
        while alignInstance.read( f ):
            listAlignInstance.append(alignInstance)
            alignInstance = pyRepetUnit.commons.coord.Align.Align()
        f.close
        return (listAlignInstance)
    
    read = staticmethod( read )
    
    ## write a file in align format from an AlignList
    #
    # @param alignListInstance list list of align instance object
    # @param  inFileName string name of file
    def write( alignListInstance, inFileName ):
        f = open( inFileName , "w")
        for alignInstance in alignListInstance.getList():
            alignInstance.write( f )
        f.close
        
    write = staticmethod( write )
    
    ## Filter an AlignList by removing all is <= minScore
    #
    # @param listAlignInstance list list of align instance object
    # @param minScore integer minimum score to keep in result
    # 
    def filterOnAMinimalScore( listAlignInstance, minScore ):
        listAlignInstanceOld = pyRepetUnit.align.AlignList.AlignList() 
        for alignInstance in listAlignInstance.getList():  
            listAlignInstanceOld.append(alignInstance)
        for alignInstance in listAlignInstanceOld.getList():
            if alignInstance.score <= minScore:
                listAlignInstance.remove(alignInstance)
        
    filterOnAMinimalScore = staticmethod( filterOnAMinimalScore )    
    
if __name__ == "__main__":                 
    main() 
