import pyRepet.sql.RepetDBMySQL


class RepetDB ( pyRepet.sql.RepetDBMySQL.RepetDB ):
    
    def execute( self, qry, params=None ):
        if params == None:
            self.cursor.execute( qry )
        else:
            self.cursor.execute( qry, params )
            
            
    ## Record a new table in the 'info_table' table
    #
    # @param tablename table name
    # @param info information on the origin of the table
    # 
    def updateInfoTable( self, tablename, info ):
        self.execute( """SHOW TABLES""" )
        results = self.fetchall()
        if ("info_tables",) not in results:
            sqlCmd = "CREATE TABLE info_tables ( name varchar(255), file varchar(255) )"
            self.execute( sqlCmd )
        qryParams = "INSERT INTO info_tables VALUES (%s, %s)"
        params = ( tablename, info )
        self.execute( qryParams,params )
