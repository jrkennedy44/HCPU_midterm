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

## Interface for TableSetAdaptator
#
class ITableSetAdaptator (object):
    
    ## Insert a set instance
    #
    # @param obj a set instance
    # @param delayed boolean indicating if the insert must be delayed
    #
    # @warning old name was insASet
    #
    def insert(self, obj, delayed = False):
        pass

    ## Insert a list of Set instances
    #
    # @param l a list of object instances
    # @param delayed boolean
    #
    # @warning old name was insSetList
    #
    def insertList(self, l, delayed = False):
        pass
    
    ## Give a list of identifier numbers contained in the table
    #
    # @return l integer list
    #
    # @warning old name was getSet_num
    #
    def getIdList(self):
        pass
    
    ## Give a list of Set instances having a given seq name
    #
    # @param seqName string seq name
    # @return lSets list of instances
    #
    # @warning old name was get_SetList_from_contig
    #
    def getSetListFromSeqName(self, seqName):
        pass
        
    ## Give a set instances list with a given identifier number
    #
    # @param id integer identifier number
    # @return lSet list of set instances
    #
    # @warning old name was getSetList_from_num
    #
    def getSetListFromId(self, id):
        pass
    
    ## Give a set instances list with a list of identifier numbers
    #
    # @param lId integers list identifiers list numbers
    # @return lSet list of set instances
    #
    # @warning old name was getSetList_from_numlist
    #   
    def getSetListFromIdList(self,lId):
        pass
    
    ## Return a list of Set instances overlapping a given sequence
    #   
    # @param seqName string sequence name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    # @warning old name was getSetList_from_qcoord
    #
    def getSetListOverlappingCoord( self, seqName, start, end ):
        pass
    
    ## Delete set corresponding to a given identifier number
    #
    # @param id integer identifier number
    #
    # @warning old name was delSet_from_num 
    #  
    def deleteFromId(self, id):
        pass
    
    ## Delete set corresponding to a given list of identifier number
    #
    # @param lId integers list list of identifier number
    #  
    # @warning old name was delSet_from_listnum 
    #
    def deleteFromIdList(self, lId):
        pass
    
    ## Join two set by changing id number of id1 and id2 set to the least of id1 and id2
    #
    # @param id1 integer id path number
    # @param id2 integer id path number
    #
    # @warning old name was joinSet
    #    
    def joinTwoSets(self, id1, id2):
        pass
    
    ## Get a new id number
    #
    # @return new_id integer max_id + 1 
    #
    def getNewId(self):
        pass
    
    ## Give the data contained in the table as a list of Sets instances
    #
    # @return lSets list of set instances
    #
    def getListOfAllSets( self ):
        pass