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


from pyRepetUnit.commons.coord.Align import Align
from pyRepetUnit.commons.coord.Set import Set
from pyRepetUnit.commons.coord.Range import Range


## Handle a match between two sequences, query and subject (pair of coordinates with E-value, score and identity) with an identifier
#
class Path( Align ):
    
    ## Constructor
    #
    # @param id identifier
    # @param range_q: a Range instance for the query
    # @param range_s: a Range instance for the subject
    # @param e_value: E-value of the match 
    # @param score: score of the match
    # @param identity: identity percentage of the match
    #
    def __init__( self, id=-1, range_q=Range(), range_s=Range(), e_value=0, score=0, identity=0 ):
        self.id = int( id )
        Align.__init__( self, range_q, range_s, e_value, score, identity )
        
    ## Equal operator
    #
    def __eq__(self, o):
        if self.id != o.id:
            return False
        else:
            return Align.__eq__(self, o)
        
    ## Set attributes from tuple
    #
    # @param tuple a tuple with (id,queryName,queryStart,queryEnd,subjectName,subjectStar,subjectEnd,E-value,score,identity)
    # @note data are loaded such that the query is always on the direct strand
    #
    def setFromTuple(self, tuple):
        self.id = int(tuple[0])
        Align.setFromTuple(self, tuple[1:])
        
    ## Reset
    #
    def reset(self):
        self.id = -1
        Align.reset(self)
        
    ## Return the attributes as a formatted string
    #
    def toString(self):
        string = "%i" % ( self.id )
        string += "\t%s" % (Align.toString(self))
        return string
    
    
    ## Return the identifier of the Path instance
    #
    def getIdentifier( self ):
        return self.id
    
    ## Return a Set instance with the subject mapped on the query
    #
    def getSubjectAsSetOfQuery(self):
        iSet = Set()
        iSet.id = self.id
        iSet.name = self.range_subject.seqname
        iSet.seqname = self.range_query.seqname
        if self.range_subject.isOnDirectStrand():
            iSet.start = self.range_query.start
            iSet.end = self.range_query.end
        else:
            iSet.start = self.range_query.end
            iSet.end = self.range_query.start
        return iSet
    
    ## Return True if the instance can be merged with another Path instance, False otherwise
    #
    # @param o a Path instance
    #
    def canMerge(self, o):
        return o.id != self.id \
            and o.range_query.seqname == self.range_query.seqname \
            and o.range_subject.seqname == self.range_subject.seqname \
            and o.range_query.isOnDirectStrand() == self.range_query.isOnDirectStrand() \
            and o.range_subject.isOnDirectStrand() == self.range_subject.isOnDirectStrand() \
            and o.range_query.isOverlapping(self.range_query) \
            and o.range_subject.isOverlapping(self.range_subject)
            
    ## Return an Align instance with the same attributes, except the identifier
    #
    def getAlignInstance(self):
        iAlign = Align()
        lAttributes = []
        lAttributes.append( self.range_query.seqname )
        lAttributes.append( self.range_query.start )
        lAttributes.append( self.range_query.end )
        lAttributes.append( self.range_subject.seqname )
        lAttributes.append( self.range_subject.start )
        lAttributes.append( self.range_subject.end )
        lAttributes.append( self.e_value )
        lAttributes.append( self.score )
        lAttributes.append( self.identity )
        iAlign.setFromTuple( lAttributes )
        return iAlign
