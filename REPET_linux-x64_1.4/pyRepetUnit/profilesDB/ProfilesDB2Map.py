from pyRepetUnit.profilesDB.ProfilesDatabankUtils import ProfilesDatabankUtils


class ProfilesDB2Map ( object ):
    """
    write a file in map format from a ProfilDatabank object
    You have to set an input File and an Output File names
    """

    def __init__(self):
        self.profilesDBUtils = ProfilesDatabankUtils()
        self._inputFile = "" 
        self._outputFile =  ""    
        
    def setInputFile(self, input):
        self._inputFile = input
         
    def setOutputFile(self, output):
        self._outputFile = output   
         
    def _readProfilesDB( self ):
        pfamDB = self.profilesDBUtils.read( self._inputFile )
        return pfamDB
    
    def _writeMapFile( self, pfamDBList ):
        """
        write a file in map format from a ProfilDatabank object
        """
        if pfamDBList.getList() != []:
            f = open( self._outputFile , "w")
            for ProfilInstance in pfamDBList.getList():
                f.write(ProfilInstance.name + "\t" + ProfilInstance.desc + "\t1\t" + str(ProfilInstance.length) + "\n")
            f.close()   
    
    def run( self ):
        """
        read a profiles DB file, parse it and, write the corresponding .map file
        """
        pfamDBList = self._readProfilesDB()
        self._writeMapFile(pfamDBList)
