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
import time
import ConfigParser
import MySQLdb
from pyRepetUnit.commons.seq.Bioseq import Bioseq
from pyRepetUnit.commons.sql.RepetDB import RepetDB


## Handle connections to MySQL tables formatted for REPET
#
class DbMySql( RepetDB ):

    ## Constructor
    #
    # @param user string db user name
    # @param host string db host name
    # @param passwd string db user password
    # @param dbname string database name
    # @param port integer database port
    # @param cfgFileName string configuration file name
    #
    # @note when a parameter is left blank, the constructor is able
    #   to set attribute values from environment variables: REPET_HOST,
    #   REPET_USER, REPET_PW, REPET_DB, REPET_PORT
    #
    def __init__(self, user = "", host = "", passwd = "", dbname = "", port = 3306, cfgFileName = ""):
        self.port = int(port)

        if cfgFileName != "":
            self.setAttributesFromConfigFile(cfgFileName)
            
        elif host != "" and user != "" and passwd != "" and dbname != "":
            self.host = host
            self.user = user
            self.passwd = passwd
            self.dbname = dbname
            
        else:
            for envVar in ["REPET_HOST","REPET_USER","REPET_PW","REPET_DB"]:
                if os.environ.get( envVar ) == None:
                    msg = "ERROR: can't find environment variable '%s'" % ( envVar )
                    sys.stderr.write( "%s\n" % msg )
                    sys.exit(1)
            self.host = os.environ.get("REPET_HOST")
            self.user = os.environ.get("REPET_USER")
            self.passwd = os.environ.get("REPET_PW")
            self.dbname = os.environ.get("REPET_DB")
        if os.environ.get("REPET_PORT") != None:
            self.port = int( os.environ.get("REPET_PORT") )
            
        maxNbTry = 10
        for i in xrange(1,maxNbTry+1):
            if not self.open():
                time.sleep(2)
                if i == maxNbTry:
                    print "ERROR: failed to connect to the MySQL database"
                    sys.exit(1)
            else:
                break
            
        self.cursor = self.db.cursor()
        self.execute("""use %s""" %(self.dbname))
        
        
    ## Set the attributes from the configuration file
    #
    # @param configFileName string configuration file name
    #
    def setAttributesFromConfigFile(self, configFileName):
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        self.host = config.get("repet_env","repet_host")
        self.user = config.get("repet_env","repet_user")
        self.passwd = config.get("repet_env","repet_pw")
        self.dbname = config.get("repet_env","repet_db")
        self.port = int( config.get("repet_env","repet_port") )
        
        
    ## Connect to the MySQL database
    #
    # @param verbose integer (default = 0)
    #
    def open( self, verbose = 0 ):
        try:
            if int(MySQLdb.get_client_info().split(".")[0]) >= 5:
                self.db = MySQLdb.connect( user = self.user, host = self.host,\
                                           passwd = self.passwd, db = self.dbname, \
                                           port = self.port, \
                                           local_infile = 1 )
            else:
                self.db = MySQLdb.connect( user = self.user, host = self.host,\
                                           passwd = self.passwd, db = self.dbname, \
                                           port = self.port )
        except MySQLdb.Error, e:
            if verbose > 0:
                print "*** Error %d: %s" % (e.args[0], e.args[1]); sys.stdout.flush()
            return False

        return True
    
    
    ## Execute a SQL query
    #
    # @param qry string SQL query to execute
    # @param params parameters of SQL query 
    #
    def execute( self, qry, params=None ):
        RepetDB.execute(self, qry, params)
        
        
    ## Close the connection
    #
    def close( self ):
        self.db.close()
        
        
    ## Retrieve the results of a SQL query
    #
    def fetchall(self):
        return self.cursor.fetchall()
    
    
    ## Test if a table exists
    #
    # @param table string table name
    # @return boolean True if the table exists, False otherwise
    #
    def doesTableExist( self, table ):
        self.execute( """SHOW TABLES""" )
        results = self.cursor.fetchall()
        if (table,) in results:
            return True
        return False
    
    
    ## Remove a table if it exists
    #
    # @param table string table name
    # @param verbose integer (default = 0)
    #
    def dropTable( self, table, verbose = 0 ):
        if self.doesTableExist( table ):
            sqlCmd = "DROP TABLE %s" % ( table )
            self.execute( sqlCmd )
            sqlCmd = 'DELETE FROM info_tables WHERE name = "%s"' % ( table )
            self.execute( sqlCmd )
            
            
    ## Rename a table
    #
    # @param table string existing table name
    # @param newName string new table name
    #
    def renameTable( self, table, newName ):
        self.dropTable( newName )
        self.execute( 'RENAME TABLE %s TO %s ;' % (table, newName) )
        self.execute( 'UPDATE info_tables SET name="%s" WHERE name="%s";' % (newName, table) )
        
        
    ## Duplicate a table
    #
    # @param tableName string source table name
    # @param newTableName string new table name
    # @param verbose integer (default = 0)
    #
    def copyTable( self, tableName, newTableName, verbose = 0 ):
        self.dropTable( newTableName )
        sqlCmd = 'CREATE TABLE %s SELECT * FROM %s;' % (newTableName, tableName)
        if verbose > 0:
            print "copying table data,", tableName, "in", newTableName
        self.execute( sqlCmd )
        self.updateInfoTable( newTableName, "" )
        
        
    ## Give the rows number of the table
    #
    # @param tableName string table name
    #
    def getSize( self, tableName ):
        qry = "SELECT count(*) FROM %s;" % ( tableName )
        self.execute( qry )
        res = self.fetchall()
        return int( res[0][0] )
    
    
    ## Test if table is empty
    #
    # @param tableName string table name
    # @return boolean True if the table is empty, False otherwise
    #
    def isEmpty( self, tableName ):
        return self.getSize( tableName ) == 0
    
    
    ## Record a new table in the 'info_table' table
    #
    # @param tableName string table name
    # @param info string information on the table origin
    #
    def updateInfoTable( self, tableName, info ):
        if not self.doesTableExist( "info_tables" ):
            sqlCmd = "CREATE TABLE info_tables ( name varchar(255), file varchar(255) )"
            self.execute( sqlCmd )
        sqlCmd = 'INSERT INTO info_tables VALUES ("%s","%s")' % (tableName, info)
        self.execute( sqlCmd )
        
        
    ## Get a list with the fields
    #
    def getFieldList( self, table ):
        lFields = []
        sqlCmd = "DESCRIBE %s" % ( table )
        self.execute( sqlCmd )
        lResults = self.fetchall()
        for res in lResults:
            lFields.append( res[0] )
        return lFields
    
    
    ## Check that the input file has as many fields than it is supposed to according to its format
    #
    # @note fields should be separated by tab
    #
    def checkDataFormatting( self, dataType, fileName ):
        dataType = dataType.lower()
        if dataType in [ "fa", "fasta", "seq", "teclassif" ]:
            return
        dDataType2NbFields = { "map": 4, "set": 5, "align": 9, "path": 10, "match": 15, "tab": 15 }
        fileHandler = open( fileName, "r" )
        line = fileHandler.readline()
        if line != "":
            tokens = line.split("\t")
            if len(tokens) < dDataType2NbFields[ dataType ]:
                msg = "ERROR: '%s' file has less than %i fields" % ( dataType, dDataType2NbFields[ dataType ] )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
            if len(tokens) > dDataType2NbFields[ dataType ]:
                msg = "ERROR: '%s' file has more than %i fields" % ( dataType, dDataType2NbFields[ dataType ] )
                sys.stderr.write( "%s\n" % msg )
                sys.exit(1)
        fileHandler.close()
        
        
    ## Create a MySQL table of specified data type and load data
    #
    # @param tableName string name of the table to be created
    # @param fileName string name of the file containing the data to be loaded in the table
    # @param dataType string type of the data (map, set, align, path, match)
    # @param overwrite boolean (default = False)
    # @param verbose integer (default = 0)
    #
    def createTable( self, tableName, dataType, fileName="", overwrite=False, verbose=0 ):
        if verbose > 0:
            print "creating table '%s' from file '%s' of type '%s'..." % ( tableName, fileName, dataType )
            sys.stdout.flush()
            
        if fileName != "":
            self.checkDataFormatting( dataType, fileName )
            
        if overwrite:
            self.dropTable( tableName )
            
        if dataType == "map" or dataType == "Map":
            self.createMapTable( tableName, fileName )

        elif dataType == "set" or dataType == "Set":
            self.createSetTable( tableName, fileName )

        elif dataType == "tab" or dataType == "match" or dataType == "Match":
            self.createMatchTable( tableName, fileName )

        elif dataType == "path" or dataType == "Path":
            self.createPathTable( tableName, fileName )

        elif dataType == "align" or dataType == "Align":
            self.createAlignTable( tableName, fileName )

        elif dataType == "fa" or dataType == "fasta" or dataType == "Fasta" or dataType == "seq":
            self.createSeqTable( tableName, fileName )

        else:
            print "ERROR: unknown type %s" % ( dataType )
            self.close()
            sys.exit(1)

        if verbose > 0:
            print "done!"; sys.stdout.flush()
            
            
    ## Load data from a file into a MySQL table
    #
    # @param tableName string table name
    # @param fileName string file name
    # @param escapeFirstLine boolean True to ignore the first line of file, False otherwise 
    # @param verbose integer (default = 0)
    #
    def loadDataFromFile( self, tableName, fileName, escapeFirstLine = False, verbose = 0 ):
        if fileName != "":
            if escapeFirstLine == False:
                sqlCmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' " % ( fileName, tableName )
            else:
                sqlCmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' IGNORE 1 LINES" % ( fileName, tableName )
            self.execute( sqlCmd )

        if verbose > 0:
            print "nb of entries in the table = %i" % ( self.getSize( tableName ) )
            sys.stdout.flush()
            
            
    ## Create index for a map table
    #
    # @param tableName string table name
    # @param verbose integer (default = 0)
    #
    def createMapIndex( self, tableName, verbose = 0 ) :
        sqlCmd = "SHOW INDEX FROM %s;"% (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "iname" not in lIndex:
            sqlCmd = "CREATE INDEX iname ON %s ( name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "ichr" not in lIndex:   
            sqlCmd = "CREATE INDEX ichr ON %s ( chr(10) );" % (tableName)
            self.execute(sqlCmd)
        if "istart" not in lIndex:
            sqlCmd = "CREATE INDEX istart ON %s ( start );" % (tableName)
            self.execute(sqlCmd)
        if "istart" not in lIndex:
            sqlCmd = "CREATE INDEX iend ON %s ( end );" % (tableName)
            self.execute(sqlCmd)
        if "icoord" not in lIndex:
            sqlCmd = "CREATE INDEX icoord ON %s ( start,end );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a map table and load the data
    #
    # @param tableName string new table name
    # @param fileName string data file name containing the data to be loaded in the table
    #
    def createMapTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s (name varchar(255), chr varchar(255), start int, end int)" % (tableName)
        self.execute(sqlCmd)
        self.createMapIndex(tableName)
        self.loadDataFromFile( tableName, fileName )
        self.updateInfoTable(tableName, fileName)
        
        
    ## Create index for a match table
    #
    # @param tableName string table name
    # @param verbose integer (default = 0)
    #
    def createMatchIndex( self, tableName, verbose = 0 ):
        sqlCmd = "SHOW INDEX FROM %s;" % (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "id" not in lIndex:
            sqlCmd = "CREATE UNIQUE INDEX id ON %s ( path );" % (tableName)
            self.execute(sqlCmd)
        if "qname" not in lIndex:        
            sqlCmd = "CREATE INDEX qname ON %s ( query_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "qstart" not in lIndex:
            sqlCmd = "CREATE INDEX qstart ON %s ( query_start );" % (tableName)
            self.execute(sqlCmd)
        if "qend" not in lIndex:
            sqlCmd = "CREATE INDEX qend ON %s ( query_end );" % (tableName)
            self.execute(sqlCmd)
        if "sname" not in lIndex:
            sqlCmd = "CREATE INDEX sname ON %s ( subject_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "sstart" not in lIndex:
            sqlCmd = "CREATE INDEX sstart ON %s ( subject_start );" % (tableName)
            self.execute(sqlCmd)
        if "send" not in lIndex:
            sqlCmd = "CREATE INDEX send ON %s ( subject_end );" % (tableName)
            self.execute(sqlCmd)
        if "qcoord" not in lIndex:
            sqlCmd = "CREATE INDEX qcoord ON %s ( query_start,query_end );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a match table and load the data
    #
    # @param tableName string new table name
    # @param fileName string data file name containing the data to be loaded in the table
    #
    def createMatchTable( self, tableName, fileName = "" ):
        sqlCmd="CREATE TABLE %s (query_name varchar(255), query_start int, query_end int, query_length int unsigned, query_length_perc float, match_length_perc float, subject_name varchar(255), subject_start int unsigned, subject_end int unsigned, subject_length int unsigned, subject_length_perc float, E_value double, score int unsigned, identity float, path int unsigned)" % (tableName)
        self.execute( sqlCmd )
        self.createMatchIndex( tableName )
        self.loadDataFromFile( tableName, fileName, True )
        self.updateInfoTable( tableName, fileName )
        
        
    ## Create index for a path table
    #
    # @param tableName string table name
    # @param verbose integer (default = 0)
    #
    def createPathIndex( self, tableName, verbose = 0 ):
        sqlCmd = "SHOW INDEX FROM %s;" % (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "id" not in lIndex:
            sqlCmd = "CREATE INDEX id ON %s ( path );" % (tableName)
            self.execute(sqlCmd)
        if "qname" not in lIndex:        
            sqlCmd = "CREATE INDEX qname ON %s ( query_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "qstart" not in lIndex:
            sqlCmd = "CREATE INDEX qstart ON %s ( query_start );" % (tableName)
            self.execute(sqlCmd)
        if "qend" not in lIndex:
            sqlCmd = "CREATE INDEX qend ON %s ( query_end );" % (tableName)
            self.execute(sqlCmd)
        if "sname" not in lIndex:
            sqlCmd = "CREATE INDEX sname ON %s ( subject_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "sstart" not in lIndex:
            sqlCmd = "CREATE INDEX sstart ON %s ( subject_start );" % (tableName)
            self.execute(sqlCmd)
        if "send" not in lIndex:
            sqlCmd = "CREATE INDEX send ON %s ( subject_end );" % (tableName)
            self.execute(sqlCmd)
        if "qcoord" not in lIndex:
            sqlCmd = "CREATE INDEX qcoord ON %s ( query_start,query_end );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a path table and load the data
    #
    # @param tableName string name of the new table
    # @param fileName string name of the file containing the data to be loaded in the table
    #
    # @note the data are updated such that query coordinates are always direct (start<end)
    #
    def createPathTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s (path int unsigned, query_name varchar(255), query_start int , query_end int, subject_name varchar(255), subject_start int unsigned, subject_end int unsigned, E_value double, score int unsigned, identity float)" % ( tableName )
        self.execute( sqlCmd )
        self.createPathIndex( tableName )
        self.loadDataFromFile( tableName, fileName )
        self.changePathQueryCoordinatesToDirectStrand( tableName )
        self.updateInfoTable( tableName, fileName )
            
            
    ## Create a stat table for TEannot results and load the data from a path file
    #
    # @param tableName string name of the new table
    # @param fileName string name of the file containing the data to be loaded in the table
    #
    # @note Identity, length and percentage of length are "varchar" because of "NA" value
    #
    #TODO: Change varchar to float ? need index ?
    def createPathStatTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s" % tableName
        sqlCmd += " (family varchar(255), maxLength int, meanLength int, covg int"
        sqlCmd += ", frags int, fullLgthFrags int, copies int, fullLgthCopies int"
        sqlCmd += ", meanId varchar(255), sdId varchar(255), minId varchar(255), q25Id varchar(255), medId varchar(255), q75Id varchar(255), maxId varchar(255)"
        sqlCmd += ", meanLgth varchar(255), sdLgth varchar(255), minLgth varchar(255), q25Lgth varchar(255), medLgth varchar(255), q75Lgth varchar(255), maxLgth varchar(255)"
        sqlCmd += ", meanLgthPerc varchar(255), sdLgthPerc varchar(255), minLgthPerc varchar(255), q25LgthPerc varchar(255), medLgthPerc varchar(255), q75LgthPerc varchar(255), maxLgthPerc varchar(255))"
        self.execute( sqlCmd )
        self.loadDataFromFile( tableName, fileName, True )
        self.updateInfoTable( tableName, fileName )
        
        
    ## Create index for a align table
    #
    # @param tableName string table name
    # @param verbose integer ( default = 0 )
    #
    def createAlignIndex( self, tableName, verbose = 0 ):
        sqlCmd = "SHOW INDEX FROM %s;" % (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "qname" not in lIndex:        
            sqlCmd = "CREATE INDEX qname ON %s ( query_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "qstart" not in lIndex:
            sqlCmd = "CREATE INDEX qstart ON %s ( query_start );" % (tableName)
            self.execute(sqlCmd)
        if "qend" not in lIndex:
            sqlCmd = "CREATE INDEX qend ON %s ( query_end );" % (tableName)
            self.execute(sqlCmd)
        if "sname" not in lIndex:
            sqlCmd = "CREATE INDEX sname ON %s ( subject_name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "sstart" not in lIndex:
            sqlCmd = "CREATE INDEX sstart ON %s ( subject_start );" % (tableName)
            self.execute(sqlCmd)
        if "send" not in lIndex:
            sqlCmd = "CREATE INDEX send ON %s ( subject_end );" % (tableName)
            self.execute(sqlCmd)
        if "qcoord" not in lIndex:
            sqlCmd = "CREATE INDEX qcoord ON %s ( query_start,query_end );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a align table and load data
    #
    # @param tableName string new table name
    # @param fileName string data file name containing the data to be loaded in the table
    #
    def createAlignTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s (query_name varchar(255), query_start int, query_end int,subject_name varchar(255), subject_start int unsigned, subject_end int unsigned,E_value double, score int unsigned, identity float)" % (tableName)
        self.execute(sqlCmd)
        self.createAlignIndex(tableName)
        self.loadDataFromFile( tableName, fileName )
        self.updateInfoTable(tableName,fileName)
        
        
    ## Create index for set table  
    #  
    # @param tableName string table name
    # @param verbose integer (default = 0)
    #
    def createSetIndex( self, tableName, verbose = 0 ):       
        sqlCmd = "SHOW INDEX FROM %s;" % (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "id" not in lIndex:
            sqlCmd = "CREATE INDEX id ON %s ( path );" % (tableName)
            self.execute(sqlCmd)
        if "iname" not in lIndex:
            sqlCmd = "CREATE INDEX iname ON %s ( name(10) );" % (tableName)
            self.execute(sqlCmd)
        if "ichr" not in lIndex:   
            sqlCmd = "CREATE INDEX ichr ON %s ( chr(10) );" % (tableName)
            self.execute(sqlCmd)
        if "istart" not in lIndex:
            sqlCmd = "CREATE INDEX istart ON %s ( start );" % (tableName)
            self.execute(sqlCmd)
        if "istart" not in lIndex:
            sqlCmd = "CREATE INDEX iend ON %s ( end );" % (tableName)
            self.execute(sqlCmd)
        if "icoord" not in lIndex:
            sqlCmd = "CREATE INDEX icoord ON %s ( start,end );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a set table and load data
    #
    # @param tableName string new table name
    # @param fileName string data file name containing the data to be loaded in the table
    #
    def createSetTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s (path int unsigned, name varchar(255), chr varchar(255), start int, end int);" % (tableName)
        self.execute(sqlCmd)
        self.createSetIndex(tableName)
        self.loadDataFromFile( tableName, fileName )
        self.updateInfoTable( tableName, fileName )
        
        
    ## Create index for a seq table
    #
    # @param tableName string table name
    # @param verbose integer (default = 0)
    #
    def createSeqIndex( self, tableName, verbose = 0 ):
        sqlCmd = "SHOW INDEX FROM %s;" % (tableName)
        self.execute(sqlCmd)
        res = self.fetchall()
        lIndex = []
        for i in res:
            lIndex.append(i[2])
        if verbose > 0:
            print "existing index:", lIndex
        if "iacc" not in lIndex:
            sqlCmd = "CREATE UNIQUE INDEX iacc ON %s ( accession );" % (tableName)
            self.execute(sqlCmd)
        if "idescr" not in lIndex:
            sqlCmd = "CREATE INDEX idescr ON %s ( description(10) );" % (tableName)
            self.execute(sqlCmd)
            
            
    ## Create a seq table and load data
    #
    # @param tableName: new table name
    # @param fileName: data file name containing the data to be loaded in the table
    #  
    def createSeqTable( self, tableName, fileName = "" ):
        sqlCmd = "CREATE TABLE %s (accession varchar(255), sequence longtext, description varchar(255), length int unsigned )" % (tableName)
        self.execute( sqlCmd )
        self.createSeqIndex( tableName )
        self.updateInfoTable( tableName, fileName )
        
        if fileName != "":
            inFile = open( fileName )
            tmpFileName = fileName.split("/")[-1] + ".tmp" + str(os.getpid())
            tmpFile = open(tmpFileName, "w")
            bioseq = Bioseq()
            seqNb = 0
            while True:
                bioseq.read( inFile )
                if bioseq.sequence == None:
                    break
                seqLen = bioseq.getLength()
                tmpFile.write("%s\t%s\t%s\t%d\n" % (bioseq.header.split()[0], \
                                                bioseq.sequence, bioseq.header, seqLen))
                seqNb += 1
            inFile.close()
            tmpFile.close()
            sqlCmd = "LOAD DATA LOCAL INFILE '%s' IGNORE INTO TABLE %s FIELDS ESCAPED BY ''" % \
                     (tmpFileName, tableName)
            self.execute( sqlCmd )
            os.remove( tmpFileName )
            
            
    ## Change the coordinates such that the query is on the direct strand.
    #
    # @param inTable string path table name to update
    #    
    def changePathQueryCoordinatesToDirectStrand( self, inTable ):
        sqlCmd = "ALTER TABLE %s ADD COLUMN tmpid INT NOT NULL AUTO_INCREMENT PRIMARY KEY" % ( inTable )
        self.execute( sqlCmd )
        
        tmpTable = "%s_tmp" % ( inTable )
        sqlCmd = "CREATE TABLE %s SELECT * FROM %s WHERE query_start > query_end" % ( tmpTable, inTable )
        self.execute( sqlCmd )
        
        sqlCmd = "UPDATE %s, %s" % ( inTable, tmpTable )
        sqlCmd += " SET %s.query_start=%s.query_end," % ( inTable, tmpTable )
        sqlCmd += " %s.query_end=%s.query_start," % ( inTable, tmpTable )
        sqlCmd += " %s.subject_start=%s.subject_end," % ( inTable, tmpTable )
        sqlCmd += " %s.subject_end=%s.subject_start" % ( inTable, tmpTable )
        sqlCmd += " WHERE %s.tmpid=%s.tmpid" % ( inTable, tmpTable )
        self.execute( sqlCmd )
        
        sqlCmd = "ALTER TABLE %s DROP COLUMN tmpid" % ( inTable )
        self.execute( sqlCmd )
        self.dropTable( tmpTable )
        
        
    ## Export data from a table in a file.
    #
    # @param tableName string table name 
    # @param outFileName string output file name
    # @param keepFirstLine boolean if you want the first line (column name) in output file
    # @param param string sql parameters to select data expected 
    #
    def exportDataToFile( self, tableName, outFileName="", keepFirstLine=False, param="" ):
        if outFileName == "": outFileName = tableName
        prg = "mysql"
        cmd = prg
        cmd += " -h %s" % ( self.host )
        cmd += " -u %s" % ( self.user )
        cmd += " -p\"%s\"" % ( self.passwd )
        cmd += " --database=%s" % ( self.dbname )
        cmd += " -e\"SELECT * FROM %s" % ( tableName )
        if param != "": cmd += " %s" % ( param )
        cmd += ";\""
        cmd += " > "
        if keepFirstLine == False:
            cmd += "%s.tmp" % ( outFileName )
        else:
            cmd += "%s" % ( outFileName )
        log = os.system( cmd )
        if log != 0: print "ERROR: mysql returned %i" % ( log ); sys.exit(1)
    
        if keepFirstLine == False:
            tmpFileName = "%s.tmp" % ( outFileName )
            tmpFile = open( tmpFileName, "r" )
            outFile = open( outFileName, "w" )
            i = 0
            for line in tmpFile:
                if i > 0:
                    outFile.write( line )
                i += 1
            tmpFile.close()
            outFile.close()
            os.remove( tmpFileName )
            
            
    ## Convert a Path table into an Align table
    #
    # @param inPathTable string name of the input Path table
    # @param outAlignTable string name of the output Align table
    #
    def convertPathTableIntoAlignTable( self, inPathTable, outAlignTable ):
        sqlCmd = "CREATE TABLE %s SELECT query_name,query_start,query_end,subject_name,subject_start,subject_end,E_value,score,identity FROM %s;" % ( outAlignTable, inPathTable )
        self.execute( sqlCmd )
        self.updateInfoTable( outAlignTable, "" )
        
        
    ## Convert an Align table into a Path table
    #
    # @param inAlignTable string name of the input Align table
    # @param outPathTable string name of the output Path table
    #
    def convertAlignTableIntoPathTable( self, inAlignTable, outPathTable ):
        self.createTable( outPathTable, "path", "", True )
        sqlCmd = "SELECT * FROM %s" % ( inAlignTable )
        self.execute( sqlCmd )
        lResults = self.fetchall()
        rowIndex = 0
        for res in lResults:
            rowIndex += 1
            sqlCmd = "INSERT INTO %s" % ( outPathTable )
            sqlCmd += " (path,query_name,query_start,query_end,subject_name,subject_start,subject_end,E_value,score,identity)"
            sqlCmd += " VALUES ( '%i'" % ( rowIndex )
            for i in res:
                sqlCmd += ', "%s"' % ( i )
            sqlCmd += " )"
            self.execute( sqlCmd )
        self.updateInfoTable( outPathTable, "" )
        
        
    ## Give a list of instances according to the SQL command
    #
    # @param SQLCmd string is a SQL command
    # @param methodGetInstance2Adapt a getter method name. With this method you choose the type of intances contained in lObjs. See example in Test_DbMySql.py.
    # @return lObjs list of instances
    #
    def getObjectListWithSQLCmd( self, SQLCmd,  methodGetInstance2Adapt):
        self.execute( SQLCmd )
        res = self.fetchall()
        lObjs = []
        for t in res:
            iObj = methodGetInstance2Adapt()
            iObj.setFromTuple( t )
            lObjs.append( iObj )
        return lObjs
    
    
    ## Give a list of integer according to the SQL command
    #
    # @param sqlCmd string is a SQL command
    # @return lInteger integer list
    #
    def getIntegerListWithSQLCmd( self, sqlCmd ):
        self.execute(sqlCmd)
        res = self.fetchall()
        lInteger = []
        for t in res:
            if t[0] != None:
                lInteger.append(int(t[0]))
        return lInteger
    
    
    ## Give a int according to the SQL command
    #
    # @param sqlCmd string is a SQL command
    # @return nb integer 
    #
    def getIntegerWithSQLCmd( self, sqlCmd ):
        self.execute(sqlCmd)
        res = self.fetchall()
        nb = res[0][0]
        if nb == None:
            nb = 0
        return nb
    
    
    ## Give a list of str according to the SQL command
    #
    # @param sqlCmd string is a SQL command
    # @return lString str list
    #
    def getStringListWithSQLCmd( self, sqlCmd ):
        self.execute(sqlCmd)
        res = self.fetchall()
        lString = []
        for i in res:
            lString.append(i[0])
        return lString
    
    
    ## Remove doublons in a given table
    #
    # @param table string name of a MySQL table
    #
    def removeDoublons( self, table ):
        tmpTable = "%s_%s" % ( table, time.strftime("%Y%m%d%H%M%S") )
        sqlCmd = "CREATE TABLE %s SELECT DISTINCT * FROM %s" % ( tmpTable, table )
        self.execute( sqlCmd )
        self.dropTable( table )
        self.rename(tmpTable, table )
        
        
    ## Get a list of table names from a pattern
    #
    # @note for instance pattern = 'MyProject_%'
    #
    def getTableListFromPattern( self, pattern ):
        if pattern == "*" or pattern == "%":
            sqlCmd = "SHOW TABLES"
        else:
            sqlCmd = "SHOW TABLES like '%s'" % ( pattern )
        lTables = self.getStringListWithSQLCmd( sqlCmd )
        return lTables
