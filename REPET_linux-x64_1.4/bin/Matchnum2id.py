#!/usr/bin/env python

##@file Adapt the input file which is the concatenation of several files
# usage: Matchnum2id.py [ options ]
# options:
#      -h: this help
#      -i: name of the input file (format=match)
#      -o: name of the output file (default=inFile+'.out')
#      -v: verbosity level (default=0/1)


import os
import sys
import getopt

from pyRepetUnit.commons.coord.Match import Match


class Matchnum2id( object ):
    
    def __init__( self ):
        """
        Constructor.
        """
        self._inFile = ""
        self._outFile = ""
        self._verbose = 0
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage: %s [ options ]" % ( sys.argv[0] )
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file (format=match)"
        print "     -o: name of the output file (default=inFile+'.out')"
        print "     -v: verbosity level (default=0/1)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:o:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self._inFile = a
            elif o == "-o":
                self._outFile = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._inFile == "":
            print "ERROR: missing input file"
            self.help(); sys.exit(1)
        if not os.path.exists( self._inFile ):
            print "ERROR: can't find file '%s'" % ( self._inFile )
            self.help(); sys.exit(1)
        if self._outFile == "":
            self._outFile = "%s.out" % ( self._inFile )
            
            
    def start( self ):
        """
        Useful commands before running the program.
        """
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ ); sys.stdout.flush()
        self.checkAttributes()
        if self._verbose > 0:
            print "input file: '%s'" % ( self._inFile )
            print "output file: '%s'" % ( self._outFile )
            sys.stdout.flush()
            
            
    def end( self ):
        """
        Useful commands before ending the program.
        """
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ ); sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        if os.path.exists( os.environ["REPET_PATH"] + "/bin/" + "tabnum2id" ):
            cmd = "tabnum2id"
            cmd += " -i %s" % ( self._inFile )
            cmd += " -o %s" % ( self._outFile )
            cmd += " -v 0"
            returnStatus = os.system( cmd )
            if returnStatus != 0:
                print "ERROR: 'tabnum2id returned '%i'" % ( returnStatus )
                sys.exit(1)
        else:
            inFileHandler = open( self._inFile, "r" )
            outFileHandler = open( self._outFile, "w" )
            outFileHandler.write( "query.name\tquery.start\tquery.end\tquery.length\tquery.length.%\tmatch.length.%\tsubject.name\tsubject.start\tsubject.end\tsubject.length\tsubject.length.%\tE.value\tScore\tIdentity\tpath\n" )
            m = Match()
            dID2count = {}
            count = 1
            while True:
                line = inFileHandler.readline()
                if line == "":
                    break
                if line[0:10] == "query.name":
                    continue
                tokens = line[:-1].split("\t")
                m.set_from_tuple( tokens )
                currentPath = str(m.id) + "_|_" + m.range_query.seqname + "_|_" + m.range_subject.seqname
                if currentPath not in dID2count.keys():
                    newPath = count
                    count += 1
                    dID2count[ currentPath ] = newPath
                else:
                    newPath = dID2count[ currentPath ]
                m.id = newPath
                outFileHandler.write( "%s\n" % ( m.toString() ) )
                m.reset()
            inFileHandler.close()
            outFileHandler.close()
            
        self.end()
        
        
if __name__ == "__main__":
    i = Matchnum2id()
    i.setAttributesFromCmdLine()
    i.run()
