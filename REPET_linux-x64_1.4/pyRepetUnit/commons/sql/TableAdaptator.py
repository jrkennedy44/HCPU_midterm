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


## Abstract class, Ancestor of Table*Adaptator
#
class TableAdaptator( object ):
    
    ## Constructor
    #
    # @param iDb DbMySql instance
    # @param table str table name
    #
    def __init__( self, iDb = None, table = "" ):
        self._iDb = iDb
        self._table = table
        
    ## Set connector to database
    #
    # @param iDb database instance
    #
    def setDbConnector( self, iDb ):
        self._iDb = iDb
        
    ## Set table
    #
    # @param table string table name
    #
    def setTable( self, table ):
        self._table = table
    
    ## Return the table name
    #
    def getTable( self ):
        return self._table
        
    ## Return the number of rows in the table
    #
    def getSize( self ):
        return self._iDb.getSize( self._table )
    
    ## Test if table is empty
    #    
    def isEmpty( self ):
        return self._iDb.isEmpty( self._table )
    
    ## Insert an instance of Map or Set or Match or Path or Seq instances
    #
    # @param obj a Map or Set or Match or Path or Seq instance
    # @param delayed boolean
    #
    def insert(self, obj, delayed = False):
        if obj.isEmpty():
            return
        self._escapeAntislash(obj)
        sql_cmd = self._genSqlCmdForInsert(obj, delayed)
        self._iDb.execute(sql_cmd)
    
    ## Insert a list of Map or Set or Match or Path instances
    #
    # @param l a list of object instances
    # @param delayed boolean
    #
    def insertList(self, l, delayed = False):
        for i in l:
            self.insert(i, delayed)
            
    ## Give the data contained in the table as a list of coord object instances
    #
    # @return lObject list of coord object instances
    #
    def getListOfAllCoordObject( self ):
        sqlCmd = "SELECT * FROM %s" % ( self._table )
        lObjs = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lObjs
    
    ## Generate sql command for GetListOverlappingCoord method 
    #  
    # @param obj Map, Set or Match instance
    # @param delayed boolean
    # @return sqlCmd string generated sql command
    #
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
   
    def _getTypeAndAttr2Insert(self, obj):
        pass
    
    def _getInstanceToAdapt(self):
        pass
    
    def _escapeAntislash(self, obj):
        pass
