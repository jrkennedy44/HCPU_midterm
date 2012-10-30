import os
from pyRepetUnit.hmmer.hmmOutput.HmmOutput import HmmOutput

##Concrete implementation for hmmscan and  hmmpfam output methods
#
class HmmOutputProcessing (object):
   
    ## write a align file from a HmmOutput object
    #
    # @param fout handle of align file
    # @param HmmOutput HmmOutput object in fact a list of hmmOutput containing datas required
    #        
    def writeHmmOutputToAlignFile( self, pfamOutput, fout ):    
        for item in pfamOutput.getList():
            for i in item:
                fout.write(i + "\t")
            fout.write("0\n")
    
    ## read an output file from hmm profiles search program and write the corresponding .align file
    #
    # @param inputFile file
    # @param outputFile file
    #
    def readHmmOutputsAndWriteAlignFile( self, inputFile, outputFile ):
        if not os.path.exists(inputFile):
            print "Warning your input file " + inputFile + " does not exist!\n"
            return
        file2parse = open( inputFile )
        pfamOutput = HmmOutput()
        if outputFile == "":
            print "Warning have to specify an output name file!\n"
            return
        fout = open(outputFile, "w")        
        while pfamOutput != None:      
            pfamOutput = self.readHmmOutput(file2parse)             
            if pfamOutput != None:  
                self.writeHmmOutputToAlignFile(pfamOutput, fout)
        fout.close()
        file2parse.close() 
