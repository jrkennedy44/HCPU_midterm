'''
Created on 25 juin 2009

@author: choede
'''
from pyRepetUnit.commons.coord.Map import Map
from pyRepet.sql.TableAdaptator import TableMapAdaptator

class InsertProfilesMapFileInDB(object):
    '''
    Insert a map File in a database
    You have to specified the input file name, the table name and the repetDB object when you create the object
    '''


    def __init__(self, inputFileName, tableName, db):
        '''
        Constructor
        '''
        self.inputFileName = inputFileName
        self.tableName = tableName
        self.db = db
        
    def createAndLoadTable(self):
        '''
        Create the table and load the map data from input table
        '''
        self.db.create_table( self.db, self.tableName, "", "map" )
        f = open (self.inputFileName, "r")
        iMap = Map()
        lMap = []
        while iMap.read( f ):
            lMap.append(iMap)
            iMap = Map()
        f.close()
        self._tMapA = TableMapAdaptator( self.db, self.tableName )
        self._tMapA.insMapList( lMap )
        
        
if __name__ == "__main__":                 
    main()     