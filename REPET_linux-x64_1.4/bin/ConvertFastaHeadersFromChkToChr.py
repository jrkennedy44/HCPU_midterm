#!/usr/bin/env python

## @file
# usage: ConvertFastaHeadersFromChkToChr.py [ options ]

import sys
import os
import getopt
import glob
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils


class ConvertFastaHeadersFromChkToChr( object ):
    
    def __init__( self ):
        self._inData = ""
        self._mapFile = ""
        self._outFile = ""
        self._verbose = 0
        
        
    def help( self ):
        print
        print "usage: ConvertFastaHeadersFromChkToChr.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: input data (format='fasta')"
        print "         can be a single fasta file"
        print "         if directory, give a pattern (e.g. '/tmp/*.fa')"
        print "     -m: name of the map file (format='map')"
        print "     -o: name of the output file (format='fasta', default=inFile+'.onChr')"
        print "         if input directory, default is compulsory"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt( sys.argv[1:], "hi:m:o:v:" )
        except getopt.GetoptError, err:
            msg = str(err)
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self._inData = a
            elif o == "-m":
                self._mapFile = a
            elif o == "-o":
                self._outFile = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        if self._inData == "":
            msg = "ERROR: missing input data (-i)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if self._mapFile == "":
            msg = "ERROR: missing map file (-m)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if not os.path.exists( self._mapFile ):
            msg = "ERROR: can't find map file '%s'" % ( self._mapFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help()
            sys.exit(1)
        if self._outFile == "" and os.path.isfile( self._inData ):
            self._outFile = "%s.onChr" % ( self._inData )
            
            
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            msg = "START ConvertFastaHeadersFromChkToChr.py"
            msg += "\ninput data: %s" % ( self._inData )
            msg += "\nmap file: %s" % ( self._mapFile )
            if os.path.isfile( self._inData ):
                msg += "\noutput file: %s" % ( self._outFile )
            sys.stdout.write( "%s\n" % ( msg ) )
            sys.stdout.flush()
            
    def end( self ):
        if self._verbose > 0:
            msg = "END ConvertFastaHeadersFromChkToChr.py"
            sys.stdout.write( "%s\n" % ( msg ) )
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        
        if os.path.isfile( self._inData ):
            FastaUtils.convertFastaHeadersFromChkToChr( self._inData, self._mapFile, self._outFile )
            
        else:
            lInFiles = glob.glob( self._inData )
            if len(lInFiles) == 0:
                msg = "WARNING: no file corresponds to pattern '%'" % ( self._inData )
                sys.stdout.write( "%s\n" % ( msg ) )
                self.end()
            for inFile in lInFiles:
                outFile = "%s.onChr" % ( inFile )
                FastaUtils.convertFastaHeadersFromChkToChr( inFile, self._mapFile, outFile )
                
        self.end()
                
                
if __name__ == "__main__":
    i = ConvertFastaHeadersFromChkToChr()
    i.setAttributesFromCmdLine()
    i.run()
