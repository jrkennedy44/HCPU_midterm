
import sys, re, string, cStringIO, math, random

from pyRepet.coord.Map import *

#------------------------------------------------------------------------------

class Bioseq:

    header = ""
    sequence = ""

    #--------------------------------------------------------------------------

    def __init__( self, name="", seq="" ):
        self.header = name
        self.sequence = seq
        
    #--------------------------------------------------------------------------
        
    def _create_word_list(self,size,l=['A','T','G','C']):
        if size == 1 :
            return l
        else:
            l2 = []
            for i in l:
                for j in ['A','T','G','C']:
                    l2.append( i + j )
        return self._create_word_list(size-1,l2)
    
    #--------------------------------------------------------------------------

    def copyBioseqInstance(self, bioSeqInstanceToTranslate):
        seq1 = Bioseq()
        seq1.sequence = bioSeqInstanceToTranslate.sequence
        seq1.header = bioSeqInstanceToTranslate.header
        return seq1
    
    #--------------------------------------------------------------------------


    def setFrameInfoOnHeader(self, bioSeqInstance, phase):
        if " " in bioSeqInstance.header:
            name, desc = bioSeqInstance.header.split(" ", 1)
            name = name + "_" + str(phase)
            bioSeqInstance.header = name + " " + desc
        else:
            bioSeqInstance.header = bioSeqInstance.header + "_" + str(phase)
        

    #--------------------------------------------------------------------------

    def read( self, faFile ):
        line = faFile.readline()
	if line == "":
	    self.header = None
	    self.sequence = None
	    return
        if line[0] == '>':
	    self.header = string.rstrip(line[1:])
        else:
	    print "error, line is",string.rstrip(line)
	    return
        line = " "
	seq = cStringIO.StringIO()
	while line:
	    prev_pos = faFile.tell()
	    line = faFile.readline()
	    if line == "":
	        break
	    if line[0] == '>':
	        faFile.seek( prev_pos )
		break
	    seq.write( string.rstrip(line) )
	self.sequence = seq.getvalue()
    
    
    #--------------------------------------------------------------------------

    def read_extract(self,file):
	while 1:
	    line=file.readline()
	    if line=="":
	        self.header=None
		self.sequence=None
		return
	    if line[0]=='>':
	        self.header=string.rstrip(line[1:])
		break
	line=" "
	seq=cStringIO.StringIO()
	while line:
	    prev_pos=file.tell()
	    line=file.readline()
	    if line=="":
	        break
	    if line[0]=='>' or  line[0]==' ' or  line[0]=='\n':
	        file.seek(prev_pos)
		break
	    seq.write(string.rstrip(line))
	self.sequence=seq.getvalue()

    #--------------------------------------------------------------------------

    def load( self, faFileName ):
        faFile = open( faFileName )
	self.read( faFile )

    #--------------------------------------------------------------------------

    def save( self, faFileName ):
        faFile = open( faFileName, "a" )
	self.write( faFile )
	faFile.close()

    #--------------------------------------------------------------------------

    def write( self, outFile ):
        outFile.write( ">" + self.header + "\n" )
	i = 0
	while i < self.getLength():
	    outFile.write( self.sequence[i:i+60] + "\n" )
	    i += 60

    #--------------------------------------------------------------------------

    def writeWithOtherHeader( self, outFile, newHeader ):
        outFile.write( ">" + newHeader + "\n" )
	i = 0
	while i < self.getLength():
	    outFile.write( self.sequence[i:i+60] + "\n" )
	    i += 60

    #--------------------------------------------------------------------------

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

    #--------------------------------------------------------------------------

    def view(self,l=0):
        print '>'+self.header
	i=0
	if(l==0):
	    l=len(self.sequence)
	seq=self.sequence[0:l]
		
	while i<len(seq):
	    print seq[i:i+60]
	    i=i+60		

    #--------------------------------------------------------------------------

    def getLength( self ):

        """
        return the length of the sequence
        """

        return len(self.sequence)

    #--------------------------------------------------------------------------

    def getSeqAsFasta( self ):

        """
        return the sequence in fasta format
        """

        seq = ""
        i = 0
	while i < self.getLength():
	    seq += self.sequence[i:i+60] + "\n"
	    i += 60

        return seq

    #--------------------------------------------------------------------------

    def countNt( self, nt ):

        """
        Count the number of times the given nucleotide is present in the sequence.
        """

        return self.sequence.count( nt )

    #--------------------------------------------------------------------------

    def countAllNt( self ):

        """
        Count the occurences for each nucleotide (A,T,G,C,N).
        """

        dNt2Count = {}
        for nt in ["A","T","G","C","N"]:
            dNt2Count[ nt ] = self.countNt( nt )
        return dNt2Count

    #--------------------------------------------------------------------------

    def occ_word( self, size ):

        occ = {}
	nbword = 0
	srch = re.compile('[^ATGC]+')
	wordlist = self._create_word_list( size )
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

    #--------------------------------------------------------------------------

    def freq_word( self, size ):

        """
	Calculate the frequence of any word of size 'size'.
	Return a dictionary whose keys are the words, and values are the frequencies.
	"""

	dOcc, nbWords = self.occ_word( size )
	freq = {}
	for word in dOcc.keys():
	    freq[word] = float(dOcc[word]) / nbWords
	return freq

    #--------------------------------------------------------------------------

    def countCpG(self):
        occ1,nbword1=self.occ_word(1)
	occ2,nbword2=self.occ_word(2)

	pG=float(occ1["G"])/nbword1
	pC=float(occ1["C"])/nbword1
	pCG=float(occ2["CG"])/nbword2

	return math.log(pCG/(pG*pC))/math.log(2),pCG,pC,pG

    #--------------------------------------------------------------------------

    def markov(self,ordre):
        occ,nbword=self.occ_word(ordre+1)
	count={}
	proba={}
	for i in occ.keys():
	    evt=i[-1]
	    cond=i[:-1]
	    if not count.has_key(cond):
	        count[cond]={'A':0,'T':0,'G':0,'C':0}
	    count[cond][evt]=count[cond][evt]+occ[i]
	for i in count.keys():
	    sum=0
	    for j in ['A','T','G','C']:
	        sum=sum+count[i][j]
	    proba[i]={'A':0.0,'T':0.0,'G':0.0,'C':0.0}
	    for j in ['A','T','G','C']:
	        if sum!=0:
		    proba[i][j]=float(count[i][j])/sum
	return proba

    #--------------------------------------------------------------------------

    def entropy( self, size=1 ):

        """
    	compute the entropy of the sequence
	    """

	freq = self.freq_word( size )
	my_sum = 0
	base = math.log(4)
	if size > 1:
	    prob = self.markov( size - 1 )		
	    for i in freq.keys():
	        evt = i[-1]
		cond = i[:-1]
		p = prob[cond][evt]
		if p != 0:
		    my_sum = my_sum + freq[i] * (math.log(p)/base)
	else:
	    for word in freq.keys():
	        p = freq[word]
		if p != 0:
		    my_sum = my_sum + p * (math.log(p)/base)
	return -my_sum

    #--------------------------------------------------------------------------

    def shuffle( self, seed=1 ):

        rng = random.Random( seed )
	lenseq = len(self.sequence)
	newseq = ""
	index = range(lenseq)
	random.shuffle( index )
	for i in index:
	    newseq = newseq + self.sequence[i]
	s = Bioseq()
	s.sequence = newseq
	s.header = "%s shuffled" % ( self.header )
	return s

    #--------------------------------------------------------------------------

    def rel_entropy( self, reffreq ):

        size = len(reffreq.keys()[0])
	occ = self.occ_word( size )
	nbword = len(self.sequence) - size
	freq = {}
	for i in occ.keys():
	    freq[i] = float(occ[i]+1) / nbword
	sum = 0
	for i in freq.keys():
	    f = freq[i]
	    r = reffreq[i]
	    sum = sum + f * ( math.log(f/r) / math.log(4) )
	return -sum

    #--------------------------------------------------------------------------

    def complement( self ):

        """
        return the reverse complement of the sequence        
        """
        #We need capital letters !
        Bioseq.upCase( self )
        complement = ""

	for i in xrange(len(self.sequence)-1,-1,-1):
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
	    else:
	        print "*** Warning:",self.sequence[i],"unknown, replacing by N"
		complement += "N"

	return complement

#--------------------------------------------------------------------------

    def realComplement( self ):

        """
        return the complement of the sequence
        """

        complement = ""
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
            else:
                print "*** Warning:",self.sequence[i],"unknown, replacing by N"
                complement += "N"

        return complement
               
                
    #--------------------------------------------------------------------------

    def findORF(self):
        orf = {0:[],1:[],2:[]}
        length = len(self.sequence)
        for i in xrange(0,length):
           if ( self.sequence[i:i+3] == "TAA" or
		                 self.sequence[i:i+3] == "TAG" or
		                       self.sequence[i:i+3] == "TGA" ):
                   phase = i % 3
                   orf[phase].append( i )
        return orf

    #--------------------------------------------------------------------------

    def upCase( self ):

        """
        convert the sequence into upper case
        """

        newSeq = string.upper( self.sequence )
        self.sequence = newSeq

    #--------------------------------------------------------------------------

    def lowCase( self ):

        """
        convert the sequence into lower case
        """

        newSeq = string.lower( self.sequence )
        self.sequence = newSeq

    #--------------------------------------------------------------------------

    def reverse( self ):

        """
	reverse the sequence
	"""

	return self.sequence[::-1]

    #--------------------------------------------------------------------------

    def getClusterID( self ):

        """
	extract the cluster of the fragment (output from Grouper)
	"""

	data = self.header.split()
	return data[0].split("Cl")[1]

    #--------------------------------------------------------------------------

    def getGroupID( self ):

        """
	extract the group of the sequence (output from Grouper)
	"""

	data = self.header.split()
	return data[0].split("Gr")[1].split("Cl")[0]

    #--------------------------------------------------------------------------

    def getHeaderFullSeq( self ):

        """
	return the header of the full sequence (output from Grouper)
	( 'Dmel_Grouper_3091_Malign_3:LARD' from '>MbS1566Gr81Cl81 Dmel_Grouper_3091_Malign_3:LARD {Fragment} 1..5203' )
	"""

	data = self.header.split()
	return data[1]

    #--------------------------------------------------------------------------

    def getFragStrand( self ):

        """
        return the strand of the fragment (output from Grouper)

        @return: strand (+ or -)
        @rtype: string
        """

        data = self.header.split()
        coord = data[3].split("..")
        if int(coord[0]) < int(coord[-1]):
            return "+"
        else:
            return "-"

    #--------------------------------------------------------------------------

    def getATGCNFromIUPAC( self, nt ):

        """
        Return A, T, G, C or N from an IUPAC letter.
        IUPAC = ['A','T','G','C','U','R','Y','M','K','W','S','B','D','H','V','N']
        """

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

    #--------------------------------------------------------------------------

    def IUPAC_checkNt( self ):

        """
        Check the sequence is made of nucleotides from the IUPAC nomenclature. Otherwise, replace by 'N'.
        """

        newSeq = ""

        for nt in self.sequence:
            newSeq += self.getATGCFromIUPAC( nt )

        self.sequence = newSeq

    #--------------------------------------------------------------------------

    def partialIUPAC( self ):

        """
        Replace any symbol not in (A,T,G,C,N) by another nucleotide it represents.
        """

        newSeq = ""

        for nt in self.sequence:
            newSeq += self.getATGCNFromIUPAC( nt )

        self.sequence = newSeq

    #--------------------------------------------------------------------------

    def checkEOF( self ):

        """
        Remove non Unix end-of-line symbols, if any.
        """

        symbol = "\r"   # corresponds to '^M' from Windows

        if symbol in self.sequence:
            print  "** Warning: Windows EOF removed in %s" % ( self.header )
            sys.stdout.flush()
            newSeq = self.sequence.replace( symbol, "" )
            self.sequence = newSeq

    #--------------------------------------------------------------------------

    def getMap( self ):

        """
        
        """

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
                    endMap = countSite - 1
                    lMaps.append( Map( "%s_subSeq%i" % (self.header,countSubseq), self.header, startMap, endMap ) )

        return lMaps
