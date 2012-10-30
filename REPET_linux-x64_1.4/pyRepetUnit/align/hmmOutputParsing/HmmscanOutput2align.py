from pyRepetUnit.hmmer.hmmOutput.HmmscanOutputProcessing import HmmscanOutputProcessing
##data processor : read an output from hmmscan and transform it into .align file
#
class HmmscanOutput2align( object ):
    
    ## constructor
    #
    def __init__(self):
        self.hmmscanOutputProcess = HmmscanOutputProcessing()
        self._inputFile = "" 
        self._outputFile =  ""    
     
    ## set input file
    #
    # @param input file input file
    #    
    def setInputFile(self, input):
        self._inputFile = input
    ## set output file
    # @param output file output file
    #     
    def setOutputFile(self, output):
        self._outputFile = output   
    
    ##read a hmmscan output file, parse it and, write the corresponding .align file
    #    
    def run( self ):
        self.hmmscanOutputProcess.readHmmOutputsAndWriteAlignFile( self._inputFile, self._outputFile )
