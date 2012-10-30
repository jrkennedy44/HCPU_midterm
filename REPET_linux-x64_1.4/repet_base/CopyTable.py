#! /usr/bin/env python

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


import os
import sys
import getopt
import ConfigParser
from pyRepetUnit.commons.sql.DbMySql import DbMySql


class CopyTable( object ):
    
    def __init__(self):
        self._inTable = ""
        self._outTable = ""
        self._configFile = ""
        self._host = ""
        self._user = ""
        self._passwd = ""
        self._dbname = ""
        self._verbose = 0
        
        
    def help(self):
        print
        print "usage: %s.py [ options ]" % self.__class__.__name__
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input table (that will be copied)"
        print "     -o: name of the output table (the new copy)"
        print "     -C: configuration file (to access MySQL)"
        print "     -H: MySQL host (if no configuration file)"
        print "     -U: MySQL user (if no configuration file)"
        print "     -P: MySQL password (if no configuration file)"
        print "     -D: MySQL database (if no configuration file)"
        print "     -v: verbosity level (default=0/1)"
        print
        
        
    def setAttributesFromCmdLine(self):
        try:
            opts, args = getopt.getopt( sys.argv[1:], "hi:o:C:H:U:P:D:v:" )
        except getopt.GetoptError, err:
            sys.stderr.write( "%s\n" % str(err) )
            self.help()
            sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help()
                sys.exit(0)
            elif o == "-i":
                self._inTable = a
            elif o == "-o":
                self._outTable = a
            elif o == "-C":
                self._configFile = a
            elif o == "-H":
                self._host = a
            elif o == "-U":
                self._user = a 
            elif o == "-P":
                self._passwd = a
            elif o == "-D":
                self._dbname = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes(self):
        if self._inTable == "":
            msg = "ERROR: missing input table (-i)"
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
            
        if self._configFile != "":
            config = ConfigParser.ConfigParser()
            config.readfp( open( self._configFile ) )
            self._host = config.get("repet_env","repet_host")
            self._user = config.get("repet_env","repet_user")
            self._passwd = config.get("repet_env","repet_pw")
            self._dbname = config.get("repet_env","repet_db")
            
        if self._host == "" and os.environ.get( "REPET_HOST" ) != "":
            self._host = os.environ.get( "REPET_HOST" )
        if self._user == "" and os.environ.get( "REPET_USER" ) != "":
            self._user = os.environ.get( "REPET_USER" )
        if self._passwd == "" and os.environ.get( "REPET_PW" ) != "":
            self._passwd = os.environ.get( "REPET_PW" )
        if self._dbname == "" and os.environ.get( "REPET_DB" ) != "":
            self._dbname = os.environ.get( "REPET_DB" )
            
        if self._host == "" or self._user == "" or self._passwd == "" or self._dbname == "":
            msg = "ERROR: missing information about MySQL connection"
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
            
            
    def run(self):
        self.checkAttributes()
        
        if self._verbose > 0:
            msg = "START %s.py" % self.__class__.__name__
            msg += "\ninput table: %s" % self._inTable
            msg += "\noutput table: %s" % self._outTable
            if self._configFile != "":
                msg += "\nconfiguration file: %s" % self._configFile
            sys.stdout.write( "%s\n" % msg )
            sys.stdout.flush()
            
        iDb = DbMySql( self._user, self._host, self._passwd, self._dbname )
        
        iDb.copyTable( self._inTable, self._outTable, self._verbose )
        
        iDb.close()
        
        if self._verbose > 0:
            msg = "END %s.py" % self.__class__.__name__
            sys.stdout.write( "%s\n" % msg )
            sys.stdout.flush()
            
            
if __name__ == "__main__":
    i = CopyTable()
    i.setAttributesFromCmdLine()
    i.run()
