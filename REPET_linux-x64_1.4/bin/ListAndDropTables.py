#!/usr/bin/env python

##@file
# List and drop MySQL tables.
#
# usage: ListAndDropTables.py [ options ]
# options:
#      -h: this help
#      -l: tables to list (can be a pattern, '*' for all)
#      -d: tables to drop (can be a pattern, '*' for all)
#      -C: configuration file
#      -v: verbose (default=0/1)
# it doesn't drop 'info_tables'


import sys
import getopt
from pyRepetUnit.commons.sql.DbMySql import DbMySql


class ListAndDropTables( object ):
    
    def __init__( self ):
        self._action = "list"
        self._tableNames = ""
        self._configFileName = ""
        self._verbose = 0
        self._db = None
        
        
    def help( self ):
        print
        print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
        print "options:"
        print "     -h: this help"
        print "     -l: tables to list (can be a pattern, '*' for all)"
        print "     -d: tables to drop (can be a pattern, '*' for all)"
        print "     -C: configuration file (otherwise, use env variables)"
        print "     -v: verbose (default=0/1)"
        print "Note: it doesn't drop 'info_tables'."
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hl:d:C:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-l":
                self._action = "list"
                self._tableNames = a
            elif o == "-d":
                self._action = "drop"
                self._tableNames = a
            elif o == "-C":
                self._configFileName = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        """
        Before running, check the required attributes are properly filled.
        """
        if self._tableNames == "":
            print "ERROR: missing input table"
            self.help()
            sys.exit(1)
#        if self._configFileName == "":
#            print "ERROR: missing configuration file"
#            self.help()
#            sys.exit(1)
            
            
    def getlistTables( self ):
        """
        Return a list with the table names corresponding to the given pattern.
        """
        lTables = []
        if self._tableNames != "*":
            sql_cmd = "SHOW TABLES like '%s%%'" % ( self._tableNames )
        else:
            sql_cmd = "SHOW TABLES"
        self._db.execute( sql_cmd )
        res = self._db.fetchall()
        for i in res:
            lTables.append( i[0] )
        return lTables
    
    
    def list( self ):
        """
        List the tables corresponding to the pattern.
        """
        lTables = i.getlistTables()
        if len(lTables) == 0:
            print "no table corresponding to '%s'" % ( self._tableNames )
        else:
            print "list of tables:"
            for t in lTables:
                print t
            print "%i tables corresponding to '%s'" % ( len(lTables), self._tableNames )
        sys.stdout.flush()
        
        
    def drop( self ):
        """
        Drop the tables corresponding to the pattern.
        """
        lTables = i.getlistTables()
        if len(lTables) == 0:
            print "no table corresponding to '%s'" % ( self._tableNames )
        else:
            print "deleting %i tables corresponding to '%s'" % ( len(lTables), self._tableNames )
            for t in lTables:
                if t != "info_tables":
                    self._db.dropTable( t )
        sys.stdout.flush()
        
        
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()
        if self._configFileName != "":
            self._db = DbMySql( cfgFileName = self._configFileName )
        else:
            if self._verbose > 0:
                print "WARNING: use environment variables to connect to MySQL"
                sys.stdout.flush()
            self._db = DbMySql()
            
            
    def end( self ):
        self._db.close()
        if self._verbose > 0:
            print "END %s" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        if i._action == "list":
            i.list()
        if i._action == "drop":
            i.drop()
        self.end()
        
        
if __name__ == "__main__":
    i = ListAndDropTables()
    i.setAttributesFromCmdLine()
    i.run()
