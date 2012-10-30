from pyRepet.coord.Range import *

class Map(Range):
    """
    Record a named subsequence region

    @ivar name: the name of the region
    @type name: string

    @ivar id: identifier number
    @type id: integer
    """
    
    def __init__(self,name="",seqname="",start=-1,end=-1,id="-1"):
        """
        constructor
        
        @param id: identifier number
        @type id: integer
    
        @param name: the name of the region
        @type name: string

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
        self.name=name
        self.id=id
        
    def set_from_tuple(self,tuple,id="-1"):
        """
        set attribute data from a tuple

        @param tuple: a tuple with (name,seqname,start,end)
        @type tuple: python tuple

        @param id: identifier number
        @type id: integer
        """
        self.name=tuple[0]
        self.seqname=tuple[1]
        self.start=int(tuple[2])
        self.end=int(tuple[3])
        self.id=id
        
    def read(self,file):
        """
        read attribute data from a map file

        @param file: file identifier of the file being read
        @type file: file identifier
        @return: 1 on success, 0 at the end of the file 
        """
        self.name=""
        self.seqname=""
        self.start=-1
        self.end=-1
        line=file.readline()
        if line=="":
            return 0
        tok=line.split("\t")
        if len(tok)<4:
            return 0
        self.set_from_tuple(tok)
        return 1
    
    def toString(self):
        """
        return a formated string of the attribut data
        """
        str="%s\t%s\t%d\t%d"%\
                   (self.name,self.seqname,self.start,self.end)
        return str

    def write(self,file):
        """
        write attribute data from a map file

        @param file: file identifier of the file being read
        @type file: file identifier
        """
        file.write(self.toString()+"\n")


    def get_id(self):
        """
        return identifier number
        """
        return self.id

    def diff(self,map):
	n=Range.diff(self,map)
        new=Map()
        if not n.empty():
            new.id=self.id
            new.name=self.name
	    new.seqname=n.seqname
	    new.start=n.start
	    new.end=n.end
        return new
            
