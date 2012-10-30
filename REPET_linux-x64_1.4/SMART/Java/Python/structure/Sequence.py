#
# Copyright INRA-URGI 2009-2010
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software. You can use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
# 
# As a counterpart to the access to the source code and rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty and the software's author, the holder of the
# economic rights, and the successive licensors have only limited
# liability.
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading, using, modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean that it is complicated to manipulate, and that also
# therefore means that it is reserved for developers and experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and, more generally, to use and operate it in the
# same conditions as regards security.
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
#
import sys
import re
from pyRepetUnit.commons.seq.Bioseq import Bioseq

reverseComplementString = {
    "A": "T",
    "C": "G",
    "G": "C",
    "T": "A",
    "U": "A",
    "M": "K",
    "R": "Y",
    "W": "W",
    "S": "S",
    "Y": "R",
    "K": "M",
    "V": "B",
    "H": "D",
    "D": "H",
    "B": "V",
    "N": "N",
    "a": "t",
    "c": "g",
    "g": "c",
    "t": "a",
    "u": "a",
    "m": "k",
    "r": "y",
    "w": "w",
    "s": "s",
    "y": "r",
    "k": "m",
    "v": "b",
    "h": "d",
    "d": "h",
    "b": "v",
    "n": "n"
}

class Sequence(Bioseq):
    """A class that codes for a sequence"""

    def __init__(self, name = "", sequence = ""):
        Bioseq.__init__(self, name, sequence)
        self.name = self.header        
        self.quality = None
        self.chunkedSequence = None
        self.chunkedQuality = None

    def setName(self, name=""):
        if not name:
            self.header = None
        else:
            self.header = name  
            
    def getName(self):
        return self.getHeader()
    
    def setSequence(self, seq=""):
        if not seq:
            self.sequence = None
        else:
            self.sequence = seq 

    def setQuality(self, quality):
        self.quality = quality
        
    def getQuality(self):
        return self.quality
    
    def getSize(self):
        return len(self.getSequence())

    def chunkSequence(self):
        self.chunkedSequence = []
        for i in range (0, self.getSize() / 60 + 1):
            self.chunkedSequence.append(self.getSequence()[i * 60 : min(self.getSize(), (i+1) * 60)])
        if self.quality != None:
            self.chunkedQuality = []
            for i in range (0, self.getSize() / 60 + 1):
                self.chunkedQuality.append(self.quality[i * 60 : min(self.getSize(), (i+1) * 60)])

    def concatenate(self, seq):
        sequence = self.getSequence()
        sequence += seq.getSequence()
        self.setSequence(sequence)
        if self.quality != None:
            self.quality += seq.getQuality()
        self.chunkedSequence = None
        self.chunkedQuality = None
        

    def printFasta(self):
        if self.chunkedSequence == None:
            self.chunkSequence()
        return ">%s\n%s\n" % (self.getHeader(), "\n".join(self.chunkedSequence))


    def printFastq(self):
        if self.chunkedSequence == None:
            self.chunkSequence()
        return "@%s\n%s\n+%s\n%s\n" % (self.getHeader(), self.getSequence(), self.getHeader(), self.quality)


    def reverseComplement(self):
        seq = ""
        self.chunkedSequence = None
        self.chunkedQuality = None
        for i in range(0, self.getSize()):
            char = self.getSequence()[i:i+1]
            if char not in reverseComplementString:
                sys.exit("Cannot understand character %s from string %s" % (char, self.getSequence()))
            seq = "%s%s" % (reverseComplementString[char], seq)
        self.setSequence(seq) 
        if self.quality != None:
            self.quality = self.quality[::-1]
        
        
    def containsAmbiguousNucleotides(self):
        m = re.search("[^ACGTUacgtu]", self.getSequence())
        if m != None:
            return True
        return False
    
    
    def shrinkToFirstNucleotides(self, nbNucleotides):
        self.chunkedSequence = None
        self.chunkedQuality = None
        self.setSequence(self.getSequence()[0:nbNucleotides])
        if self.quality != None:
            self.quality = self.quality[0:nbNucleotides]
    
    
    def shrinkToLastNucleotides(self, nbNucleotides):
        self.chunkedSequence = None
        self.chunkedQuality = None
        self.setSequence(self.getSequence()[-nbNucleotides:])
        if self.quality != None:
            self.quality = self.quality[-nbNucleotides:]
