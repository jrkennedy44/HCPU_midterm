import sys, re, string, cStringIO, math, random
from pyRepet.coord.Map import *
import pyRepet.seq.Bioseq
#------------------------------------------------------------------------------

class BioseqUtils:  
    
    #--------------------------------------------------------------------------
    
    def translateSequence(bioSeqInstanceToTranslate, phase=1):
        
        """
        translate a nucleotide sequence
        """
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
    
    def setFrameInfoOnHeader(bioSeqInstance, phase):
        if " " in bioSeqInstance.header:
            name, desc = bioSeqInstance.header.split(" ", 1)
            name = name + "_" + str(phase)
            bioSeqInstance.header = name + " " + desc
        else:
            bioSeqInstance.header = bioSeqInstance.header + "_" + str(phase)
            
    setFrameInfoOnHeader = staticmethod(setFrameInfoOnHeader)
    
    def replaceStopCodonsByX( bioSeqInstance ):
        bioSeqInstance.sequence = bioSeqInstance.sequence.replace ("*", "X")
            
    replaceStopCodonsByX = staticmethod(replaceStopCodonsByX)
    
    def translateInAllFrame( bioSeqInstanceToTranslate ):
        listBioseqInstances = []        
        positives = BioseqUtils._translateInPositiveFrames( bioSeqInstanceToTranslate )        
        negatives = BioseqUtils._translateInNegativeFrames( bioSeqInstanceToTranslate )         
        listAll6Frames = []
        listAll6Frames.extend(positives)
        listAll6Frames.extend(negatives)
        return listAll6Frames
    
    translateInAllFrame = staticmethod(translateInAllFrame)
    
    def _translateInNegativeFrames(bioSeqInstanceToTranslate):
        seq4 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        seq4.sequence = seq4.complement()
        BioseqUtils.setFrameInfoOnHeader(seq4, 4)
        BioseqUtils.translateSequence(seq4, 1)
        seq5 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        seq5.sequence = seq5.complement()
        BioseqUtils.setFrameInfoOnHeader(seq5, 5)
        BioseqUtils.translateSequence(seq5, 2)
        seq6 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        seq6.sequence = seq6.complement()
        BioseqUtils.setFrameInfoOnHeader(seq6, 6)
        BioseqUtils.translateSequence(seq6, 3)
        return [seq4, seq5, seq6]
    
    _translateInNegativeFrames = staticmethod( _translateInNegativeFrames )

    def _translateInPositiveFrames( bioSeqInstanceToTranslate ):
        seq1 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        BioseqUtils.setFrameInfoOnHeader(seq1, 1)
        BioseqUtils.translateSequence(seq1, 1)
        seq2 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        BioseqUtils.setFrameInfoOnHeader(seq2, 2)
        BioseqUtils.translateSequence(seq2, 2)
        seq3 = bioSeqInstanceToTranslate.copyBioseqInstance( bioSeqInstanceToTranslate )
        BioseqUtils.setFrameInfoOnHeader(seq3, 3)
        BioseqUtils.translateSequence(seq3, 3)
        return [seq1, seq2, seq3]
    
    _translateInPositiveFrames = staticmethod( _translateInPositiveFrames )    

    def translateBioseqListInAllFrames( bioseqList ):
        bioseqListInAllFrames = []
        for bioseq in bioseqList:
            bioseqListInAllFrames.extend(BioseqUtils.translateInAllFrame(bioseq))
        return bioseqListInAllFrames
    
    translateBioseqListInAllFrames = staticmethod( translateBioseqListInAllFrames )
    
    def replaceStopCodonsByXInBioseqList ( bioseqListWithStops ):
        bioseqListWithStopsreplaced = []
        for bioseq in bioseqListWithStops:
            BioseqUtils.replaceStopCodonsByX(bioseq)
            bioseqListWithStopsreplaced.append(bioseq)            
        return bioseqListWithStopsreplaced
    
    replaceStopCodonsByXInBioseqList = staticmethod( replaceStopCodonsByXInBioseqList )
    
    # FASTA Stuff ...
    def writeBioseqListIntoFastaFile( bioseqListInAllFrames, fileName ):
        fout = open(fileName, "w")
        for bioseq in bioseqListInAllFrames:
                bioseq.write(fout)       
        fout.close()
    
    writeBioseqListIntoFastaFile = staticmethod( writeBioseqListIntoFastaFile )
    
    def extractBioseqListFromFastaFile( filename ):
        file = open( filename )
        bioseqList = []
        currentHeader = ""
        while currentHeader != None:
            seq = pyRepet.seq.Bioseq.Bioseq()
            seq.read(file)
            currentHeader = seq.header
            if currentHeader != None:
                bioseqList.append(seq)
        return bioseqList
    
    extractBioseqListFromFastaFile = staticmethod( extractBioseqListFromFastaFile )
    
    def getSeqLengthWithSeqName( bioseqList, seqName ):
        length = 0
        for bioseq in bioseqList:
            if bioseq.header == seqName:
                length = bioseq.getLength()
                break        
        return length

    getSeqLengthWithSeqName = staticmethod( getSeqLengthWithSeqName )

if __name__ == "__main__":                 
    main() 



