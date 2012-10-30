# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


from pyRepetUnit.commons.coord.Range import Range


## Record a named region on a given sequence
#
class Map( Range ):
    
    ## Constructor
    #
    # @param name the name of the region
    # @param seqname the name of the sequence
    # @param start the start coordinate
    # @param end the end coordinate
    # 
    def __init__(self, name="", seqname="", start=-1, end=-1):
        self.name = name
        Range.__init__( self, seqname, start, end )
        
    ## Equal operator
    #
    # @param o a Map instance
    #    
    def __eq__(self, o):
        if self.name == o.name:
            return Range.__eq__(self, o)
        return False
    
    ## Return name
    #
    def getName( self ):
        return self.name
    
    ## Set attributes from tuple
    #
    # @param tuple: a tuple with (name,seqname,start,end)
    # 
    def setFromTuple(self, tuple):
        self.name = tuple[0]
        Range.setFromTuple(self, tuple[1:])
    
    ## Set attributes from string
    #
    # @param string a string formatted like name<sep>seqname<sep>start<sep>end
    # @param sep field separator
    #
    def setFromString(self, string, sep="\t"):
        if string[-1] == "\n":
            string = string[:-1]
        self.setFromTuple( string.split(sep) )
        
    ## Reset
    #
    def reset(self):
        self.setFromTuple( [ "", "", -1, -1 ] )
        
    ## Read attributes from a Map file
    # 
    # @param fileHandler: file handler of the file being read
    # @return: 1 on success, 0 at the end of the file
    #
    def read(self, fileHandler):
        self.reset()
        line = fileHandler.readline()
        if line == "":
            return 0
        tokens = line.split("\t")
        if len(tokens) < len(self.__dict__.keys()):
            return 0
        self.setFromTuple(tokens)
        return 1
    
    ## Return the attributes as a formatted string
    #
    def toString(self):
        string = "%s" % (self.name)
        string += "\t%s" % (Range.toString(self))
        return string
    
    ## Write attributes into a Map file
    #
    # @param fileHandler: file handler of the file being filled
    #
    def write(self, fileHandler):
        fileHandler.write("%s\n" % (self.toString()))
        
    ## Save attributes into a Map file
    #
    # @param file: name of the file being filled
    #
    def save(self, file):
        fileHandler = open( file, "a" )
        self.write( fileHandler )
        fileHandler.close()
        
    ## Return a Range instance with the attributes
    #
    def getRange(self):
        return Range( self.seqname, self.start, self.end)
    
    ## Remove in the instance the region overlapping with another Map instance
    #
    # @param o a Map instance
    # 
    def diff(self, o):
        iRange = Range.diff(self, o.getRange())
        new = Map()
        if not iRange.isEmpty():
            new.name = self.name
            new.seqname = self.seqname
            new.start = iRange.start
            new.end = iRange.end
        return new
    
    ## Write attributes in a Path file, the name being the subject and the rest the Range query
    #
    # @param fileHandler: file handler of a Path file
    #
    def writeAsQueryOfPath(self, fileHandler):
        string = "0"
        string += "\t%s" % ( self.seqname )
        string += "\t%i" % ( self.getMin() )
        string += "\t%i" % ( self.getMax() )
        string += "\t%s" % ( self.name )
        string += "\t0"
        string += "\t0"
        string += "\t0.0"
        string += "\t0"
        string += "\t0"
        fileHandler.write( "%s\n" % ( string ) )
