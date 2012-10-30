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


from pyRepetUnit.commons.sql.ITableSetAdaptator import ITableSetAdaptator
from pyRepetUnit.commons.sql.TableAdaptator import TableAdaptator
from pyRepetUnit.commons.coord.Set import Set


## Adaptator for a Set table
#
class TableSetAdaptator( TableAdaptator, ITableSetAdaptator ):
            
    ## Give a list of Set instances having a given seq name
    #
    # @param seqName string seq name
    # @return lSet list of instances
    #
    def getListFromSeqName( self, seqName ):
        sqlCmd = "SELECT * FROM %s" % (self._table)
        colum2Get, type2Get, attr2Get = self._getTypeColumAttr2Get(seqName)
        sqlCmd += " WHERE " + colum2Get
        sqlCmd += " = "
        sqlCmd = sqlCmd + type2Get
        sqlCmd = sqlCmd % "'" + attr2Get + "'"
        lSet = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lSet
        
    ## Give a list of set instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of set instances
    #
    def getListOverlappingCoord(self, query, start, end):
        sqlCmd = 'select * from %s where chr="%s" and ((start between least(%d,%d) and greatest(%d,%d) or end between least(%d,%d) and greatest(%d,%d)) or (least(start,end)<=least(%d,%d) and greatest(start,end)>=greatest(%d,%d)))  ;' % (self._table, query, start, end, start, end, start, end, start, end, start, end, start, end)
        lSet = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lSet

    ## Give a list of identifier numbers contained in the table
    #
    # @return lId integer list
    #
    def getIdList(self):
        sqlCmd = "select distinct path from %s;" % (self._table)
        lId = self._iDb.getIntegerListWithSQLCmd( sqlCmd )
        return lId
    
    ## Give a list of the distinct seqName/chr present in the table
    #
    # @return lDistinctContigNames string list
    #
    def getSeqNameList(self):
        sqlCmd = "SELECT DISTINCT chr FROM %s" % ( self._table )
        lDistinctContigNames = self._iDb.getStringListWithSQLCmd(sqlCmd)
        return lDistinctContigNames
    
    ## Give a list of Set instances having a given seq name
    #
    # @param seqName string seq name
    # @return lSet list of instances
    #
    def getSetListFromSeqName( self, seqName):
        lSets = self.getListFromSeqName(seqName)
        return lSets
    
    ## Give a set instances list with a given identifier number
    #
    # @param id integer identifier number
    # @return lSet list of set instances
    #
    def getSetListFromId(self, id):
        SQLCmd = "select * from %s where path=%d;" % (self._table, id)
        return self._iDb.getObjectListWithSQLCmd( SQLCmd, self._getInstanceToAdapt )
   
    ## Give a set instances list with a list of identifier numbers
    #
    # @param lId integers list identifiers list numbers
    # @return lSet list of set instances
    #   
    def getSetListFromIdList(self,lId):
        lSet = []
        if lId == []:
            return lSet
        SQLCmd = "select * from %s where path=%d" % (self._table, lId[0])
        for i in lId[1:]:
            SQLCmd += " or path=%d" % (i)
        SQLCmd += ";"
        return self._iDb.getObjectListWithSQLCmd( SQLCmd, self._getInstanceToAdapt )
    
    ## Return a list of Set instances overlapping a given sequence
    #   
    # @param seqName string sequence name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    def getSetListOverlappingCoord( self, seqName, start, end ):
        lSet = self.getListOverlappingCoord( seqName, start, end )
        return lSet
    
    ## Delete set corresponding to a given identifier number
    #
    # @param id integer identifier number
    #  
    def deleteFromId(self, id):
        sqlCmd = "delete from %s where path=%d;" % (self._table, id)
        self._iDb.execute(sqlCmd)
        
    ## Delete set corresponding to a given list of identifier number
    #
    # @param lId integers list list of identifier number
    #  
    def deleteFromIdList(self, lId):
        if lId == []:
            return
        sqlCmd = "delete from %s where path=%d" % ( self._table, lId[0] )
        for i in lId[1:]:
            sqlCmd += " or path=%d"%(i)
        sqlCmd += ";"
        self._iDb.execute(sqlCmd)
        
    ## Join two set by changing id number of id1 and id2 set to the least of id1 and id2
    #
    # @param id1 integer id path number
    # @param id2 integer id path number
    #    
    def joinTwoSets(self, id1, id2):
        if id1 < id2:
            newId = id1
            oldId = id2
        else:
            newId = id2
            oldId = id1
        sqlCmd = "UPDATE %s SET path=%d WHERE path=%d" % (self._table, newId, oldId)
        self._iDb.execute(sqlCmd)
    
    ## Get a new id number
    #
    # @return new_id integer max_id + 1 
    #
    def getNewId(self):
        sqlCmd = "select max(path) from %s;" % (self._table)
        maxId = self._iDb.getIntegerWithSQLCmd(sqlCmd)
        newId = int(maxId) + 1
        return newId
    
    ## Give the data contained in the table as a list of Sets instances
    #
    # @return lSets list of set instances
    #
    def getListOfAllSets( self ):
        return self.getListOfAllCoordObject()
   
    def _getInstanceToAdapt(self):
            iSet = Set()
            return iSet
    
    def _getTypeColumAttr2Get(self, contig):
        colum2Get = 'chr'
        type2Get = '%s'
        attr2Get = contig
        return colum2Get, type2Get, attr2Get
    
    def _getTypeAndAttr2Insert(self, set):
        type2Insert = ("'%d'","'%s'","'%s'","'%d'","'%d'")
        attr2Insert = (set.id, set.name, set.seqname, set.start, set.end)
        return type2Insert, attr2Insert

    def _escapeAntislash(self, obj):
        obj.name = obj.name.replace("\\", "\\\\")
        obj.seqname = obj.seqname.replace("\\", "\\\\")
