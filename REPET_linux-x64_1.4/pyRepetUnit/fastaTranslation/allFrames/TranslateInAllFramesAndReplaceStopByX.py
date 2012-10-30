import os
import pyRepet.seq.Bioseq
import pyRepet.seq.BioseqUtils 
from pyRepet.util.file.FileUtils import FileUtils


class TranslateInAllFramesAndReplaceStopByX( object ):

    def __init__(self):
        self.fileUtils = FileUtils()
        self.bioseq = pyRepet.seq.Bioseq.Bioseq()
        self._inputFile = "" 
        self._outputFile =  ""
        self._bioseqUtils =  pyRepet.seq.BioseqUtils.BioseqUtils
    
    def setInputFile(self, input):
        self._inputFile = input

    def setOutputFile(self, output):
        self._outputFile = output    
        
    def run(self):
        """
        read a fasta file with nucleotide sequences and translate all sequences in all frames, write the result in a file
        """
        if not self.fileUtils.isRessourceExists(self._inputFile):
            print "Warning your input file " + self._inputFile + " does not exist!\n"
            return
        bioseqList = self._bioseqUtils.extractBioseqListFromFastaFile(self._inputFile)
        # translate in All frames
        bioseqListInAllFrames = self._bioseqUtils.translateBioseqListInAllFrames(bioseqList)
        #replace Stops by X
        bioseqListTranslatedAndStopsReplace = self._bioseqUtils.replaceStopCodonsByXInBioseqList( bioseqListInAllFrames )
        # write in a file
        self._bioseqUtils.writeBioseqListIntoFastaFile(bioseqListTranslatedAndStopsReplace, self._outputFile)   
                