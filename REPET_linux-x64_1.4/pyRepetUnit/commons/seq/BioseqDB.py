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
import re
from pyRepetUnit.commons.seq.Bioseq import Bioseq
from pyRepetUnit.commons.stat.Stat import Stat


## Handle a collection of a Bioseq (header-sequence) 
#
class BioseqDB( object ):
    
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
        
        
    ## Equal operator
    #
    def __eq__( self, o ):
        selfSize = self.getSize()
        if selfSize != o.getSize():
            return False
        nbEqualInstances = 0
        for i in self.db:
            atLeastOneIsEqual = False
            for j in o.db:
                if i == j:
                    atLeastOneIsEqual = True
                    continue
            if atLeastOneIsEqual:
                nbEqualInstances += 1
        if nbEqualInstances == selfSize:
            return True
        return False
    
    
    ## Change the name of the BioseqDB
    #
    # @param name the BioseqDB name
    # 
    def setName(self, name):
        self.name = name
        
        
    ## Record each sequence of the input file as a list of Bioseq instances
    #
    # @param faFileHandler handler of a fasta file
    #
    def read( self, faFileHandler ):
        while True:
            seq = Bioseq()
            seq.read( faFileHandler )
            if seq.sequence == None:
                break
            self.add( seq )
            
            
    ## Write all Bioseq of BioseqDB in a formatted fasta file (60 character long)
    #
    # @param faFileHandler file handler of a fasta file
    #
    def write( self, faFileHandler ):
        for bs in self.db:
            bs.writeABioseqInAFastaFile( faFileHandler )
            
            
    ## Write all Bioseq of BioseqDB in a formatted fasta file (60 character long)
    #
    # @param outFaFileName file name of fasta file
    # @param mode 'write' or 'append'
    #
    def save( self, outFaFileName, mode="w" ):
        outFaFile = open( outFaFileName, mode )
        self.write( outFaFile )
        outFaFile.close()
        
        
    ## Read a formatted fasta file and load it in the BioseqDB instance
    #
    # @param inFaFileName file name of fasta file
    #    
    def load(self, inFaFileName):
        fichier = open(inFaFileName)
        self.read(fichier)
        fichier.close()
        
        
    ## Reverse each sequence of the collection
    #
    def reverse( self ):
        for bs in self.db:
            bs.reverse()
            
            
    ## Turn each sequence into its complement
    #
    def complement( self ):
        for bs in self.db:
            bs.complement()
            
            
    ## Reverse and complement each sequence
    #
    def reverseComplement( self ):
        for bs in self.db:
            bs.reverseComplement()
            
            
    ## Set the collection from a list of Bioseq instances
    #
    def setData( self, lBioseqs ):
        for i in lBioseqs:
            self.add( i )
            
            
    ## Initialization of each attribute of the collection
    #
    def reset( self ):
        self.db = []
        self.idx = {}
        self.name = None
        self.mean_seq_lgth = None
        self.stat.reset()
        
        
    ## Remove all the gap of the sequences of the collection
    #
    def cleanGap(self): 
        for iBioSeq in self.db:
            iBioSeq.cleanGap()
            
            
    ## Add a Bioseq instance and update the attributes
    #
    # @param bs a Bioseq instance
    # 
    def add( self, bs ):
        if self.idx.has_key( bs.header ):
            sys.stderr.write( "ERROR: two sequences with same header '%s'\n" % ( bs.header ) )
            sys.exit(1)
        self.db.append( bs )
        self.idx[ bs.header ] = len(self.db) - 1
        self.idx_renamed[ bs.header.replace("::","-").replace(":","-").replace(",","-").replace(" ","_") ] = len(self.db) - 1
        
        
    ## Give the Bioseq instance corresponding to specified index
    #
    # @return a Bioseq instance
    #
    def __getitem__(self,index):
        if index < len(self.db):
            return self.db[index]
        
        
    ## Give the number of sequences in the bank
    #
    # @return an integer
    #
    def getSize( self ):
        return len( self.db )
    
    
    ## Give the cumulative sequence length in the bank
    #
    # @return an integer
    #
    def getLength( self ):
        cumLength = 0
        for iBioseq in self.db:
            cumLength += iBioseq.getLength()

        return cumLength
    
    
    ## Return the length of a given sequence via its header
    #
    # @return an integer
    #
    def getSeqLength( self, header ):
        return self.fetch(header).getLength()
    
    
    ## Return a list with the sequence headers
    #
    def getHeaderList( self ):
        lHeaders = []
        for bs in self.db:
            lHeaders.append( bs.header )
        return lHeaders
    
    
    ## Give the Bioseq instance of the BioseqDB specified by its header
    # 
    # @warning name of this method not appropriate getBioseqByHeader is proposed
    # @param header string
    # @return a Bioseq instance
    #
    def fetch( self, header ):
        return self.db[self.idx[header]]
    
    
    ## Give the Bioseq instance of the BioseqDB specified by its renamed header
    # In renamed header "::", ":", "," character are been replaced by "-" and " " by "_"
    #
    # @param renamedHeader string
    # @return a Bioseq instance
    #
    def getBioseqByRenamedHeader( self, renamedHeader ):
        return self.db[self.idx_renamed[renamedHeader]]
    
    
    ## Count the number of times the given nucleotide is present in the bank.
    #
    # @param nt character (nt or aa)
    # @return an integer
    #
    def countNt( self, nt ):
        total = 0
        for iBioseq in self.db:
            total+= iBioseq.sequence.count( nt )
        return total
    
    
    ## Count the number of times each nucleotide (A,T,G,C,N) is present in the bank.
    #
    # @return a dictionary with nucleotide as key and an integer as values
    #
    def countAllNt( self ):
        dNt2Count = {}
        for nt in ["A","T","G","C","N"]:
            dNt2Count[ nt ] = self.countNt( nt )
        return dNt2Count
    
    
    ## Extract a sub BioseqDB of specified size which beginning at specified start
    #
    # @param start integer index of first included Bioseq
    # @param size integer size of expected BioseqDB 
    # @return a BioseqDB
    #
    def extractPart(self, start, size):
        iShorterBioseqDB = BioseqDB()
        for iBioseq in self.db[start:(start + size)]:
            iShorterBioseqDB.add(iBioseq)    
        return iShorterBioseqDB  
    
    
    ## Extract a sub BioseqDB with the specified number of best length Bioseq
    #
    # @param numBioseq integer the number of Bioseq searched
    # @return a BioseqDB
    #
    def bestLength(self, numBioseq):
        length_list = []
        numseq = 0
        for each_seq in self.db:
            if each_seq.sequence == None:
                l=0
            else:
                l = each_seq.getLength()
            length_list.append(l)
            numseq = numseq + 1

        length_list.sort()
        size = len(length_list)
        if numBioseq < size:
            len_min = length_list[size-numBioseq]
        else:
            len_min = length_list[0]

        numseq = 0
        nbsave = 0
        bestSeqs = BioseqDB()
        bestSeqs.setName(self.name)
        for each_seq in self.db:
            if each_seq.sequence == None:
                l=0 
            else :
                l = each_seq.getLength()
            numseq = numseq + 1
            if l >= len_min:
                bestSeqs.add(each_seq)
                nbsave = nbsave + 1
            if nbsave == numBioseq :
                break      
        return bestSeqs
    
    
    ## Extract a sub BioseqDB from a file with Bioseq header containing the specified pattern
    #
    # @param pattern regular expression of wished Bioseq header
    # @param inFileName name of fasta file in which we want extract the BioseqDB
    #
    def extractPatternOfFile(self, pattern, inFileName):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        file_db=open(inFileName)
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
        
        
    ## Extract a sub BioseqDB from the instance with all Bioseq header containing the specified pattern
    #
    # @param pattern regular expression of wished Bioseq header
    #
    # @return a BioseqDB
    #
    def getByPattern(self,pattern):
        if pattern=="" :
            return
        iBioseqDB=BioseqDB()
        srch=re.compile(pattern)
        for iBioseq in self.db:
            if srch.search(iBioseq.header):
                iBioseqDB.add(iBioseq)
        return iBioseqDB
    
    
    ## Remove from the instance all Bioseq which header contains the specified pattern
    #
    # @param pattern regular expression of not wished Bioseq header
    #
    def rmByPattern(self,pattern):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        for seq in self.db:
            if srch.search(seq.header):
                self.db.remove(seq)     
                
                
    ## Copy a part from another BioseqDB in the BioseqDB if Bioseq have got header containing the specified pattern
    # 
    # @warning this method is called extractPattern in pyRepet.seq.BioseqDB
    #
    # @param pattern regular expression of wished Bioseq header
    # @param sourceBioseqDB the BioseqDB from which we want extract Bioseq
    #
    def addBioseqFromABioseqDBIfHeaderContainPattern(self, pattern, sourceBioseqDB):
        if pattern=="" :
            return
        srch=re.compile(pattern)
        for seq in sourceBioseqDB.db:
            m=srch.search(seq.header)
            if m:
                self.add(seq)   
                
                
    ## Up-case the sequence characters in all sequences
    # 
    def upCase( self ):
        for bs in self.db:
            bs.upCase()
            
            
    ## Split each gapped Bioseq in a list and store all in a dictionary
    #
    # @return a dict, keys are bioseq headers, values are list of Map instances 
    #
    def getDictOfLMapsWithoutGaps( self ):
        dSeq2Maps = {}

        for bs in self.db:
            dSeq2Maps[ bs.header ] = bs.getLMapWhithoutGap()

        return dSeq2Maps
 