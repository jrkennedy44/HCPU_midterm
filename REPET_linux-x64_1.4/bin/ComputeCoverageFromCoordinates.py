#!/usr/bin/env python

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
import getopt

from pyRepetUnit.commons.coord.Map import Map
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.coord.AlignUtils import AlignUtils
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.checker.CheckerUtils import CheckerUtils


class ComputeCoverageFromCoordinates( object ):

    def __init__( self ):
        self._inputData = ""
        self._formatData = ""
        self._sequences = ""
        self._length = 0.0
        self._lRefSeqs = []
        self._configFile = ""
        self._clean = False
        self._verbose = 0
        self._db = None
        
        
    def help( self ):
        print
        print "usage: ComputeCoverageFromCoordinates.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: input data (can be file or table)"
        print "     -f: format of the data (map/set/align/path)"
        print "     -s: sequences to use ('qs'/'q'/'s')"
        print "         'q' for queries and 's' for subjects"
        print "     -l: bank length (in bp, to get coverage in %)"
        print "         or the coverage is returned only in bp"
        print "     -r: reference sequences to consider"
        print "         e.g. 'seq1+TE6+chr2'"
        print "         all by default"
        print "     -C: configuration file (if table as input)"
        print "     -c: clean"
        print "     -v: verbosity level (default=0/1)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:f:s:l:r:C:cv:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputData( a )
            elif o == "-f":
                self.setFormatData( a )
            elif o == "-s":
                self.setSequences( a )
            elif o == "-l":
                self.setBankLength( a )
            elif o == "-r":
                self.setRefSeqList( a )
            elif o == "-C":
                self.setConfigFile( a )
            elif o == "-c":
                self.setClean()
            elif o == "-v":
                self.setVerbosityLevel( a )
                
                
    def setInputData( self, a ):
        self._inputData = a
        
        
    def setFormatData( self, a ):
        self._formatData = a
        
        
    def setSequences( self, a ):
        self._sequences = a
        
        
    def setBankLength( self, a ):
        self._length = float(a)
        
        
    def setRefSeqList( self, a ):
        for refSeq in a.split("+"):
            self._lRefSeqs.append( refSeq )
            
            
    def setConfigFile( self, a ):
        self._configFile = a
        
        
    def setClean( self ):
        self._clean = True
        
        
    def setVerbosityLevel( self, a ):
        self._verbose = int(a)
        
        
    def checkAttributes( self ):
        if self._inputData == "":
            print "ERROR: missing input data (-i)"
            self.help()
            sys.exit(1)
        if not os.path.exists( self._inputData ):
            if not os.path.exists( self._configFile ):
                print "ERROR: neither input file '%s' nor configuration file '%s'" % ( self._inputData, self._configFile )
                self.help()
                sys.exit(1)
            if not os.path.exists( self._configFile ):
                msg = "ERROR: can't find config file '%s'" % ( self._configFile )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
            self._db = DbMySql( cfgFileName=self._configFile )
            if not self._db.exist( self._inputData ):
                print "ERROR: can't find table '%s'" % ( self._inputData )
                self.help()
                sys.exit(1)
        if self._formatData == "":
            print "ERROR: need to precise format (-f)"
            self.help()
            sys.exit(1)
        if self._formatData not in [ "map", "set", "align", "path" ]:
            print "ERROR: format '%s' not yet supported" % ( self._formatData )
            self.help()
            sys.exit(1)
        if self._formatData in [ "align", "path" ] and self._sequences == "":
            print "ERROR: need to precise sequences (-s) with format '%s'" % ( self._formatData )
            self.help()
            sys.exit(1)
        if self._formatData in [ "align", "path" ] and self._sequences not in [ "qs", "q" ]:
            print "ERROR: option '-s %s' not yet available" % ( self._sequences )
            self.help()
            sys.exit(1)
            
            
    def computeCoverageWithPythonLib( self, mapFile ):
        coverage = 0
        mapFileHandler = open( mapFile, "r" )
        lLines = mapFileHandler.readlines()
        mapFileHandler.close()
        lMaps = []
        for line in lLines:
            iMap = Map()
            iMap.setFromString( line )
            if not iMap.isOnDirectStrand():
                iMap.reverse()
            lMaps.append( iMap )
        if self._verbose > 0:
            print "nb of 'Map' instances: %i" % ( len(lMaps) )
            sys.stdout.flush()
            
        if len(lMaps) <= 1000:
            lSets = SetUtils.getSetListFromMapList( lMaps )
            lMergedSets = SetUtils.mergeSetsInList( lSets )
            if self._verbose > 0:
                print "nb of merged 'Set' instances: %i" % ( len(lMergedSets) )
            if self._verbose > 0:
                for i in lMergedSets: i.show()
            sys.stdout.flush()
            coverage = SetUtils.getCumulLength( lMergedSets )
            
        return coverage
    
    
    def computeCoverageWithCppLib( self, mapFile ):
        if self._verbose > 0:
            print "use mapOp"; sys.stdout.flush()
        if not CheckerUtils.isExecutableInUserPath( "mapOp" ):
            msg = "ERROR: 'mapOp' is not in your PATH"
            sys.stderr.write( "%s\n" % msg )
            sys.exit(1)
        cmd = "mapOp"
        cmd += " -q %s" % ( mapFile )
        cmd += " -m"
        cmd += " 2>&1 > /dev/null"
        exitStatus = os.system( cmd )
        if exitStatus != 0:
            print "ERROR: mapOp returned %i" % ( exitStatus )
            sys.exit(1)
        mergeFile = "%s.merge" % ( mapFile )
        if self._verbose > 0:
            print "compute coverage..."
        mergeFileHandler = open( mergeFile, "r" )
        coverage = 0
        while True:
            line = mergeFileHandler.readline()
            if line == "":
                break
            tokens = line.split("\t")
            coverage += abs( int(tokens[3]) - int(tokens[2]) ) + 1
        mergeFileHandler.close()
        if self._clean: os.remove( mergeFile )
        return coverage
    
    
    def getCoverageFromMapFile( self, mapFile ):
        mapFileHandler = open( mapFile, "r" )
        tmpFile = "%s.tmp" % ( mapFile )
        tmpFileHandler = open( tmpFile, "w" )
        iMap = Map()
        nbMaps = 0
        while True:
            line = mapFileHandler.readline()
            if line == "": break
            iMap.setFromString( line )
            nbMaps += 1
            if self._lRefSeqs == [] \
            or iMap.getName() in self._lRefSeqs \
            or iMap.getSeqname() in self._lRefSeqs:
                iMap.write( tmpFileHandler )
        tmpFileHandler.close()
        mapFileHandler.close()
        if nbMaps <= 10:
            coverage = self.computeCoverageWithPythonLib( tmpFile )
        else:
            coverage = self.computeCoverageWithCppLib( tmpFile )
        if self._clean: os.remove( tmpFile )
        return coverage
    
    
    def getCoverageFromAlignFile( self ):
        mapFile = "%s.map" % ( self._inputData )
        if self._sequences == "qs":
            AlignUtils.convertAlignFileIntoMapFileWithQueriesAndSubjects( self._inputData, mapFile )
        if self._sequences == "q":
            AlignUtils.convertAlignFileIntoMapFileWithSubjectsOnQueries( self._inputData, mapFile )
        coverage = self.getCoverageFromMapFile( mapFile )
        if self._clean: os.remove( mapFile )
        return coverage
    
    
    def start( self ):
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ )
            sys.stdout.flush()
        self.checkAttributes()
        
        
    def end( self ):
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ )
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        
        if self._db != None:
            cmd = "srptExportTable.py"
            cmd += " -i %s" % ( self._inputData )
            cmd += " -C %s" % ( self._configFile )
            cmd += " -o %s.%s" % ( self._inputData, self._formatData )
            exitStatus = os.system( cmd )
            if exitStatus != 0:
                print "ERROR while exporting data from table"
                sys.exit(1)
            self._inputData += ".%s" % ( self._formatData )
            self._db.close()
            
        if self._formatData == "map":
            coverage = self.getCoverageFromMapFile( self._inputData )
        elif self._formatData == "set":
            mapFile = "%s.map" % ( self._inputData )
            SetUtils.convertSetFileIntoMapFile( self._inputData, mapFile )
            self._inputData = mapFile
            coverage = self.getCoverageFromMapFile( self._inputData )
            if self._clean: os.remove( self._inputData )
        elif self._formatData == "align":
            coverage = self.getCoverageFromAlignFile()
        elif self._formatData == "path":
            PathUtils.convertPathFileIntoAlignFile( self._inputData, "%s.align" % ( self._inputData ) )
            self._inputData += ".align"
            coverage = self.getCoverageFromAlignFile()
            if self._clean: os.remove( self._inputData )
            
        print "coverage: %i bp" % ( coverage )
        if self._length > 0:
            print "coverage: %.2f%%" % ( 100 * coverage / self._length )
        sys.stdout.flush()
        
        self.end()
        
        
if __name__ == "__main__":
    i = ComputeCoverageFromCoordinates()
    i.setAttributesFromCmdLine()
    i.run()
