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


## Interface for TableMapAdaptator 
#
class ITableMapAdaptator(object):
  
    ## Insert a map instance
    #
    # @param obj map or set
    # @param delayed boolean must the insert be delayed 
    #
    # @warning old name was insAMap
    #
    def insert(self, obj, delayed=False):
        pass

        
    ## Insert a list of Map or Set or Match instances
    #
    # @param l a list of object instances
    # @param delayed boolean
    #
    # @warning old name was insMapList
    #
    def insertList(self, l, delayed = False):
        pass
    
    ## Give a list of the distinct seqName/chr present in the table
    #
    # @return lDistinctContigNames string list
    #
    # @warning old name was getContig_name
    #
    def getSeqNameList(self):
        pass
    
    
    ## Give a list of Map instances having a given seq name
    #
    # @param seqName string seq name
    # @return lMap list of instances
    #
    # @warning old name was get_MapList_from_contig
    #
    def getMapListFromSeqName(self, seqName):
        pass
    
    
    ## Return a list of Set instances from a given sequence name
    #
    # @param seqName string sequence name
    # @return lSets list of Set instances
    #
    # @warning old name was getSetList_from_contig 
    #
    def getSetListFromSeqName( self, seqName ):
        pass

    
    ## Give a map instances list overlapping a given region
    #
    # @param seqName string seq name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lMap list of map instances
    #
    # @warning old name was getMapList_from_qcoord
    #
    def getMapListOverlappingCoord(self, seqName, start, end):
        pass
    
    
    ## Return a list of Set instances overlapping a given region
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
    