import MySQLdb
import os, re, sys, time
import ConfigParser
import pyRepet.seq.Bioseq
import pyRepet.coord.Path
import pyRepet.coord.Set
import pyRepet.coord.Map
import pyRepet.coord.Align
import pyRepet.coord.Match

#------------------------------------------------------------------------------

class RepetDB:

    """
    connector to a repet database (managed by MySQL)

    @ivar user: db user name
    @type user: string

    @ivar host: db host name
    @type host: string

    @ivar passwd: db user password
    @type passwd: string

    @ivar dbname: database name
    @type dbname: string

    @ivar db: MySQL connector
    @type db: MySQLdb instance

    @ivar db_cursor: MySQL connection
    @type db_cursor: cursor() returned by a MySQLdb instance
    """

    #--------------------------------------------------------------------------

    def __init__(self,user="",host="",passwd="",dbname="",port=3306,cfgFileName=""):

        """
        constructor

        @param user: db user name
        @type user: string
        
        @param host: db host name
        @type host: string
        
        @param passwd: db user password
        @type passwd: string
        
        @param dbname: database name
        @type dbname: string

    	@param port: port of the database
    	@type port: integer

        @note: when a parameter is left blank, the constructor is able
        to set attribute values from environment variables: REPET_HOST,
        REPET_USER, REPET_PW, REPET_DB, REPET_PORT
        """
        self.port = int(port)

        if cfgFileName != "":
            self.setAttributesFromConfigFile(cfgFileName)
            
        elif host!="" and user!="" and passwd!="" and dbname!="":
            self.host = host
            self.user = user
            self.passwd = passwd
            self.dbname = dbname
            
        else:
            if os.environ.get("REPET_HOST") != None:
                self.host = os.environ.get("REPET_HOST")
            else:
                print "*** Error: can't find $REPET_HOST"
                sys.exit(1)
            self.user = os.environ.get("REPET_USER")
            self.passwd = os.environ.get("REPET_PW")
            self.dbname = os.environ.get("REPET_DB")
	    if os.environ.get("REPET_PORT") != None:
                self.port = int( os.environ.get("REPET_PORT") )
                
        maxNbTry = 10
        for i in xrange(1,maxNbTry+1):
            if not self.connect():
                time.sleep(2)
                if i == maxNbTry:
                    print "*** Error: failed to connect to the MySQL database"; sys.exit(1)
            else:
                break
            
        self.cursor = self.db.cursor()
        self.execute("""use %s"""%(self.dbname))
        
    #----------------------------------------------------------------------

    def setAttributesFromConfigFile(self,configFileName):

        """
	Set the attributes from the configuration file.
	@param configFileName: name of the configuration file
	@type configFileName: string
        """
        
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        self.host = config.get("repet_env","repet_host")
        self.user = config.get("repet_env","repet_user")
        self.passwd = config.get("repet_env","repet_pw")
        self.dbname = config.get("repet_env","repet_db")
	self.port = int( config.get("repet_env","repet_port") )
        
    #----------------------------------------------------------------------

    def connect( self, verbose=0 ):
        
        """
        Connect to the MySQL database.
        """
        
        try:
            if int(MySQLdb.get_client_info().split(".")[0]) >= 5:
                self.db = MySQLdb.connect( user=self.user, host=self.host,\
                                           passwd=self.passwd, db=self.dbname, \
					   port=self.port, \
                                           local_infile=1 )
            else:
                self.db = MySQLdb.connect( user=self.user, host=self.host,\
                                           passwd=self.passwd, db=self.dbname, \
					   port=self.port )
        except MySQLdb.Error, e:
            if verbose > 0:
                print "*** Error %d: %s" % (e.args[0], e.args[1]); sys.stdout.flush()
            return False

        return True

    #----------------------------------------------------------------------

    def close( self ):

        """
        Close the connection.
        """

        self.db.close()

    #----------------------------------------------------------------------

    def execute( self, qry ):

        """
        Execute a SQL query.
        """

        self.cursor.execute( qry )

    #----------------------------------------------------------------------

    def fetchall(self):

        """
        Retrieve the results of a SQL query.
        """

        return self.cursor.fetchall()
    
    #----------------------------------------------------------------------

    def show_tables(self):

        """
        Show database tables.
        """

        self.execute( """SHOW TABLES""" )
        results = self.fetchall()
        for i in results:
            print i[0]

    #----------------------------------------------------------------------

    def exist( self, table ):

        """
        Test if a table exists.

        @param table: table name
        @type table: string
        
        @return: True if the table exist, False otherwise
        @rtype: boolean
        """

        self.execute( """SHOW TABLES""" )
        results = self.cursor.fetchall()
        if (table,) in results:
            return True
        return False

    #----------------------------------------------------------------------

    def remove_if_exist( self, table, verbose=0 ):

        """
        Remove a table if it exists.

        @param table: table name
        @type table: string

        @param verbose: verbose (default=0/1)
	@type verbose: integer
        """

        self.execute( """SHOW TABLES""" )
        result = self.cursor.fetchall()
        if (table,) in result:
            if verbose > 0:
                print "table",table," exist, removing it!"
            self.execute( "DROP TABLE %s" % ( table ) )
            self.execute( 'DELETE FROM info_tables WHERE name="%s"' % ( table ) )

    #----------------------------------------------------------------------

    def update_info_table( self, tablename, info ):

        """
        Record a new table in the 'info_table' table.

        @param tablename: table name
        @type tablename: string

        @param info: information on the origine of the table
        @type info: string

        @note: info_table record the origine of table data
        """

        self.execute( """SHOW TABLES""" )
        results = self.cursor.fetchall()
        if ("info_tables",) not in results:
            sql_cmd = "CREATE TABLE info_tables ( name varchar(255), file varchar(255) )"
            self.execute( sql_cmd )
        self.execute('INSERT INTO info_tables VALUES ("%s","%s")'%(tablename,info))

    #----------------------------------------------------------------------

    def rename( self, table, new_name ):

        """
        Rename a table.

        @param table: old table name
        @type table: string

        @param new_name: new table name
        @type new_name: string
        """

        self.remove_if_exist( new_name )
        self.execute( 'RENAME TABLE %s TO %s ;'%(table,new_name) )
        self.execute( 'UPDATE info_tables SET name="%s" WHERE name="%s";'%(new_name,table) )

    #----------------------------------------------------------------------

    def copy_table( self, tablename, new_tablename, verbose=0 ):

        """
        Duplicate a table.

        @param tablename: source table name
        @type tablename: string

        @param new_tablename: new table name
        @type new_tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """

        self.remove_if_exist( new_tablename )
        sql_cmd='CREATE TABLE '+new_tablename+' SELECT * FROM '+tablename+';'
        if verbose > 0:
            print "copying table data,",tablename,"in",new_tablename
        self.execute( sql_cmd )
        self.update_info_table( new_tablename, "" )

    #----------------------------------------------------------------------

    def getSize( self, tablename ):

        qry = "SELECT count(*) FROM %s;" % ( tablename )
        self.execute( qry )
        res = self.fetchall()
        if len(res) == 0:
            return 0
        else:
            return int( res[0][0] )
        
    def getFieldListFromTable( self, tablename ):
        sql = "DESCRIBE %s" % ( tablename )
        self.execute( sql )
        res = self.fetchall()
        lFields = []
        for i in res:
            lFields.append( i )
        return lFields

    #----------------------------------------------------------------------

    def create_table( self, db, tablename, filename, filetype, verbose=0 ):

        """
        Create a MySQL table and load data.

        @param db: connector to a MySQL database
        @type db: RepetDB object

        @param tablename: name of the table to be created
        @type tablename: string

        @param filename: name of the file containing the data to be loaded in the table
        @type filename: string

        @param filetype: type of the data (fasta, map, set, align, path, match, TEclassif)
        @type filetype: string

    	@param verbose: verbose (default=0/1)
    	@type verbose: integer
        """

        if verbose > 0:
            print "creating table '%s' from file '%s' of type '%s'..." % ( tablename, filename, filetype )
            sys.stdout.flush()

        if filetype == "map":
            db.create_map( tablename, filename )

        elif filetype == "set":
            db.create_set( tablename, filename )

        elif filetype == "tab" or filetype == "match":
            db.create_match( tablename, filename )

        elif filetype == "path" :
            db.create_path( tablename, filename )

        elif filetype == "align":
            db.create_align( tablename, filename )

        elif filetype == "fa" or filetype == "fasta":
            db.create_seq( tablename, filename )

        elif filetype == "TEclassif":
            db.create_TEclassif( tablename, filename )

        else:
            print "*** Error: unknown type %s" % ( filetype )
            db.close()
            sys.exit(1)

        if verbose > 0:
            print "done !"; sys.stdout.flush()

    #----------------------------------------------------------------------

    def check_format( self, inFileName, format ):

        """
        Check the format of the file containing the data to be loaded.

        @param inFileName: name of the input file
        @type inFileName: string

        @param format: format of the data
        @type format: string

        @return: '0' if the format given in parameter is in agreement with the data file provided, '1' otherwise
        @rtype: integer
        """

        inFile = open( inFileName, "r" )
        line1 = inFile.readline()

        if format == "fasta":
            if ">" in line1:
                return 0

        # name, chr, start, end
        elif format == "map":
            line1 = line1.split("\t")
            if len(line1) == 4:
                return 0
            else:
                return 1

        # path, name, chr, start, end
        elif format == "set":
            line1 = line1.split("\t")
            if len(line1) == 5:
                return 0
            else:
                return 1

        # query_name, query_start, query_end, subject_name, subject_start, subject_end, E_value, score, identity
        elif format == "align":
            line1 = line1.split("\t")
            if len(line1) == 9:
                return 0
            else:
                return 1

        # path, query_name, query_start, query_end, subject_name, subject_start, subject_end, E_value, score, identity
        elif format == "path":
            line1 = line1.split("\t")
            if len(line1) == 10:
                return 0
            else:
                return 1

        # query_name, query_start, query_end, query_length, query_length_perc, match_length_perc, subject_name, subject_start, subject_end, subject_length, subject_length_perc, E_value, score, identity, path
        elif format == "match":
            line1 = line1.split("\t")
            if len(line1) == 15:
                return 0
            else:
                return 1

        # accession, class, order, category, comments, best_match
        elif format == "TEclassif":
            line1 = line1.split("\t")
            if len(line1) == 7:
                return 0
            else:
                return 1

        else:
            print "*** Error: RepetDB.check_format() not yet implemented for" + format
            sys.exit(1)

        return 1

    #----------------------------------------------------------------------

    def loadData( self, tablename, filename, escapeFirstLine=False, verbose=0 ):

        """
        Load data from a file into a MySQL table.

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """

        if filename != "":

            if escapeFirstLine == False:
                sql_cmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' " % ( filename, tablename )

            else:
                sql_cmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' IGNORE 1 LINES" % ( filename, tablename )

            self.execute( sql_cmd )

        if verbose > 0:
            print "nb of entries in the table = %i" % ( self.getSize( tablename ) )
            sys.stdout.flush()

    #----------------------------------------------------------------------

    def create_map( self, tablename, filename="" ):

        """
        create a L{Map<pyRepet.coord.Map.Map>} table and load data
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """        

        self.remove_if_exist(tablename)
        sql_cmd="CREATE TABLE %s ( name varchar(255), chr varchar(255), start int, end int)"% (tablename)

        self.execute(sql_cmd)
        self.create_map_index(tablename)
        self.loadData( tablename, filename )
        self.update_info_table(tablename,filename)

    #----------------------------------------------------------------------

    def create_map_index( self, tablename, verbose=0 ) :

        """
        Create indexes for a L{Map<pyRepet.coord.Map.Map>} table.
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        

        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "iname" not in lindex:
            sql_cmd="CREATE INDEX iname ON %s ( name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "ichr" not in lindex:   
            sql_cmd="CREATE INDEX ichr ON %s ( chr(10) );"% (tablename)
            self.execute(sql_cmd)
        if "istart" not in lindex:
            sql_cmd="CREATE INDEX istart ON %s ( start );"% (tablename)
            self.execute(sql_cmd)
        if "istart" not in lindex:
            sql_cmd="CREATE INDEX iend ON %s ( end );"% (tablename)
            self.execute(sql_cmd)
        if "icoord" not in lindex:
            sql_cmd="CREATE INDEX icoord ON %s ( start,end );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def create_match( self, tablename, filename="" ):

        """
        Create a L{Match<pyRepet.coord.Match.Match>} table and load data.
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """        

        self.remove_if_exist( tablename )
        sql_cmd="CREATE TABLE %s ( query_name varchar(255), query_start int, query_end int, query_length int unsigned, query_length_perc float, match_length_perc float, subject_name varchar(255), subject_start int unsigned, subject_end int unsigned, subject_length int unsigned, subject_length_perc float, E_value double, score int unsigned, identity float, path int unsigned)"% (tablename)

        self.execute( sql_cmd )
        self.create_match_index( tablename )
        self.loadData( tablename, filename, escapeFirstLine=True )
        self.update_info_table( tablename, filename )

    #----------------------------------------------------------------------

    def create_match_index( self, tablename, verbose=0 ):

        """
        Create indexes for a L{Match<pyRepet.coord.Match.Match>} table.
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        

        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "id" not in lindex:
            sql_cmd="CREATE UNIQUE INDEX id ON %s ( path );"% (tablename)
            self.execute(sql_cmd)
        if "qname" not in lindex:        
            sql_cmd="CREATE INDEX qname ON %s ( query_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "qstart" not in lindex:
            sql_cmd="CREATE INDEX qstart ON %s ( query_start );"% (tablename)
            self.execute(sql_cmd)
        if "qend" not in lindex:
            sql_cmd="CREATE INDEX qend ON %s ( query_end );"% (tablename)
            self.execute(sql_cmd)
        if "sname" not in lindex:
            sql_cmd="CREATE INDEX sname ON %s ( subject_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "sstart" not in lindex:
            sql_cmd="CREATE INDEX sstart ON %s ( subject_start );"% (tablename)
            self.execute(sql_cmd)
        if "send" not in lindex:
            sql_cmd="CREATE INDEX send ON %s ( subject_end );"% (tablename)
            self.execute(sql_cmd)
        if "qcoord" not in lindex:
            sql_cmd="CREATE INDEX qcoord ON %s ( query_start,query_end );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def create_path( self, tablename, filename="" ):

        """
        create a L{Path<pyRepet.coord.Path.Path>} table and load data
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """        

        self.remove_if_exist( tablename )
        sql_cmd = "CREATE TABLE %s ( path int unsigned, query_name varchar(255), query_start int , query_end int,subject_name varchar(255), subject_start int unsigned, subject_end int unsigned,E_value double, score int unsigned, identity float)" % ( tablename )
        self.execute( sql_cmd )
        self.create_path_index( tablename )
        self.loadData( tablename, filename, escapeFirstLine=False )
        self.update_info_table( tablename, filename )

    #----------------------------------------------------------------------

    def create_path_index( self, tablename, verbose=0 ):

        """
        Create indexes for a L{Path<pyRepet.coord.Path.Path>} table.
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        

        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "id" not in lindex:
            sql_cmd="CREATE INDEX id ON %s ( path );"% (tablename)
            self.execute(sql_cmd)
        if "qname" not in lindex:        
            sql_cmd="CREATE INDEX qname ON %s ( query_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "qstart" not in lindex:
            sql_cmd="CREATE INDEX qstart ON %s ( query_start );"% (tablename)
            self.execute(sql_cmd)
        if "qend" not in lindex:
            sql_cmd="CREATE INDEX qend ON %s ( query_end );"% (tablename)
            self.execute(sql_cmd)
        if "sname" not in lindex:
            sql_cmd="CREATE INDEX sname ON %s ( subject_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "sstart" not in lindex:
            sql_cmd="CREATE INDEX sstart ON %s ( subject_start );"% (tablename)
            self.execute(sql_cmd)
        if "send" not in lindex:
            sql_cmd="CREATE INDEX send ON %s ( subject_end );"% (tablename)
            self.execute(sql_cmd)
        if "qcoord" not in lindex:
            sql_cmd="CREATE INDEX qcoord ON %s ( query_start,query_end );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def create_align( self, tablename, filename="" ):

        """
        create a L{Align<pyRepet.coord.Align.Align>} table and load data
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """        

        self.remove_if_exist(tablename)
        sql_cmd="CREATE TABLE %s ( query_name varchar(255), query_start int, query_end int,subject_name varchar(255), subject_start int unsigned, subject_end int unsigned,E_value double, score int unsigned, identity float)"% (tablename)

        self.execute(sql_cmd)
        self.create_align_index(tablename)
        self.loadData( tablename, filename )
        self.update_info_table(tablename,filename)

    #----------------------------------------------------------------------

    def create_align_index( self, tablename, verbose=0 ):

        """
        Create indexes for a L{Align<pyRepet.coord.Align.Align>} table.
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        

        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "qname" not in lindex:        
            sql_cmd="CREATE INDEX qname ON %s ( query_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "qstart" not in lindex:
            sql_cmd="CREATE INDEX qstart ON %s ( query_start );"% (tablename)
            self.execute(sql_cmd)
        if "qend" not in lindex:
            sql_cmd="CREATE INDEX qend ON %s ( query_end );"% (tablename)
            self.execute(sql_cmd)
        if "sname" not in lindex:
            sql_cmd="CREATE INDEX sname ON %s ( subject_name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "sstart" not in lindex:
            sql_cmd="CREATE INDEX sstart ON %s ( subject_start );"% (tablename)
            self.execute(sql_cmd)
        if "send" not in lindex:
            sql_cmd="CREATE INDEX send ON %s ( subject_end );"% (tablename)
            self.execute(sql_cmd)
        if "qcoord" not in lindex:
            sql_cmd="CREATE INDEX qcoord ON %s ( query_start,query_end );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def create_set( self, tablename, filename="" ):

        """
        create a L{Set<pyRepet.coord.Set.Set>} table and load data
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """                

        self.remove_if_exist(tablename)
        sql_cmd="CREATE TABLE %s ( path int unsigned, name varchar(255), chr varchar(255), start int, end int);"% (tablename)

        self.execute(sql_cmd)
        self.create_set_index(tablename)
        self.loadData( tablename, filename )
        self.update_info_table(tablename,filename)

    #----------------------------------------------------------------------

    def create_set_index( self, tablename, verbose=0 ):

        """
        Create indexes for a L{Set<pyRepet.coord.Set.Set>} table.
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        
        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "id" not in lindex:
            sql_cmd="CREATE INDEX id ON %s ( path );"% (tablename)
            self.execute(sql_cmd)
        if "iname" not in lindex:
            sql_cmd="CREATE INDEX iname ON %s ( name(10) );"% (tablename)
            self.execute(sql_cmd)
        if "ichr" not in lindex:   
            sql_cmd="CREATE INDEX ichr ON %s ( chr(10) );"% (tablename)
            self.execute(sql_cmd)
        if "istart" not in lindex:
            sql_cmd="CREATE INDEX istart ON %s ( start );"% (tablename)
            self.execute(sql_cmd)
        if "istart" not in lindex:
            sql_cmd="CREATE INDEX iend ON %s ( end );"% (tablename)
            self.execute(sql_cmd)
        if "icoord" not in lindex:
            sql_cmd="CREATE INDEX icoord ON %s ( start,end );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def create_annot( self, table_annot ):

        """
        Create an annotation table.
        
        @param table_annot: new table name
        @type table_annot: string
        """        
        
        self.remove_if_exist(table_annot)
        sql_cmd="CREATE TABLE %s ( chunk varchar(255), range_name  varchar(255),selected_path varchar(255), span_set_name text, feature_name varchar(255), feature_type varchar(255), start int, end int);"% (table_annot)

        self.execute(sql_cmd)
        self.update_info_table(table_annot,"from other tables")


    #-----------------------------------------------------------------------

    def create_TEclassif( self, tablename, filename ):

        """
        Create an TE classification table (from TEclassifier data).
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be loaded in the table
        @type: string
        """

        self.remove_if_exist( tablename )
        f = open( filename, "r" )
        line = f.readline()
        f.close()
        if len( line.split("\t") ) == 8:
            sql_cmd = "CREATE TABLE " + tablename + " (accession varchar(255), length int unsigned, strand varchar(10), confusedness varchar(255), category varchar(255), TEorder varchar(255), completeness varchar(255), comments TEXT)"
        if len( line.split("\t") ) == 9:
            sql_cmd = "CREATE TABLE " + tablename + " (accession varchar(255), length int unsigned, strand varchar(10), confusedness varchar(255), category varchar(255), TEorder varchar(255), superfamily varchar(255), completeness varchar(255), comments TEXT)"
        self.execute( sql_cmd )
        self.loadData( tablename, filename )
        self.update_info_table( tablename, filename )

    #-----------------------------------------------------------------------

    def create_seq( self, tablename, filename="" ):

        """
        Create a seq table and load data.
        
        @param tablename: new table name
        @type tablename: string

        @param filename: data file name containing the data to be
        loaded in the table
        @type filename: string
        """
        
        self.remove_if_exist( tablename )
        sql_cmd = "CREATE TABLE %s ( accession varchar(255), sequence longtext, description varchar(255), length int unsigned )"% (tablename)
        self.execute( sql_cmd )
        self.create_seq_index( tablename )
        self.update_info_table( tablename, filename )
        
        if filename != "":
            file_db = open( filename )
            tmp_filename = filename.split("/")[-1]+".tmp"+str(os.getpid())
            file_db_out = open(tmp_filename,"w")
            seq = pyRepet.seq.Bioseq.Bioseq()
            numseq = 0
            while 1:
                seq.read( file_db )
                if seq.sequence == None:
                    break
                l = seq.getLength()
                file_db_out.write("%s\t%s\t%s\t%d\n"%(seq.header.split()[0]\
                                                ,seq.sequence,seq.header,l))
                numseq = numseq + 1
            file_db.close()
            file_db_out.close()
            sql_cmd = "LOAD DATA LOCAL INFILE '%s' IGNORE INTO TABLE %s FIELDS ESCAPED BY ''"%\
                     (tmp_filename,tablename)
            self.execute( sql_cmd )
            os.system( "rm " + tmp_filename )

    #-----------------------------------------------------------------------

    def create_seq_index( self, tablename, verbose=0 ):

        """
        create indexes for a seq table
        
        @param tablename: table name
        @type tablename: string

	@param verbose: verbose (default=0/1)
	@type verbose: integer
        """        

        sql_cmd="SHOW INDEX FROM %s;"% (tablename)
        self.execute(sql_cmd)
        res=self.fetchall()
        lindex=[]
        for i in res:
            lindex.append(i[2])
        if verbose > 0:
            print "existing indexes:", lindex
        if "iacc" not in lindex:
            sql_cmd="CREATE UNIQUE INDEX iacc ON %s ( accession );"% (tablename)
            self.execute(sql_cmd)
        if "idescr" not in lindex:
            sql_cmd="CREATE INDEX idescr ON %s ( description(10) );"% (tablename)
            self.execute(sql_cmd)

    #-----------------------------------------------------------------------

    def path2path_range(self,tablename,tmp_id=""):
        """
        create a L{Path<pyRepet.coord.Path.Path>} range table from a L{Path<pyRepet.coord.Path.Path>} table.

        This table summarize the L{Path<pyRepet.coord.Path.Path>} information according
        to the identifier numbers. The min and max value is taken
        
        @param tablename: table name
        @type tablename: string

        @param tmp_id: a temporary id to avoid overwrite of existing table. If
        different from empty, the table is temporary.
        @type tmp_id: string
        
        @note: the new table is created with suffix '_range'
        """                
        if tmp_id!="":
            range_tablename=tablename+"_range"+"_"+tmp_id
            tmp="temporary"
        else:
            range_tablename=tablename+"_range"
            tmp=""
        self.remove_if_exist(range_tablename)

        sqlcmd="create %s table %s select path, query_name, min(query_start) AS query_start, max(query_end) AS query_end, subject_name, min(subject_start) AS subject_start, max(subject_end) AS subject_end, min(e_value) AS e_value, sum(score) AS score, avg(identity) AS identity  from %s where query_start<query_end and subject_start<subject_end group by path;"%(tmp,range_tablename,tablename)
        self.execute(sqlcmd)

        sqlcmd="insert into %s select path, query_name, min(query_start) AS query_start, max(query_end) AS query_end, subject_name, max(subject_start) AS subject_start, min(subject_end) AS subject_end, min(e_value) AS e_value, sum(score) AS score, avg(identity) AS identity from %s where query_start<query_end and subject_start>subject_end group by path;"%(range_tablename,tablename)
        self.execute(sqlcmd)

        sqlcmd="insert into %s select path, query_name, max(query_start) AS query_start, min(query_end) AS query_end, subject_name, min(subject_start) AS subject_start, max(subject_end) AS subject_end, min(e_value) AS e_value, sum(score) AS score, avg(identity) AS identity from %s where query_start>query_end and subject_start<subject_end group by path;"%(range_tablename,tablename)
        self.execute(sqlcmd)

        sqlcmd="insert into %s select path, query_name, max(query_start) AS query_start, min(query_end) AS query_end, subject_name, max(subject_start) AS subject_start, min(subject_end) AS subject_end, min(e_value) AS e_value, sum(score) AS score, avg(identity) AS identity from %s where query_start>query_end and subject_start>subject_end group by path;"%(range_tablename,tablename)
        self.execute(sqlcmd)

        self.create_path_index(range_tablename)
    #-----------------------------------------------------------------------
    def set2set_range(self,tablename,tmp_id=""):    
        """
        create a L{Set<pyRepet.coord.Set.Set>} range table from a L{Set<pyRepet.coord.Set.Set>} table.

        This table summarize the L{Set<pyRepet.coord.Set.Set>} information according
        to the identifier numbers. The min and max value is taken
        
        @param tablename: table name
        @type tablename: string

        @param tmp_id: a temporary id to avoid overwrite of existing table. If
        different from empty, the table is temporary.
        @type tmp_id: string

        @note: the new table is created with suffix '_range'
        """                
        if tmp_id!="":
            range_tablename=tablename+"_range"+"_"+tmp_id
            tmp="temporary"
        else:
            range_tablename=tablename+"_range"
            tmp=""
        self.remove_if_exist(range_tablename)

        sqlcmd="create %s table %s select path, name, chr, min(start) AS start, max(end) AS end from %s where start<end group by path;"%(tmp,range_tablename,tablename)
        self.execute(sqlcmd)

        sqlcmd="insert into %s select path, name, chr, max(start) AS start, min(end) AS end from %s where start>end group by path;"%(range_tablename,tablename)
        self.execute(sqlcmd)
        self.create_set_index(range_tablename)

    #-----------------------------------------------------------------------

    def get_sequence(self,table,ac,start=0,end=0):
        """
        get a subsequence from a seq table.

        It can retreive a subsequence from a given seq table entry

        @param table: seq table name
        @type table: string
        
        @param ac: sequence name
        @type ac: string

        @param start: start coordinate
        @type start: integer

        @param end: end coordinate (if set to 0, it means the end of the sequence) 
        @type end: integer

        @note : if start and end are set to 0 or missing, the entire sequence is retreived
        @return: L{Bioseq<pyRepet.seq.Bioseq.Bioseq>}

        """
        ac=ac.replace("\\","\\\\")
        sql_cmd='SELECT length from %s WHERE accession="%s" or accession like "%s#%%";'\
                     %(table,ac,ac)
        self.execute(sql_cmd)
        res=self.fetchall()
        length=int(res[0][0])
        if start>length or end>length or start<0 or end<0:
            print "coordinate error:",start,",",end,"out of sequence",ac,"range"
            sys.exit()
        if start==0 and end==0:
            sql_cmd='SELECT description, sequence from %s WHERE accession="%s" or accession like "%s#%%";'\
                     %(table,ac,ac)
        elif end!=0 :
            begin=min(start,end)
            finish=max(start,end)
            sql_cmd='SELECT description, SUBSTRING(sequence,%d,%d) from %s WHERE accession="%s" or accession like "%s#%%";'\
                     %(begin,finish-begin+1,table,ac,ac)
        else:
            sql_cmd='SELECT description, SUBSTRING(sequence,%d) from %s WHERE accession="%s" or accession like "%s#%%";'\
                     %(start,table,ac,ac)

        self.execute(sql_cmd)
        res=self.fetchall()
        if len(res)!=0:
            seq=pyRepet.seq.Bioseq.Bioseq()      
            seq.header=res[0][0]
            seq.sequence=res[0][1]
            if start>end and end!=0:
                seq.sequence=seq.complement()
        else:
            print ac,"not found in",table
            sys.exit(1)
        return seq

    #-----------------------------------------------------------------------

    def get_sequence_from_chr(self,table,ac,start,end,contig_map=""):

        """
        get a subsequence from a seq table.

        It can retreive a subsequence splitted in two seq table entries

        @param table: seq table name
        @type table: string
        
        @param ac: sequence name
        @type ac: string

        @param start: start coordinate
        @type start: integer

        @param end: end coordinate
        @type end: integer

        @param contig_map: the contig_map table name
        @type contig_map: string
        """

        if contig_map=="":
            seq=self.get_sequence(table,ac,start,end)
        else:
            begin=min(start,end)
            finish=max(start,end)
            sql_cmd='SELECT name,start,end FROM %s WHERE chr="%s" AND %d BETWEEN least(start,end) AND greatest(start,end);'\
                     %(contig_map,ac,begin)
            self.execute(sql_cmd)
            res1=self.fetchall()
            if len(res1)==0:
                print ac,"coord",begin,"not found in",contig_map
                sys.exit()
            name_chunk1=res1[0][0]
            start_chunk1=int(res1[0][1])
            end_chunk1=int(res1[0][2])

            sql_cmd='SELECT name,start,end FROM %s WHERE chr="%s" AND %d BETWEEN least(start,end) AND greatest(start,end);'\
                     %(contig_map,ac,finish)
            self.execute(sql_cmd)
            res2=self.fetchall()
            if len(res2)==0:
                print ac,"coord",finish,"not found in",contig_map
                sys.exit()
            name_chunk2=res2[0][0]
            start_chunk2=int(res2[0][1])
            end_chunk2=int(res2[0][2])

            if name_chunk1==name_chunk2:
                begin_chunk=begin-start_chunk1+1
                finish_chunk=finish-start_chunk1+1
                seq=self.get_sequence(table,name_chunk1,\
                                      begin_chunk,finish_chunk)
            else:
                print name_chunk1,start_chunk1,end_chunk1
                print name_chunk2,start_chunk2,end_chunk2
                begin_chunk=begin-start_chunk1+1
                print name_chunk1,begin_chunk
                seq1=self.get_sequence(table,name_chunk1,\
                                      begin_chunk,0)
                finish_chunk=finish-start_chunk2+1
                print name_chunk2,finish_chunk
                over=end_chunk1-start_chunk2+1
                print "overlap",over
                if over<0:
                    print "chunks",name_chunk1,name_chunk2,\
                          "are not consecutives"
                    sys.exit()

                seq2=self.get_sequence(table,name_chunk2,\
                                      over+1,finish_chunk)

                seq=pyRepet.seq.Bioseq.Bioseq()  
                seq.header=seq1.header+" "+seq2.header
                seq.sequence=seq1.sequence+seq2.sequence
            if start>end:
                seq.sequence=seq.complement()
        return seq

    #-----------------------------------------------------------------------

    def get_set_sequence(self,set_list,table,contig_map=""):

        """
        get sequences from a L{Set<pyRepet.coord.Set.Set>} list.

        @param set_list: the coordinates list in a L{Set<pyRepet.coord.Set.Set>} format
        @type set_list: python list of L{Set<pyRepet.coord.Set.Set>}

        @param table: seq table name
        @type table: string
        
        @param contig_map: the contig_map table name
        @type contig_map: string
        """

        header=set_list[0].name+"::"+str(set_list[0].id)\
                +" "+set_list[0].seqname+" "
        sequence=""
        set_list.sort()
        if not set_list[0].isOnDirectStrand():
            set_list.reverse()
            
        for i in set_list:
            seq=self.get_sequence_from_chr(table,i.seqname,\
                                           i.start,i.end,contig_map)
            header+="%d..%d,"%(i.start,i.end)
            sequence+=seq.sequence
        return pyRepet.seq.Bioseq.Bioseq(header[:-1],sequence)

    #-----------------------------------------------------------------------

    def auto_annot_from_match(self,table_comput,table_annot):

        """
        produce an annot table from a L{Match<pyRepet.coord.Match.Match>} table

        @param table_comput: source data table name
        @type  table_comput: string
        
        @note: obsolete
        """

        self.execute('SELECT * FROM %s;'%(table_comput))
        result=self.fetchall()
        if result==():
            print "table:",table,"empty!!"
        match=pyRepet.coord.Match.Match()
        for i in result:
            match.set_from_tuple(i)
            self.execute('SELECT range_name, span_set_name FROM %s WHERE chunk="%s" AND start=%d AND end=%d;'%(table_annot,match.range_query.seqname,match.range_query.start,match.range_query.end))
            name_list=self.fetchall()
            if name_list!=():
                print "range already exist:",name_list[0][0]," ",name_list[0][1]
                if match.range_subject.seqname not in name_list[0][0].split("/"):
                    new_name=name_list[0][0]+"/"+match.range_subject.seqname
                    print "new name",new_name
                else:
                    new_name=name_list[0][0]
                new_span_name=name_list[0][1]+"/"+str(match.id)
                print "new span name",new_span_name
                
                self.execute('UPDATE %s SET range_name="%s", feature_name="%s", span_set_name="%s" WHERE chunk="%s" AND start=%d AND end=%d;'%( table_annot,new_name,new_name,new_span_name,match.range_query.seqname,match.range_query.start,match.range_query.end))
            else:
                self.execute('INSERT INTO %s VALUES("%s","%s","%s","%s","%s","%s",%d,%d)'%(table_annot,match.range_query.seqname,match.range_subject.seqname,str(match.id),str(match.id),match.range_subject.seqname,"TE",match.range_query.start,match.range_query.end))
        print "end automatique annotation"
     
    #-----------------------------------------------------------------------

    def classif2seq( self, classifTable, seqTable ):

        """
        convert a 'classif' table into a 'seq' table, i.e. add the classification to the headers

        @param classifTable: name of the 'classif' table
        @type classifTable: string

        @param seqTable: name of the 'seq' table
        @type seqTable: string
        """

        qry = "SELECT accession from "
        self.execute( qry )
        res = self.fetchall()
        print res

    #-----------------------------------------------------------------------

    def extend_set(self, table, size):
	"""
	extend coordinate in 5' and 3' from set table

	@param table : name of the input table
	@type: string

	@param size : size in bp for extention
	@type: integer
	"""
        self.remove_if_exist("%s_5p%d"%(table,size))
	qry="""create table %s_5p%d
select path, name, chr, start-%d as start, start-1 as end from %s
where start<end
union
select path, name, chr, start+%d as start, start+1 as end from %s
where start>end;
	"""%(table,size,size,table,size,table)
	self.execute( qry )	

        self.remove_if_exist("%s_3p%d"%(table,size))
	qry="""create table %s_3p%d
select path, name, chr, end+1 as start, end+%d as end from %s
where start<end
union
select path, name, chr, end-1 as start, end-%d as end from %s
where start>end;
	"""%(table,size,size,table,size,table)
	self.execute( qry )	

    #-----------------------------------------------------------------------

    def export( self, inTable, outFileName="", keepFirstLine=False, param="" ):
        if outFileName == "": outFileName = inTable
        prg = "mysql"
        cmd = prg
        cmd += " -h %s" % ( self.host )
        cmd += " -u %s" % ( self.user )
        cmd += " -p\"%s\"" % ( self.passwd )
        cmd += " --database=%s" % ( self.dbname )
        cmd += " -e\"SELECT * FROM %s" % ( inTable )
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
