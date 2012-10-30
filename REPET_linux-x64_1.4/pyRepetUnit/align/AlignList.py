## class of list of align object
#
class AlignList:

    list;
    
    def __init__( self ):
        self.list = []

    ## append align instance in the align instance list
    #
    # @param AlignInstance instance of align object
    #
    def append(self, AlignInstance):
        self.list.append(AlignInstance)
       
    ## get length of list of align instance
    #
    #@return length integer length of list
    #
    def len(self):
        return len(self.list)   
    
    ## get list of align instance
    #
    #@return list of align instance
    #
    def getList(self):
        return self.list
    
    ## get item in list of align instance according to index
    #
    #@param index integer index of list
    #@return align instance item of list of align instance
    #
    def get(self, index):
        return self.list[index]
    
    ## extend align instance in the align instance list
    #
    # @param AlignInstance instance of align object
    #
    def extend(self, AlignInstance):
        self.list.extend(AlignInstance)
        
    ## take off an align instance from the align instance list
    #
    # @param AlignInstance instance of align object
    #
    def remove(self, AlignInstance):
       self.list.remove(AlignInstance)