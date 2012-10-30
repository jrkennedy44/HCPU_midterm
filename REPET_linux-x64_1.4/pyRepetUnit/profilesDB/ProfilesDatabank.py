class ProfilesDatabank:
    
    """
    List of profiles objects.
    """
    
    list;
    
    def __init__( self ):
        self._profilesDatabank = []
    
    def append( self, list ):
       self._profilesDatabank.append(list)
       
    def len (self):
        return len(self._profilesDatabank)
    
    def get(self, index):
        return self._profilesDatabank[index]
    
    def getList(self):
        return self._profilesDatabank