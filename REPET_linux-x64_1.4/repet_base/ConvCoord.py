#!/usr/bin/env python

##@file
# Convert coordinates from chunks to chromosomes or the opposite.
#
# usage: ConvCoord.py [ options ]
# options:
#      -h: this help
#      -i: input data with coordinates to convert (file or table)
#      -f: input data format (default='align'/'path')
#      -c: coordinates to convert (query, subject or both; default='q'/'s'/'qs')
#      -m: mapping of chunks on chromosomes (format='map')
#      -x: convert from chromosomes to chunks (opposite by default)
#      -o: output data (file or table, same as input)
#      -C: configuration file (for database connection)
#      -v: verbosity level (default=0/1/2)


import os
import sys
import getopt
import time
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.coord.MapUtils import MapUtils
from pyRepetUnit.commons.sql.TableMapAdaptator import TableMapAdaptator
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.Align import Align
from pyRepetUnit.commons.coord.Path import Path
from pyRepetUnit.commons.coord.Range import Range


## Class to handle coordinate conversion
#
class ConvCoord( object ):
    
    ## Constructor
    #
    def __init__( self ):
        self._inData = ""
        self._formatInData = "align"
        self._coordToConvert = "q"
        self._mapData = ""
        self._mergeChunkOverlaps = True
        self._convertChunks = True
        self._outData = ""
        self._configFile = ""
        self._verbose = 0
        self._typeInData = "file"
        self._typeMapData = "file"
        self._iDb = None
        self._tpa = None
        
        
    ## Display the help on stdout
    #
    def help( self ):
        print
        print "usage: ConvCoord.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: input data with coordinates to convert (file or table)"
        print "     -f: input data format (default='align'/'path')"
        print "     -c: coordinates to convert (query, subject or both; default='q'/'s'/'qs')"
        print "     -m: mapping of chunks on chromosomes (format='map')"
        print "     -M: merge chunk overlaps (default=yes/no)"
        print "     -x: convert from chromosomes to chunks (opposite by default)"
        print "     -o: output data (file or table, same as input)"
        print "     -C: configuration file (for database connection)"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
        
    ## Set the attributes from the command-line
    #
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:f:c:m:M:xo:C:v:")
        except getopt.GetoptError, err:
            sys.stderr.write( "%s\n" % ( str(err) ) )
            self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputData( a )
            elif o == "-f":
                self.setInputFormat( a )
            elif o == "-c":
                self.setCoordinatesToConvert( a )
            elif o == "-m":
                self.setMapData( a )
            elif o == "-M":
                self.setMergeChunkOverlaps( a )
            elif o == "-o":
                self.setOutputData( a )
            elif o == "-C":
                self.setConfigFile( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
                
    def setInputData( self, inData ):
        self._inData = inData
        
    def setInputFormat( self, formatInData ):
        self._formatInData = formatInData
        
    def setCoordinatesToConvert( self, coordToConvert ):
        self._coordToConvert = coordToConvert
        
    def setMapData( self, mapData ):
        self._mapData = mapData
        
    def setMergeChunkOverlaps( self, mergeChunkOverlaps ):
        if mergeChunkOverlaps == "yes":
            self._mergeChunkOverlaps = True
        else:
            self._mergeChunkOverlaps = False
            
    def setOutputData( self, outData ):
        self._outData = outData
        
    def setConfigFile( self, configFile ):
        self._configFile = configFile
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
        
    ## Check the attributes are valid before running the algorithm
    #
    def checkAttributes( self ):
        if self._inData == "":
            msg = "ERROR: missing input data (-i)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._formatInData not in ["align","path"]:
            msg = "ERROR: unrecognized format '%s' (-f)" % ( self._formatInData )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._configFile == "":
            msg = "ERROR: missing configuration file (-C)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if not os.path.exists( self._configFile ):
            msg = "ERROR: configuration file '%s' doesn't exist" % ( self._configFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        self._iDb = DbMySql( cfgFileName=self._configFile )
        if not os.path.exists( self._inData ) and not self._iDb.doesTableExist( self._inData ):
            msg = "ERROR: input data '%s' doesn't exist" % ( self._inData )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if os.path.exists( self._inData ):
            self._typeInData = "file"
        elif self._iDb.doesTableExist( self._inData ):
            self._typeInData = "table"
        if self._coordToConvert == "":
            msg = "ERROR: missing coordinates to convert (-c)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._coordToConvert not in [ "q", "s", "qs" ]:
            msg = "ERROR: unrecognized coordinates to convert '%s' (-c)" % ( self._coordToConvert )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._mapData == "":
            msg = "ERROR: missing mapping coordinates of chunks on chromosomes (-m)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if not os.path.exists( self._mapData ) and not self._iDb.doesTableExist( self._mapData ):
            msg = "ERROR: mapping data '%s' doesn't exist" % ( self._mapData )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if os.path.exists( self._mapData ):
            self._typeMapData = "file"
        elif self._iDb.doesTableExist( self._mapData ):
            self._typeMapData = "table"
        if self._outData == "":
            if self._convertChunks:
                self._outData = "%s.onChr" % ( self._inData )
            else:
                self._outData = "%s.onChk" % ( self._inData )
            if self._typeInData == "table":
                self._outData = self._outData.replace(".","_")
                
                
    ## Return a dictionary with the mapping of the chunks on the chromosomes
    #
    def getChunkCoordsOnChromosomes( self ):
        if self._typeMapData == "file":
            dChunks2CoordMaps = MapUtils.getDictPerNameFromMapFile( self._mapData )
        elif self._typeMapData == "table":
            tma = TableMapAdaptator( self._iDb, self._mapData )
            dChunks2CoordMaps = tma.getDictPerName()
        if self._verbose > 0:
            msg = "nb of chunks: %i" % ( len(dChunks2CoordMaps.keys()) )
            sys.stdout.write( "%s\n" % ( msg ) )
        return dChunks2CoordMaps
    
    
    def getRangeOnChromosome( self, chkRange, dChunks2CoordMaps ):
        chrRange = Range()
        chunkName = chkRange.seqname
        chrRange.seqname = dChunks2CoordMaps[ chunkName ].seqname
        if dChunks2CoordMaps[ chunkName ].start == 1:
            chrRange.start = chkRange.start
            chrRange.end = chkRange.end
        else:
            startOfChkOnChr = dChunks2CoordMaps[ chunkName ].start
            chrRange.start = startOfChkOnChr + chkRange.start - 1
            chrRange.end = startOfChkOnChr + chkRange.end - 1
        return chrRange
    
    
    def convCoordsChkToChrFromAlignFile( self, inFile, dChunks2CoordMaps ):
        return self.convCoordsChkToChrFromAlignOrPathFile( inFile, dChunks2CoordMaps, "align" )
    
    
    def convCoordsChkToChrFromPathFile( self, inFile, dChunks2CoordMaps ):
        return self.convCoordsChkToChrFromAlignOrPathFile( inFile, dChunks2CoordMaps, "path" )
    
    
    
    ## Convert coordinates of a Path or Align file from chunks to chromosomes
    #
    def convCoordsChkToChrFromAlignOrPathFile( self, inFile, dChunks2CoordMaps, format ):
        if self._verbose > 0:
            msg = "start method 'convCoordsChkToChrFromAlignOrPathFile'"
            sys.stdout.write( "%s\n" % ( msg ) )
        outFile = "%s.tmp" % ( inFile )
        inFileHandler = open( inFile, "r" )
        outFileHandler = open( outFile, "w" )
        if format == "align":
            iObject = Align()
        else:
            iObject = Path()
        countLine = 0
        
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            countLine += 1
            iObject.setFromString( line )
            if self._coordToConvert in [ "q", "qs" ]:
                queryOnChr = self.getRangeOnChromosome( iObject.range_query, dChunks2CoordMaps )
                iObject.range_query = queryOnChr
            if self._coordToConvert in [ "s", "qs" ]:
                subjectOnChr = self.getRangeOnChromosome( iObject.range_subject, dChunks2CoordMaps )
                iObject.range_subject = subjectOnChr
            iObject.write( outFileHandler )
            iObject.reset()
            
        inFileHandler.close()
        outFileHandler.close()
        if self._verbose > 0:
            msg = "end method 'convCoordsChkToChrFromAlignOrPathFile'"
            sys.stdout.write( "%s\n" % ( msg ) )
        return outFile
    
    
    ## Convert coordinates of a file from chunks to chromosomes
    #
    def convCoordsChkToChrFromFile( self, inFile, format, dChunks2CoordMaps ):
        if self._verbose > 0:
            msg = "start convCoordsChkToChrFromFile"
            sys.stdout.write( "%s\n" % ( msg ) )
        if format == "align":
            tmpAlignFile = self.convCoordsChkToChrFromAlignFile( inFile, dChunks2CoordMaps )
            tmpAlignTable = tmpAlignFile.replace(".","_").replace("-","_")
            self._iDb.createTable( tmpAlignTable, "align", tmpAlignFile, True, self._verbose-1 )
            os.remove( tmpAlignFile )
            self._iDb.removeDoublons( tmpAlignTable )
            outTable = "%s_path" % ( tmpAlignTable )
            self._iDb.convertAlignTableIntoPathTable( tmpAlignTable, outTable )
            self._iDb.dropTable( tmpAlignTable )
        elif format == "path":
            tmpPathFile = self.convCoordsChkToChrFromPathFile( inFile, dChunks2CoordMaps )
            outTable = tmpPathFile.replace(".","_").replace("-","_")
            self._iDb.createTable( outTable, "path", tmpPathFile, True, self._verbose-1 )
            os.remove( tmpPathFile )
        if self._verbose > 0:
            msg = "end convCoordsChkToChrFromFile"
            sys.stdout.write( "%s\n" % ( msg ) )
        return outTable
    
    
    ## Convert coordinates of a table from chunks to chromosomes
    #
    def convCoordsChkToChrFromTable( self, inTable, format, dChunks2CoordMaps ):
        tmpFile = inTable
        self._iDb.exportDataToFile( inTable, tmpFile, False )
        outTable = self.convCoordsChkToChrFromFile( tmpFile, format, dChunks2CoordMaps )
        os.remove( tmpFile )
        return outTable
    
    
    def getListsDirectAndReversePaths( self, lPaths ):
        lDirectPaths = []
        lReversePaths = []
        for iPath in lPaths:
            if iPath.isQueryOnDirectStrand() and iPath.isSubjectOnDirectStrand():
                lDirectPaths.append( iPath )
            else:
                lReversePaths.append( iPath )
        return lDirectPaths, lReversePaths
    
    
    def mergePaths( self, lPaths, lIdsToInsert, lIdsToDelete, dOldIdToNewId ):
        if len(lPaths) < 2:
            lIdsToInsert.append( lPaths[0].id )
            return
        i = 0
        while i < len(lPaths) - 1:
            i += 1
            if self._verbose > 1:
                print lPaths[i-1]
                print lPaths[i]
                sys.stdout.flush()
            idPrev = lPaths[i-1].id
            idNext = lPaths[i].id
            if lPaths[i-1].canMerge( lPaths[i] ):
                dOldIdToNewId[ idNext ] = idPrev
                if idPrev not in lIdsToInsert:
                    lIdsToInsert.append( idPrev )
                if idNext not in lIdsToDelete:
                    lIdsToDelete.append( idNext )
                lPaths[i-1].merge( lPaths[i] )
                del lPaths[i]
                i -= 1
#            else:
#                if idPrev not in lIdsToInsert:
#                    lIdsToInsert.append( idPrev )
#                if idNext not in lIdsToInsert:
#                    lIdsToInsert.append( idNext )
                    
                    
    def insertPaths( self, lPaths, lIdsToInsert, dOldIdToNewId ):
        for iPath in lPaths:
            if dOldIdToNewId.has_key( iPath.id ):
                iPath.id = dOldIdToNewId[ iPath.id ]
            if iPath.id in lIdsToInsert:
                self._tpa.insert( iPath )
                
                
    ## Merge Path instances in a Path table when they correspond to chunk overlaps
    #
    def mergeCoordsOnChunkOverlaps( self, dChunks2CoordMaps, tmpPathTable ):
        if self._verbose > 0:
            msg = "start method 'mergeCoordsOnChunkOverlaps'"
            sys.stdout.write( "%s\n" % ( msg ) )
        self._tpa = TablePathAdaptator( self._iDb, tmpPathTable )
        nbChunks = len(dChunks2CoordMaps.keys())
        for numChunk in range(1,nbChunks):
            chunkName1 = "chunk%s" % ( str(numChunk).zfill( len(str(nbChunks)) ) )
            chunkName2 = "chunk%s" % ( str(numChunk+1).zfill( len(str(nbChunks)) ) )
            if not dChunks2CoordMaps.has_key( chunkName2 ):
                break
            if self._verbose > 1:
                msg = "try merge on '%s' and '%s'" % ( chunkName1, chunkName2 )
                sys.stdout.write( "%s\n" % ( msg ) )
                sys.stdout.flush()
            chrName = dChunks2CoordMaps[ chunkName1 ].seqname
            if dChunks2CoordMaps[ chunkName2 ].seqname != chrName:
                if self._verbose > 1:
                    msg = "not on same chromosome (%s != %s)" % ( dChunks2CoordMaps[ chunkName2 ].seqname, chrName )
                    sys.stdout.write( "%s\n" % ( msg ) )
                    sys.stdout.flush()
                continue
            minCoord = min( dChunks2CoordMaps[ chunkName1 ].end, dChunks2CoordMaps[ chunkName2 ].start )
            maxCoord = max( dChunks2CoordMaps[ chunkName1 ].end, dChunks2CoordMaps[ chunkName2 ].start )
            lPaths = self._tpa.getChainListOverlappingQueryCoord( chrName, minCoord, maxCoord )
            if len(lPaths) == 0:
                if self._verbose > 1:
                    msg = "no overlapping matches on %s (%i->%i)" % ( chrName, minCoord, maxCoord )
                    sys.stdout.write( "%s\n" % ( msg ) )
                    sys.stdout.flush()
                continue
            if self._verbose > 1:
                msg = "%i overlapping matche(s) on %s (%i->%i)" % ( len(lPaths), chrName, minCoord, maxCoord )
                sys.stdout.write( "%s\n" % ( msg ) )
                sys.stdout.flush()
            lSortedPaths = PathUtils.getPathListSortedByIncreasingMinQueryThenMaxQueryThenIdentifier( lPaths )
            lDirectPaths, lReversePaths = self.getListsDirectAndReversePaths( lSortedPaths )
            lIdsToInsert = []
            lIdsToDelete = []
            dOldIdToNewId = {}
            if len(lDirectPaths) > 0:
                self.mergePaths( lDirectPaths, lIdsToInsert, lIdsToDelete, dOldIdToNewId )
            if len(lReversePaths) > 0:
                self.mergePaths( lReversePaths, lIdsToInsert, lIdsToDelete, dOldIdToNewId )
            self._tpa.deleteFromIdList( lIdsToDelete )
            self._tpa.deleteFromIdList( lIdsToInsert )
            self.insertPaths( lDirectPaths, lIdsToInsert, dOldIdToNewId )
            self.insertPaths( lReversePaths, lIdsToInsert, dOldIdToNewId )
        if self._verbose > 0:
            msg = "end method 'mergeCoordsOnChunkOverlaps'"
            sys.stdout.write( "%s\n" % ( msg ) )
            sys.stdout.flush()
            
            
    def saveChrCoordsAsFile( self, tmpPathTable, outFile ):
        self._iDb.exportDataToFile( tmpPathTable, tmpPathTable, False )
        self._iDb.dropTable( tmpPathTable )
        if self._formatInData == "align":
            PathUtils.convertPathFileIntoAlignFile( tmpPathTable, outFile )
            os.remove( tmpPathTable )
        elif self._formatInData == "path":
            os.rename( tmpPathTable, outFile )
            
            
    def saveChrCoordsAsTable( self, tmpPathTable, outTable ):
        if self._formatInData == "align":
            self._iDb.convertPathTableIntoAlignTable( tmpPathTable, outTable )
            self._iDb.dropTable( tmpPathTable )
        elif self._formatInData == "path":
            self._iDb.renameTable( tmpPathTable, outTable )
            
            
    ## Convert coordinates from chunks to chromosomes
    #
    def convertCoordinatesFromChunksToChromosomes( self ):
        dChunks2CoordMaps = self.getChunkCoordsOnChromosomes()
        
        if self._typeInData == "file":
            tmpPathTable = self.convCoordsChkToChrFromFile( self._inData, self._formatInData, dChunks2CoordMaps )
        elif self._typeInData == "table":
            tmpPathTable = self.convCoordsChkToChrFromTable( self._inData, self._formatInData, dChunks2CoordMaps )
            
        if self._mergeChunkOverlaps:
            self.mergeCoordsOnChunkOverlaps( dChunks2CoordMaps, tmpPathTable );
            
        if self._typeInData == "file":
            self.saveChrCoordsAsFile( tmpPathTable, self._outData )
        elif self._typeInData == "table":
            self.saveChrCoordsAsTable( tmpPathTable, self._outData )
            
            
    ## Convert coordinates from chromosomes to chunks
    #
    def convertCoordinatesFromChromosomesToChunks( self ):
        msg = "ERROR: convert coordinates from chromosomes to chunks not yet available"
        sys.stderr.write( "%s\n" % ( msg ) )
        sys.exit(1)
        
        
    ## Useful commands before running the program
    #
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            msg = "START ConvCoord.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            msg += "\ninput data: %s" % ( self._inData )
            if self._typeInData == "file":
                msg += " (file)\n"
            else:
                msg += " (table)\n"
            msg += "format: %s\n" % ( self._formatInData )
            msg += "coordinates to convert: %s\n" % ( self._coordToConvert )
            msg += "mapping data: %s" % ( self._mapData )
            if self._typeMapData == "file":
                msg += " (file)\n"
            else:
                msg += " (table)\n"
            if self._mergeChunkOverlaps:
                msg += "merge chunk overlaps\n"
            else:
                msg += "don't merge chunk overlaps\n"
            if self._convertChunks:
                msg += "convert chunks to chromosomes\n"
            else:
                msg += "convert chromosomes to chunks\n"
            msg += "output data: %s" % ( self._outData )
            if self._typeInData == "file":
                msg += " (file)\n"
            else:
                msg += " (table)\n"
            sys.stdout.write( msg )
            
            
    ## Useful commands before ending the program
    #
    def end( self ):
        self._iDb.close()
        if self._verbose > 0:
            msg = "END ConvCoord.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            sys.stdout.write( "%s\n" % ( msg ) )
            
            
    ## Run the program
    #
    def run( self ):
        self.start()
        
        if self._convertChunks:
            self.convertCoordinatesFromChunksToChromosomes()
        else:
            self.convertCoordinatesFromChromosomesToChunks()
            
        self.end()
        
        
if __name__ == "__main__":
    i = ConvCoord()
    i.setAttributesFromCmdLine()
    i.run()
