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


## Interface for TableSeqAdaptator
#
class ITableSeqAdaptator(object):

    ## Retrieve all the distinct accession names in a list.
    #
    # @return lAccessions list of accessions
    #
    # @warning old name was getListAccession
    #
    def getAccessionsList( self ):
        pass
    
    ## Save sequences in a fasta file from a list of accession names.
    # 
    # @param lAccessions list of accessions
    # @param outFileName string Fasta file
    #
    # @warning old name saveListAccessionInFastaFile
    #
    def saveAccessionsListInFastaFile( self, lAccessions, outFileName ):
        pass
    
    ## insert bioseq instance
    #
    # @param seq bioseq 
    # @param delayed boolean must the insert be delayed 
    # 
    # @warning old name was insASeq
    #
    def insert(self, seq, delayed = False):
        pass