#!/usr/bin/env python

"""
Connect TE paths via a 'long join' procedure.
"""

import os
import sys
import getopt

from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.LoggerFactory import LoggerFactory


class LongJoinsForTEs:
    """
    Connect TE paths via a long join procedure.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inTable = ""
        self._maxOverlap = 15
        self._maxGapLength = 5000
        self._maxMismatchLength = 500
        self._identityTolerance = 2.0
        self._minNestedTEcoverage = 0.95
        self._minLengthToSplit = 100
        self._minLengthToKeepChain = 20
        self._outTable = ""
        self._configFileName = ""
        self._verbose = 0
        self._db = None
        self._tpA = None
        self._tmpTable = ""
        self._logger = None
        self._name = "LongJoinsForTEs"
        
    def help( self ):
        """
        Display the help.
        """
        print
        print "usage:",sys.argv[0].split("/")[-1],"[options]"
        print "options:"
        print "     -h: this help"
        print "     -t: name of the input table (format='path')"
        print "     -i: identity tolerance, in % (default=2)"
        print "     -o: max overlap size, in bp (default=15)"
        print "     -g: max gap size, in bp (default=5000)"
        print "     -m: max mismatch size, in bp (default=500)"
        print "     -c: TE insertion coverage, (default=0.95)"
        print "     -s: min length to split a connection, in bp (default=100)"
        print "     -l: min length to keep a chain (default=20)"
        print "     -O: name of the output table (default=inTable+'_join')"
        print "     -C: configuration file"
        print "     -v: verbose (default=0/1/2)"
        print
        
    def setAttributesFromCmdLine( self ):
        """
        Set attributes from the command-line arguments.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"ht:i:o:g:m:c:s:l:O:C:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-t":
                self.setInputTable( a )
            elif o == "-i":
                self.setIdentityTolerance( a )
            elif o == "-o":
                self.setMaxOverlap( a )
            elif o == "-g":
                self.setMaxGapLength( a )
            elif o == "-m":
                self.setMaxMismatchLength( a )
            elif o == "-c":
                self.setMinNestedTEcoverage( a )
            elif o == "-s":
                self.setMinLengthToSplit( a )
            elif o == "-l":
                self.setMinLengthToKeepChain( a )
            elif o == "-O":
                self.setOutputTable( a )
            elif o == "-C":
                self.setConfigFileName( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setInputTable( self, inTable ):
        self._inTable = inTable
        
    def setIdentityTolerance( self, identityTolerance ):
        self._identityTolerance = float(identityTolerance)
        
    def setMaxOverlap( self, maxOverlap ):
        self._maxOverlap = int(maxOverlap)
        
    def setMaxGapLength( self, maxGapLength ):
        self._maxGapLength = int(maxGapLength)
        
    def setMaxMismatchLength( self, maxMismatchLength ):
        self._maxMismatchLength = int(maxMismatchLength)
        
    def setMinNestedTEcoverage( self, minNestedTEcoverage ):
        self._minNestedTEcoverage = float(minNestedTEcoverage)
        
    def setMinLengthToSplit( self, minLengthToSplit ):
        self._minLengthToSplit = int(minLengthToSplit)
        
    def setMinLengthToKeepChain( self, minLengthToKeepChain ):
        self._minLengthToKeepChain = int(minLengthToKeepChain)
        
    def setOutputTable( self, outTable ):
        self._outTable = outTable
        
    def setConfigFileName( self, configFileName ):
        self._configFileName = configFileName
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
    def setLogger( self, logFile="" ):
        if logFile == "":
            logFile = "%s_%s.log" % ( self._inTable, self._name )
        if os.path.exists( logFile ):
            os.remove( logFile )
        self._logger = LoggerFactory.createLogger( logFile )
        
        
    def checkAttributes( self ):
        """
        Before running, check the required attributes are properly filled.
        """
        if self._inTable == "":
            print "ERROR: missing input table name"
            self.help(); sys.exit(1)
        if self._configFileName == "" or not os.path.exists( self._configFileName ):
            print "ERROR: missing configuration file"
            self.help(); sys.exit(1)
        if self._outTable == "":
            self._outTable = "%s_join" % ( self._inTable )
            
            
    def getDistanceBetweenRanges( self, r1, r2 ):
        """
        Return the distance between both ranges by handling all possible strands.
        """
        if r1.isOnDirectStrand() != r2.isOnDirectStrand():
            print "ERROR: can't compute distance for ranges on different strands"
            sys.exit(1)
        if r1.isOnDirectStrand() and r2.isOnDirectStrand():
            if r1.start < r2.start:
                return r2.start - r1.end
            else:
                return r1.start - r2.end
        else:
            if r1.end < r2.end:
                return r2.end - r1.start
            else:
                return r1.end - r2.start
            
            
    def getDiagonalsGapAndMismatch( self, path1, path2, distQ, distS ):
        """
        Return the diagonals, gap and mismatch between two path instances.
        """
        diag1 = path1.range_subject.getMax() - path1.range_query.getMax()
        diag2 = path2.range_subject.getMin() - path2.range_query.getMin()
        gap = diag1 - diag2
        if gap > 0:  # gap on query
            mismatch = distS
        else:
            mismatch = distQ
        return diag1, diag2, gap, mismatch
    
    
    def joinTEpathsPerQuerySubject( self, qry, sbj, lPaths, lJoinedPaths ):
        """
        Try to join TE paths for a given TE family.
        @param qry: query name
        @type qry: string
        @param sbj: subject name
        @type sbj: string
        @param lPaths: list of paths to join, if possible
        @type lPaths: list of {Path<Path>} instances
        @param lJoinedPaths: list of {Path<Path>} instances that have already been joined
        @type lJoinedPaths: list of {Path<Path>} instances
        """
        
        if len(lPaths) < 2: return
        string = "* query '%s' with subject '%s' (%i hits)" % ( qry, sbj, len(lPaths) )
        self._logger.info( string )
        if self._verbose > 1: print string; sys.stdout.flush()
        
        for p in lPaths:
            if not p.range_query.isOnDirectStrand():
                string = "query in table is on reverse strand"
                self._logger.error( string )
                print "ERROR: %s" % ( string )
                sys.exit(1)
                
        for i in xrange(1,len(lPaths)):
            string = "try to join path[i-1] (%s)\nwith path[i] (%s)" % ( lPaths[i-1].toString().replace("\t","-"), lPaths[i].toString().replace("\t","-") )
            self._logger.info( string )
            if self._verbose > 1: print string
            
            if lPaths[i].range_query.start == lPaths[i-1].range_query.start:
                string = "deny long join: query[i] start = query[i-1] start"
                self._logger.info( string )
                if self._verbose > 1: print string; sys.stdout.flush()
                continue
            
            if lPaths[i].range_query.end == lPaths[i-1].range_query.end:
                string = "deny long join: query[i] end = query[i-1] end"
                self._logger.info( string )
                if self._verbose > 1: print string; sys.stdout.flush()
                continue
            
            distBetweenQueries = self.getDistanceBetweenRanges( lPaths[i-1].range_query, lPaths[i].range_query )
            distBetweenSubjects = self.getDistanceBetweenRanges( lPaths[i-1].range_subject, lPaths[i].range_subject )
            string = "distBetweenQueries=%i distBetweenSubjects=%i" % ( distBetweenQueries, distBetweenSubjects )
            self._logger.info( string )
            if self._verbose > 1: print string
            
            if distBetweenQueries > 100000:  # > 100 kb
                string = "deny long join: too long gap on query (%i bp)" % ( distBetweenQueries )
                self._logger.info( string )
                if self._verbose > 1: print string
                continue
            
            if distBetweenSubjects > 30000:  # > 30 kb
                string = "deny long join: too long gap on subject (%i bp)" % ( distBetweenSubjects )
                self._logger.info( string )
                if self._verbose > 1: print string
                continue
            
            if distBetweenQueries < (self._maxOverlap*-1):
                string = "deny long join: too much overlap on query (%i bp)" % ( distBetweenQueries )
                self._logger.info( string )
                if self._verbose > 1: print string
                continue
            
            if distBetweenSubjects < (self._maxOverlap*-1):
                string = "deny long join: too much overlap on subject (%i bp)" % ( distBetweenSubjects )
                self._logger.info( string )
                if self._verbose > 1: print string
                continue
            
            diag1, diag2, gap, mismatch = self.getDiagonalsGapAndMismatch( lPaths[i-1], lPaths[i], distBetweenQueries, distBetweenSubjects )
            string = "diag1=%i diag2=%i" % ( diag1, diag2 )
            self._logger.info( string )
            if self._verbose > 1: print string
            string = "gap=%i mismatch=%i" % ( gap, mismatch )
            self._logger.info( string )
            if self._verbose > 1: print string
            
            if mismatch > self._maxMismatchLength:
                if gap > 0:
                    string = "deny long join: too much mismatch on subject (%i bp)" % ( mismatch )
                else:
                    string = "deny long join: too much mismatch on query (%i bp)" % ( mismatch )
                self._logger.info( string )
                if self._verbose > 1: print string
                continue
            
            meanIdentity = PathUtils.getIdentityFromPathList( lPaths[ i-1 : i+1 ], True )
            string = "meanIdentity=%.3f" % ( meanIdentity )
            self._logger.info( string )
            if self._verbose > 1: print string
            if abs( lPaths[i-1].identity - meanIdentity ) > self._identityTolerance:
                string = "deny long join: | identity[i-1] %.3f - meanIdentity | > %.3f" %\
                ( lPaths[i-1].identity, self._identityTolerance )
                self._logger.info( string )
                if self._verbose > 1: print string; sys.stdout.flush()
                continue
            if abs( lPaths[i].identity - meanIdentity ) > self._identityTolerance:
                string = "deny long join: | identity[i] %.3f - meanIdentity | > %.3f" %\
                ( lPaths[i].identity, self._identityTolerance )
                self._logger.info( string )
                if self._verbose > 1: print string; sys.stdout.flush()
                continue
            
            else:
                
                if gap <= self._maxGapLength:
                    string = "allow long join: identity %.2f and %.2f" % ( lPaths[i].identity, lPaths[i-1].identity )
                    self._logger.info( string )
                    if self._verbose > 1: print string
                    newPathId = self._tpA.joinTwoPaths( lPaths[i-1].id, lPaths[i].id )
                    lJoinedPaths.append( ( qry, lPaths[i-1], lPaths[i], distBetweenQueries, distBetweenSubjects ) )
                    continue
                
                lNestedPaths = self._tpA.getPathListIncludedInQueryCoord( qry, lPaths[i-1].range_query.end+1, lPaths[i].range_query.start-1 )
                if lNestedPaths == []:
                    string = "deny long join: no nested TEs"
                    self._logger.info( string )
                    if self._verbose > 1: print string
                else:
                    identityNestedPaths = PathUtils.getIdentityFromPathList( lNestedPaths, False )
                    identityCheckedPaths = PathUtils.getIdentityFromPathList( [ lPaths[i-1], lPaths[i] ], True )
                    if identityNestedPaths < identityCheckedPaths:
                        string = "deny long join: nested TEs are older (%.2f < %.2f)" % ( identityNestedPaths, identityCheckedPaths )
                        self._logger.info( string )
                        if self._verbose > 1: print string
                        continue
                    
                    lNestedSets = PathUtils.getSetListFromQueries( lNestedPaths )
                    lMergedNestedSets = SetUtils.mergeSetsInList( lNestedSets )
                    size = SetUtils.getCumulLength( lMergedNestedSets )
                    nestedTEcoverage = float(size) / float(distBetweenQueries)
                    if nestedTEcoverage < self._minNestedTEcoverage:
                        string = "deny long join: too low coverage of younger, nested TEs (%.2f < %.2f)" % ( nestedTEcoverage, self._minNestedTEcoverage )
                        self._logger.info( string )
                        if self._verbose > 1: print string
                        continue
                    
                    string = "allow long join: high coverage of younger, nested TEs (%.2f > %.2f)" % \
                             ( nestedTEcoverage, self._minNestedTEcoverage )
                    self._logger.info( string )
                    if self._verbose > 1: print string
                    newPathId = self._tpA.joinTwoPaths( lPaths[i-1].id, lPaths[i].id )
                    lJoinedPaths.append( ( qry, lPaths[i-1], lPaths[i], distBetweenQueries, distBetweenSubjects ) )
                    
                    
    def join( self ):
        """
        Try to join path ranges from a TE annotation table (output from Matcher).
        """
        
        string = "beginning of the 'long join' procedure..."
        self._logger.info( string )
        if self._verbose > 0: print "%s" % ( string ); sys.stdout.flush()
        string = "max overlap length: %d" % ( self._maxOverlap )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        string = "max gap length: %d" % ( self._maxGapLength )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        string = "max mismatch length: %d" % ( self._maxMismatchLength )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        string = "identity tolerance: %.2f" % ( self._identityTolerance )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        string = "inserted TE coverage: %.2f" % ( self._minNestedTEcoverage )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        
        self._tmpTable = self._tpA.path2PathRange()
        lJoinedPaths = []
        
        lQueryNames = self._tpA.getQueryList()
        lQueryNames.sort()
        for qry in lQueryNames:
            
            lSubjectNames = self._tpA.getSubjectListFromQuery( qry)
            lSubjectNames.sort()
            for sbj in lSubjectNames:
                
                self._tpA._table = self._tmpTable   # get data as 'pathranges'
                lPaths = self._tpA.getPathListWithDirectQueryDirectSubjectFromQuerySubject( qry, sbj )
                self._tpA._table = self._inTable    # do the joins on the input table
                self.joinTEpathsPerQuerySubject( qry, sbj, lPaths, lJoinedPaths )
                
                self._tpA._table = self._tmpTable
                lPaths = self._tpA.getPathListWithDirectQueryReverseSubjectFromQuerySubject( qry, sbj )
                self._tpA._table = self._inTable
                self.joinTEpathsPerQuerySubject( qry, sbj, lPaths, lJoinedPaths )
                
        string = "nb of long joins: %i" % ( len(lJoinedPaths) )
        self._logger.info( string )
        if self._verbose > 0:
            print string; sys.stdout.flush()
            
            
    def split( self ):
        """
        Try to split the connections made in method L{join<join>} by considering all the TE families.
        A connection is cut if it overlaps with a more recent hit (using weighted identity).
        """
        
        string = "beginning of the 'split' procedure..."
        self._logger.info( string )
        if self._verbose > 0: print "%s" % ( string ); sys.stdout.flush()
        string = "min length to split: %i" % ( self._minLengthToSplit )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        
        self._db.remove_if_exist( self._outTable )
        self._db.create_path( self._outTable, "" )
        tpAout = TablePathAdaptator( self._db, self._outTable )
        nbSplits = 0
        newId = self._tpA.getNewId()
        
        lQueryNames = self._tpA.getQueryList()
        lQueryNames.sort()
        for qry in lQueryNames:
            
            lPathLists = self._tpA.getListOfChainsSortedByAscIdentityFromQuery( qry )
            string = "query '%s': %i path collection(s)" % ( qry, len(lPathLists) )
            self._logger.info( string )
            if self._verbose > 1: print string
            
            for i in xrange(0,len(lPathLists)):
                lMostAncientPaths = lPathLists[i]
                lPathnums = PathUtils.getListOfDistinctIdentifiers( lMostAncientPaths )
                if len(lPathnums) > 1:
                    string = "connected paths have different identifiers"
                    self._logger.error( string )
                    print "ERROR: %s" % ( string )
                    sys.exit(1)
                initId = lPathnums[0]
                string = "try split on query '%s' id=%i" % ( qry, initId )
                self._logger.info( string )
                if self._verbose > 1: print string
                
                lPathsToInsert = []
                
                if len( lMostAncientPaths ) == 1:  # a single path, no connection that could be cut
                    string = "no connection to test"
                    self._logger.info( string )
                    if self._verbose > 1: print string
                    lPathsToInsert += lMostAncientPaths
                    
                else:   # several connected paths, try to split them (cut the connections)
                    lQryN = PathUtils.getListOfDistinctQueryNames( lMostAncientPaths )
                    if len(lQryN) > 1:
                        string = "connected paths have different query names"
                        self._logger.error( string )
                        print "ERROR: %s" % ( string )
                        sys.exit(1)
                        
                    lJoinCoordinates = PathUtils.getListOfJoinCoordinatesOnQuery( lMostAncientPaths, self._minLengthToSplit )
                    if lJoinCoordinates == []:
                        string = "neglect connections"
                        self._logger.info( string )
                        if self._verbose > 1: print string
                        lPathsToInsert += lMostAncientPaths
                    else:
                        lOverlapPaths = []
                        for i in lJoinCoordinates:
                            string = "search for overlaps between %i and %i" % ( i[0], i[1] )
                            self._logger.info( string )
                            if self._verbose > 1: print string
                            lTmp = tpAout.getPathListIncludedInQueryCoord( qry, i[0], i[1] )
                            if lTmp == []:
                                string = "no overlap"
                                self._logger.info( string )
                                if self._verbose > 1: print string
                            else:
                                if PathUtils.getLengthOnQueryFromPathList( lTmp ) > self._minLengthToSplit:
                                    lOverlapPaths += lTmp
                                else:
                                    string = "too short overlaps (< %i bp)" % ( self._minLengthToSplit )
                                    self._logger.info( string )
                                    if self._verbose > 1: print string
                                    
                        if lOverlapPaths == []:
                            lPathsToInsert += lMostAncientPaths
                        else:
                            lLists = PathUtils.getPathListUnjoinedBasedOnQuery( lOverlapPaths, lMostAncientPaths )
                            string = "%i connection" % ( len(lLists) - 1 )
                            if len(lLists) - 1 > 1:
                                string += "s"
                            string += " to cut"
                            self._logger.info( string )
                            if self._verbose > 1: print string
                            nbSplits += len(lLists) - 1
                            lPathsToInsert += lLists[0]
                            for lPaths in lLists[1:]:
                                PathUtils.changeIdInList( lPaths, newId )
                                newId += 1
                                lPathsToInsert += lPaths

                lFilteredPathsToInsert = PathUtils.filterPathListOnChainLength( lPathsToInsert, self._minLengthToKeepChain )
                tpAout.insertList( lFilteredPathsToInsert )
                self._tpA.deleteFromId( initId )
                
        string = "nb of splits: %i" % ( nbSplits )
        self._logger.info( string )
        if self._verbose > 0: print string
        if not self._tpA.isEmpty():
            string = "remaining paths in temporary table"
            self._logger.error( string )
            print "ERROR: %s" % ( string )
            sys.exit(1)
            
            
    def start( self ):
        """
        Open the connection with MySQL, copy the input table and print some stats.
        """
        self.checkAttributes()
        self.setLogger()
        string = "START %s.py" % ( self._name )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        
        self._db = DbMySql( cfgFileName=self._configFileName )
        self._db.copy_table( self._inTable, self._inTable + "_copy" )
        self._db.changePathQueryCoordinatesToDirectStrand( self._inTable )
        self._tpA = TablePathAdaptator( self._db, self._inTable )
        string = "nb of distinct queries: %i" % ( len(self._tpA.getQueryList()) )
        self._logger.info( string )
        if self._verbose > 0: print string
        string = "nb of distinct paths: %i" % ( self._tpA.getSize() )
        self._logger.info( string )
        if self._verbose > 0: print string
        string = "nb of distinct identifiers: %i" % ( self._tpA.getNbIds() )
        self._logger.info( string )
        if self._verbose > 0: print string
        
        
    def finish( self ):
        """
        Show some stats, clean temporary tables, close the connection with MySQL.
        """
        self._tpA._table = self._outTable
        string = "nb of distinct queries: %i" % ( len(self._tpA.getQueryList()) )
        self._logger.info( string )
        if self._verbose > 0: print string
        string = "nb of distinct paths: %i" % ( self._tpA.getSize() )
        self._logger.info( string )
        if self._verbose > 0: print string
        string = "nb of distinct identifiers: %i" % ( self._tpA.getNbIds() )
        self._logger.info( string )
        if self._verbose > 0: print string
        self._db.remove_if_exist( self._inTable )
        self._db.remove_if_exist( self._tmpTable )
        self._db.rename( self._inTable + "_copy", self._inTable )
        self._db.close()
        
        string = "END %s.py" % ( self._name )
        self._logger.info( string )
        if self._verbose > 0: print string; sys.stdout.flush()
        
        
    def run( self ):
        """
        Run the whole program.
        """
        self.start()
        self.join()
        self.split()
        self.finish()
        
        
if __name__ == "__main__":
    i = LongJoinsForTEs()
    i.setAttributesFromCmdLine()
    i.run()

#    try:
#        import profile, pstats
#    except ImportError:
#        pass
#    else:
#        profile.run( "i.run()", "prof" )
#        #p = pstats.Stats( "prof" )
#        #p.strip_dirs().print_stats()
#        #p.strip_dirs().sort_stats('name').sort_stats('cumulative').print_stats(15)
#        p.strip_dirs().sort_stats('time').print_stats(15)
