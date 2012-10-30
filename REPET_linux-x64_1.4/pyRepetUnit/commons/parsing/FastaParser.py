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
from pyRepetUnit.commons.parsing.SequenceListParser import SequenceListParser
from SMART.Java.Python.structure.Sequence import Sequence

class FastaParser(SequenceListParser):
    """A class that reads a list of sequences in FASTA"""

    def __init__(self, fileName, verbosity = 0):
        super(FastaParser, self).__init__(fileName, verbosity)
        self.tags = {}
        
        
    def getTags(self):
        return self.tags


    def getFileFormats():
        return ["fasta", "mfa", "fas"]
    getFileFormats = staticmethod(getFileFormats)


    def getInfos(self):
        """
        Get some generic information about the sequences
        """
        self.nbSequences = 0
        self.size = 0
        self.reset()
        if self.verbosity >= 10:
            print "Getting information on %s." % (self.fileName)
        for line in self.handle:
            line = line.strip()
            if line == "":
                continue
            if line[0] == ">":
                self.nbSequences += 1
            else:
                self.size += len(line)
            if self.verbosity >= 10 and self.nbSequences % 100000 == 0:
                sys.stdout.write("    %d sequences read\r" % (self.nbSequences))
                sys.stdout.flush()
        self.reset()
        if self.verbosity >= 10:
            print "    %d sequences read" % (self.nbSequences)
            print "Done."


    def parseOne(self):
        """
        Parse only one element in the file
        """
        name     = None
        string = ""

        if self.currentLine != None:
            if self.currentLine[0] != ">":
                sys.exit("First line is weird: %s" % (self.currentLine))
            name = self.currentLine[1:].split()[0]
            self.currentLine = None
        for line in self.handle:
            line = line.strip()
            if line == "":
                pass
            elif line[0] == ">":
                if name == None:
                    name = line[1:].split()[0]
                else:
                    self.currentLine = line
                    return Sequence(name, string)
            else:
                string += line

        if name == None:
            return None
        return Sequence(name, string)
    
    
    def setTags(self):
        mark = self.handle.tell()
        thisTag = mark
        
        line = self.handle.readline()
        while line != "":
            if line[0] == ">":
                line = line.strip()
                self.tags[line[1:].split()[0]] = thisTag
            thisTag = self.handle.tell()
            line = self.handle.readline()
            
        self.handle.seek(mark)
        

    def getSubSequence(self, chromosome, start, end, direction, name = None):
        if not self.tags:
            self.setTags()

        if chromosome not in self.tags:
            sys.exit("Cannot find " + chromosome)
            
        if name == None:
            name = "%s:%d-%d (%d)" % (chromosome, start, end, direction)
        sequence = Sequence(name)
        
        self.handle.seek(self.tags[chromosome])
        line = self.handle.readline().strip()
        if line != ">" + chromosome:
            sys.exit("Arrived in a wrong place (got %s)" % (line))
            
        position1 = self.handle.tell()
        line            = self.handle.readline().strip()
        position2 = self.handle.tell()
        size            = len(line)
        address = position1 + ((start - (start % size)) / size) * (position2 - position1);

        count = max(0, start - (start % size));
        self.handle.seek(address)

        newSequence = ""
        for line in self.handle:
            line = line.strip()

            if line[0] == ">":
                break
            
            subStart = start - count
            if subStart < 0:
                subStart = 0
            subEnd    = end - count
            subSize = subEnd - subStart + 1
            if subSize + subStart > len(line):
                subSize = len(line) - subStart
            if subEnd < 0:
                break
            if subStart <= len(line):
                newSequence += line[subStart:subStart+subSize]
            count += len(line)

        if newSequence == "":
            sys.exit("Error, sequence %s is empty" % (name))
        sequence.sequence = newSequence
        if direction == -1:
            sequence.reverseComplement()
        return sequence
