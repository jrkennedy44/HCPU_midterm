import os, sys, re, copy
from math import *
from string import *

from pyRepet.seq.Bioseq import *
from pyRepet.util.Stat import *

#------------------------------------------------------------------------------

class BioseqDB:

    #--------------------------------------------------------------------------

    def __init__( self, name="" ):
        self.idx = {}
        self.idx_renamed = {}
        self.db = []
        self.name = name
        if name != "":
            faFile = open( name )
            self.read( faFile )
        self.mean_seq_lgth = None
        self.stat = Stat()

    #--------------------------------------------------------------------------

    def setName(self,name):

        """
        change the attribute 'name'
        """

        self.name=name

    #--------------------------------------------------------------------------

    def __getitem__(self,i):
        if i < len(self.db):
            return self.db[i]

    #--------------------------------------------------------------------------

    def fetch( self, header ):

        """
        return the Bioseq instance of the sequence specified by its header
        """

        return self.db[self.idx[header]]

    #--------------------------------------------------------------------------

    def fetch_renamed( self, header ):

        """
        return the Bioseq instance of the sequence specified by its renamed header removing '::' and spaces
        """

        return self.db[self.idx_renamed[header]]
    
    #--------------------------------------------------------------------------

    def read( self, faFile ):

        """
        record each sequence of the input file as Bioseq object
        """

        while 1:
            seq = Bioseq()
            seq.read( faFile )
            if seq.sequence == None:
                break
            self.add( seq )

    #--------------------------------------------------------------------------

    def write( self, faFile ):
         for bs in self.db:
             bs.write( faFile )

    #--------------------------------------------------------------------------

    def save( self, outFaFileName ):
         outFaFile = open( outFaFileName, "w" )
         self.write( outFaFile )
         outFaFile.close()

    #--------------------------------------------------------------------------

    def copy(self):
        copy=BioseqDB()
        for i in self.db:
            copy.add(i)
        return copy

    #--------------------------------------------------------------------------

    def add( self, bs ):
        self.db.append( bs )
        self.idx[ bs.header ] = len(self.db) - 1
        self.idx_renamed[ bs.header.replace("::","-").replace(":","-").replace(",","-").replace(" ","_") ] = len(self.db) - 1
    #--------------------------------------------------------------------------

    def view(self):
        for i in self.db:
            i.view()

    #--------------------------------------------------------------------------

    def view_name(self):
        for i in self.db:
            print i.header
            
    #--------------------------------------------------------------------------

    def load(self,file_name):
        fichier=open(file_name)
        self.read(fichier)
        fichier.close()

        #--------------------------------------------------------------------------

    def reverse( self ):
        for bs in self.db:
            bs.reverse()

    #--------------------------------------------------------------------------

    def getSize( self ):

        """
        return the number of sequences in the bank
        """

        return len( self.db )

    #--------------------------------------------------------------------------

    def getLength( self ):

        """
        return the cumulative sequence length in the bank
        """

        cumLength = 0

        for bs in self.db:
            cumLength += bs.getLength()

        return cumLength

    #--------------------------------------------------------------------------

    def meanSeqLgth( self ):

        """
        return the mean of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.mean()

    #--------------------------------------------------------------------------

    def sdSeqLgth( self ):

        """
        return the standard deviation of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.sd()

    #--------------------------------------------------------------------------

    def medianSeqLgth( self ):

        """
        return the median of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.median()

    #--------------------------------------------------------------------------

    def maxSeqLgth( self ):

        """
        return the max of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.max

    #--------------------------------------------------------------------------

    def minSeqLgth( self ):

        """
        return the min of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.min

    #--------------------------------------------------------------------------

    def quantileSeqLgth( self ):

        """
        return the quantiles of the sequence lengths
        """

        if self.stat.n == 0:
            for bs in self.db:
                self.stat.add( bs.getLength() )
        return self.stat.stringQuantiles()

    #--------------------------------------------------------------------------

    def countNt( self, nt ):

        """
        Count the number of times the given nucleotide is present in the bank.
        """

        total = 0
        for bs in self.db:
            total+= bs.sequence.count( nt )
        return total

    #--------------------------------------------------------------------------

    def countAllNt( self ):

        """
        Count the occurrences for each nucleotide (A,T,G,C,N).
        """

        dNt2Count = {}
        for nt in ["A","T","G","C","N"]:
            dNt2Count[ nt ] = self.countNt( nt )
        return dNt2Count

    #--------------------------------------------------------------------------

    def getSeqHeaders( self ):

        """
        return a list with the sequence headers
        """

        lHeaders = []

        for bs in self.db:
            if bs.header in lHeaders:
                print "*** Error: two sequences with the same header %s" % ( bs.header )
                return 1, ""
            else:
                lHeaders.append( bs.header )

        return 0, lHeaders

    #--------------------------------------------------------------------------

    def extractPart(self,deb,taille):
        shorterBSDB=BioseqDB()
        for i in self.db[deb:(deb+taille)]:
            shorterBSDB.add(i)    
        return shorterBSDB  

    #--------------------------------------------------------------------------

    def makeSequenceSets(self,sizeOfSet):
        ori_size=self.nbOfSequence()
        listOfShorterBSDB=[]
        new_size=ori_size
        while(new_size>sizeOfSet):
            new_size=new_size/2
        pos=0
        while 1:
            if pos>ori_size:
                break
            if (ori_size-pos)<new_size and (ori_size-pos!=0):
                listOfShorterBSDB.append(self.extractPart(pos,(ori_size-pos)))
            else:
                if (ori_size-pos!=0):
                    listOfShorterBSDB.append(self.extractPart(pos,new_size))
            pos=pos+new_size 
        return listOfShorterBSDB
            
        
    #--------------------------------------------------------------------------

    def bestLength(self,num):
	length_list=[]
	numseq=0
	for each_seq in self.db:
            if each_seq.sequence==None:
                break
            l=each_seq.length()
            length_list.append(l)
            numseq=numseq+1

	length_list.sort()
	size=len(length_list)
	if num<size:
		len_min=length_list[size-num]
	else:
		len_min=length_list[0]

	numseq=0
	nbsave=0
        bestSeqs=BioseqDB()
        bestSeqs.setName(self.name)
        for each_seq in self.db:
            if each_seq.sequence==None:
                break
            l=each_seq.length()
            numseq=numseq+1
            if l>=len_min:
                
                bestSeqs.add(each_seq)
                nbsave=nbsave+1

		if nbsave==num :
                    break      
        return bestSeqs

    #--------------------------------------------------------------------------

#si mvClust=1 (fichier .fa de grouper) retourne la liste des noms de sequences d'un cluster donne sans le "MbGrCl"
#sinon retourne la liste des header de sequences correpondant e un pattern donne 

    def extractSeqName(self,pattern,db_filename,mvClust):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        file_db=open(db_filename)
        numseq=0
        lst_header=[]
        while 1:
            seq=Bioseq()
            seq.read(file_db)
            if seq.sequence==None:
                break
            numseq+=1
            m=srch.search(seq.header)
            if m:
                lst_header.append(seq.header)
        file_db.close()
        if mvClust==1:
            seqname=[]
            for i in lst_header:
                seqname.append(join(split(i)[1:]))
                d=dict([(i,0)for i in seqname]).keys()
            
        else :
            d=dict([(i,0)for i in lst_header]).keys()
        return d

    #--------------------------------------------------------------------------

    def extractPatternOfFile(self,pattern,db_filename):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        file_db=open(db_filename)
        numseq=0
        nbsave=0
        while 1:
            seq=Bioseq()
            seq.read(file_db)
            if seq.sequence==None:
                break
            numseq+=1
            m=srch.search(seq.header)
            if m:
                self.add(seq)
                nbsave+=1
        file_db.close()
        
    #--------------------------------------------------------------------------

    def getByPattern(self,pattern):
        if pattern=="" :
            return
        db=BioseqDB()
        srch=re.compile(pattern)
        for seq in self.db:
            if srch.search(seq.header):
                db.add(seq)
        return db

    #--------------------------------------------------------------------------

    def rmByPattern(self,pattern):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        for seq in self.db:
            if srch.search(seq.header):
                self.db.remove(seq)
        
    #--------------------------------------------------------------------------

    def extractPattern(self,pattern,bsdb):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        for seq in bsdb.db:
            m=srch.search(seq.header)
            if m:
                self.add(seq)

    #--------------------------------------------------------------------------

    def cleanByPattern(self,pattern,bsdb):
        if pattern=="":
		return
	srch=re.compile(pattern)
        seq=Bioseq()
	for seq in bsdb.db:
            if not srch.search(seq.header):
               self.add(seq)

    #--------------------------------------------------------------------------

    #retourne un diplet de bioseqDB le premier contient les sequences extraites le 2eme tous sauf ces sequences    

    def ExtractAndCleanByPattern(self,pattern):
        if pattern=="":
		return
	srch=re.compile(pattern)
        extracted_seq=BioseqDB()
        resting_seq=BioseqDB()
	for seq in self.db:
            if seq.sequence==None:
                    break
            if srch.search(seq.header):
               extracted_seq.add(seq)
            else :
                resting_seq.add(seq)
        return (extracted_seq,resting_seq)

    #--------------------------------------------------------------------------

    def getDicoClust2Grp2Seq( self ):

        """
        get the relationships between clusters, groups and sequences

        @return: dictionaries dClust2Grp, dGrp2Seq and dSeq2Grp
        """

        dClust2Grp = {}
        dGrp2Seq = {}
        dSeq2Grp = {}

        for bs in self.db:

            cluster = bs.getClusterID()
            group = bs.getGroupID()
            headerFullSeq = bs.getHeaderFullSeq()

            if not dClust2Grp.has_key( cluster ):
                dClust2Grp[ cluster ] = [ group ]
            else:
                dClust2Grp[ cluster ].append( group )
            if not dGrp2Seq.has_key( group ):
                dGrp2Seq[ group ] = [ headerFullSeq ]
            else:
                dGrp2Seq[ group ].append( headerFullSeq )
            if not dSeq2Grp.has_key( headerFullSeq ):
                dSeq2Grp[ headerFullSeq ] = [ group ]
            else:
                dSeq2Grp[ headerFullSeq ].append( group )

        return dClust2Grp, dGrp2Seq, dSeq2Grp

    #--------------------------------------------------------------------------

    def getGrpPerSeq( self, dSeq2Grp ):

        """
        give the number of sequences belonging to several groups

        @param dSeq2Grp: dictionary whose keys are sequence headers and values the group(s) to which they belong
        @type dSeq2Grp: dictionary
        """

        nbSeq = 0
        for seq in dSeq2Grp.keys():
            if len(dSeq2Grp[ seq ]) > 1:
                nbSeq += 1
        return nbSeq

    #--------------------------------------------------------------------------

    def getStatsOutGrouper( self ):

        """
        print summary statistics when the BioseqDB is a Grouper output
        """

        dClust2Grp, dGrp2Seq, dSeq2Grp = self.getDicoClust2Grp2Seq()

        print "nb of clusters = %i" % ( len(dClust2Grp.keys()) )
        print "nb of groups = %i" % ( len(dGrp2Seq.keys()) )
        print "nb of distinct sequences in the input file = %i" % ( len(dSeq2Grp.keys()) )
        print "nb of fragments in the input file = %i" % ( self.getSize() )
        print "nb of sequences belonging to several groups = %i" % ( self.getGrpPerSeq( dSeq2Grp ) )
        sys.stdout.flush()

    #--------------------------------------------------------------------------

    def getLongestSeqHeader( self ):

        maxLgth = self.maxSeqLgth()
        for bs in self.db:
            if bs.getLength() == maxLgth:
                return bs.header

    #--------------------------------------------------------------------------

    def getShortestSeqHeader( self ):

        minLgth = self.minSeqLgth()
        for bs in self.db:
            if bs.getLength() == minLgth:
                return bs.header

    #--------------------------------------------------------------------------

    def upCase( self ):

        for bs in self.db:
            bs.upCase()

    #--------------------------------------------------------------------------

    def lowCase( self ):

        for bs in self.db:
            bs.lowCase()
