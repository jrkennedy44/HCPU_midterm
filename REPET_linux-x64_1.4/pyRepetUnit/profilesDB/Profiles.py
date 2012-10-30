import re

#------------------------------------------------------------------------------

class Profiles:
    '''
    Hmm profile Class
    Attributes are name, desc, length, accNumber, GA_cut_off and retrieve
    '''
    
    #--------------------------------------------------------------------------

    def __init__( self, name="", desc="", length=0, accNumber = "", GA_cut_off = 0, retrieve = False ):
        self.name = name
        self.desc = desc
        self.length = length
        self.accNumber = accNumber
        self.GA_cut_off = GA_cut_off
        self.retrieve = retrieve
        self.tab_profile = []
        
    #--------------------------------------------------------------------------

    def _noProfileInFile(self):
        self.name = None
        self.desc = None
        self.length = None
        self.accNumber = None
        self.GA_cut_off = None

    #--------------------------------------------------------------------------

    def _initialisation(self):
        self.name = ""
        self.desc = ""
        self.length = 0
        self.accNumber = ""
        GA_cut_off = 0
        self.tab_profile = []
        
    #--------------------------------------------------------------------------

    def read( self, hmmFile ):
        '''
        Read a profile and characterize the object profile
        attributes name, length, desc, accNumber and GA_cut_off are specified
        '''
        line = hmmFile.readline()
        if line == "":
            self._noProfileInFile()
            return
        self._initialisation()
        if self.retrieve:
            self.tab_profile.append(line)        
        while not re.match("\/\/.*", line):            
            line = hmmFile.readline()
            if self.retrieve:
                self.tab_profile.append(line)                  
            name = re.match("NAME\s*(.*)", line)
            if name:                    
                self.name = name.group(1)
            desc = re.match("DESC\s*(.*)", line)
            if desc:                    
                self.desc = desc.group(1)
            length = re.match("LENG\s*(.*)", line)
            if length:                    
                self.length = int(length.group(1))
            accNumber = re.match("ACC\s*(.*)", line)
            if accNumber:                    
                self.accNumber = accNumber.group(1)
            GA_cut_off = re.match("GA\s*\d*\.\d*\s*(.*);", line)
            if GA_cut_off:                    
                self.GA_cut_off = float(GA_cut_off.group(1))
            else : 
                if (self.GA_cut_off == 0):
                    self.GA_cut_off = "NA"
        if self.retrieve:
            return self.tab_profile
        else:
            return 1
            
    #--------------------------------------------------------------------------

    def readAndRetrieve( self, hmmFile ):  
        '''
        Read a profile and characterize the object profile
        attributes name, length, desc, accNumber and GA_cut_off are specified
        And a list of each line of profile is returned
        '''
        self.retrieve = True
        return self.read(hmmFile)
