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


from pyRepetUnit.commons.coord.Path import Path
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.sql.TableAdaptator import TableAdaptator
from pyRepetUnit.commons.sql.ITablePathAdaptator import ITablePathAdaptator


## Adaptator for a Path table
#
class TablePathAdaptator( TableAdaptator, ITablePathAdaptator ):

    ## Give a list of Path instances having the same identifier
    #
    # @param id integer identifier number
    # @return lPath a list of Path instances
    #
    def getPathListFromId( self, id ):
        sqlCmd = "SELECT * FROM %s WHERE path='%d';" % ( self._table, id )
        lPath = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPath
    
    ## Give a list of Path instances according to the given list of identifier numbers
    #
    # @param lId integer list 
    # @return lPath a list of Path instances
    #
    def getPathListFromIdList( self, lId ):
        lPath=[]
        if lId == []:
            return lPath
        sqlCmd = "select * from %s where path=%d" % (self._table, lId[0])
        for i in lId[1:]:
            sqlCmd += " or path=%d" % (i)
        sqlCmd += ";"
        lPath = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPath
    
    ## Give a list of Path instances having the same given query name
    #
    # @param query string name of the query 
    # @return lPath a list of Path instances
    #
    def getPathListFromQuery( self, query ):
        lPath = self._getPathListFromTypeName("query", query)
        return lPath
    
    ## Give a list of Path instances having the same given subject name
    #
    # @param subject string name of the subject 
    # @return lPath a list of Path instances
    #
    def getPathListFromSubject( self, subject ):
        lPath = self._getPathListFromTypeName("subject", subject)
        return lPath
    
    ## Give a list of the distinct subject names present in the table
    #
    # @return lDistinctSubjectNames string list
    #
    def getSubjectList(self):
        lDistinctSubjectNames = self._getDistinctTypeNamesList("subject")
        return lDistinctSubjectNames
    
    ## Give a list of the distinct query names present in the table
    #
    # @return lDistinctQueryNames string list
    #
    def getQueryList(self):
        lDistinctQueryNames = self._getDistinctTypeNamesList("query")
        return lDistinctQueryNames
    
    ## Give a list with all the distinct identifiers corresponding to the query
    #
    # @param query string name of the subject 
    # @return lId a list of integer
    #
    def getIdListFromQuery( self, query ):
        lId = self._getIdListFromTypeName("query", query)
        return lId
    
    ## Give a list with all the distinct identifiers corresponding to the subject
    #
    # @param subject string name of the subject 
    # @return lId a list of integer
    #
    def getIdListFromSubject( self, subject ):
        lId = self._getIdListFromTypeName("subject", subject)
        return lId
    
    ## Give a list of identifiers contained in the table
    #
    # @return lId integer list
    #
    def getIdList(self):
        sqlCmd = "SELECT DISTINCT path from %s;" % (self._table)
        lId = self._iDb.getIntegerListWithSQLCmd( sqlCmd )
        return lId
        
    ## Give a list of the distinct subject names present in the table given a query name
    #
    # @param queryName string 
    # @return lDistinctSubjectNamesPerQuery string list
    #
    def getSubjectListFromQuery( self, queryName ):
        sqlCmd = "SELECT DISTINCT subject_name FROM %s WHERE query_name='%s'" % ( self._table, queryName )
        lDistinctSubjectNamesPerQuery = self._iDb.getStringListWithSQLCmd(sqlCmd)
        return lDistinctSubjectNamesPerQuery
    
    ## Give the data contained in the table as a list of Paths instances
    #
    # @return lPaths list of paths instances
    #
    def getListOfAllPaths( self ):
        return self.getListOfAllCoordObject()
    
    ## Give a list of Path instances with the given query and subject, both on direct strand
    #
    # @param query string query name
    # @param subject string subject name
    # @return lPaths list of path instances
    #
    def getPathListWithDirectQueryDirectSubjectFromQuerySubject( self, query, subject ):
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s' AND subject_name='%s' AND query_start<query_end AND subject_start<subject_end ORDER BY query_name, subject_name, query_start;" % ( self._table, query, subject )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    ## Give a list of Path instances with the given query on direct strand and the given subject on reverse strand
    #
    # @param query string query name
    # @param subject string subject name
    # @return lPaths list of path instances
    #
    def getPathListWithDirectQueryReverseSubjectFromQuerySubject( self, query, subject ):
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s' AND subject_name='%s' AND query_start<query_end AND subject_start>subject_end ORDER BY query_name, subject_name, query_start;" % ( self._table, query, subject )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths

    ## Give the number of Path instances with the given query name
    #
    # @param query string query name
    # @return pathNb integer the number of Path instances
    #
    def getNbPathsFromQuery( self, query ):
        pathNb = self._getPathsNbFromTypeName("query", query)
        return pathNb
    
    ## Give the number of Path instances with the given subject name
    #
    # @param subject string subject name
    # @return pathNb integer the number of Path instances
    #
    def getNbPathsFromSubject( self, subject ):
        pathNb = self._getPathsNbFromTypeName("subject", subject)
        return pathNb
    
    ## Give the number of distinct path identifiers
    #
    # @return idNb integer the number of Path instances
    #
    def getNbIds( self ):
        sqlCmd = "SELECT COUNT( DISTINCT path ) FROM %s" % ( self._table )
        idNb = self._iDb.getIntegerWithSQLCmd( sqlCmd )
        return idNb
    
    ## Give the number of distinct path identifiers for a given subject
    #
    # @param subjectName string subject name
    # @return idNb integer the number of Path instances
    #
    def getNbIdsFromSubject( self, subjectName ):
        idNb = self._getIdNbFromTypeName("subject", subjectName)
        return idNb
    
    ## Give the number of distinct path identifiers for a given query
    #
    # @param queryName string query name
    # @return idNb integer the number of Path instances
    #
    def getNbIdsFromQuery( self, queryName ):
        idNb = self._getIdNbFromTypeName("query", queryName)
        return idNb
    
    ## Give a list of Path instances included in a given query region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lPaths list of Path instances
    #
    def getPathListIncludedInQueryCoord( self, query, start, end ):
        if( start > end ):
            tmp = start
            start = end
            end = tmp
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s' AND query_start>=%i AND query_end<=%i" % ( self._table, query, start, end )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    ## Give a list of Path instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lPath list of Path instances
    #
    def getPathListOverlappingQueryCoord( self, query, start, end ):
        if( start > end ):
            tmp = start
            start = end
            end = tmp
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s'" % ( self._table, query )
        sqlCmd += " AND ( ( query_start < %i AND query_end >= %i AND query_end <= %i )" % ( start, start, end )
        sqlCmd += " OR ( query_start >= %i AND query_end <= %i )" % ( start, end )
        sqlCmd += " OR ( query_start >= %i AND query_start <= %i AND query_end > %i )" % ( start, end, end )
        sqlCmd += " OR ( query_start < %i AND query_end > %i ) )" % ( start, end )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    ## Give a list of Path instances overlapping a given region
    #
    # @note whole chains are returned, even if only a fragment overlap with the given region
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lPath list of Path instances
    #
    def getChainListOverlappingQueryCoord( self, query, start, end ):
        if( start > end ):
            tmp = start
            start = end
            end = tmp
        sqlCmd = "SELECT DISTINCT path FROM %s WHERE query_name='%s'" % ( self._table, query )
        sqlCmd += " AND ( ( query_start < %i AND query_end >= %i AND query_end <= %i )" % ( start, start, end )
        sqlCmd += " OR ( query_start >= %i AND query_end <= %i )" % ( start, end )
        sqlCmd += " OR ( query_start >= %i AND query_start <= %i AND query_end > %i )" % ( start, end, end )
        sqlCmd += " OR ( query_start < %i AND query_end > %i ) )" % ( start, end )
        lIdentifiers = self._iDb.getIntegerListWithSQLCmd( sqlCmd )
        lPaths = self.getPathListFromIdList( lIdentifiers )
        return lPaths
    
    ## Give a list of Set instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    def getSetListOverlappingQueryCoord(self, query, start, end):
        lPath = self.getPathListOverlappingQueryCoord(query, start, end)
        lSet = PathUtils.getSetListFromQueries(lPath)
        return lSet
    
    ## Give a list of Set instances included in a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    def getSetListIncludedInQueryCoord(self, query, start, end):
        lPath=self.getPathListIncludedInQueryCoord(query, start, end)
        lSet = PathUtils.getSetListFromQueries(lPath) 
        return lSet
    
    ## Give a a list of Path instances sorted by query coordinates
    #
    # @return lPaths list of Path instances
    #
    def getPathListSortedByQueryCoord( self ):
        sqlCmd = "SELECT * FROM %s ORDER BY query_name, LEAST(query_start,query_end)" % ( self._table )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    ## Give a a list of Path instances sorted by query coordinates for a given query
    #
    # @return lPaths list of Path instances
    #
    def getPathListSortedByQueryCoordFromQuery( self, queryName ):
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s' ORDER BY LEAST(query_start,query_end)" % ( self._table, queryName )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    ## Give a cumulative length of all paths (fragments) for a given subject name
    #
    # @param subjectName string subject name
    # @return nb Cumulative length for all path
    #
    # @warning doesn't take into account the overlaps !!
    #
    def getCumulLengthFromSubject( self, subjectName ):
        sqlCmd = "SELECT SUM(ABS(query_end-query_start)+1) FROM %s WHERE subject_name='%s'" % ( self._table, subjectName )
        nb = self._iDb.getIntegerWithSQLCmd(sqlCmd)
        return nb
    
    ## Give a list of the length of all chains of paths for a given subject name
    #
    # @param subjectName string  name of the subject
    # @return lChainLengths list of lengths per chain of paths
    #
    # @warning doesn't take into account the overlaps !!
    #
    def getChainLengthListFromSubject( self, subjectName ):
        sqlCmd = "SELECT SUM(ABS(query_end-query_start)+1) FROM %s WHERE subject_name='%s' GROUP BY PATH" % ( self._table, subjectName )
        lChainLengths = self._iDb.getIntegerListWithSQLCmd(sqlCmd)
        return lChainLengths
    
    ## Give a list of identity of all chains of paths for a given subject name
    #
    # @param subjectName string name of the subject
    # @return lChainIdentities list of identities per chain of paths
    #
    # @warning doesn't take into account the overlaps !!
    #
    def getChainIdentityListFromSubject( self, subjectName ):
        lChainIdentities = []
        sqlCmd = "SELECT SUM(identity*(ABS(query_start-query_end)+1)) / SUM(ABS(query_end-query_start)+1) FROM %s WHERE subject_name='%s' GROUP BY PATH" % ( self._table, subjectName )
        self._iDb.execute( sqlCmd )
        res = self._iDb.fetchall()
        for i in res:
            if i[0] != None:
                lChainIdentities.append( round( float( i[0] ), 2 ) )
        return lChainIdentities
    
    ## Give a list of the length of all paths for a given subject name
    #
    # @param subjectName string name of the subject
    # @return lPathLengths list of lengths per path
    #
    # @warning doesn't take into account the overlaps !!
    #
    def getPathLengthListFromSubject( self, subjectName ):
        sqlCmd = "SELECT ABS(query_end-query_start)+1 FROM %s WHERE subject_name='%s'" % ( self._table, subjectName )
        lPathLengths = self._iDb.getIntegerListWithSQLCmd(sqlCmd)
        return lPathLengths

    ## Give a a list with all distinct identifiers for a given subject sorted in decreasing order according to the length of the chains
    #    
    # @param subjectName string subject name
    # @return lPathNums a list of paths Id
    #
    def getIdListSortedByDecreasingChainLengthFromSubject( self, subjectName ):
        sqlCmd = "SELECT DISTINCT path, SUM( ABS(query_end - query_start) + 1 ) AS length"
        sqlCmd += " FROM %s" % ( self._table )
        sqlCmd += " WHERE subject_name='%s'" % ( subjectName )
        sqlCmd += " GROUP BY path"
        sqlCmd += " ORDER BY length DESC";
        lPathNums = self._iDb.getIntegerListWithSQLCmd(sqlCmd)
        return lPathNums

    ## Give a a list with all distinct identifiers for a given subject where the chain lengths is above a given threshold
    #    
    # @param subjectName string subject name
    # @lengthThreshold length threshold below which chains are filtered
    # @return lPathNums a list of paths Id
    #
    def getIdListFromSubjectWhereChainsLongerThanThreshold( self, subjectName, lengthThreshold ):
        lPathNums = []
        sqlCmd = "SELECT DISTINCT path, SUM( ABS(query_end - query_start) + 1 ) AS length"
        sqlCmd += " FROM %s" % ( self._table )
        sqlCmd += " WHERE subject_name='%s'" % ( subjectName )
        sqlCmd += " GROUP BY path"
        sqlCmd += " ORDER BY length DESC";
        self._iDb.execute( sqlCmd )
        res = self._iDb.fetchall()
        for i in res:
            if int(i[1]) >= int(lengthThreshold):
                lPathNums.append( i[0] )
        return lPathNums
    
    ## Give a list of Set instance list from the path contained on a query name
    #
    # @param query string query name
    # @return lSet list of set instance 
    #
    def getSetListFromQuery(self, query):
        lpath = self.getPathListFromQuery(query)
        lSet = PathUtils.getSetListFromQueries(lpath)
        return  lSet
    
    ## Delete path corresponding to a given identifier number
    #
    # @param id integer identifier number
    #
    def deleteFromId(self,id):
        sqlCmd = "delete from %s where path=%d;" % (self._table, id)
        self._iDb.execute(sqlCmd)

    ## Delete path corresponding to a given list of identifier number
    #
    # @param lId list of identifier number
    #
    def deleteFromIdList(self,lId):
        if lId == []:
            return        
        sqlCmd = "delete from %s where path=%d" % (self._table, lId[0])
        for id in lId[1:]:
            sqlCmd += " or path=%d" %(id)
        sqlCmd += ";"
        self._iDb.execute(sqlCmd)

    ## Get a new id number
    #
    # @return newId integer new id
    #
    def getNewId(self):
        sqlCmd = 'select max(path) from %s;' % (self._table)
        maxId = self._iDb.getIntegerWithSQLCmd(sqlCmd)
        newId = int(maxId)+1
        return newId
    
    ##  Join two path by changing id number of id1 and id2 path to the least of id1 and id2
    #
    # @param id1 integer id path number
    # @param id2 integer id path number
    # @return newId integer minimum of id1 id2
    # @note this method modify the ID even if this one not existing in the path table  
    #     
    def joinTwoPaths(self, id1, id2):
        if id1 < id2:
            newId = id1
            oldId = id2
        else:
            newId = id2
            oldId = id1
        sqlCmd = "UPDATE %s SET path=%d WHERE path=%d"\
                % (self._table, newId, oldId)
        self._iDb.execute(sqlCmd)
        return newId
    
    ## Create a 'pathRange' table from a 'path' table. 
    # The output table summarizes the information per identifier. 
    # The min and max value are taken. 
    # The identity is averaged over the fragments. 
    # It may overwrite an existing table.
    #
    # @param outTable string name of the output table
    # @return outTable string Table which summarizes the information per identifier
    #
    def path2PathRange( self, outTable="" ):
        return self._path2PathRangeOrPath2PathRangeQuery(outTable)
  
    ## Create a 'pathrange' table from a 'path' table for the given query name
    #  The output table summarizes the information per identifier
    #  The min and max value are taken
    #  The identity is averaged over the fragments, weighted by the length of the of the query
    #  It may overwrite an existing table
    #
    # @param outTable string name of the output table
    # @param query string query name
    # @return outTable string  Table which summarizes the information per identifier
    #
    def _path2PathRangeFromQuery( self, queryName, outTable="" ):
        return self._path2PathRangeOrPath2PathRangeQuery(outTable, queryName)
    
    def _path2PathRangeOrPath2PathRangeQuery(self, outTable, queryName=""):
        self._iDb.createPathIndex( self._table )
        if outTable == "":
            outTable = "%s_range" % ( self._table )
        self._iDb.dropTable( outTable )
        
        tmpTable = "%s_tmp" % ( self._table )
        self._iDb.dropTable( tmpTable )
        
        sqlCmd = self._genSqlCmdForTmpTableAccordingToQueryName(queryName, tmpTable)
        self._iDb.execute(sqlCmd)
            
        sqlCmd = "CREATE TABLE %s SELECT path, query_name, MIN(query_start) AS query_start, MAX(query_end) AS query_end, subject_name, MIN(subject_start) AS subject_start, MAX(subject_end) AS subject_end, MIN(e_value) AS e_value, SUM(score) AS score, FORMAT(SUM(identity)/SUM(ABS(query_end-query_start)+1),2) AS identity FROM %s WHERE query_start<query_end AND subject_start<subject_end GROUP BY path;" % ( outTable, tmpTable )
        self._iDb.execute( sqlCmd )
        
        sqlCmd = "INSERT into %s SELECT path, query_name, MIN(query_start) AS query_start, MAX(query_end) AS query_end, subject_name, MAX(subject_start) AS subject_start, MIN(subject_end) AS subject_end, MIN(e_value) AS e_value, SUM(score) AS score, FORMAT(SUM(identity)/SUM(ABS(query_end-query_start)+1),2) AS identity FROM %s WHERE query_start<query_end AND subject_start>subject_end GROUP BY path;" % ( outTable, tmpTable )
        self._iDb.execute( sqlCmd )
        
        self._iDb.createPathIndex( outTable )
        self._iDb.dropTable( tmpTable )
        return outTable
            
    ## Give a list of Path lists sorted by weighted identity.
    #
    # @return lChains list of chains
    #
    def getListOfChainsSortedByAscIdentityFromQuery( self, qry ):
        lChains = []
        tmpTable = self._path2PathRangeFromQuery( qry )
        sqlCmd = "SELECT path FROM %s ORDER BY identity" % ( tmpTable )
        self._iDb.execute( sqlCmd )
        lPathnums = self._iDb.fetchall()
        self._iDb.dropTable( tmpTable )
        for pathnum in lPathnums:
            lChains.append( self.getPathListFromId( int(pathnum[0]) ) )
        return lChains
    
    ## Give a list of path instances sorted by increasing E-value
    #
    # @return lPaths list of path instances
    #
    def getPathListSortedByIncreasingEvalueFromQuery( self, queryName ):
        sqlCmd = "SELECT * FROM %s WHERE query_name='%s' ORDER BY E_value ASC" % ( self._table, queryName )
        lPaths = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPaths
    
    
    ## Return the number of times a given instance is present in the table
    # The identifier is not considered,
    # only coordinates, score, E-value and identity.
    #
    # @return nbOcc integer
    #
    def getNbOccurrences( self, iPath ):
        sqlCmd = "SELECT COUNT(*) FROM %s WHERE" % ( self._table )
        sqlCmd += " query_name='%s'" % ( iPath.range_query.seqname )
        sqlCmd += " AND query_start='%s'" % ( iPath.range_query.start )
        sqlCmd += " AND query_end='%s'" % ( iPath.range_query.end )
        sqlCmd += " AND subject_name='%s'" % ( iPath.range_subject.seqname )
        sqlCmd += " AND subject_start='%s'" % ( iPath.range_subject.start )
        sqlCmd += " AND subject_end='%s'" % ( iPath.range_subject.end )
        sqlCmd += " AND score='%s'" % ( iPath.score )
        sqlCmd += " AND e_value='%s'" % ( iPath.e_value )
        sqlCmd += " AND identity='%s'" % ( iPath.identity )
        nbOcc = self._iDb.getIntegerWithSQLCmd( sqlCmd )
        return nbOcc
    
    
    def _getPathListFromTypeName( self, type, typeName ):
        sqlCmd = "SELECT * FROM %s WHERE %s_name='%s';" % ( self._table, type, typeName )
        lPath = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lPath
    
    def _getDistinctTypeNamesList( self, type ):
        sqlCmd = "SELECT DISTINCT %s_name FROM %s" % ( type, self._table )
        lDistinctTypeNames = self._iDb.getStringListWithSQLCmd(sqlCmd)
        return lDistinctTypeNames
    
    def _getPathsNbFromTypeName( self, type, typeName ):
        sqlCmd = "SELECT COUNT(*) FROM %s WHERE %s_name='%s'" % ( self._table, type, typeName )
        pathNb = self._iDb.getIntegerWithSQLCmd( sqlCmd )
        return pathNb
    
    def _getIdListFromTypeName( self, type, typeName ):
        sqlCmd = "SELECT DISTINCT path FROM %s WHERE %s_name='%s'" % ( self._table, type, typeName )
        lId = self._iDb.getIntegerListWithSQLCmd( sqlCmd )
        return lId
    
    def _getIdNbFromTypeName( self, type, typeName ):
        sqlCmd = "SELECT COUNT( DISTINCT path ) FROM %s WHERE %s_name='%s'" % ( self._table, type, typeName )
        idNb = self._iDb.getIntegerWithSQLCmd( sqlCmd )
        return idNb
    
    def _genSqlCmdForInsert(self, obj, delayed):
        sqlCmd = 'INSERT '
        if delayed :
            sqlCmd += ' DELAYED '
        type2Insert, attr2Insert = self._getTypeAndAttr2Insert(obj)
        sqlCmd +=  'INTO %s VALUES (' % (self._table) 
        sqlCmd +=  ",".join(type2Insert)
        sqlCmd += ")" 
        sqlCmd = sqlCmd % attr2Insert
        return sqlCmd
    
    def _getTypeAndAttr2Insert(self, path):
        type2Insert = ("'%d'", "'%s'", "'%d'", "'%d'", "'%s'", "'%d'", "'%d'", "'%g'", "'%d'", "'%f'")
        if path.range_query.isOnDirectStrand():
            queryStart = path.range_query.start
            queryEnd = path.range_query.end
            subjectStart = path.range_subject.start
            subjectEnd = path.range_subject.end
        else:
            queryStart = path.range_query.end
            queryEnd = path.range_query.start
            subjectStart = path.range_subject.end
            subjectEnd = path.range_subject.start
        attr2Insert = ( path.id,\
                     path.range_query.seqname,\
                     queryStart,\
                     queryEnd,\
                     path.range_subject.seqname,\
                     subjectStart,\
                     subjectEnd,\
                     path.e_value,\
                     path.score,\
                     path.identity\
                     )
        return type2Insert, attr2Insert
    
    def _getInstanceToAdapt(self):
        iPath = Path()
        return iPath
    
    def _escapeAntislash(self, obj):
        obj.range_query.seqname = obj.range_query.seqname.replace("\\", "\\\\")
        obj.range_subject.seqname = obj.range_subject.seqname.replace("\\", "\\\\")
    
    def _genSqlCmdForTmpTableAccordingToQueryName(self, queryName, tmpTable):
        sqlCmd = ""
        if queryName == "":
            sqlCmd = "CREATE TABLE %s SELECT path, query_name, query_start, query_end, subject_name, subject_start, subject_end, e_value, score, (ABS(query_end-query_start)+1)*identity AS identity FROM %s" % (tmpTable, self._table)
        else:
            sqlCmd = "CREATE TABLE %s SELECT path, query_name, query_start, query_end, subject_name, subject_start, subject_end, e_value, score, (ABS(query_end-query_start)+1)*identity AS identity FROM %s WHERE query_name='%s'" % (tmpTable, self._table, queryName)
        return sqlCmd
