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
import math

class SequenceList(object):
    """A class that codes for a list of sequences"""

    def __init__(self, verbosity = 0):
        self.sequences = []
        self.verbosity = verbosity


    def nbSequences(self):
        return len(self.sequences)


    def getSequence(self, index):
        return self.sequences[index]
        

    def addSequence(self, sequence):
        self.sequences.append(sequence)
        

    def split(self, number):
        sequenceLists = []
        size = math.ceil(self.nbSequences() / number)

        sequenceList = SequenceList()
        for i in range(0, self.nbSequences()):
            sequenceList.addSequence(self.getSequence(i))
            if (sequenceList.nbSequences() == size):
                sequenceLists.append(sequenceList)
                sequenceList = SequenceList()
        if (sequenceList.nbSequences() != 0):
            sequenceLists.append(sequenceList)
        return sequenceLists


    def printFasta(self):
        string = ""
        for sequence in self.sequences:
            string += sequence.printFasta()
        return string

