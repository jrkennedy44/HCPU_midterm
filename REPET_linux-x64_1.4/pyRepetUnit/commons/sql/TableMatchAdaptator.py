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


from pyRepetUnit.commons.sql.TableAdaptator import TableAdaptator
from pyRepetUnit.commons.sql.ITableMatchAdaptator import ITableMatchAdaptator
from pyRepetUnit.commons.coord.Match import Match

## Adaptator for Match table
#
class TableMatchAdaptator( TableAdaptator, ITableMatchAdaptator ):
        
    ## Give a list of Match instances given a query name
    #
    # @param query string sequence name
    # @return lMatches list of Match instances
    #
    def getMatchListFromQuery( self, query ):
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s';" % ( self._table, query )
        return self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
    
    ## Give a list of Match instances having the same identifier
    #
    # @param id integer identifier number
    # @return lMatch a list of Match instances
    #
    def getMatchListFromId( self, id ):
        sqlCmd = "SELECT * FROM %s WHERE path='%d';" % ( self._table, id )
        lMatch = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lMatch
    
    ## Give a list of Match instances according to the given list of identifier numbers
    #
    # @param lId integer list 
    # @return lMatch a list of Match instances
    # 
    def getMatchListFromIdList( self, lId ):
        lMatch=[]
        if lId == []:
            return lMatch
        sqlCmd = "select * from %s where path=%d" % (self._table, lId[0])
        for i in lId[1:]:
            sqlCmd += " or path=%d" % (i)
        sqlCmd += ";"
        lMatch = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lMatch
    
    ## Give the data contained in the table as a list of Match instances
    #
    # @return lMatchs list of match instances
    #
    def getListOfAllMatches( self ):
        sqlCmd = "SELECT * FROM %s" % ( self._table )
        lMatches = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lMatches    
    
    def _getInstanceToAdapt(self):
        iMatch = Match()
        return iMatch
    
    def _getTypeAndAttr2Insert(self, match):
        type2Insert = ("'%s'","'%d'","'%d'","'%d'","'%f'","'%f'","'%s'","'%d'","'%d'","'%d'","'%f'","'%g'","'%d'","'%f'","'%d'")
        attr2Insert = ( match.range_query.seqname, match.range_query.start, \
                        match.range_query.end, match.query_length, match.query_length_perc, \
                        match.match_length_perc, match.range_subject.seqname, match.range_subject.start,\
                        match.range_subject.end, match.subject_length, match.subject_length_perc, \
                        match.e_value, match.score, match.identity, \
                        match.id)
        return type2Insert, attr2Insert
    
    def _escapeAntislash(self, obj):
        obj.range_query.seqname = obj.range_query.seqname.replace("\\", "\\\\")
        obj.range_subject.seqname = obj.range_subject.seqname.replace("\\", "\\\\")
