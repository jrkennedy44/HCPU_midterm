from pyRepet.coord.Range import *
from pyRepet.coord.Align import *
from pyRepet.coord.Set import *

#------------------------------------------------------------------------------

class Path( Align ):

    """
    Record a match between two subsequences (a query and a subject) with
    an identifier number

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

    def set_from_tuple( self, tokens ):

        """
        Set attribute data from a tuple.

        @param tokens: a tuple with (id,query name,query start,query end,
        subject name,subject start,subject end,e_value,score,identity)

        @type tokens: python tuple
        """

        self.id = int(tokens[0])
        qryName = tokens[1]
        start_q = int(tokens[2])
        end_q = int(tokens[3])
        sbjName = tokens[4]
        start_s = int(tokens[5])
        end_s = int(tokens[6])
        if len(tokens) > 7:   # otherwise simple path source (i.e. path_range)
            self.e_value=float(tokens[7])
            self.score=float(tokens[8])
            self.identity=float(tokens[9])

##         if start_s < end_s:
##             self.range_query = Range( qryName, start_q, end_q )
##             self.range_subject = Range( sbjName, start_s, end_s )
##         else:
##             self.range_query = Range( qryName, end_q, start_q )
##             self.range_subject = Range( sbjName, end_s, start_s )

        if start_q < end_q:
            self.range_query = Range( qryName, start_q, end_q )
            self.range_subject = Range( sbjName, start_s, end_s )
        else:
            self.range_query = Range( qryName, end_q, start_q )
            self.range_subject = Range( sbjName, end_s, start_s )

        return 1

    #--------------------------------------------------------------------------

    def toString( self ):

        """
        Return a formatted string of the attribut data.
        """

        string = "%d\t%s\t%d\t%d\t%s\t%d\t%d\t%g\t%d\t%f"%\
                 (self.id,\
                  self.range_query.seqname,\
                  self.range_query.start,\
                  self.range_query.end,\
                  self.range_subject.seqname,\
                  self.range_subject.start,\
                  self.range_subject.end,\
                  self.e_value,self.score,self.identity)
        return string
    
    #--------------------------------------------------------------------------

    def rangeQ2Set( self ):

        """
        Extract the query range to return a set.
        """

        set = Set()
        set.id = self.id
        set.name = self.range_subject.seqname
        if self.range_subject.isPlusStrand():
            set.start = self.range_query.start
            set.end = self.range_query.end
        else:
            set.start = self.range_query.end
            set.end = self.range_query.start
        set.seqname = self.range_query.seqname
        return set

    #--------------------------------------------------------------------------

    def rangeS2Set( self ):

        """
        Extract the subject range to return a set.
        DEPRECATED
        """

        set = Set()
        set.id = self.id
        set.name = self.range_query.seqname
        if self.range_query.isPlusStrand():
            set.start = self.range_subject.start
            set.end = self.range_subject.end
        else:
            set.start = self.range_subject.end
            set.end = self.range_subject.start
        set.seqname = self.range_subject.seqname
        return set

    #--------------------------------------------------------------------------

    def getBin( self ):

        """
        Return a bin for fast database access.
        """

        return self.range_query.getBin()

#-----------------------------------------------------------
# Functions on list of paths

def path_list_rangeQ2Set(path_list):
    """
    transform a L{Path<Path>} instances list to a L{Set<Set>} instances
    list containing the query range

    @param path_list: a list of L{Path<Path>} instances
    @return a list of L{Set<Set>} instances
    """
    l=[]
    for i in path_list:
        l.append(i.rangeQ2Set())
    return l

#------------------------------------------------------------------------------

def path_list_boundaries(path_list):
    """
    return min et max query coordinates of L{Path<Path>} instances contained in a list

    @param path_list: lists of L{Path<Path>} instances
    @type path_list: python list of L{Path<Path>} instances

    @return: python tuple (min,max)
    """
    qmin=-1
    qmax=-1
    for i in path_list:
        if qmin==-1:
            qmin=i.range_query.start
        qmin=min(qmin,i.range_query.getMin())
        qmax=max(qmax,i.range_query.getMax())
    return (qmin,qmax)

#------------------------------------------------------------------------------

def path_list_sbj_boundaries( lPaths ):

    """
    Return min et max subject coordinates of L{Path<Path>} instances contained in a list.

    @param path_list: lists of L{Path<Path>} instances
    @type path_list: python list of L{Path<Path>} instances

    @return: python tuple (min,max)
    """

    smin = -1
    smax = -1
    for i in lPaths:
        if smin == -1:
            smin = i.range_subject.start
        smin = min( smin, i.range_subject.getMin() )
        smax = max( smax, i.range_subject.getMax() )
    return ( smin, smax )

#------------------------------------------------------------------------------

def path_list_overlapQ(lpath1,lpath2):
    """
    return if it exists overlaps between two lists of L{Path<Path>} instances

    @param lpath1: lists of L{Path<Path>} instances
    @type lpath1: python list of L{Path<Path>} instances
    
    @param lpath2: lists of L{Path<Path>} instances
    @type lpath2: python list of L{Path<Path>} instances

    """

    lpath1.sort()
    lpath2.sort()

    osize=0
    
    i=0
    j=0
    while i!= len(lpath1):
        while j!= len(lpath2) and lpath1[i]>lpath2[j]\
             and not(lpath1[i].overlap(lpath2[j])):
            j+=1
        if j!= len(lpath2) \
               and lpath1[i].range_query.overlap(lpath2[j].range_query):
            return True
        i+=1
    return False

#------------------------------------------------------------------------------

def path_list_show(path_list):
    """
    show L{Path<Path>} attributes contained in a list

    @param path_list: a list of L{Path<Path>} instances
    """
    for i in path_list:
        i.show()

#------------------------------------------------------------------------------

def path_list_write(path_list,filename,mode="w"):
    """
    write L{Path<Path>} contained in a list

    @param path_list: a list of L{Path<Path>} instances
    @param filename: a filename
    @param mode: the open mode of the file ""w"" or ""a"" 
    """
    file=open(filename,mode)
    for i in path_list:
        i.write(file)

#------------------------------------------------------------------------------

def path_list_remove_doublons(lpath):
    """
    find doublons L{Path<Path>} instances in the list

    @return: a list L{Path<Path>} instances with no doublons
    """

    lpath_out=lpath
    lpath_out.sort()
    idx2del=[]
    i=0
    j=0
    while i< len(lpath_out):
        while j< len(lpath_out) and (lpath_out[i]>lpath_out[j] or i==j)\
            and not(lpath_out[i].range_query.start==lpath_out[j].range_query.start \
                    and lpath_out[i].range_query.end==lpath_out[j].range_query.end \
                    and lpath_out[i].range_query.seqname==lpath_out[j].range_query.seqname \
                    and lpath_out[i].range_subject.start==lpath_out[j].range_subject.start \
                    and lpath_out[i].range_subject.end==lpath_out[j].range_subject.end \
                    and lpath_out[i].range_subject.seqname==lpath_out[j].range_subject.seqname):
            j+=1

        while j<len(lpath_out) \
                  and lpath_out[i].range_query.start==lpath_out[j].range_query.start \
                  and lpath_out[i].range_query.end==lpath_out[j].range_query.end \
                  and lpath_out[i].range_query.seqname==lpath_out[j].range_query.seqname \
                  and lpath_out[i].range_subject.start==lpath_out[j].range_subject.start \
                  and lpath_out[i].range_subject.end==lpath_out[j].range_subject.end \
                  and lpath_out[i].range_subject.seqname==lpath_out[j].range_subject.seqname \
                  and i!=j :
            idx2del.append(j)
            j+=1
        i+=1
    idx2del.sort()
    idx2del.reverse()
    for idx in idx2del:
        del lpath_out[idx]
    return lpath_out

#------------------------------------------------------------------------------

def path_list_split(path_list):
    """
    split a L{Path<Path>} list in several L{Path<Path>}
    list according to the id number

    @param path_list: a list of L{Path<Path>} instances
    @return: several path list
    """
    by_id_list={}
    for i in path_list:
        if by_id_list.has_key(i.id):
            by_id_list[i.id].append(i)
        else:
            by_id_list[i.id]=[i]
    return by_id_list

#------------------------------------------------------------------------------

def path_list_unjoin(pl1,pl2):
    """
    unjoin a L{Path<Path>} list according to another

    @param pl1: a list of L{Path<Path>} instances to keep 
    @param pl2: a list of L{Path<Path>} instances to unjoin

    @return: pl2 split in several list or an empty list if no split occurs 
    """
    pl1.sort()
    pl2.sort()
    i=0
    list_pl=[]
    while i<len(pl1):
        j1=0
        while j1<len(pl2) and pl1[i]>pl2[j1]:
            j1+=1
        if j1==len(pl2):
            break
        if j1!=0:
            list_pl.append(pl2[:j1])
            del pl2[:j1]
            j1=0
        if i+1==len(pl1):
            break
        j2=j1
        if j2<len(pl2) and pl1[i+1]>pl2[j2]:
            while j2<len(pl2) and pl1[i+1]>pl2[j2]:
                j2+=1
            list_pl.append(pl2[j1:j2])
            del pl2[j1:j2]
        i+=1

    if list_pl!=[]:
        list_pl.append(pl2)
    return list_pl

#------------------------------------------------------------------------------

def path_list_changeId(path_list,newId):
    """
    change in place the id of L{Path<Path>} instances contained in a list

    @param path_list: lists of L{Path<Path>} instances
    @type path_list: python list of L{Path<Path>} instances

    @param newId: a new path number
    @type newId: integer
    """
    for i in path_list:
        i.id=newId
