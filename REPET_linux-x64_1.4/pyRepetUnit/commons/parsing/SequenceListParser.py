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
from SMART.Java.Python.structure.SequenceList import SequenceList
from SMART.Java.Python.misc.Progress import Progress

class SequenceListParser(object):
    """
    A virtual class that reads a list of sequences
    @ivar verbosity:             verbosity
    @type verbosity:             int
    @ivar fileName:                name of the file to parse
    @type fileName:                string
    @ivar handle:                    file to parse
    @type handle:                    file
    @ivar nbSequences:         number of sequences in the file
    @type nbSequences:         int
    @ivar nbReadSequences: number of sequences read
    @type nbReadSequences: int
    @ivar currentLine:         line currently read
    @type currentLine:         string
    @ivar size:                        total number of nucleotides in the sequences
    @type size:                        int
    @ivar sizes:                     number of nucleotides per sequences
    @type sizes:                     dict of string to int
    """

    def __init__(self, fileName, verbosity = 0):
        """
        Constructor
        @param verbosity:             verbosity
        @type    verbosity:             int
        @param fileName:                name of the file to parse
        @type    fileName:                string
        """
        self.verbosity = verbosity
        self.fileName = fileName
        self.nbSequences = None
        self.nbReadSequences = 0
        self.currentLine = None
        self.size = None
        self.sizes = None
        try:
            self.handle = open(self.fileName)
        except IOError:
            sys.exit("Error! Sequence file '%s' does not exist! Exiting..." % (self.fileName))


    def __del__(self):
        """
        Destructor
        """
        if not self.handle.closed:
            self.handle.close()
        

    def close(self):
        """
        Close file handle
        """
        self.handle.close()
        

    def reset(self):
        """
        Prepare the file to be read again from start
        """
        self.handle.seek(0)
        self.currentLine = None
        self.nbReadSequences = 0
                
        
    def getFileFormats(self):
        pass
    getFileFormats = staticmethod(getFileFormats)


    def parse(self):
        """
        Parse the whole file in one shot
        @return: a list of sequence
        """
        sequenceList = SequenceList()
        progress = Progress(self.getNbSequences(), "Reading %s" % (self.fileName), self.verbosity)
        for sequence in self.getIterator():
            sequenceList.addSequence(sequence)
            progress.inc()
        progress.done()
        return sequenceList


    def getIterator(self):
        """
        Iterate on the file, sequence by sequence
        @return: an iterator to sequences
        """
        self.reset()
        sequence = self.parseOne()
        while sequence != None:
            self.nbReadSequences += 1
            yield sequence
            sequence = self.parseOne()


    def getInfos(self):
        """
        Get some generic information about the sequences
        """
        self.nbSequences = 0
        self.size = 0
        self.reset()
        if self.verbosity >= 10:
            print "Getting information on %s." % (self.fileName)
        for sequence in self.getIterator():
            self.nbSequences += 1
            self.size += sequence.getSize()
            if self.verbosity >= 10 and self.nbSequences % 100000 == 0:
                sys.stdout.write("    %d sequences read\r" % (self.nbSequences))
                sys.stdout.flush()
        self.reset()
        if self.verbosity >= 10:
            print "    %d sequences read" % (self.nbSequences)
            print "Done."

    
    def getNbSequences(self):
        """
        Get the number of sequences in the file
        @return: the number of sequences
        """
        if self.nbSequences != None:
            return self.nbSequences
        self.getInfos()
        return self.nbSequences


    def getNbItems(self):
        """
        Get the number of sequences in the file
        @return: the number of sequences
        """
        return self.getNbSequences()


    def getSize(self):
        """
        Get the size of all the sequences
        @return: the size
        """
        if self.size != None:
            return self.size
        self.getInfos()
        return self.size
    

    def getRegions(self):
        """
        Get the names of the sequences
        @return: the names
        """
        if self.sizes != None:
            return self.sizes.keys()

        self.sizes = {}
        self.reset()
        if self.verbosity >= 10:
            print "Getting information on %s." % (self.fileName)
        self.nbSequences = 0
        for sequence in self.getIterator():
            self.sizes[sequence.name] = sequence.getSize()
            self.nbSequences += 1
            if self.verbosity >= 10 and self.nbSequences % 100000 == 0:
                sys.stdout.write("    %d sequences read\r" % (self.nbSequences))
                sys.stdout.flush()
        self.reset()
        if self.verbosity >= 10:
            print "    %d sequences read" % (self.nbSequences)
            print "Done."
        return self.sizes.keys()
            
            
    def getSizeOfRegion(self, region):
        """
        Get the size of a sequence
        @param region: the name of the sequence
        @type    region: string
        @return: the size of the sequence
        """
        if self.sizes != None:
            if region not in self.sizes:
                sys.exit("Region %s is not found" % region)
            return self.sizes[region]

        self.getRegions()
        if region not in self.sizes:
            sys.exit("Region %s is not found" % region)
            
    def __eq__(self, o):
        return self.fileName == o.fileName and self.nbSequences == o.nbSequences
            
        


