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


import math
import re
from pyRepetUnit.commons.seq.Bioseq import Bioseq

## Static methods for sequences manipulation
#
class BioseqUtils(object):
    
    ## Translate a nucleotide sequence
    #
    # @param bioSeqInstanceToTranslate a bioseq instance to translate
    # @param phase a integer : 1 (default), 2 or 3
    # 
    def translateSequence(bioSeqInstanceToTranslate, phase=1):
        pep = ""
        #length = math.floor((len(self.sequence)-phase-1)/3)*3
        length = int( math.floor( ( len(bioSeqInstanceToTranslate.sequence )-( phase-1 ) )/3 )*3 )
        #We need capital letters !
        bioSeqInstanceToTranslate.upCase() 
        sequence = bioSeqInstanceToTranslate.sequence                
        for i in xrange(phase-1,length,3):
            if (sequence[i:i+3] == "TTT" or sequence[i:i+3] == "TTC"):
                pep = pep + "F"
            elif ( sequence[i:i+3] == "TTA" or sequence[i:i+3] == "TTG" ):
                pep = pep + "L"
            elif ( sequence[i:i+2] == "CT" ):
                pep = pep + "L"
            elif ( sequence[i:i+3] == "ATT" or sequence[i:i+3] == "ATC" or sequence[i:i+3] == "ATA" ):
                pep = pep + "I"
            elif ( sequence[i:i+3] == "ATG" ):
                pep = pep + "M"
            elif ( sequence[i:i+2] == "GT" ):
                pep = pep + "V"
            elif ( sequence[i:i+2] == "TC" ) :
                pep = pep + "S"
            elif ( sequence[i:i+2] == "CC" ) :
                pep = pep + "P"
            elif ( sequence[i:i+2] == "AC" ) :
                pep = pep + "T"
            elif ( sequence[i:i+2] == "GC" ) :
                pep = pep + "A"
            elif ( sequence[i:i+3] == "TAT" or sequence[i:i+3] == "TAC" ) :
                pep = pep + "Y"
            elif ( sequence[i:i+3] == "TAA" or sequence[i:i+3] == "TAG" ) :
                pep = pep + "*"
            elif ( sequence[i:i+3] == "CAT" or sequence[i:i+3] == "CAC" ) :
                pep = pep + "H"
            elif ( sequence[i:i+3] == "CAA" or sequence[i:i+3] == "CAG" ) :
                pep = pep + "Q"
            elif ( sequence[i:i+3] == "AAT" or sequence[i:i+3] == "AAC" ) :
                pep = pep + "N"
            elif ( sequence[i:i+3] == "AAA" or sequence[i:i+3] == "AAG" ) :
                pep = pep + "K"
            elif ( sequence[i:i+3] == "GAT" or sequence[i:i+3] == "GAC" ) :
                pep = pep + "D"
            elif ( sequence[i:i+3] == "GAA" or sequence[i:i+3] == "GAG" ) :
                pep = pep + "E"
            elif ( sequence[i:i+3] == "TGT" or sequence[i:i+3] == "TGC" ) :
                pep = pep + "C"
            elif ( sequence[i:i+3] == "TGA" ) :
                pep = pep + "*"
            elif ( sequence[i:i+3] == "TGG" ) :
                pep = pep + "W"
            elif ( sequence[i:i+2] == "CG" ) :
                pep = pep + "R"
            elif ( sequence[i:i+3] == "AGT" or sequence[i:i+3] == "AGC" ) :
                pep = pep + "S"
            elif ( sequence[i:i+3] == "AGA" or sequence[i:i+3] == "AGG" ) :
                pep = pep + "R"
            elif ( sequence[i:i+2] == "GG" ):
                pep = pep + "G"
            #We don't know the amino acid because we don't have the nucleotide
            #R      Purine (A or G)
            #Y      Pyrimidine (C, T, or U)
            #M      C or A
            #K      T, U, or G
            #W      T, U, or A
            #S      C or G
            #B      C, T, U, or G (not A)
            #D      A, T, U, or G (not C)
            #H      A, T, U, or C (not G)
            #V      A, C, or G (not T, not U)
            #N      Unknown nucleotide
            elif ( re.search("N|R|Y|M|K|W|S|B|D|H|V", sequence[i:i+3])):
                pep = pep + "X"                      
        bioSeqInstanceToTranslate.sequence = pep
        
    translateSequence = staticmethod(translateSequence)
    
    ## Add the frame info in header
    #
    # @param bioSeqInstance a bioseq instance to translate
    # @param phase a integer : 1 , 2 or 3
    # 
    def setFrameInfoOnHeader(bioSeqInstance, phase):
        if " " in bioSeqInstance.header:
            name, desc = bioSeqInstance.header.split(" ", 1)
            name = name + "_" + str(phase)
            bioSeqInstance.header = name + " " + desc
        else:
            bioSeqInstance.header = bioSeqInstance.header + "_" + str(phase)
            
    setFrameInfoOnHeader = staticmethod(setFrameInfoOnHeader)
    
    ## Translate a nucleotide sequence for all frames (positives and negatives)
    #
    # @param bioSeqInstanceToTranslate a bioseq instance to translate
    #
    def translateInAllFrame( bioSeqInstanceToTranslate ):
        positives = BioseqUtils._translateInPositiveFrames( bioSeqInstanceToTranslate )        
        negatives = BioseqUtils._translateInNegativeFrames( bioSeqInstanceToTranslate )         
        listAll6Frames = []
        listAll6Frames.extend(positives)
        listAll6Frames.extend(negatives)
        return listAll6Frames
            
    translateInAllFrame = staticmethod(translateInAllFrame)
    
    ## Replace the stop codons by X in sequence
    #
    # @param bioSeqInstance a bioseq instance
    #
    def replaceStopCodonsByX( bioSeqInstance ):
        bioSeqInstance.sequence = bioSeqInstance.sequence.replace ("*", "X")
            
    replaceStopCodonsByX = staticmethod(replaceStopCodonsByX)  

    ## Translate in a list all the frames of all the bioseq of bioseq list
    #
    # @param bioseqList a list of bioseq instances
    # @return a list of translated bioseq instances
    #
    def translateBioseqListInAllFrames( bioseqList ):
        bioseqListInAllFrames = []
        for bioseq in bioseqList :
            bioseqListInAllFrames.extend(BioseqUtils.translateInAllFrame(bioseq))
        return bioseqListInAllFrames
    
    translateBioseqListInAllFrames = staticmethod( translateBioseqListInAllFrames )
    
    ## Replace the stop codons by X for each sequence of a bioseq list
    #
    # @param lBioseqWithStops a list of bioseq instances
    # @return a list of bioseq instances
    #
    def replaceStopCodonsByXInBioseqList ( lBioseqWithStops ):
        bioseqListWithStopsreplaced = []
        for bioseq in lBioseqWithStops:
            BioseqUtils.replaceStopCodonsByX(bioseq)
            bioseqListWithStopsreplaced.append(bioseq)            
        return bioseqListWithStopsreplaced
    
    replaceStopCodonsByXInBioseqList = staticmethod( replaceStopCodonsByXInBioseqList )
    
    ## Write a list of bioseq instances in a fasta file (60 characters per line)
    #
    # @param lBioseq a list of bioseq instances
    # @param fileName string
    #
    def writeBioseqListIntoFastaFile( lBioseq, fileName ):
        fout = open(fileName, "w")
        for bioseq in lBioseq:
                bioseq.write(fout)       
        fout.close()
    
    writeBioseqListIntoFastaFile = staticmethod( writeBioseqListIntoFastaFile )
    
    ## read in a fasta file and create a list of bioseq instances
    #
    # @param fileName string
    # @return a list of bioseq
    #
    def extractBioseqListFromFastaFile( fileName ):
        file = open( fileName )
        lBioseq = []
        currentHeader = ""
        while currentHeader != None:
            bioseq = Bioseq()
            bioseq.read(file)
            currentHeader = bioseq.header
            if currentHeader != None:
                lBioseq.append(bioseq)
        return lBioseq
    
    extractBioseqListFromFastaFile = staticmethod( extractBioseqListFromFastaFile )
    
    ## Give the length of a sequence search by name
    #
    # @param lBioseq a list of bioseq instances
    # @param seqName string
    # @return an integer
    #
    def getSeqLengthWithSeqName( lBioseq, seqName ):
        length = 0
        for bioseq in lBioseq:
            if bioseq.header == seqName:
                length = bioseq.getLength()
                break        
        return length

    getSeqLengthWithSeqName = staticmethod( getSeqLengthWithSeqName )

    def _translateInPositiveFrames( bioSeqInstanceToTranslate ):
        seq1 = bioSeqInstanceToTranslate.copyBioseqInstance()
        BioseqUtils.setFrameInfoOnHeader(seq1, 1)
        BioseqUtils.translateSequence(seq1, 1)
        seq2 = bioSeqInstanceToTranslate.copyBioseqInstance()
        BioseqUtils.setFrameInfoOnHeader(seq2, 2)
        BioseqUtils.translateSequence(seq2, 2)
        seq3 = bioSeqInstanceToTranslate.copyBioseqInstance()
        BioseqUtils.setFrameInfoOnHeader(seq3, 3)
        BioseqUtils.translateSequence(seq3, 3)
        return [seq1, seq2, seq3]
    
    _translateInPositiveFrames = staticmethod( _translateInPositiveFrames )
    
    def _translateInNegativeFrames(bioSeqInstanceToTranslate):
        seq4 = bioSeqInstanceToTranslate.copyBioseqInstance()
        seq4.reverseComplement()
        BioseqUtils.setFrameInfoOnHeader(seq4, 4)
        BioseqUtils.translateSequence(seq4, 1)
        seq5 = bioSeqInstanceToTranslate.copyBioseqInstance()
        seq5.reverseComplement()
        BioseqUtils.setFrameInfoOnHeader(seq5, 5)
        BioseqUtils.translateSequence(seq5, 2)
        seq6 = bioSeqInstanceToTranslate.copyBioseqInstance()
        seq6.reverseComplement()
        BioseqUtils.setFrameInfoOnHeader(seq6, 6)
        BioseqUtils.translateSequence(seq6, 3)
        return [seq4, seq5, seq6]
    
    _translateInNegativeFrames = staticmethod( _translateInNegativeFrames )
    
    
    ## Return a dictionary which keys are sequence headers and values sequence lengths.
    #
    def getLengthPerSeqFromFile( inFile ):
        dHeader2Length = {}
        inFileHandler = open( inFile, "r" )
        while True:
            iBs = Bioseq()
            iBs.read( inFileHandler )
            if iBs.sequence == None:
                break
            dHeader2Length[ iBs.header ] = iBs.getLength()
        inFileHandler.close()
        return dHeader2Length
    
    getLengthPerSeqFromFile = staticmethod( getLengthPerSeqFromFile )
    
    
    ## Return the list of Bioseq instances, these being sorted in decreasing length
    #
    def getBioseqListSortedByDecreasingLength( lBioseqs ):
        return sorted( lBioseqs, key=lambda iBs: ( iBs.getLength() ), reverse=True )
    
    getBioseqListSortedByDecreasingLength = staticmethod( getBioseqListSortedByDecreasingLength )
    
    
    ## Return the list of Bioseq instances, these being sorted in decreasing length (without gaps)
    #
    def getBioseqListSortedByDecreasingLengthWithoutGaps( lBioseqs ):
        return sorted( lBioseqs, key=lambda iBs: ( len(iBs.sequence.replace("-","")) ), reverse=True )
    
    getBioseqListSortedByDecreasingLengthWithoutGaps = staticmethod( getBioseqListSortedByDecreasingLengthWithoutGaps )
