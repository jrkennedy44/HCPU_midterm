## List of Hmmpfam or Hmmscan Output (that are too lists).
#
class HmmOutput( object ):
   
    list;
    
    def __init__( self ):
        self._hmmpfamOutput = []
    
    ## append an output in the list of output
    #    
    # @param list name of the list  
    #
    def append( self, list ):
        self._hmmpfamOutput.append(list)
    
    ## return the length of the list of output
    def len (self):
        return len(self._hmmpfamOutput)
    
    ## return the output corresponding at the element number index in the list of output
    # 
    # @param index number of index
    # 
    def get(self, index):
        return self._hmmpfamOutput[index]
    
    ## return the list of output
    def getList(self):
        return self._hmmpfamOutput
