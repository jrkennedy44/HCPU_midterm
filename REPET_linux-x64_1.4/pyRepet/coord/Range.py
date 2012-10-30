import logging

#------------------------------------------------------------------------------

class Range:

    """
    Record a subsequence region

    @ivar seqname: the sequence name
    @type seqname: string

    @ivar start: start coordinate
    @type start: integer

    @ivar end: end coordinate
    @type end: integer

    @note: on reverse strand if start>end
    """

    #--------------------------------------------------------------------------

    def __init__(self,seqname="",start=-1,end=-1):
        """
        constructor

        @param seqname: the sequence name
        @type seqname: string
        
        @param start: start coordinate
        @type start: integer

        @param end: end coordinate
        @type end: integer
        """
        self.seqname=seqname
        self.start=start
        self.end=end

    #--------------------------------------------------------------------------

    def __lt__(self,o):
        """
        less than operator
        """
        if self.getMin()<o.getMin():
            return True
        elif self.getMin()==o.getMin() and self.getMax()<o.getMax():
            return True
        return False
    
    #--------------------------------------------------------------------------

    def __le__(self,o):
        """
        less or equal operator
        """
        if self.getMin()<o.getMin():
            return True
        elif self.getMin()==o.getMin() and self.getMax()<=o.getMax():
            return True
        return False

    #--------------------------------------------------------------------------

    def __eq__(self,o):
        """
        equal operator

        @note: coordinates must be equal, but not the orientation
        """
        if self.getMin()==o.getMin() and self.getMax()==o.getMax():
             return True       
        return False

    #--------------------------------------------------------------------------

    def __gt__(self,o):
        """
        greater than operator
        """
        if self.getMin()>o.getMin():
            return True
        elif self.getMin()==o.getMin() and self.getMax()>o.getMax():
            return True
        return False
    
    #--------------------------------------------------------------------------

    def __ge__(self,o):
        """
        greater or equal operator
        """
        if self.getMin()>o.getMin():
            return True
        elif self.getMin()==o.getMin() and self.getMax()>=o.getMax():
            return True
        return False

    #--------------------------------------------------------------------------

    def __ne__(self,o):
        """
        not equal operator

        @note: coordinates must not be equal, but not the orientation
        """
        if self.getMin()!=o.getMin() and self.getMax()!=o.getMax():
             return True       
        return False
        
    #--------------------------------------------------------------------------

    def toString(self):
        """
        return a formated string of the attribut data
        """
        str="%s\t%d\t%d"%\
                   (self.seqname,self.start,self.end)
        return str
               
    #--------------------------------------------------------------------------

    def show(self):
        """
        show the attribute values
        """
        print self.toString()

    #--------------------------------------------------------------------------

    def print_log(self,log_level):
        """
        print in log the attribute values
        
        @param log_level: a log level
        """
        if log_level=="debug":
            logging.debug(self.toString())
        elif log_level=="info":
            logging.info(self.toString())
        elif log_level=="error":
            logging.error(self.toString())
        else:
            print "log_level",log_level,"not implemented in Range.print_log"

    #--------------------------------------------------------------------------

    def getMin(self):
        """
        return the lowest value between start and end attributes
        """
        return min(self.start,self.end)

    #--------------------------------------------------------------------------

    def getMax(self):
        """
        return the greatest value between start and end attributes
        """
        return max(self.start,self.end)

    #--------------------------------------------------------------------------

    def isPlusStrand(self):
        """
        return 1 if L{Range<Range>} instance is on the direct strand
        """
        if self.start<=self.end:
            return True
        else:
            return False
        
    def isOnDirectStrand(self):
        self.isPlusStrand()

    #--------------------------------------------------------------------------

    def getStrand(self):
        """
        return '+' if L{Range<Range>} instance is on the direct strand or '-' if not
        """
        if self.start<=self.end:
            return '+'
        else:
            return '-'

    #--------------------------------------------------------------------------

    def reverse(self):
        """
        exchange start and end coordinates
        """
        tmp=self.start
        self.start=self.end
        self.end=tmp
        
    #--------------------------------------------------------------------------

    def getLength(self):
        """
        return the length of the L{Range<Range>} instance
        """
        return int(abs(self.start-self.end))+1

    def length(self):
        return self.getLength()

    #--------------------------------------------------------------------------

    def empty(self):
        """
        return if a L{Range<Range>} instance is empty
        """
        if self.start==self.end and (self.start==0 or self.start==-1):
            return True
        return False

    #--------------------------------------------------------------------------

    def merge(self,r):
        """
        merge self with a L{Range<Range>} instance

        @param r: a L{Range<Range>} instance
        @type r: class L{Range<Range>}
        """
        if self.seqname != r.seqname:
            return
        if self.isPlusStrand():
            self.start=min(self.getMin(),r.getMin())
            self.end=max(self.getMax(),r.getMax())
        else:
            self.start=max(self.getMax(),r.getMax())
            self.end=min(self.getMin(),r.getMin())
            
    #--------------------------------------------------------------------------

    def overlap(self,range):
        """
        return 1 if self overlap L{Range<Range>} instance, 0 if not

        @param range: a L{Range<Range>} instance
        @type range: class L{Range<Range>}
        """
        if range.seqname != self.seqname:
            return False
        
        smin=self.getMin()
        smax=self.getMax()
        rmin=range.getMin()
        rmax=range.getMax()
        
        if rmin<=smin and rmax>=smax:
            return True
        if rmin>=smin and rmin<=smax or rmax>=smin and rmax<=smax:
            return True
        return False

    #--------------------------------------------------------------------------

    def overlap_size(self,range):
        """
        return the overlap size between self and a L{Range<Range>} instance, 0 if not

        @param range: a L{Range<Range>} instance
        @type range: class L{Range<Range>}
        """
        if self.overlap(range):
            if self.include(range):
                return range.length()
            elif range.include(self):
                return self.length()
            elif range.getMin()<=self.getMax() \
                     and range.getMin()>=self.getMin():
                return self.getMax()-range.getMin()+1
            elif range.getMax()<=self.getMax() \
                     and range.getMax()>=self.getMin():
                return range.getMax()-self.getMin()+1
        return 0

    #--------------------------------------------------------------------------

    def include(self,range):
        """
        return 1 if L{Range<Range>} instance included in self, 0 if not

        @param range: a L{Range<Range>} instance
        @type range: class L{Range<Range>}
        """        
        #is range included in self?
        if range.seqname != self.seqname:
            return False
        if range.getMin()>=self.getMin()\
           and range.getMax()<=self.getMax():
            return True
        else:
            return False

    #--------------------------------------------------------------------------

    def distance(self,range):
        """
        return the distance between self.start and L{Range<Range>}
        instance start

        @param range: a L{Range<Range>} instance
        @type range: class L{Range<Range>}
        """        
        if self.isPlusStrand()==range.isPlusStrand():
            if self.overlap(range):
                return 0
            elif self.isPlusStrand():
                if self.start > range.start:
                    return self.start-range.end
                else:
                    return range.start-self.end
            else:
                if self.start > range.start:
                    return self.end-range.start
                else:
                    return range.end-self.start
        return -1

    #--------------------------------------------------------------------------

    def diff(self,range):
        """
        remove in self the region overlapping with a L{Range<Range>}
        instance

        @param range: a L{Range<Range>} instance
        @type range: class L{Range<Range>}
        """

        new_range=Range(self.seqname)
        if not self.overlap(range) or self.seqname!=range.seqname:
            return new_range

        istart=min(self.start,self.end)
        iend=max(self.start,self.end)
        jstart=min(range.start,range.end)
        jend=max(range.start,range.end)
        if istart<jstart:
            if iend<=jend:
                if self.isPlusStrand():
                    self.start=istart
                    self.end=jstart-1
                else:
                    self.start=jstart-1
                    self.end=istart
            else:
                if self.isPlusStrand():
                    self.start=istart
                    self.end=jstart-1
                    new_range.start=jend+1
                    new_range.end=iend
                else:
                    self.start=jstart-1;
                    self.end=istart;
                    new_range.start=iend
                    new_range.end=jend+1
        else: #istart>=jstart
            if iend<=jend:
                self.start=0
                self.end=0
            else:
                if self.isPlusStrand():
                    self.start=jend+1
                    self.end=iend
                else:
                    self.start=iend
                    self.end=jend+1
        return new_range;

    #--------------------------------------------------------------------------

    def getBin(self):
        """
        return a bin for fast database access
        """
        for i in xrange(3,8):
            bin_lvl=pow(10,i)
            #if int(self.start/i)==int(self.end/i): error
            if int(self.start/bin_lvl)==int(self.end/bin_lvl):
                return float(bin_lvl+(int(self.start/bin_lvl)/1e10))
        
        bin_lvl=pow(10,8)
        return float(bin_lvl+(int(self.start/bin_lvl)/1e10))
