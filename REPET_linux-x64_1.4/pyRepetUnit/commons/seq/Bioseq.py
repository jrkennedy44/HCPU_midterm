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
import string
import re
import random
import cStringIO
from pyRepetUnit.commons.coord.Map import Map

DNA_ALPHABET_WITH_N = set( ['A','T','G','C','N'] )
IUPAC = set(['A','T','G','C','U','R','Y','M','K','W','S','B','D','H','V','N'])


## Record a sequence with its header
#
class Bioseq( object ):
    
    header = ""
    sequence = ""
    
    ## constructor
    #
    # @param name the header of sequence
    # @param seq sequence (DNA, RNA, protein)
    #
    def __init__( self, name="", seq="" ):
        self.header = name
        self.sequence = seq
        
        
    ## Equal operator
    #        
    def __eq__( self, o ):
        if self.header==o.header and self.sequence==o.sequence:
            return True
        return False
    
    
    ## overload __repr__
    #
    def __repr__( self ):
        return "%s;%s" % ( self.header, self.sequence )
    
    
    ## set attribute header
    #
    # @param header a string
    #
    def setHeader( self, header ):
        self.header = header
        
        
    ## get attribute header
    #
    # @return header
    def getHeader(self):
        return self.header
    
    
    ## set attribute sequence
    #
    # @param sequence a string
    #
    def setSequence( self, sequence ):
        self.sequence = sequence
        
        
    def getSequence(self):
        return self.sequence
        
    ## reset
    #
    def reset( self ):
        self.setHeader( "" )
        self.setSequence( "" )
        
        
    ## Test if bioseq is empty
    #
    def isEmpty( self ):
        return self.header == "" and self.sequence == ""
    
    
    ## Reverse the sequence
    #
    def reverse( self ):
        tmp = self.sequence
        self.sequence = tmp[::-1]
        
        
    ## Turn the sequence into its complement
    #  Force upper case letters
    #  @warning: old name in pyRepet.Bioseq realComplement
    #
    def complement( self ):
        complement = ""
        self.upCase()
        for i in xrange(0,len(self.sequence),1):
            if self.sequence[i] == "A":
                complement += "T"
            elif self.sequence[i] == "T":
                complement += "A"
            elif self.sequence[i] == "C":
                complement += "G"
            elif self.sequence[i] == "G":
                complement += "C"
            elif self.sequence[i] == "M":
                complement += "K"
            elif self.sequence[i] == "R":
                complement += "Y"
            elif self.sequence[i] == "W":
                complement += "W"
            elif self.sequence[i] == "S":
                complement += "S"
            elif self.sequence[i] == "Y":
                complement += "R"
            elif self.sequence[i] == "K":
                complement += "M"
            elif self.sequence[i] == "V":
                complement += "B"
            elif self.sequence[i] == "H":
                complement += "D"
            elif self.sequence[i] == "D":
                complement += "H"
            elif self.sequence[i] == "B":
                complement += "V"
            elif self.sequence[i] == "N":
                complement += "N"
            elif self.sequence[i] == "-":
                complement += "-"
            else:
                print "WARNING: unknown symbol '%s', replacing it by N" % ( self.sequence[i] )
                complement += "N"
        self.sequence = complement
        
        
    ## Reverse and complement the sequence
    #
    #  Force upper case letters
    #  @warning: old name in pyRepet.Bioseq : complement  
    # 
    def reverseComplement( self ):
        self.reverse()
        self.complement()
        
        
    ## Remove gap in the sequence
    #
    def cleanGap(self):
        self.sequence = self.sequence.replace("-","")
        
        
    ## Copy current Bioseq Instance
    #
    # @return: a Bioseq instance, a copy of current sequence.
    #
    def copyBioseqInstance(self):
        seq = Bioseq()
        seq.sequence = self.sequence
        seq.header = self.header
        return seq
    
    
    ## Add phase information after the name of sequence in header
    #
    # @param phase integer representing phase (1, 2, 3, -1, -2, -3)
    #
    def setFrameInfoOnHeader(self, phase):
        if " " in self.header:
            name, desc = self.header.split(" ", 1)
            name = name + "_" + str(phase)
            self.header = name + " " + desc
        else:
            self.header = self.header + "_" + str(phase)
            
            
    ## Fill Bioseq attributes with fasta file
    #  
    # @param faFileHandler file handler of a fasta file
    #
    def read( self, faFileHandler ):
        line = faFileHandler.readline()
        if line == "":
            self.header = None
            self.sequence = None
            return
        while line == "\n":
            line = faFileHandler.readline()
        if line[0] == '>':
            self.header = string.rstrip(line[1:])
        else:
            print "error, line is",string.rstrip(line)
            return
        line = " "
        seq = cStringIO.StringIO()
        while line:
            prev_pos = faFileHandler.tell()
            line = faFileHandler.readline()
            if line == "":
                break
            if line[0] == '>':
                faFileHandler.seek( prev_pos )
                break
            seq.write( string.rstrip(line) )
        self.sequence = seq.getvalue()
        
        
    ## Create a subsequence with a modified header
    #  
    # @param s integer start a required subsequence
    # @param e integer end a required subsequence
    #
    # @return a Bioseq instance, a subsequence of current sequence
    #       
    def subseq( self, s, e=0 ):
        if e == 0 :
            e=len( self.sequence )
        if s > e :
            print "error: start must be < or = to end"
            return
        if s <= 0 :
            print "error: start must be > 0"
            return
        sub = Bioseq()
        sub.header = self.header + " fragment " + str(s) + ".." + str(e)
        sub.sequence = self.sequence[(s-1):e]
        return sub
    
    
    ## Print in stdout the Bioseq in fasta format with 60 characters lines
    #  
    # @param l length of required sequence default is whole sequence
    # 
    def view(self,l=0):
        print '>'+self.header
        i=0
        if(l==0):
            l=len(self.sequence)
        seq=self.sequence[0:l]
            
        while i<len(seq):
            print seq[i:i+60]
            i=i+60        
            
            
    ## Get length of sequence
    #
    # @return length of current sequence
    # 
    def getLength( self ):
        return len(self.sequence)
    
    
    ## Return the proportion of a specific character
    # 
    # @param nt character that we want to count
    #
    def propNt( self, nt ):
        return self.countNt( nt ) / float( self.getLength() )
    
    
    ## Count occurrence of specific character
    # 
    # @param nt character that we want to count
    #
    # @return nb of occurrences
    #
    def countNt( self, nt ):
        return self.sequence.count( nt )
    
    
    ## Count occurrence of each nucleotide in current seq 
    #
    # @return a dict, keys are nucleotides, values are nb of occurrences
    #
    def countAllNt( self ):
        dNt2Count = {}
        for nt in ["A","T","G","C","N"]:
            dNt2Count[ nt ] = self.countNt( nt )
        return dNt2Count
    
    
    ## Return a dict with the number of occurrences for each combination of ATGC of specified size and number of word found
    #
    # @param size integer required length word
    #
    def occ_word( self, size ):
        occ = {}
        if size == 0:
            return occ,0
        nbword = 0
        srch = re.compile('[^ATGC]+')
        wordlist = self._createWordList( size )
        for i in wordlist:
            occ[i] = 0
        lenseq = len(self.sequence)
        i = 0
        while i < lenseq-size+1:
            word = self.sequence[i:i+size].upper()
            m = srch.search(word)
            if m == None:
                occ[word] = occ[word]+1
                nbword = nbword + 1
                i = i + 1
            else:
                i = i + m.end(0)
        return occ, nbword
    
    
    ## Return a dictionary with the frequency of occurs for each combination of ATGC of specified size
    #
    # @param size integer required length word
    #
    def freq_word( self, size ):
        dOcc, nbWords = self.occ_word( size )
        freq = {}
        for word in dOcc.keys():
            freq[word] = float(dOcc[word]) / nbWords
        return freq
    
    
    ## Find ORF in each phase
    #
    # @return: a dict, keys are phases, values are stop codon positions.
    #
    def findORF (self):
        orf = {0:[],1:[],2:[]}
        length = len (self.sequence)
        for i in xrange(0,length):
            triplet = self.sequence[i:i+3] 
            if ( triplet == "TAA" or triplet == "TAG" or triplet == "TGA"):
                phase = i % 3
                orf[phase].append(i)
        return orf
    
    
    ## Convert the sequence into upper case
    #
    def upCase( self ):
        newSeq = string.upper( self.sequence )
        self.sequence = newSeq
        
        
    ## Convert the sequence into lower case
    #
    def lowCase( self ):
        newSeq = string.lower( self.sequence )
        self.sequence = newSeq
        
        
    ## Extract the cluster of the fragment (output from Grouper)
    #
    # @return cluster id (string)
    #    
    def getClusterID( self ):
        data = self.header.split()
        return data[0].split("Cl")[1]
    
    
    ## Extract the group of the sequence (output from Grouper)
    #
    # @return group id (string)
    #
    def getGroupID( self ):
        data = self.header.split()
        return data[0].split("Gr")[1].split("Cl")[0]
    
    
    ## Get the header of the full sequence (output from Grouper)
    #
    # @example  'Dmel_Grouper_3091_Malign_3:LARD' from '>MbS1566Gr81Cl81 Dmel_Grouper_3091_Malign_3:LARD {Fragment} 1..5203' 
    # @return header (string)
    #
    def getHeaderFullSeq( self ):
        data = self.header.split()
        return data[1]
    
    
    ## Get the strand of the fragment (output from Grouper)
    #
    # @return: strand (+ or -)
    #
    def getFragStrand( self ):
        data = self.header.split()
        coord = data[3].split("..")
        if int(coord[0]) < int(coord[-1]):
            return "+"
        else:
            return "-"
        
        
    ## Get A, T, G, C or N from an IUPAC letter
    #  IUPAC = ['A','T','G','C','U','R','Y','M','K','W','S','B','D','H','V','N']
    #
    # @return A, T, G, C or N
    #
    def getATGCNFromIUPAC( self, nt ):
        subset = ["A","T","G","C","N"]

        if nt in subset:
            return nt
        elif nt == "U":
            return "T"
        elif nt == "R":
            return random.choice( "AG" )
        elif nt == "Y":
            return random.choice( "CT" )
        elif nt == "M":
            return random.choice( "CA" )
        elif nt == "K":
            return random.choice( "TG" )
        elif nt == "W":
            return random.choice( "TA" )
        elif nt == "S":
            return random.choice( "CG" )
        elif nt == "B":
            return random.choice( "CTG" )
        elif nt == "D":
            return random.choice( "ATG" )
        elif nt == "H":
            return random.choice( "ATC" )
        elif nt == "V":
            return random.choice( "ACG" )
        else:
            return "N"
        
        
    def getSeqWithOnlyATGCN( self ):
        newSeq = ""
        for nt in self.sequence:
            newSeq += self.getATGCNFromIUPAC( nt )
        return newSeq
    
    
    ## Replace any symbol not in (A,T,G,C,N) by another nucleotide it represents
    #
    def partialIUPAC( self ):
        self.sequence = self.getSeqWithOnlyATGCN()
    
    
    ## Remove non Unix end-of-line symbols, if any
    #
    def checkEOF( self ):
        symbol = "\r"   # corresponds to '^M' from Windows
        if symbol in self.sequence:
            print "WARNING: Windows EOF removed in '%s'" % ( self.header )
            sys.stdout.flush()
            newSeq = self.sequence.replace( symbol, "" )
            self.sequence = newSeq
            
            
    ## Write Bioseq instance into a fasta file handler
    #
    # @param faFileHandler file handler of a fasta file
    # 
    def write( self, faFileHandler ):
        faFileHandler.write( ">%s\n" % ( self.header ) )
        self.writeSeqInFasta( faFileHandler )
        
        
    ## Write only the sequence of Bioseq instance into a fasta file handler
    #
    # @param faFileHandler file handler of a fasta file
    #
    def writeSeqInFasta( self, faFileHandler ):
        i = 0
        while i < self.getLength():
            faFileHandler.write( "%s\n" % ( self.sequence[i:i+60] ) )
            i += 60
            
            
    ## Append Bioseq instance to a fasta file
    #
    # @param faFile name of a fasta file as a string
    # @param mode 'write' or 'append'
    #
    def save( self, faFile, mode="a" ):
        faFileHandler = open( faFile, mode )
        self.write( faFileHandler )
        faFileHandler.close()
        
        
    ## Append Bioseq instance to a fasta file
    #  
    # @param faFile name of a fasta file as a string
    #
    def appendBioseqInFile( self, faFile ):
        self.save( faFile, "a" )
        
        
    ## Write Bioseq instance into a fasta file handler
    #  
    # @param faFileHandler file handler on a file with writing right
    #
    def writeABioseqInAFastaFile( self, faFileHandler ):
        self.write( faFileHandler )
        
        
    ## Write Bioseq instance with other header into a fasta file handler
    #
    # @param faFileHandler file handler on a file with writing right
    # @param otherHeader a string representing a new header (without the > and the \n)
    #
    def writeWithOtherHeader( self, faFileHandler, otherHeader ):
        self.header = otherHeader
        self.write( faFileHandler )
        
        
    ## Append Bioseq header and Bioseq sequence in a fasta file
    #  
    # @param faFileHandler file handler on a file with writing right
    # @param otherHeader a string representing a new header (without the > and the \n)
    #
    def writeABioseqInAFastaFileWithOtherHeader( self, faFileHandler, otherHeader ):
        self.writeWithOtherHeader( faFileHandler, otherHeader )
        
        
    ## get the list of Maps corresponding to seq without gap
    #
    # @warning This method was called getMap() in pyRepet.Bioseq
    # @return a list of Map object 
    # 
    def getLMapWhithoutGap( self ):
        lMaps = []
        countSite = 1
        countSubseq = 1
        inGap = False
        startMap = -1
        endMap = -1

        # initialize with the first site
        if self.sequence[0] == "-":
            inGap = True
        else:
            startMap = countSite

        # for each remaining site
        for site in self.sequence[1:]:
            countSite += 1

            # if it is a gap
            if site == "-":

                # if this is the beginning of a gap, record the previous subsequence
                if inGap == False:
                    inGap = True
                    endMap = countSite - 1
                    lMaps.append( Map( "%s_subSeq%i" % (self.header,countSubseq), self.header, startMap, endMap ) )
                    countSubseq += 1

            # if it is NOT a gap
            if site != "-":

                # if it is the end of a gap, begin the next subsequence
                if inGap == True:
                    inGap = False
                    startMap = countSite

                # if it is the last site
                if countSite == self.getLength():
                    endMap = countSite
                    lMaps.append( Map( "%s_subSeq%i" % (self.header,countSubseq), self.header, startMap, endMap ) )

        return lMaps
    
    
    ## get the percentage of GC
    #
    # @return a percentage
    # 
    def getGCpercentage( self ):
        tmpSeq = self.getSeqWithOnlyATGCN()
        nbGC = tmpSeq.count( "G" ) + tmpSeq.count( "C" )
        return 100 * nbGC / float( self.getLength() )
    
    ## get the percentage of GC of a sequence without counting N in sequence length
    #
    # @return a percentage
    # 
    def getGCpercentageInSequenceWithoutCountNInLength(self):
        tmpSeq = self.getSeqWithOnlyATGCN()
        nbGC = tmpSeq.count( "G" ) + tmpSeq.count( "C" )
        return 100 * nbGC / float( len(self.sequence) - self.countNt("N") )
    
    ## get the 5 prime subsequence of a given length at the given position 
    #
    # @param position integer
    # @param flankLength integer subsequence length
    # @return a sequence string
    # 
    def get5PrimeFlank(self, position, flankLength):
        if(position == 1):
            return ""
        else:
            startOfFlank = 1
            endOfFlank = position -1
        
            if((position - flankLength) > 0):
                startOfFlank = position - flankLength
            else:
                startOfFlank = 1
            
            return self.subseq(startOfFlank, endOfFlank).sequence
            
            
    ## get the 3 prime subsequence of a given length at the given position 
    #  In the case of indels, the polymorphism length can be specified
    #
    # @param position integer
    # @param flankLength integer subsequence length
    # @param polymLength integer polymorphism length
    # @return a sequence string
    # 
    def get3PrimeFlank(self, position, flankLength, polymLength = 1):
        if((position + polymLength) > len( self.sequence )):
            return ""
        else:
            startOfFlank = position + polymLength
         
            if((position+polymLength+flankLength) > len( self.sequence )):
                endOfFlank =  len( self.sequence )
            else:
                endOfFlank =  position+polymLength+flankLength-1
        
            return self.subseq(startOfFlank, endOfFlank).sequence
    
    
    def _createWordList(self,size,l=['A','T','G','C']):
        if size == 1 :
            return l
        else:
            l2 = []
            for i in l:
                for j in ['A','T','G','C']:
                    l2.append( i + j )
        return self._createWordList(size-1,l2)
    
    
    def removeSymbol( self, symbol ):
        tmp = self.sequence.replace( symbol, "" )
        self.sequence = tmp
