#!/usr/bin/env python

##@file
# usage: getCumulLengthFromTEannot.py [ options ]
# options:
#      -h: this help
#      -i: table with the annotations (format=path)
#      -r: name of a TE reference sequence (if empty, all subjects are considered)
#      -g: length of the genome (in bp)
#      -C: configuration file
#      -c: clean
#      -v: verbosity level (default=0/1)


import sys
import os
import getopt
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator


class getCumulLengthFromTEannot( object ):
    """
    Give the cumulative length of TE annotations (subjects mapped on queries).
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._tableName = ""
        self._TErefseq = ""
        self._genomeLength = 0
        self._configFileName = ""
        self._clean = False
        self._verbose = 0
        self._db = None
        self._tpA = None
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage: getCumulLengthFromTEannot.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: table with the annotations (format=path)"
        print "     -r: name of a TE reference sequence (if empty, all subjects are considered)"
        print "     -g: length of the genome (in bp)"
        print "     -C: configuration file"
        print "     -c: clean"
        print "     -v: verbosity level (default=0/1)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:r:g:C:cv:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputTable( a )
            elif o == "-r":
                self.setTErefseq( a )
            elif o == "-g":
                self.setGenomeLength( a )
            elif o == "-C":
                self.setConfigFileName( a )
            elif o == "-c":
                self.setClean()
            elif o == "-v":
                self.setVerbosityLevel( a )
                
                
    def setInputTable( self, inTable ):
        self._tableName = inTable
        
    def setTErefseq( self, a ):
        self._TErefseq = a
        
    def setGenomeLength( self, genomeLength ):
        self._genomeLength = int(genomeLength)
        
    def setConfigFileName( self, configFileName ):
        self._configFileName = configFileName
        
    def setClean( self ):
        self._clean = True
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._tableName == "":
            print "ERROR: missing input table"; self.help(); sys.exit(1)
            
            
    def setAdaptatorToTable( self ):
        self._db = DbMySql( cfgFileName=self._configFileName )
        self._tpA = TablePathAdaptator( self._db, self._tableName )
        
        
    def getAllSubjectsAsMapOfQueries( self ):
        mapFileName = "%s.map" % self._tableName
        mapFile = open( mapFileName, "w" )
        if self._TErefseq != "":
            lPathnums = self._tpA.getIdListFromSubject( self._TErefseq )
        else:
            lPathnums = self._tpA.getIdList()
        if self._verbose > 0:
            print "nb of paths: %i" % ( len(lPathnums) )
        for pathnum in lPathnums:
            lPaths = self._tpA.getPathListFromId( pathnum )
            for path in lPaths:
                map = path.getSubjectAsMapOfQuery()
                map.write( mapFile )
        mapFile.close()
        return mapFileName
    
    
    def mergeRanges( self, mapFileName ):
        mergeFileName = "%s.merge" % mapFileName
        prg = os.environ["REPET_PATH"] + "/bin/mapOp"
        cmd = prg
        cmd += " -q %s" % ( mapFileName )
        cmd += " -m"
        cmd += " 2>&1 > /dev/null"
        log = os.system( cmd )
        if log != 0:
            print "*** Error: %s returned %i" % ( prg, log )
            sys.exit(1)
        if self._clean:
            os.remove( mapFileName )
        return mergeFileName
    
    
    def getCumulLength( self, mergeFileName ):
        mergeFile = open( mergeFileName, "r" )
        total = 0
        while True:
            line = mergeFile.readline()
            if line == "":
                break
            tok = line.split("\t")
            total += abs( int(tok[3]) - int(tok[2]) ) + 1
        mergeFile.close()
        if self._clean:
            os.remove( mergeFileName )
        return total
    
    
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ ); sys.stdout.flush()
        self.setAdaptatorToTable()
        
        
    def end( self, mapFileName, mergeFileName ):
        """
        Useful commands before ending the program.
        """
        self._db.close()
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ ); sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        mapFileName = self.getAllSubjectsAsMapOfQueries()
        mergeFileName = self.mergeRanges( mapFileName )
        total = self.getCumulLength( mergeFileName )
        print "cumulative length: %i bp" % total
        if self._genomeLength > 0:
            print "TE content: %.2f%%" % ( 100 * total / float(self._genomeLength) )
            
        self.end( mapFileName, mergeFileName )
        
        
if __name__ == "__main__":
    i = getCumulLengthFromTEannot()
    i.setAttributesFromCmdLine()
    i.run()
