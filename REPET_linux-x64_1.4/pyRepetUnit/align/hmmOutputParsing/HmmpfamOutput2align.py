from pyRepetUnit.hmmer.hmmOutput.HmmpfamOutputProcessing import HmmpfamOutputProcessing

##data processor : read an output from hmmpfam and transform it into .align file
#    
class HmmpfamOutput2align( object ):

    ## constructor
    #
    def __init__(self):
        self.hmmpfamOutputProcess = HmmpfamOutputProcessing()
        self._inputFile = "" 
        self._outputFile =  ""    
    
    ## set input file
    #
    # @param input file input file
    #    
    def setInputFile(self, input):
        self._inputFile = input
    
    ## set output file
    #
    # @param output file output file
    #         
    def setOutputFile(self, output):
        self._outputFile = output   
    
    
    ##read a hmmpfam output file, parse it and, write the corresponding .align file
    #
    def run( self ):
        self.hmmpfamOutputProcess.readHmmOutputsAndWriteAlignFile( self._inputFile, self._outputFile )
