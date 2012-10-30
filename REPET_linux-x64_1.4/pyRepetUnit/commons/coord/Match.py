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


import sys
from pyRepetUnit.commons.coord.Range import Range
from pyRepetUnit.commons.coord.Path import Path


## Handle a chain of match(es) between two sequences, query and subject, with an identifier and the length of the input sequences
#
class Match( Path ):
    
    ## Constructor
    #
    def __init__(self):
        Path.__init__(self)
        self.query_length = -1
        self.query_length_perc = -1    # length of the match on the query / length of the query
        self.query_seqlength = -1
        self.match_length_perc = -1    # length of the match on the query / total length of the subject
        self.subject_length = -1
        self.subject_length_perc = -1    # length of the match on the subject / length of the subject
        self.subject_seqlength = -1
        
    ## Equal operator
    #
    def __eq__(self, o):
        if self.query_length != o.query_length or self.query_length_perc != o.query_length_perc\
        or self.query_seqlength != o.query_seqlength or self.subject_length != o.subject_length\
        or self.subject_length_perc != o.subject_length_perc or self.subject_seqlength != o.subject_seqlength\
        or self.match_length_perc != o.match_length_perc:
            return False
        else:
            return Path.__eq__(self, o)
        
    ## Return the length of the match on the query divided by the total length of the query
    #
    def getLengthPercOnQuery(self):
        return self.query_length_perc
    
    ## Return the length of the match on the subject divided by the total length of the subject
    #
    def getLengthPercOnSubject(self):
        return self.subject_length_perc
    
    ## Return the length of the match on the subject
    #
    def getLengthMatchOnSubject(self):
        return self.subject_length
    
    ## Set attributes from a tuple
    # 
    # @param tuple: a tuple with (query name,query start,query end,
    #  query length, query length perc (between 0-1), match length perc (between 0-1), subject name,
    #  subject start,subject end,subject length, subject length percentage (between 0-1), e_value,score,identity,id)
    #
    def setFromTuple( self, tuple ):
        queryStart = int(tuple[1])
        queryEnd = int(tuple[2])
        subjectStart = int(tuple[7])
        subjectEnd = int(tuple[8])
        if queryStart < queryEnd:
            self.range_query = Range(tuple[0],queryStart,queryEnd)
            self.range_subject = Range(tuple[6],subjectStart,subjectEnd)
        else:
            self.range_query = Range(tuple[0],queryEnd,queryStart)
            self.range_subject = Range(tuple[6],subjectEnd,subjectStart)
        self.query_length = int(tuple[3])
        self.query_length_perc = float(tuple[4])
        self.query_seqlength = int( self.query_length / self.query_length_perc )
        self.match_length_perc = float(tuple[5])
        self.subject_length = int(tuple[9])
        self.subject_length_perc = float(tuple[10])
        self.subject_seqlength = int( self.subject_length / self.subject_length_perc )
        self.e_value = float(tuple[11])
        self.score = float(tuple[12])
        self.identity = float(tuple[13])
        self.id = int(tuple[14])
        
    ## Reset
    #
    def reset( self ):
        Path.reset( self )
        self.query_length = -1
        self.query_length_perc = -1
        self.query_seqlength = -1
        self.match_length_perc = -1
        self.subject_length = -1
        self.subject_length_perc = -1
        self.subject_seqlength = -1
        
    ## Return a formated string of the attribute data
    # 
    def toString( self ):
        string = "%s" % ( self.range_query.toString() )
        string += "\t%i\t%f" % ( self.query_length,
                                     self.query_length_perc )
        string += "\t%f" % ( self.match_length_perc )
        string += "\t%s" % ( self.range_subject.toString() )
        string += "\t%i\t%f" % ( self.subject_length,
                                 self.subject_length_perc )
        string += "\t%g\t%i\t%f" % ( self.e_value,
                                     self.score,
                                     self.identity )
        string += "\t%i" % ( self.id )
        return string
    
    ## Return a Path instance
    #
    def getPathInstance( self ):
        p = Path()
        tuple = ( self.id,
                  self.range_query.seqname,
                  self.range_query.start,
                  self.range_query.end,
                  self.range_subject.seqname,
                  self.range_subject.start,
                  self.range_subject.end,
                  self.e_value,
                  self.score,
                  self.identity )
        p.setFromTuple( tuple )
        return p
    
    ## Give information about a match whose query is included in the subject
    # 
    # @return string
    #
    def getQryIsIncluded( self ):
        string = "query %s (%d bp: %d-%d) is contained in subject %s (%d bp: %d-%d): id=%.2f - %.3f - %.3f - %.3f" %\
                 ( self.range_query.seqname, self.query_seqlength, self.range_query.start, self.range_query.end,
                   self.range_subject.seqname, self.subject_seqlength, self.range_subject.start, self.range_subject.end,
                   self.identity, self.query_length_perc, self.match_length_perc, self.subject_length_perc )
        return string
    
    ## Compare the object with another match and see if they are equal
    # (same identity, E-value and score + same subsequences whether in query or subject)
    #
    # @return True if objects are equals False otherwise
    #
    def isDoublonWith( self, match, verbose=0 ):

        # if both matches have same identity, score and E-value
        if self.identity == match.identity and self.score == match.score and self.e_value == match.e_value:

            # if query and subject are identical
            if ( self.range_query.seqname == match.range_query.seqname \
                 and self.range_subject.seqname == match.range_subject.seqname ):

                # if the coordinates are equal
                if self.range_query.__eq__( match.range_query ) and self.range_subject.__eq__( match.range_subject ):
                    return True

                else:
                    if verbose > 0: print "different coordinates"; sys.stdout.flush()
                    return False

            # if query and subject are reversed but identical
            elif self.range_query.seqname == match.range_subject.seqname and self.range_subject.seqname == match.range_query.seqname:

                # if the coordinates are equal
                if self.range_query.__eq__( match.range_subject ) and self.range_subject.__eq__( match.range_query ):
                    return True

                else:
                    if verbose > 0: print "different coordinates"; sys.stdout.flush()
                    return False

            else:
                if verbose > 0: print "different sequence names"; sys.stdout.flush()
                return False

        else:
            if verbose > 0: print "different match numbers"; sys.stdout.flush()
            return False
