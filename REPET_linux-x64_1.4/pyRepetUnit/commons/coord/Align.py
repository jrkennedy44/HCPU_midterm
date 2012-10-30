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

import time

from pyRepetUnit.commons.coord.Range import Range
from pyRepetUnit.commons.coord.Map import Map


## Handle a match between two sequences, query and subject (pair of coordinates with E-value, score and identity)
#
class Align( object ):
    
    ## Constructor
    #
    # @param range_q: a Range instance for the query
    # @param range_s: a Range instance for the subject
    # @param e_value: E-value of the match 
    # @param identity: identity percentage of the match
    # @param score: score of the match
    #
    def __init__(self, range_q=Range(), range_s=Range(), e_value=0, identity=0, score=0):
        self.range_query = range_q
        self.range_subject = range_s
        self.e_value = float(e_value)
        self.score = int(score)
        self.identity = float(identity)
       
    ## Return True if the instance is empty, False otherwise
    #
    def isEmpty(self):
        return self.range_query.isEmpty() or self.range_subject.isEmpty()
        
    ## Equal operator
    #
    def __eq__(self, o):
        if self.range_query==o.range_query and self.range_subject==o.range_subject and \
        self.e_value==o.e_value and self.score==o.score and self.identity==o.identity:
            return True
        return False
    
    ## Unequal operator
    #
    # @param o a Range instance
    #
    def __ne__(self, o):
        return not self.__eq__(o)
    
    ## Convert the object into a string
    #
    # @note used in 'print myObject'
    #
    def __str__( self ):
        return self.toString()
    
    ## Read attributes from an Align file
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
    
    ## Set attributes from tuple
    #
    # @param tuple a tuple with (queryName,queryStart,queryEnd,subjectName,subjectStar,subjectEnd,E-value,score,identity)
    # @note data are loaded such that the query is always on the direct strand
    #
    def setFromTuple( self, tuple ):
        #TODO: we need to create Range instances because of __eq__() and isEmpty() tests, but WHY ???
        self.range_query = Range()
        self.range_subject = Range()
        if int(tuple[1]) < int(tuple[2]):
            self.range_query.setFromTuple( ( tuple[0], tuple[1], tuple[2] ) )
            self.range_subject.setFromTuple( ( tuple[3], tuple[4], tuple[5] ) )
        else:
            self.range_query.setFromTuple( ( tuple[0], tuple[2], tuple[1] ) )
            self.range_subject.setFromTuple( ( tuple[3], tuple[5], tuple[4] ) )
        self.e_value = float(tuple[6])
        self.score = float(tuple[7])
        self.identity = float(tuple[8])
        
    ## Reset
    #
    def reset( self ):
        self.range_query.reset()
        self.range_subject.reset()
        self.e_value = 0
        self.score = 0
        self.identity = 0
        
    ## Return the attributes as a formatted string
    #
    def toString(self):
        string = "%s" % ( self.range_query.toString() )
        string += "\t%s" % ( self.range_subject.toString() )
        string += "\t%g\t%i\t%f" % ( self.e_value, self.score, self.identity )
        return string
    
    
    ## Return the attributes as a GFF-formatted string
    #
    def toStringAsGff( self, source="REPET", type="match", phase=".", ID="", Parent="" ):
        if not self.isSubjectOnDirectStrand():
            self.reverse()
        string = "%s" % ( self.getQueryName() )
        string += "\t%s" % ( source )
        string += "\t%s" % ( type )
        string += "\t%s" % ( self.getQueryMin() )
        string += "\t%s" % ( self.getQueryMax() )
        string += "\t%g" % ( self.e_value )
        string += "\t%s" % ( self.getQueryStrand() )
        string += "\t%s" % ( phase )
        attributes = ""
        if ID != "":
            attributes += "ID=%s" % ( ID )
        else:
            attributes += "ID=%i" % ( str(time.time())[-8:-1].replace(".","") )
        if Parent != "":
            attributes += ";Parent=%s" % ( Parent )
        attributes += ";Target=%s %i %i" % ( self.getSubjectName(), self.getSubjectStart(), self.getSubjectEnd() )
        string += "\t%s" % ( attributes )
        return string
    
    
    ## Reverse query and subject
    #
    def reverse(self):
        self.range_query.reverse()
        self.range_subject.reverse()
        
    ## Show the attributes
    #
    def show(self):
        print self.toString()
 
    ## Write attributes into an Align file
    #
    # @param fileHandler: file handler of the file being filled
    #
    def write(self, fileHandler):
        fileHandler.write("%s\n" % (self.toString()))
        
    ## Save attributes into an Align file
    #
    # @param file: name of the file being filled
    #
    def save(self, file):
        fileHandler = open( file, "a" )
        self.write( fileHandler )
        fileHandler.close()
        
    ## Return the score
    #
    def getScore(self):
        return self.score

    ## Return the identity
    #
    def getIdentity(self):
        return self.identity
    
    def getEvalue(self):
        return self.e_value
    
    ## Return the length on the query
    #
    def getLengthOnQuery(self):
        return self.range_query.getLength()
    
    ## Return the name of the query
    #
    def getQueryName( self ):
        return self.range_query.seqname
    
    ## Return the start of the query
    #
    def getQueryStart( self ):
        return self.range_query.start
    
    ## Return the end of the query
    #
    def getQueryEnd( self ):
        return self.range_query.end
    
    ## Return the min of the query
    #
    def getQueryMin( self ):
        return self.range_query.getMin()
    
    ## Return the max of the query
    #
    def getQueryMax( self ):
        return self.range_query.getMax()
    
    ## Return the strand of the query
    #
    def getQueryStrand( self ):
        return self.range_query.getStrand()
    
    ## Return the name of the subject
    #
    def getSubjectName( self ):
        return self.range_subject.seqname
    
    ## Return the start of the subject
    #
    def getSubjectStart( self ):
        return self.range_subject.start
    
    ## Return the end of the subject
    #
    def getSubjectEnd( self ):
        return self.range_subject.end
    
    ## Return the strand of the subject
    #
    def getSubjectStrand( self ):
        return self.range_subject.getStrand()
    
    ## Return the query as a Range instance
    #
    def getQueryAsRange( self ):
        return self.range_query
    
    ## Return the subject as a Range instance
    #
    def getSubjectAsRange( self ):
        return self.range_subject
    
    ## Set the name of the query
    #
    def setQueryName( self, name ):
        self.range_query.seqname = name
        
    ## Set the start of the query
    #
    def setQueryStart( self, start ):
        self.range_query.start = start
        
    ## Set the end of the query
    #
    def setQueryEnd( self, end ):
        self.range_query.end = end
    
    ## Set the name of the subject
    #
    def setSubjectName( self, name ):
        self.range_subject.seqname = name
        
    ## Set the start of the subject
    #
    def setSubjectStart( self, start ):
        self.range_subject.start = start
        
    ## Set the end of the subject
    #
    def setSubjectEnd( self, end ):
        self.range_subject.end = end
        
    ## Merge the instance with another Align instance
    #
    # @param o an Align instance
    #
    def merge(self, o):
        if self.range_query.seqname != o.range_query.seqname \
               or self.range_subject.seqname != o.range_subject.seqname:
            return
        self.range_query.merge(o.range_query)
        self.range_subject.merge(o.range_subject)
        self.score = max(self.score,o.score)
        self.e_value = min(self.e_value,o.e_value)
        self.identity = max(self.identity,o.identity)
        
    ## Return a Map instance with the subject mapped on the query
    #
    def getSubjectAsMapOfQuery(self):
        iMap = Map()
        iMap.name = self.range_subject.seqname
        iMap.seqname = self.range_query.seqname
        if self.range_subject.isOnDirectStrand():
            iMap.start = self.range_query.start
            iMap.end = self.range_query.end
        else:
            iMap.start = self.range_query.end
            iMap.end = self.range_query.start
        return iMap
    
    ## Return True if query is on direct strand
    #
    def isQueryOnDirectStrand( self ):
        return self.range_query.isOnDirectStrand()
    
    ## Return True if subject is on direct strand
    #
    def isSubjectOnDirectStrand( self ):
        return self.range_subject.isOnDirectStrand()
    
    ## Return True if query and subject are on the same strand, False otherwise
    #
    def areQrySbjOnSameStrand(self):
        return self.isQueryOnDirectStrand() == self.isSubjectOnDirectStrand()
    
    ## Return False if query and subject are on the same strand, True otherwise
    #
    def areQrySbjOnOppositeStrands(self):
        return not self.areQrySbjOnSameStrand()

    ## Set attributes from string
    #
    # @param string a string formatted like queryName queryStart queryEnd subjectName subjectStart subjectEnd E-value score identity
    # @param sep field separator
    #
    def setFromString(self, string, sep="\t"):
        if string[-1] == "\n":
            string = string[:-1]
        self.setFromTuple( string.split(sep) )
        
    ## Return a first Map instance for the query and a second for the subject
    #
    def getMapsOfQueryAndSubject(self):
        iMapQuery = Map( name="repet",
                         seqname=self.range_query.seqname,
                         start=self.range_query.start,
                         end=self.range_query.end )
        iMapSubject = Map( name="repet",
                         seqname=self.range_subject.seqname,
                         start=self.range_subject.start,
                         end=self.range_subject.end )
        return iMapQuery, iMapSubject
    
    ## Write query coordinates as Map in a file
    #
    # @param fileHandler: file handler of the file being filled
    #
    def writeSubjectAsMapOfQuery( self, fileHandler ):
        m = self.getSubjectAsMapOfQuery()
        m.write( fileHandler )
        
    ## Return a bin for fast database access
    #
    def getBin(self):
        return self.range_query.getBin()
    
    ## Switch query and subject
    #
    def switchQuerySubject( self ):
        tmpRange = self.range_query
        self.range_query = self.range_subject
        self.range_subject = tmpRange
        if not self.isQueryOnDirectStrand():
            self.reverse()
            
    ## Return True if the query overlaps with the query of another Align instance, False otherwise
    #
    def isQueryOverlapping( self, iAlign ):
        return self.getQueryAsRange().isOverlapping( iAlign.getQueryAsRange() )
    
    ## Return True if the subject overlaps with the subject of another Align instance, False otherwise
    #
    def isSubjectOverlapping( self, iAlign ):
        return self.getSubjectAsRange().isOverlapping( iAlign.getSubjectAsRange() )
    
    ## Return True if the Align instance overlaps with another Align instance, False otherwise
    #
    def isOverlapping( self, iAlign ):
        if self.isQueryOverlapping( iAlign ) and self.isSubjectOverlapping( iAlign ):
            return True
        else:
            return False
        
    ## Update the score
    #
    # @note the new score is the length on the query times the percentage of identity
    #
    def updateScore( self ):
        newScore = self.getLengthOnQuery() * self.getIdentity() / 100.0
        self.score = newScore
