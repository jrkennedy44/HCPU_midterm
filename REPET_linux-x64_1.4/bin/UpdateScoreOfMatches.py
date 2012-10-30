#!/usr/bin/env python

import sys
import getopt
import os

from pyRepetUnit.commons.coord.AlignUtils import AlignUtils


class UpdateScoreOfMatches( object ):
    
    def __init__( self ):
        self._inputData = ""
        self._formatData = ""
        self._outputData = ""
        self._verbose = 0
        self._typeInData = "file"
        
        
    def help( self ):
        print
        print "usage: UpdateScoreOfMatches.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: input data (can be file or table)"
        print "     -f: format of the data (align/path)"
        print "     -o: output data (default=input+'.newScores')"
        print "     -v: verbosity level (default=0/1)"
        print "the new score is the length on the query times the percentage of identity"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt( sys.argv[1:], "hi:f:o:v:" )
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self._inputData = a
            elif o == "-f":
                self._formatData = a
            elif o == "-o":
                self._outputData = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        if self._inputData == "":
            msg = "ERROR: missing input data (-i)"
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
        if not os.path.exists( self._inputData ):
            msg = "ERROR: can't find input file '%s'" % ( self._inputData )
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
        if self._formatData == "":
            msg = "ERROR: need to precise format (-f)"
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
        if self._formatData not in [ "align", "path" ]:
            msg = "ERROR: format '%s' not yet supported" % ( self._formatData )
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
        if self._outputData == "":
            self._outputData = "%s.newScores" % ( self._inputData )
            
            
    def start( self ):
        if self._verbose > 0:
            print "START UpdateScoreOfMatches.py"
            sys.stdout.flush()
        self.checkAttributes()
        
        
    def end( self ):
        if self._verbose > 0:
            print "END UpdateScoreOfMatches.py"
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        
        if self._typeInData == "file":
            if self._formatData == "align":
                AlignUtils.updateScoresInFile( self._inputData,
                                               self._outputData )
            elif self._formatData == "path":
                pass
            
        self.end()
        
        
if __name__ == "__main__":
    i = UpdateScoreOfMatches()
    i.setAttributesFromCmdLine()
    i.run()
