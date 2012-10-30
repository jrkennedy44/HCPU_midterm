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


## Record a region on a given sequence
#
class Range( object ):

    ## Constructor
    #
    # @param seqname the name of the sequence
    # @param start the start coordinate
    # @param end the end coordinate
    #
    def __init__(self, seqname="", start=-1, end=-1):
        self.seqname = seqname
        self.start = int(start)
        self.end = int(end)
        
    ## Equal operator
    #
    # @param o a Range instance
    #
    def __eq__(self, o):
        if self.seqname == o.seqname and self.start == o.start and self.end == o.end:
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
    
    ## Convert the object into a string
    #
    # @note used in 'repr(myObject)' for debugging
    #
    def __repr__( self ):
        return self.toString().replace("\t",";")
    
    def setStart(self, start):
        self.start = start
        
    def setEnd(self, end):
        self.end = end
        
    def setSeqName(self, seqName):
        self.seqname = seqName
    
    ## Reset
    #
    def reset(self):
        self.seqname = ""
        self.start = -1
        self.end = -1
        
    ## Return the attributes as a formatted string
    #   
    def toString(self):
        string = "%s" % (self.seqname)
        string += "\t%d" % (self.start)
        string += "\t%d" % (self.end)
        return string
    
    ## Show the attributes
    #
    def show(self):
        print self.toString()
    
    ## Return seqname
    #
    def getSeqname(self):
        return self.seqname
    
    ## Return the start coordinate
    #
    def getStart(self):
        return self.start
    
    ## Return the end coordinate
    #
    def getEnd(self):
        return self.end
    
    ## Return the lowest value between start and end coordinates
    #
    def getMin(self):
        return min(self.start, self.end)
    
    ## Return the greatest value between start and end attributes
    # 
    def getMax(self):
        return max(self.start, self.end)
    
    ## Return True if the instance is on the direct strand, False otherwise
    # 
    def isOnDirectStrand(self):
        if self.start <= self.end:
            return True
        else:
            return False
        
    ## Return True if the instance is on the reverse strand, False otherwise
    # 
    def isOnReverseStrand(self):
        return not self.isOnDirectStrand()
    
    ## Return '+' if the instance is on the direct strand, '-' otherwise
    # 
    def getStrand(self):
        if self.isOnDirectStrand():
            return '+'
        else:
            return '-'
        
    ## Exchange start and end coordinates
    #
    def reverse(self):
        tmp = self.start
        self.start = self.end
        self.end = tmp
        
    ## Return the length of the instance
    #
    # @warning old name is 'length'
    #
    def getLength(self):
        return int(abs(self.start-self.end))+1
    
    ## Return True if the instance is empty, False otherwise
    #
    def isEmpty(self):
        if self.start==self.end and (self.start==0 or self.start==-1):
            return True
        return False
    
    ## Set attributes from tuple
    #
    # @param tuple a tuple with (name,start,end)
    #
    def setFromTuple(self, tuple):
        self.seqname = tuple[0]
        self.start = int(tuple[1])
        self.end = int(tuple[2])
        
    ## Set attributes from string
    #
    # @param string a string formatted like name<sep>start<sep>end
    # @param sep field separator
    #
    def setFromString(self, string, sep="\t"):
        if string[-1] == "\n":
            string = string[:-1]
        self.setFromTuple( string.split(sep) )
        
    ## Merge the instance with another Range instance
    #
    # @param o a Range instance
    #
    def merge(self, o):
        if self.seqname != o.seqname:
            return
        if self.isOnDirectStrand():
            self.start = min(self.getMin(), o.getMin())
            self.end = max(self.getMax(), o.getMax())
        else:
            self.start = max(self.getMax(), o.getMax())
            self.end = min(self.getMin(), o.getMin())
            
    ## Return True if the instance overlaps with another Range instance, False otherwise
    #
    # @param o a Range instance
    #
    def isOverlapping(self, o):
        if o.seqname != self.seqname:
            return False
        smin = self.getMin()
        smax = self.getMax()
        omin = o.getMin()
        omax = o.getMax()
        if omin <= smin and omax >= smax:
            return True
        if omin >= smin and omin <= smax or omax >= smin and omax <= smax:
            return True
        return False
    
    
    ## Return the length of the overlap between the instance and another Range, 0 if no overlap
    #
    # @param o a Range instance
    #
    def getOverlapLength( self, o ):
        if self.isOverlapping( o ):
            if self.isIncludedIn( o ):
                return self.getLength()
            elif o.isIncludedIn( self ):
                return o.getLength()
            elif o.getMin() <= self.getMax() and o.getMin() >= self.getMin():
                return self.getMax() - o.getMin() + 1
            elif o.getMax() <= self.getMax() and o.getMax() >= self.getMin():
                return o.getMax() - self.getMin() + 1
        return 0
    
    
    ## Return True if the instance is included within another Range, False otherwise
    #
    # @param o a Range instance
    #
    # @note the min (respectively max) coordinates can be equal
    #
    def isIncludedIn( self, o ):
        if o.seqname != self.seqname:
            return False
        if self.getMin() >= o.getMin() and self.getMax() <= o.getMax():
            return True
        else:
            return False

        
    ## Return the distance between the start of the instance and the start of another Range instance
    #
    # @param o a Range instance
    #
    def getDistance(self, o):
        if self.isOnDirectStrand() == o.isOnDirectStrand():
            if self.isOverlapping(o):
                return 0
            elif self.isOnDirectStrand():
                if self.start > o.start:
                    return self.start - o.end
                else:
                    return o.start - self.end
            else:
                if self.start > o.start:
                    return self.end - o.start
                else:
                    return o.end - self.start
        return -1
    
    ## Remove in the instance the region overlapping with another Range instance
    #
    # @param o a Range instance
    # 
    def diff(self, o):
        new_range = Range(self.seqname)
        if not self.isOverlapping(o) or self.seqname != o.seqname:
            return new_range

        istart = min(self.start, self.end)
        iend = max(self.start, self.end)
        jstart = min(o.start, o.end)
        jend = max(o.start, o.end)
        if istart < jstart:
            if iend <= jend:
                if self.isOnDirectStrand():
                    self.start = istart
                    self.end = jstart - 1
                else:
                    self.start = jstart - 1
                    self.end = istart
            else:
                if self.isOnDirectStrand():
                    self.start = istart
                    self.end = jstart - 1
                    new_range.start = jend + 1
                    new_range.end = iend
                else:
                    self.start = jstart - 1;
                    self.end = istart;
                    new_range.start = iend
                    new_range.end = jend + 1
        else: #istart>=jstart
            if iend <= jend:
                self.start = 0
                self.end = 0
            else:
                if self.isOnDirectStrand():
                    self.start = jend + 1
                    self.end = iend
                else:
                    self.start = iend
                    self.end = jend + 1
        return new_range
        
    ## Find the bin that contains the instance and compute its index
    #
    # @note Required for coordinate indexing via a hierarchical bin system
    #
    def findIdx(self):
        min_lvl = 3
        max_lvl = 6
        for bin_lvl in xrange(min_lvl, max_lvl):
            if getBin(self.start, bin_lvl) == getBin(self.end, bin_lvl):
                return getIdx(self.start, bin_lvl)
        return getIdx(self.start, max_lvl) 
    
    ## Get a bin for fast database access
    #
    # @return bin number (float)
    #
    def getBin(self):
        for i in xrange(3, 8):
            bin_lvl = pow(10, i)
            if int(self.start/bin_lvl) == int(self.end/bin_lvl):
                return float(bin_lvl+(int(self.start/bin_lvl)/1e10))
        bin_lvl = pow(10, 8)
        return float(bin_lvl+(int(self.start/bin_lvl)/1e10))
    
    
# Functions

# Get the bin number of a coordinate according to the bin level. Required for coordinate indexing with hierarchical bin system
#    
def getBin(val, bin_lvl):
    bin_size = pow(10, bin_lvl)
    return long(val / bin_size)
    
# Get an index from a coordinate according to the bin level. Required for coordinate indexing with hierarchical bin system
#
def getIdx(val, bin_lvl):
    min_lvl = 3
    max_lvl = 6
    if bin_lvl >= max_lvl:
        return long((bin_lvl-min_lvl+1)*pow(10,max_lvl))
    return long(((bin_lvl-min_lvl+1)*pow(10,max_lvl))+getBin(val,bin_lvl))
