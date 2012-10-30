#!/usr/bin/env python

##@file
# Calculate the sensitivity and specificity of one table (predictions) against the other (references).
# Also return the counts of true positives, false positives, true negatives and false negatives.
# Only consider query coordinates when comparing match boundaries.
# usage: %s [options]
# options:
#      -h: this help
#      -t: name of the table to test (format='path')
#      -r: name of the reference table (format='path')
#      -C: name of the configuration file
#      -l: cumulative length of the queries (used for TN)
#      -b: compare boundaries
#      -v: verbosity level (default=0/1/2)

import os
import sys
import getopt
from pyRepetUnit.commons.LoggerFactory import LoggerFactory
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils

class CompareTwoPathTables( object ):
    """
    Calculate the sensitivity and specificity of one table (predictions) against the other (references).
    Also return the counts of true positives, false positives, true negatives and false negatives.
    Only consider query coordinates.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._predData = ""
        self._refData = ""
        self._typeData = ""
        self._configFile = ""
        self._cumulLengthQueries = 0
        self._compareBoundaries = False
        self._mergeData = False
        self._verbose = 0
        self._db = None
        self._tpaPred = None
        self._tpaRef = None
        self._logger = None
        self._name = "CompareTwoPathTables"
        self._lCases = [ "pred_1-to-1", \
                        "exact", "near exact", "one-side exact", \
                        "equivalent", "near equivalent", \
                        "similar", "different strand", \
                        "pred_1-to-0", "pred_1-to-n" ]
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage: %s [options]" % ( sys.argv[0] )
        print "options:"
        print "     -h: this help"
        print "     -p: name of the predicted data (format='path')"
        print "     -r: name of the reference data (format='path')"
        print "     -t: type of the data (file/table)"
        print "     -C: name of the configuration file to access MySQL (e.g. 'TEannot.cfg')"
        print "     -l: cumulative length of the queries (used for TN)"
        print "     -b: compare boundaries (query coordinates)"
        print "     -m: merge data (query coordinates)"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hp:r:t:C:l:bmv:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-p":
                self._predData = a
            elif o == "-r":
                self._refData = a
            elif o == "-t":
                self._typeData = a
            elif o == "-C":
                self._configFile = a
            elif o == "-l":
                self._cumulLengthQueries = int(a)
            elif o == "-b":
                self._compareBoundaries = True
            elif o == "-m":
                self._mergeData = True
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._predData == "":
            print "ERROR: missing predicted data (-p)"
            self.help(); sys.exit(1)
        if self._refData == "":
            print "ERROR: missing reference data (-r)"
            self.help(); sys.exit(1)
        if self._typeData == "":
            print "ERROR: missing data type (-t)"
            self.help(); sys.exit(1)
        if self._configFile == "":
            print "ERROR: missing configuration file (-C)"
            self.help(); sys.exit(1)
        if not os.path.exists( self._configFile ):
            print "ERROR: can't find configuration file '%s'" % ( self._configFile )
            self.help(); sys.exit(1)
        self._db = DbMySql( cfgFileName=self._configFile )
        if self._cumulLengthQueries == 0:
            print "ERROR: need cumulative length of queries to compute true negatives (-l)"
            self.help(); sys.exit(1)
        if self._typeData == "file":
            if not os.path.exists( self._predData ):
                print "ERROR: can't find file of predicted data '%s'" % ( self._predData )
                self.help(); sys.exit(1)
            if not os.path.exists( self._refData ):
                print "ERROR: can't find file of reference data '%s'" % ( self._predData )
                self.help(); sys.exit(1)
        elif self._typeData == "table":
            if not self._db.exist( self._predData ):
                print "ERROR: can't find table of predicted data '%s'" % ( self._predData )
                self.help(); sys.exit(1)
            if not self._db.exist( self._refData ):
                print "ERROR: can't find table of reference data '%s'" % ( self._predData )
                self.help(); sys.exit(1)
        else:
            print "ERROR: unrecognized data type '%s'" % ( self._typeData )
            self.help(); sys.exit(1)
            
            
    def setAdaptatorsToTablesFromInputData( self ):
        """
        If input data are files, load them into tables. Then set adaptators to path tables.
        """
        if self._typeData == "file":
            pathPredTable = self._predData.replace(".","_")
            self._db.dropTable( pathPredTable )
            self._db.createPathTable( pathPredTable, self._predData )
            pathRefTable = self._refData.replace(".","_")
            self._db.dropTable( pathRefTable )
            self._db.createPathTable( pathRefTable, self._refData )
            self._tpaPred = TablePathAdaptator( self._db, pathPredTable )
            self._tpaRef = TablePathAdaptator( self._db, pathRefTable )
        else:
            self._tpaPred = TablePathAdaptator( self._db, self._predData )
            self._tpaRef = TablePathAdaptator( self._db, self._refData )
            
            
    def getCounts( self ):
        """
        Get the true positive, false positive, true negative and false negative:
        TP: found in test as in ref
        FP: found in test but not in ref
        TN: neither found in test nor in ref
        FN: not found in test but found in ref
        """
        tp, fp, fn = 0, 0, 0
        tn = self._cumulLengthQueries
        nbTestMatches = 0
        nbRefMatches = 0
        
        lTestQueries = self._tpaPred.getQueryList()
        lRefQueries = self._tpaRef.getQueryList()
        string = "nb of queries"
        string += "\nin predicted data: %i" % ( len(lTestQueries) )
        string += "\nin reference data: %i" % ( len(lRefQueries) )
        self._logger.info( string )
        if self._verbose > 0:
            print string
            sys.stdout.flush()
        
        for testQuery in lTestQueries:
            lTest = self._tpaPred.getSetListFromQuery( testQuery )
            nbTestMatches += len(lTest)
            lTest = SetUtils.mergeSetsInList( lTest )
            testLength = SetUtils.getCumulLength( lTest )
            lRef = self._tpaRef.getSetListFromQuery( testQuery )
            nbRefMatches += len(lRef)
            lRef = SetUtils.mergeSetsInList( lRef )
            refLength = SetUtils.getCumulLength( lRef )
            overlapLength = SetUtils.getOverlapLengthBetweenLists( lTest, lRef )
            tp += overlapLength
            fp += testLength - overlapLength
            tn -= testLength + ( refLength - overlapLength )
            fn += refLength - overlapLength
            
        string = "nb of matches"
        string += "\nin predicted data: %i" % ( nbTestMatches )
        string += "\nin reference data: %i" % ( nbRefMatches )
        self._logger.info( string )
        if self._verbose > 0:
            print string
            sys.stdout.flush()
        
        return tp, fp, tn, fn
    
    
    def getPerformanceMeasures( self, tp, fp, tn, fn ):
        """
        Get the sensitivity and specificity.
        """
        sensitivity = tp / float( tp + fn )
        specificity = tn / float( tn + fp )
        return sensitivity, specificity
    
    
    def mergeMatchesInTable( self, table ):
        mergeTable = "%s_merged" % ( table )
        cmd = "%s/bin/srptExportTable.py" % ( os.environ["REPET_PATH"] )
        cmd += " -i %s" % ( table )
        cmd += " -p 'ORDER BY query_name,query_start,subject_name,subject_start'"
        cmd += " -C %s" % ( self._configFile )
        returnStatus = os.system( cmd )
        if returnStatus != 0:
            print "ERROR while exporting table '%s'" % ( table )
            sys.exit(1)
        mergeFile = "%s.merged" % ( table )
        PathUtils.mergeMatchesOnQueries( table, mergeFile )
        os.remove( table )
        self._db.dropTable( mergeTable )
        self._db.createPathTable( mergeTable, mergeFile )
        #os.remove( mergeFile )
        return mergeTable
    
    
    def compareBoundariesBetweenPredAndRefMatches( self, predMatch, refMatch ):
        """
        Compare predicted and reference matches in terms of boundaries. Several cases exist:
        distance <= 1 bp in 5' and 3': predicted match is exact
        distance <= 1 bp in 5' (or 3') and 1 < distance <= 10 bp in 3' (or 5'): predicted match is near exact
        distance <= 1 bp in 5' (or 3') and distance > 10 bp in 3' (or 5'): predicted match is one-side exact
        1 < distance <= 10 bp in 5' and 3': predicted match is equivalent
        1 < distance <= 10 bp in 5' (or 3') and d > 10 bp in 3' (or 5'): predicted match is near equivalent
        distance > 10 bp in 5' and 3': predicted match is similar
        """
        distMinCoords = abs( predMatch.range_query.getMin() - refMatch.range_query.getMin() )
        distMaxCoords = abs( predMatch.range_query.getMax() - refMatch.range_query.getMax() )
        
        if distMinCoords <= 1 and distMaxCoords <= 1:
            return "exact"
            
        elif ( distMinCoords <= 1 and distMaxCoords <= 10 ) or ( distMinCoords <= 10 and distMaxCoords <= 1 ):
            return "near exact"
            
        elif ( distMinCoords <= 1 and distMaxCoords > 10 ) or ( distMinCoords > 10 and distMaxCoords <= 1 ):
            return "one-side exact"
            
        elif distMinCoords <= 10 and distMaxCoords <= 10:
            return "equivalent"
            
        elif ( distMinCoords <= 10 and distMaxCoords > 10 ) or ( distMinCoords > 10 and distMaxCoords <= 10 ):
            return "near equivalent"
            
        elif distMinCoords > 10 and distMaxCoords > 10:
            return "similar"
            
        else:
            print "ERROR in compareBoundariesBetweenTestAndRefMatches()"
            predMatch.show()
            refMatch.show()
            sys.exit(1)
            
            
    def compareBoundariesBetweenPredAndRefTables( self ):
        """
        Compare the predicted and reference tables in terms of match boundaries.
        """
        dCase2Count = {}
        for case in self._lCases:
            dCase2Count[ case ] = 0
            
        lQueryNames = self._tpaPred.getQueryList()
        for queryName in lQueryNames:
            
            lPredMatches = self._tpaPred.getPathListSortedByQueryCoordFromQuery( queryName )
            for predMatch in lPredMatches:
                if self._verbose > 1:
                    print "predicted match: %s %i->%i" % ( queryName, predMatch.range_query.start, predMatch.range_query.end )
                    sys.stdout.flush()
                    
                lRefMatches = self._tpaRef.getPathListOverlappingQueryCoord( queryName, predMatch.range_query.start, predMatch.range_query.end )
                
                if len(lRefMatches) == 0:
                    case = "pred_1-to-0"
                    dCase2Count[ case ] += 1
                    if self._verbose > 1:
                        print "case '%s'" % ( case )
                    continue
                
                if len(lRefMatches) > 1:
                    case = "pred_1-to-n"
                    dCase2Count[ case ] += 1
                    if self._verbose > 1:
                        print "case '%s' (n=%i)" % ( case, len(lRefMatches) )
                    continue
                
                dCase2Count[ "pred_1-to-1" ] += 1
                for refMatch in lRefMatches:
                    if not( predMatch.range_query.getStrand() == refMatch.range_query.getStrand() \
                    and predMatch.range_subject.getStrand() == refMatch.range_subject.getStrand() ):
                        dCase2Count[ "different strand" ] += 1
                    case = self.compareBoundariesBetweenPredAndRefMatches( predMatch, refMatch )
                    dCase2Count[ case ] += 1
                    if self._verbose > 1:
                        print "case '%s' with %s %i->%i" % ( case, queryName, refMatch.range_query.start, refMatch.range_query.end )
                        
        return dCase2Count
    
    
    def getResultsAsString( self, dCase2Count, nbMatchesPredTable ):
        string = "results of boundary comparisons"
        
        case = "pred_1-to-1"
        string += "\ncase '%s':" % ( case )
        string += " %i" % ( dCase2Count[ case ] )
        string += " (%.2f%%)" % ( 100 * dCase2Count[ case ] / float(nbMatchesPredTable) )
        
        lCasesOneToOne = [ "exact", "near exact", "one-side exact", \
                          "equivalent", "near equivalent", \
                          "similar", "different strand" ]
        for case in lCasesOneToOne:
            string += "\ncase '%s':" % ( case )
            string += " %i" % ( dCase2Count[ case ] )
            string += " (%.2f%%)" % ( 100 * dCase2Count[ case ] / float(dCase2Count["pred_1-to-1"]) )
            
        for case in [ "pred_1-to-0", "pred_1-to-n" ]:
            string += "\ncase '%s':" % ( case )
            string += " %i" % ( dCase2Count[ case ] )
            string += " (%.2f%%)" % ( 100 * dCase2Count[ case ] / float(nbMatchesPredTable) )
            
        return string
    
    
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s.py" % ( self._name )
            sys.stdout.flush()
        logFileName = "%s_%s_vs_%s.log" % ( "CompareTwoPathTables", self._predData, self._refData )
        if os.path.exists( logFileName ):
            os.remove( logFileName )
        self._logger = LoggerFactory.createLogger( logFileName )
        self._logger.info( "started" )
        
        string = "input data"
        if self._typeData == "file":
            string += "\npredicted file: '%s'" % ( self._predData )
            string += "\nreference file: '%s'" % ( self._refData )
        elif self._typeData == "table":
            string += "\npredicted table: '%s'" % ( self._predData )
            string += "\nreference table: '%s'" % ( self._refData )
        self._logger.info( string )
        if self._verbose > 0:
            print string
            sys.stdout.flush()
        
        
    def end( self ):
        """
        Useful commands before ending the program.
        """
        self._db.close()
        self._logger.info( "finished" )
        if self._verbose > 0:
            print "END %s" % ( self._name )
            sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        self.setAdaptatorsToTablesFromInputData()
        
        tp, fp, tn, fn = self.getCounts()
        string = "counts"
        string += "\ntrue positives: %i" % ( tp )
        string += "\nfalse positives: %i" % ( fp )
        string += "\ntrue negatives: %i" % ( tn )
        string += "\nfalse negatives: %i" % ( fn )
        self._logger.info( string )
        if self._verbose > 0:
            print string
            sys.stdout.flush()
        sn, sp = self.getPerformanceMeasures( tp, fp, tn, fn )
        string = "performance measures"
        string += "\nsensitivity: %f" % ( sn )
        string += "\nspecificity: %f" % ( sp )
        self._logger.info( string )
        if self._verbose > 0:
            print string
            sys.stdout.flush()
        
        if self._compareBoundaries:
            string = "boundaries comparisons"
            
            if self._mergeData:
                mergePredTable = self.mergeMatchesInTable( self._tpaPred.getTable() )
                mergeRefTable = self.mergeMatchesInTable( self._tpaRef.getTable() )
                self._tpaPred.setTable(mergePredTable)
                self._tpaRef.setTable(mergeRefTable)
                nbMatchesPredTable = self._tpaPred.getSize()
                nbMatchesRefTable = self._tpaRef.getSize()
                string = "nb of merged matches"
                string += "\nin predicted table: %i" % ( nbMatchesPredTable )
                string += "\nin reference table: %i" % ( nbMatchesRefTable )
                self._logger.info( string )
                if self._verbose > 0:
                    print string
                    sys.stdout.flush()
            else:
                nbMatchesPredTable = self._tpaPred.getSize()
                
            dCase2Count = self.compareBoundariesBetweenPredAndRefTables()
            
            string = self.getResultsAsString( dCase2Count, nbMatchesPredTable )
            self._logger.info( string )
            if self._verbose > 0:
                print string
                sys.stdout.flush()
            if self._mergeData:
                self._db.dropTable( mergePredTable )
                self._db.dropTable( mergeRefTable )
                
        self.end()
        
        
if __name__ == "__main__":
    i = CompareTwoPathTables()
    i.setAttributesFromCmdLine()
    i.run()
