import sys
from pyRepet.coord.Range import *
from pyRepet.coord.Align import *

#------------------------------------------------------------------------------

class Match( Align ):

    """
    Record a match summary.

    @ivar query_length: match length on the query sequence
    @type query_length: integer
    @ivar query_length_perc: match length percentage on the query sequence
    @type query_length_perc: float

    @ivar subject_length: match length on the subject sequence
    @type subject_length: integer
    @ivar subject_length_perc: match length percentage on the subject sequence
    @type subject_length_perc: float

    @ivar match_length_perc: subject over query match length ratio
    @type match_length_perc: float
    """

    #--------------------------------------------------------------------------

    def __init__( self ):

        """
        Constructor
        """

        Align.__init__( self )

        self.query_length = -1
        self.query_length_perc = -1    # length of the match on the query / length of the query
        self.query_seqlength = -1

        self.match_length_perc = -1    # length of the match on the query / total length of the subject

        self.subject_length = -1
        self.subject_length_perc = -1
        self.subject_seqlength = -1

    #--------------------------------------------------------------------------

    def read( self, inFile ):

        """
        Read attribute data from a 'tab' file.

        @param file: file identifier of the file being read
        @type file: file identifier
        @return: 0 on success, 1 otherwise (e.g. at the end of the file)
        """

        line = inFile.readline()
        print line
        if line == "":
            return 1
        if not line[0:5] == "query":
            data = line.split("\t")
            print data
            self.set_from_tuple( data )
            return 0

    #--------------------------------------------------------------------------

    def set_from_tuple( self, tuple ):

        """
        Set attribute data from a tuple.

        @param tuple: a tuple with (query name,query start,query end,
        query length, query length perc, match length perc, subject name,
        subject start,subject end,e_value,score,identity,id)
        @type tuple: python tuple
        """

        start_q = int(tuple[1])
        end_q = int(tuple[2])
        start_s = int(tuple[7])
        end_s = int(tuple[8])
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
        if start_q < end_q:
            self.range_query = Range(tuple[0],start_q,end_q)
            self.range_subject = Range(tuple[6],start_s,end_s)
        else:
            self.range_query = Range(tuple[0],end_q,start_q)
            self.range_subject = Range(tuple[6],end_s,start_s)

    #--------------------------------------------------------------------------

    def toString( self ):

        """
        Return a formated string of the attribute data.
        """

        string = "%s\t%d\t%d\t%d\t%f\t%f\t%s\t%d\t%d\t%d\t%f\t%lf\t%d\t%f\t%d"%\
                 ( self.range_query.seqname,\
                   self.range_query.start,\
                   self.range_query.end,\
                   self.query_length,\
                   self.query_length_perc,\
                   self.match_length_perc,\
                   self.range_subject.seqname,\
                   self.range_subject.start,\
                   self.range_subject.end,\
                   self.subject_length,\
                   self.subject_length_perc,\
                   self.e_value,self.score,self.identity,\
                   self.id)
        return string

    #--------------------------------------------------------------------------

    def getQryIsIncluded( self ):

        """
        Return information about a match whose query is included in the subject.
        """

        string = "query %s (%d bp: %d-%d) is contained in subject %s (%d bp: %d-%d): id=%.2f - %.3f - %.3f - %.3f" %\
                 ( self.range_query.seqname, self.query_seqlength, self.range_query.start, self.range_query.end,
                   self.range_subject.seqname, self.subject_seqlength, self.range_subject.start, self.range_subject.end,
                   self.identity, self.query_length_perc, self.match_length_perc, self.subject_length_perc )
        return string

    #--------------------------------------------------------------------------

    def isDoublonWith( self, match, verbose=0 ):

        """
        Compare the object with another match and see if they are equal (same identity, E-value and score + same subsequences whether in query or subject).

        @return: True or False
        @rtype: boolean
        """

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
