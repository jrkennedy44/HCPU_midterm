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
import os
from pyRepetUnit.commons.coord.Map import Map
from pyRepetUnit.commons.coord.Set import Set
try:
    from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils
except ImportError:
    pass


## static methods manipulating Map instances
#
class MapUtils( object ):
    
    ## Return a list of Map instances sorted in increasing order according to the min, then the max, and finally their initial order
    #
    # @param lMaps list of Map instances
    #
    def getMapListSortedByIncreasingMinThenMax( lMaps ):
        return sorted( lMaps, key=lambda iMap: ( iMap.getMin(), iMap.getMax() ) )    
    
    getMapListSortedByIncreasingMinThenMax = staticmethod( getMapListSortedByIncreasingMinThenMax )
    
    
    ## Return a dictionary which keys are Map names and values the corresponding Map instances
    #
    def getDictPerNameFromMapFile( mapFile ):
        dName2Maps = {}
        mapFileHandler = open( mapFile, "r" )
        while True:
            line = mapFileHandler.readline()
            if line == "":
                break
            iMap = Map()
            iMap.setFromString( line, "\t" )
            if dName2Maps.has_key( iMap.name ):
                if iMap == dName2Maps[ iMap.name ]:
                    continue
                else:
                    msg = "ERROR: in file '%s' two different Map instances have the same name '%s'" % ( mapFile, iMap.name )
                    sys.stderr.write( "%s\n" % ( msg ) )
                    sys.exit(1)
            dName2Maps[ iMap.name ] = iMap
        mapFileHandler.close()
        return dName2Maps
    
    getDictPerNameFromMapFile = staticmethod( getDictPerNameFromMapFile )

    
    ## Give a list of Set instances from a list of Map instances
    #
    # @param lMaps list of Map instances
    # @return lSets list of Set instances
    #
    def mapList2SetList( lMaps ):
        lSets = []
        c = 0
        for iMap in lMaps:
            c += 1
            iSet = Set()
            iSet.id = c
            iSet.name = iMap.getName()
            iSet.seqname = iMap.getSeqname()
            iSet.start = iMap.getStart()
            iSet.end = iMap.getEnd()
            lSets.append( iSet )
        return lSets
    
    mapList2SetList = staticmethod( mapList2SetList )
    
    
    ## Merge the Map instances in a Map file using 'mapOp'
    #
    def mergeCoordsInFile( inFile, outFile ):
        if not sys.modules.has_key( "pyRepetUnit.commons.checker.CheckerUtils" ):
            msg = "WARNING: can't find module 'CheckerUtils'"
            sys.stderr.write( "%s\n" % msg )
        elif not CheckerUtils.isExecutableInUserPath( "mapOp" ):
            msg = "WARNING: can't find executable 'mapOp'"
            sys.stderr.write( "%s\n" % msg )
        else:
            cmd = "mapOp"
            cmd += " -q %s" % ( inFile )
            cmd += " -m"
            cmd += " 2>&1 > /dev/null"
            returnStatus = os.system( cmd )
            if returnStatus != 0:
                print "ERROR: mapOp returned %i" % ( returnStatus )
                sys.exit(1)
            os.rename( "%s.merge" % inFile,
                       outFile )
            
    mergeCoordsInFile = staticmethod( mergeCoordsInFile )
    
    
    ## Return a dictionary which keys are Map seqnames and values the corresponding Map instances
    #
    def getDictPerSeqNameFromMapFile( mapFile ):
        dSeqName2Maps = {}
        mapFileHandler = open( mapFile, "r" )
        while True:
            line = mapFileHandler.readline()
            if line == "":
                break
            iMap = Map()
            iMap.setFromString( line, "\t" )
            if not dSeqName2Maps.has_key( iMap.seqname ):
                dSeqName2Maps[ iMap.seqname ] = []
            dSeqName2Maps[ iMap.seqname ].append( iMap )
        mapFileHandler.close()
        return dSeqName2Maps
    
    getDictPerSeqNameFromMapFile = staticmethod( getDictPerSeqNameFromMapFile )
    
    
    ## Convert an Map file into a Set file
    #
    # @param mapFile string input map file name
    # @param setFile string output set file name
    #
    def convertMapFileIntoSetFile( mapFileName, setFileName = "" ):
        if setFileName == "":
            setFileName = "%s.set" % mapFileName
        mapFileHandler = open( mapFileName, "r" )
        setFileHandler = open( setFileName, "w" )
        iMap = Map()
        count = 0
        while True:
            line = mapFileHandler.readline()
            if line == "":
                break
            iMap.setFromString(line)
            count += 1
            iSet = Set()
            iSet.id = count
            iSet.name = iMap.getName()
            iSet.seqname = iMap.getSeqname()
            iSet.start = iMap.getStart()
            iSet.end = iMap.getEnd()
            iSet.write(setFileHandler)
        mapFileHandler.close()
        setFileHandler.close()
        
    convertMapFileIntoSetFile = staticmethod( convertMapFileIntoSetFile )
