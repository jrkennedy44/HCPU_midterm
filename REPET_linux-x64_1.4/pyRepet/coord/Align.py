from pyRepet.coord.Range import *
import re

#------------------------------------------------------------------------------

class Align:

    """
    Record a match between two subsequences: a query and a subject

    @ivar range_query: the range on the query sequence
    @type range_query: class L{Range<Range>}

    @ivar range_subject: the range on the subject sequence
    @type range_subject: class L{Range<Range>}

    @ivar score: the match score
    @type score: numeric

    @ivar e_value: the match E-value
    @type e_value: float

    @ivar identity: the identity percentage between the 2 subsequences
    @type identity: float

    @ivar id: identifier number
    @type id: integer
    """

    #--------------------------------------------------------------------------

    def __init__(self,range_q=Range(),range_s=Range(),e_value=0,identity=0,score=0):
        """
        constructor
        
        @param range_q: query range
        @type range_q: class L{Range<Range>}

        @param range_s: subject range
        @type range_s: class L{Range<Range>}

        @param e_value: the match E-value
        @type e_value: float
        
        @param identity: the identity percentage between the 2 subsequences
        @type identity: float
        """

        self.range_query = range_q
        self.range_subject = range_s
        self.identity = identity
        self.score = score
        self.e_value = e_value
        self.id = -1

    #--------------------------------------------------------------------------

    def __lt__(self,o):

        """
        less than operator

        sort according first by query range 
        """

        if self.range_query<o.range_query:
            return True
        elif self.range_query==o.range_query \
                 and self.range_subject<o.range_subject:
            return True
        return False

    #--------------------------------------------------------------------------

    def __le__(self,o):

        """
        less or equal operator

        sort according first by query range 
        """

        if self.range_query<o.range_query:
            return True
        elif self.range_query==o.range_query \
                 and self.range_subject<=o.range_subject:
            return True
        return False

    #--------------------------------------------------------------------------

    def __gt__(self,o):

        """
        greater than operator

        sort according first by query range 
        """

        if self.range_query>o.range_query:
            return True
        elif self.range_query==o.range_query \
                 and self.range_subject>o.range_subject:
            return True
        return False

    #--------------------------------------------------------------------------

    def __ge__(self,o):

        """
        greater or equal operator

        sort according first by query range 
        """
        
        if self.range_query>o.range_query:
            return True
        elif self.range_query==o.range_query \
                 and self.range_subject>=o.range_subject:
            return True
        return False

    #--------------------------------------------------------------------------

    def read(self,file):

        """
        read attribute data from a align file

        @param file: file identifier of the file being read
        @type file: file identifier
        @return: 1 on success, 0 at the end of the file 
        """

        line=file.readline()
        if line=="":
            return 0      
        liste=line.split("\t")
        self.set_from_tuple(liste)
        return 1

    #--------------------------------------------------------------------------

    def set_from_tuple(self,tuple):

        """
        set attribute data from a tuple

        @param tuple: a tuple with (dummy,query name,query start,query end,
        subject name,subject start,subject end,e_value,score,identity)
        @type tuple: python tuple
        """

        start_q=int(tuple[1])
        start_s=int(tuple[4])
        end_q=int(tuple[2])
        end_s=int(tuple[5])
        if len(tuple)>6:
            if not re.match("NA", tuple[6]):
                self.e_value=float(tuple[6])
            if not re.match("NA", tuple[7]):
                self.score=float(tuple[7])
            if not re.match("NA", tuple[8]):
                self.identity=float(tuple[8])
##         if start_s<end_s:
##             self.range_query=Range(tuple[0],start_q,end_q)
##             self.range_subject=Range(tuple[3],start_s,end_s)
##         else:
##             self.range_query=Range(tuple[0],end_q,start_q)
##             self.range_subject=Range(tuple[3],end_s,start_s)
        if start_q < end_q:
            self.range_query=Range(tuple[0],start_q,end_q)
            self.range_subject=Range(tuple[3],start_s,end_s)
        else:
            self.range_query=Range(tuple[0],end_q,start_q)
            self.range_subject=Range(tuple[3],end_s,start_s)
        return 1

    #--------------------------------------------------------------------------

    def toString(self):

        """
        return a formated string of the attribut data
        """

        str = "%s\t%d\t%d\t%s\t%d\t%d\t%g\t%d\t%f" %\
              (self.range_query.seqname,\
               self.range_query.start,\
               self.range_query.end,\
               self.range_subject.seqname,\
               self.range_subject.start,\
               self.range_subject.end,\
               self.e_value,self.score,self.identity)
        return str

    #--------------------------------------------------------------------------

    def reverse(self):

        """
        reverse query and subject
        """

        self.range_query.reverse()
        self.range_subject.reverse()

    #--------------------------------------------------------------------------

    def show(self):

        """
        show the attribute values
        """

        print self.toString()
        
    #--------------------------------------------------------------------------

    def write(self,file):

        """
        write the attribute value to a file
        
        @param file: file identifier of the file being written
        @type file: file identifier
        """

        file.write(self.toString()+"\n")
    
    #--------------------------------------------------------------------------

    def get_score(self):

        """
        return the score value
        """

        return self.score

    #--------------------------------------------------------------------------

    def get_identity(self):

        """
        return the identity value
        """

        return self.identity

    #--------------------------------------------------------------------------

    def get_id(self):

        """
        return the identifier number
        """

        return self.id

    #--------------------------------------------------------------------------

    def merge(self,p):

        """
        merge self with a L{Align<Align>} instance

        @param p: a L{Align<Align>} instance
        @type p: class L{Align<Align>}
        """
        
        if self.range_query.seqname!=p.range_query.seqname \
               or self.range_subject.seqname!=p.range_subject.seqname:
            return
        self.range_query.merge(p.range_query)
        self.range_subject.merge(p.range_subject)
        self.score=max(self.score,p.score)
        self.e_value=min(self.e_value,p.e_value)
        self.identity=max(self.identity,p.identity)
        self.id=min(self.id,p.id)        
