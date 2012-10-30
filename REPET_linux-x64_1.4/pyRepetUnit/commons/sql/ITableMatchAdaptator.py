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


## Interface for TableMatchAdaptator
#
class ITableMatchAdaptator(object):
        
    ## Give a list of Match instances given a query name
    #
    # @param query string sequence name
    # @return lMatches list of Match instances
    #
    def getMatchListFromQuery( self, query ):
        pass
    
    ## Give a list of Match instances having the same identifier
    #
    # @param id integer identifier number
    # @return lMatch a list of Match instances
    #
    def getMatchListFromId( self, id ):
        pass
    
    ## Insert a Match instance
    #
    # @param iMatch a Match instance
    # @param delayed boolean
    #
    def insert(self, iMatch, delayed = False):
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