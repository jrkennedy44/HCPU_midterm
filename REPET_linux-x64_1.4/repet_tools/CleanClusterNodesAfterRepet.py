#!/usr/bin/env python

## @file
# Clean the cluster nodes after REPET was used.
#
# usage: CleanClusterNodesAfterRepet.py [ options ]
# options:
#      -h: this help
#      -n: node to clean (otherwise all nodes will be cleaned)
#      -t: temporary directory (e.g. '/tmp')
#      -p: pattern (e.g. 'DmelChr4*')
#      -v: verbosity level (default=0/1/2)

import os
import sys
import getopt

class CleanClusterNodesAfterRepet( object ):
    """
    Clean the cluster nodes after REPET was used.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._lNodes = []
        self._tmpDir = ""
        self._pattern = ""
        self._verbose = 0

    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "usage: %s.py [ options ]" % ( type(self).__name__ )
        print "options:"
        print "     -h: this help"
        print "     -n: node to clean (otherwise all nodes will be cleaned)"
        print "     -t: temporary directory (e.g. '/tmp')"
        print "     -p: pattern (e.g. 'DmelChr4*')"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:n:t:p:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-n":
                self.setLNodes( a.split(" ") )
            elif o == "-t":
                self.setTempDirectory( a )
            elif o == "-p":
                self.setPattern( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
    def setLNodes( self, a ):
        self._lNodes = a
        
    def setTempDirectory( self, a ):
        if a[-1] == "/":
            self._tmpDir = a[:-1]
        else:
            self._tmpDir = a
            
    def setPattern( self, a ):
        self._pattern = a
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
    def checkAttributes( self ):
        """
        Before running, check the required attributes are properly filled.
        """
        if self._tmpDir == "":
            print "ERROR: need a valid temporary directory"
            self.help(); sys.exit(1)
            
    def getAllNodesList( self ):
        """
        Return the list of the names of each node.
        """
        lNodes = []
        log = os.system( "qhost > qhost.txt" )
        if log != 0: print "ERROR with qhost"; sys.exit(1)
        inF = open( "qhost.txt", "r" )
        line = inF.readline()
        line = inF.readline()
        line = inF.readline()
        while True:
            if line == "":
                break
            tokens = line.split()
            if tokens[3] == "-":
                line = inF.readline()
                continue
            lNodes.append( tokens[0] )
            line = inF.readline()
        return lNodes
    
    def showNodeList( self, lNodes ):
        print "nb of nodes: %i" % ( len(lNodes) )
        for i in range(0,len(lNodes)):
            print " %i: %s" % ( i+1, lNodes[i] )
            
    def cleanNodes( self):
        """
        Connect to each job and clean the temporary directory.
        """
        nbNodes = len(self._lNodes)
        nodeCount = 0
        for node in self._lNodes:
            nodeCount += 1
            if self._verbose > 0:
                print "connect to node '%s' (%i/%i)..." % ( node, nodeCount, nbNodes )
                sys.stdout.flush()
            cmd = "ssh"
            cmd += " -q %s " % ( node )
            cmd += "'find %s" % ( self._tmpDir )
            cmd += " -user %s" % ( os.environ["USER"] )
            if self._pattern != "":
                cmd += " -name '%s'" % ( self._pattern )
            cmd += " 2> /dev/null -exec rm -rf {} \; ; exit'"
            if self._verbose > 0: print cmd; sys.stdout.flush()
            os.system( cmd )  # warning, even if everything goes right, ssh returns an error code, i.e. different than 0
    
    def clean( self ):
        if os.path.exists( "qhost.txt" ):
            os.remove( "qhost.txt" )
            
    def start( self ):
        """
        Useful commands before running the program.
        """
        if self._verbose > 0:
            print "START %s" % ( type(self).__name__ ); sys.stdout.flush()
        self.checkAttributes()        
        
    def end( self ):
        """
        Useful commands before ending the program.
        """
        self.clean()
        if self._verbose > 0:
            print "END %s" % ( type(self).__name__ ); sys.stdout.flush()
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        if self._lNodes == []:
            self._lNodes = self.getAllNodesList()
        if self._verbose > 0: self.showNodeList( self._lNodes )
        self.cleanNodes()
        self.end()

if __name__ == "__main__":
    i = CleanClusterNodesAfterRepet()
    i.setAttributesFromCmdLine()
    i.run()
