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


import sys
from pyRepetUnit.commons.sql.TableAdaptator import TableAdaptator
from pyRepetUnit.commons.sql.ITableMapAdaptator import ITableMapAdaptator
from pyRepetUnit.commons.coord.Map import Map
from pyRepetUnit.commons.coord.MapUtils import MapUtils


## Adaptator for Map table
#
class TableMapAdaptator( TableAdaptator, ITableMapAdaptator ):
            
    ## Give a list of Map instances having a given seq name
    #
    # @param seqName string seq name
    # @return lMap list of instances
    #
    def getListFromSeqName( self, seqName ):
        sqlCmd = "SELECT * FROM %s" % (self._table)
        colum2Get, type2Get, attr2Get = self._getTypeColumAttr2Get(seqName)
        sqlCmd += " WHERE " + colum2Get
        sqlCmd += " = "
        sqlCmd = sqlCmd + type2Get
        sqlCmd = sqlCmd % "'" + attr2Get + "'"
        return self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        
    ## Give a list of Map instances overlapping a given region
    #
    # @param query string query name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return list map instances
    #
    def getListOverlappingCoord(self, query, start, end):
        sqlCmd = 'select * from %s where chr="%s" and ((start between least(%d,%d) and greatest(%d,%d) or end between least(%d,%d) and greatest(%d,%d)) or (least(start,end)<=least(%d,%d) and greatest(start,end)>=greatest(%d,%d)))  ;' % (self._table, query, start, end, start, end, start, end, start, end, start, end, start, end)
        return self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
    
    ## Give a list of Map instances having a given sequence name
    #
    # @param seqName string sequence name
    # @return lMap list of instances
    #
    def getMapListFromSeqName(self, seqName):
        lMap = self.getListFromSeqName( seqName )
        return lMap
    
    ## Give a list of Map instances having a given chromosome
    #
    # @param chr string chromosome
    # @return lMap list of instances
    #
    def getMapListFromChr(self, chr):
        sqlCmd = "SELECT * FROM %s WHERE chr='%s'" % (self._table, chr)
        lMap = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lMap
    
    ## Give a list of the distinct seqName/chr present in the table
    #
    # @return lDistinctContigNames string list
    #
    def getSeqNameList(self):
        sqlCmd = "SELECT DISTINCT chr FROM %s" % ( self._table )
        lDistinctContigNames = self._iDb.getStringListWithSQLCmd(sqlCmd)
        return lDistinctContigNames
    
    ## Return a list of Set instances from a given sequence name
    #
    # @param seqName string sequence name
    # @return lSets list of Set instances
    # 
    def getSetListFromSeqName( self, seqName ):
        lMaps = self.getListFromSeqName( seqName )
        lSets = MapUtils.mapList2SetList( lMaps )
        return lSets
    
    ## Give a map instances list overlapping a given region
    #
    # @param seqName string seq name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lMap list of map instances
    #
    def getMapListOverlappingCoord(self, seqName, start, end):
        lMap = self.getListOverlappingCoord(seqName, start, end)
        return lMap
    
    ## Return a list of Set instances overlapping a given sequence
    #   
    # @param seqName string sequence name
    # @param start integer start coordinate
    # @param end integer end coordinate
    # @return lSet list of Set instances
    #
    def getSetListOverlappingCoord( self, seqName, start, end ):
        lMaps = self.getListOverlappingCoord( seqName, start, end )
        lSets = MapUtils.mapList2SetList( lMaps )
        return lSets
    
    ## Give a dictionary which keys are Map names and values the corresponding Map instances
    #
    # @return dName2Maps dict which keys are Map names and values the corresponding Map instances
    #
    def getDictPerName( self ):
        dName2Maps = {}
        lMaps = self.getListOfAllMaps()
        for iMap in lMaps:
            if dName2Maps.has_key( iMap.name ):
                if iMap == dName2Maps[ iMap.name ]:
                    continue
                else:
                    msg = "ERROR: in table '%s' two different Map instances have the same name '%s'" % ( self._table, iMap.name )
                    sys.stderr.write( "%s\n" % ( msg ) )
                    sys.exit(1)
            dName2Maps[ iMap.name ] = iMap
        return dName2Maps
    
    ## Return a list of Map instances with all the data contained in the table
    #
    # @return lMaps list of Map instances
    #
    def getListOfAllMaps( self ):
        sqlCmd = "SELECT * FROM %s" % ( self._table )
        lMaps = self._iDb.getObjectListWithSQLCmd( sqlCmd, self._getInstanceToAdapt )
        return lMaps
    
    def _getInstanceToAdapt(self):
        iMap = Map()
        return iMap

    def _getTypeColumAttr2Get(self, name):
        colum2Get = 'name'
        type2Get = '%s'
        attr2Get = name
        return colum2Get, type2Get, attr2Get
    
    def _getTypeAndAttr2Insert(self, map):
        type2Insert = ("'%s'","'%s'","'%d'","'%d'")
        attr2Insert = (map.name, map.seqname, map.start, map.end)
        return type2Insert, attr2Insert

    def _escapeAntislash(self, obj):
        obj.name = obj.name.replace("\\", "\\\\")
        obj.seqname = obj.seqname.replace("\\", "\\\\")
