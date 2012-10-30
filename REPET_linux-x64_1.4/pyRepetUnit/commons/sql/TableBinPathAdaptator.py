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

import os
from pyRepetUnit.commons.coord.Range import getIdx
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils

## Bin Adaptator for a path table.
#
class TableBinPathAdaptator(TablePathAdaptator):

    
    ## Constructor
    #
    # @param db db instance
    # @param tableName string table name (default = "")
    #
    def __init__(self, db, tableName = ""):
        TablePathAdaptator.__init__(self, db, tableName)
        self._table_idx = "%s_idx" % (self._table)
    
    #TODO: move into DbMySql ? path2path_range() migration ? range table is empty, is it normal ?
    ## Create a bin table for fast access
    #
    # @param verbose integer verbosity (default = 0)
    #    
    def createBinPathTable(self, verbose = 0):
        if not self._iDb.doesTableExist(self._table):
            return
        
        if verbose > 0:
            print "creating %s for fast access" % (self._table_idx)

        self._iDb.dropTable(self._table_idx)
        sql_cmd = "CREATE TABLE %s ( path int unsigned, idx int unsigned, contig varchar(255), min int, max int, strand int unsigned)"% (self._table_idx)
        self._iDb.execute(sql_cmd)

        sql_cmd = "CREATE INDEX id ON %s ( path );"% (self._table_idx)
        self._iDb.execute(sql_cmd)
        sql_cmd = "CREATE INDEX ibin ON %s ( idx );"% (self._table_idx)
        self._iDb.execute(sql_cmd)
        sql_cmd = "CREATE INDEX icontig ON %s ( contig );"% (self._table_idx)
        self._iDb.execute(sql_cmd)
        sql_cmd = "CREATE INDEX imin ON %s ( min );"% (self._table_idx)
        self._iDb.execute(sql_cmd)
        sql_cmd = "CREATE INDEX imax ON %s ( max );"% (self._table_idx)
        self._iDb.execute(sql_cmd)
        sql_cmd = "CREATE INDEX istrand ON %s ( strand );"% (self._table_idx)
        self._iDb.execute(sql_cmd)

        rangeTable = "%s_range" % (self._table)
        self._iDb.dropTable(rangeTable)
        self._iDb.path2path_range(self._table)
        table = TablePathAdaptator(self._iDb, rangeTable)
        if not table.isEmpty():
            tmp_file = "%s.tmp%s" % (self._table, str(os.getpid()))
            out = open(tmp_file, "w")
            contigs = table.getQueryList()
            for c in contigs:
                lpath = table.getPathListFromQuery(c)
                for i in lpath:
                    idx = i.range_query.findIdx()
                    max = i.range_query.getMax()
                    min = i.range_query.getMin()
                    strand = i.range_query.isOnDirectStrand()
                    out.write("%d\t%d\t%s\t%d\t%d\t%d\n"%(i.id, idx, i.range_query.seqname, min, max, strand))
            out.close()
            sql_cmd="LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' "%\
                     (tmp_file, self._table_idx)
            self._iDb.execute(sql_cmd)
            self._iDb.updateInfoTable(self._table_idx, self._table + " bin indexes")
            os.remove(tmp_file)
            
    ## Insert a path instance
    #
    # @param path a path instance
    # @param delayed boolean indicating if the insert must be delayed (default = false) 
    #        
    def insert( self, path, delayed = False ):
        TablePathAdaptator.insert(self, path, delayed)
        self._escapeAntislash(path)
        idx = path.range_query.findIdx()
        max = path.range_query.getMax()
        min = path.range_query.getMin()
        strand = path.range_query.isOnDirectStrand()
        if delayed:
            sql_cmd = 'INSERT DELAYED INTO %s VALUES (%d,%d,"%s",%d,%d,%d)'\
                 % (self._table_idx,\
                   path.id,\
                   idx,\
                   path.range_query.seqname,\
                   min,\
                   max,\
                   strand)
        else:
            sql_cmd = 'INSERT INTO %s VALUES (%d,%d,"%s",%d,%d,%d)'\
                 % (self._table_idx,\
                   path.id,\
                   idx,\
                   path.range_query.seqname,\
                   min,\
                   max,\
                   strand)
            
        self._iDb.execute(sql_cmd)
    
    ## Return a path instances list included in a given region using the bin scheme
    #
    # @param contig string contig name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lOutPath a path instances list
    #
    def getPathListIncludedInQueryCoord(self, contig, start, end):
        min_coord = min(start, end)
        max_coord = max(start, end)
        lpath = self.getChainListOverlappingQueryCoord(contig, start, end)
        lOutPath = []
        for i in lpath:
            if i.range_query.getMin() > min_coord and \
               i.range_query.getMax() < max_coord:
                lOutPath.append(i)
                            
        return lOutPath
    
    ## Return a path instances list overlapping (and included) in a given region using the bin scheme
    #
    # @param contig string contig name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lOutPath a path instances list
    #
    def getPathListOverlappingQueryCoord(self, contig, start, end):
        min_coord = min(start, end)
        max_coord = max(start, end)
        lpath = self.getChainListOverlappingQueryCoord(contig, start, end)
        lOutPath = []
        for i in lpath:
            if ((i.range_query.getMin() <= min_coord and i.range_query.getMax() >= min_coord) or \
                (i.range_query.getMin() >= min_coord and i.range_query.getMin() <= max_coord) or \
                (i.range_query.getMin() <= min_coord and i.range_query.getMax() >= max_coord) or \
                (i.range_query.getMin() >= min_coord and i.range_query.getMax() <= max_coord)) and \
                (i.range_query.getSeqname() == contig):
                    lOutPath.append(i)
                    
        return lOutPath
    
    ## Return a path instances list chain (by Id and Coord in chr) list overlapping a given region using the bin scheme
    #
    # @param contig string contig name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lpath a path instances list
    #    
    def getChainListOverlappingQueryCoord(self, contig, start, end):
        min_coord = min(start, end)
        max_coord = max(start, end)
        sql_cmd = 'select distinct path from %s where contig="%s" and ('\
                 % (self._table + "_idx", contig)
                 
        for bin_lvl in xrange(6, 2, -1):
            if getIdx(start,bin_lvl) == getIdx(end, bin_lvl):
                idx = getIdx(start, bin_lvl)
                sql_cmd += 'idx=%d' % (idx)
            else:
                idx1 = getIdx(min_coord, bin_lvl)
                idx2 = getIdx(max_coord, bin_lvl)
                sql_cmd += 'idx between %d and %d' % (idx1, idx2)
            if bin_lvl > 3:
                sql_cmd += " or "
                
        sql_cmd += ") and min<=%d and max>=%d;" % (max_coord, min_coord)

        
        self._iDb.execute(sql_cmd)
        res = self._iDb.fetchall()
        lnum = []
        for i in res:
            lnum.append( int(i[0]) )
        lpath = self.getPathListFromIdList(lnum)
        return lpath

    ## Delete path corresponding to a given identifier number
    #
    # @param num integer identifier number
    #
    def deleteFromId(self, num):
        TablePathAdaptator.deleteFromId(self, num)
        sqlCmd='delete from %s where path=%d;' % (self._table_idx, num)
        self._iDb.execute(sqlCmd)
    
    ## Delete path corresponding to a given list of identifier number
    #
    # @param lNum list list of integer identifier number
    #
    def deleteFromIdList(self, lNum):
        if lNum == []:
            return
        TablePathAdaptator.deleteFromIdList(self, lNum)
        sqlCmd = 'delete from %s where path=%d' % (self._table_idx, lNum[0])
        for i in lNum[1:]:
            sqlCmd += " or path=%d" % (i)
        sqlCmd += ";"
        self._iDb.execute(sqlCmd)
             
    ##  Join two path by changing id number of id1 and id2 path to the least of id1 and id2
    #
    # @param id1 integer id path number
    # @param id2 integer id path number
    # @return newId integer minimum of id1 id2
    # @note this method modify the ID even if this one not existing in the path table  
    #     
    def joinTwoPaths(self, id1, id2):
        TablePathAdaptator.joinTwoPaths(self, id1, id2)
        if id1 < id2:
            newId = id1
            oldId = id2
        else:
            newId = id2
            oldId = id1
        sqlCmd = 'UPDATE %s SET path=%d WHERE path=%d' % (self._table_idx, newId, oldId)
        self._iDb.execute(sqlCmd)
        return newId
    
    ## Get a new id number
    #
    # @return newId integer max Id in path table + 1
    #
    def getNewId(self):
        sqlCmd = 'select max(path) from %s;' % (self._table_idx)
        self._iDb.execute(sqlCmd)
        maxId = self._iDb.fetchall()[0][0]
        if maxId == None:
            maxId = 0
        newId = int(maxId) + 1
        return newId
    
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
    
    ## Give a list of identifiers contained in the table
    #
    # @return lId integer list
    #
    def getIdList(self):
        sqlCmd = "SELECT DISTINCT path from %s;" % (self._table_idx)
        lId = self._iDb.getIntegerListWithSQLCmd( sqlCmd )
        return lId
        
    ## Give a list of the distinct query names present in the table
    #
    # @return lDistinctQueryNames string list
    #
    def getQueryList(self):
        lDistinctQueryNames = self._getDistinctTypeNamesList("query")
        return lDistinctQueryNames
    
    def _getDistinctTypeNamesList( self, type ):
        sqlCmd = "SELECT DISTINCT contig FROM %s" % ( self._table_idx )
        lDistinctTypeNames = self._iDb.getStringListWithSQLCmd(sqlCmd)
        return lDistinctTypeNames