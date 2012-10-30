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


from pyRepetUnit.commons.coord.Map import Map


## Record a named region on a given sequence with an identifier
#  
class Set( Map ):
    
    ## Constructor
    #
    # @param id identifier
    # @param name the name of the region
    # @param seqname the name of the sequence
    # @param start the start coordinate
    # @param end the end coordinate
    #
    def __init__(self, id=-1, name="", seqname="", start=-1, end=-1):
        Map.__init__( self, name, seqname, start, end )
        self.id = id
        
        
    ## Equal operator
    #    
    def __eq__(self, o):
        if self.id != o.id:
            return False
        else:
            return Map.__eq__(self, o)
        
    ## Reset
    #
    def reset(self):
        self.setFromTuple([-1, "", "", -1, -1 ])
            
    ## Set attributes from tuple
    #
    # @param tuple: a tuple with (id, name, seqname, start, end)
    # 
    def setFromTuple(self, tuple):
        self.id = int(tuple[0])
        Map.setFromTuple(self, tuple[1:])
        
    ## Return the attributes as a formatted string
    #
    def toString(self):
        string = "%i" % (self.id)
        string += "\t%s" % (Map.toString(self))
        return string
    
    ## Merge the instance with another Set instance
    #
    # @param o a Set instance
    #
    def merge(self, o):
        if self.seqname == o.seqname:
            Map.merge(self, o)
            self.id = min(self.id, o.id)
    
    ## Return a Map instance with the attributes
    #
    def getMap(self):
        return Map(self.name, self.seqname, self.start, self.end)
    
    ## Remove in the instance the region overlapping with another Set instance
    #
    # @param o a Set instance
    #  
    def diff(self, o):
        iMap = Map.diff(self, o.getMap())
        new = Set()
        if not iMap.isEmpty():
            new.id = self.id
            new.name = self.name
            new.seqname = self.seqname
            new.start = iMap.start
            new.end = iMap.end
        return new
    
    ## Return a Map instance with the identifier in the name
    #
    def set2map(self):
        return Map(self.name+"::"+str(self.id),self.seqname,self.start,self.end)
    
    
    def getMapInstance( self ):
        iMap = Map()
        lAttributes = []
        lAttributes.append( self.name )
        lAttributes.append( self.seqname )
        lAttributes.append( self.start )
        lAttributes.append( self.end )
        iMap.setFromTuple( lAttributes )
        return iMap
