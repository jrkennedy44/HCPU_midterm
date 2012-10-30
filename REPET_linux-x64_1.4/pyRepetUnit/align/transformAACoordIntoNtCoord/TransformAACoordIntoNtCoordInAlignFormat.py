import os
import sys
from pyRepetUnit.align.AlignListUtils import AlignListUtils
from pyRepetUnit.commons.seq.BioseqUtils import BioseqUtils

### Transform amino acid query coord in an align format to nucleotide coord 
### according to the frame specified at the end of seqName
#
class TransformAACoordIntoNtCoordInAlignFormat( object ):
    
    def __init__(self):
        self._inFileName = None
        self._clean = False
        self._outFileName = None
        self._consensusFileName = None
        self._IsFiltered = True

    ## read input file, transform it and write the output file
    # 
    def run(self):   
        alignUtils = AlignListUtils()         
        listAlignInstance = alignUtils.read(self._inFileName)
        self.transformQueryCoord(listAlignInstance)
        #self.getOriginalQueryNameForAlignList(listAlignInstance)
        if self._IsFiltered:
            alignUtils.filterOnAMinimalScore(listAlignInstance, 0)
        alignUtils.write(listAlignInstance, self._outFileName)
        if self._clean:
            self.clean()
    
    ## Transform the amino acid query coord into nucleotides and switch subject coord if the strand is reversed
    # @param listAlignInstance list of align object instance
    #
    def transformQueryCoord(self, listAlignInstance):
        bioseqList = BioseqUtils.extractBioseqListFromFastaFile( self._consensusFileName )
        for alignInstance in listAlignInstance.getList():
            frame = self._extractFrameFromSeqName(alignInstance)
            previousEnd = alignInstance.range_query.end                            
            previousStart = alignInstance.range_query.start
            alignInstance.range_query.seqname = self._getOriginalQueryNameForAlignInstance(alignInstance)
            if frame < 4:
                self._changeStartInAAIntoNtInPositiveFrame(alignInstance, frame, previousStart) 
                self._changeEndInAAIntoNtInPositiveFrame(alignInstance, frame, previousEnd)                
            else:
                self._checkIfSeqNameIsInDNASeqFile(bioseqList, alignInstance.range_query.seqname)
                consensusLength = BioseqUtils.getSeqLengthWithSeqName(bioseqList, alignInstance.range_query.seqname)              
                self._changeStartInAAIntoNtInNegativeFrame(alignInstance, frame, consensusLength, previousEnd)
                self._changeEndInAAIntoNtInNegativeFrame(alignInstance, frame, consensusLength, previousStart)
                self._invertedSubjectCoord(alignInstance)
    
    ## remove the input file
    #
    def clean(self):
        os.remove(self._inFileName)
        
    ## set input file name
    #
    # @param fileName string name of file
    #
    def setInFileName(self, fileName):  
        self._inFileName = fileName  
    
    ## set output file name
    #
    # @param fileName string name of file
    #
    def setOutFileName(self, fileName):  
        self._outFileName = fileName    
        
    ## set consensus file name
    #
    # @param fileName string name of file
    #
    def setConsensusFileName(self, fileName):  
        self._consensusFileName = fileName     
    
    ## set is clean will be done
    #
    # @param clean boolean clean
    #
    def setIsClean(self, clean):
        self._clean = clean
        
    ## get input file name
    #
    def getInFileName(self):
        return self._inFileName
    
    ## set is negativ score filter will be done
    #
    # @param isFiltered boolean isFiltered
    #
    def setIsFiltered(self, isFiltered):
        self._IsFiltered = isFiltered

    def _getOriginalQueryNameForAlignInstance(self, alignInstance):
        return alignInstance.range_query.seqname[0:len(alignInstance.range_query.seqname) - 2]

    def _invertedSubjectCoord(self, alignInstance):
        return alignInstance.range_subject.reverse()

    def _changeEndInAAIntoNtInPositiveFrame(self, alignInstance, frame, previousEnd):
        alignInstance.range_query.end = 3 * previousEnd + frame - 1

    def _changeStartInAAIntoNtInPositiveFrame(self, alignInstance, frame, previousStart):
        alignInstance.range_query.start = 3 * (previousStart - 1) + frame
    
    def _changeEndInAAIntoNtInNegativeFrame(self, alignInstance, frame, consensusLength, previousStart):
        alignInstance.range_query.end = consensusLength - 3 * (previousStart - 1) - frame + 4

    def _changeStartInAAIntoNtInNegativeFrame(self, alignInstance, frame, consensusLength, previousEnd):
        alignInstance.range_query.start = consensusLength - 3 * (previousEnd - 1) - frame + 2

    def _extractFrameFromSeqName(self, alignInstance):
        frame = int(alignInstance.range_query.seqname[len(alignInstance.range_query.seqname) - 1])
        return frame

    def _checkIfSeqNameIsInDNASeqFile(self, bioseqList, seqName):
        isSeqNameInBioseqList = False
        for bioseq in bioseqList:
            if seqName == bioseq.header:
                isSeqNameInBioseqList = True
        if not isSeqNameInBioseqList:
            sys.stderr.write("seqName : " + seqName + " is not in the consensus file " + self._consensusFileName + "\n")
            sys.exit(1)
    