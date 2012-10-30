import os
import pyRepet.sql.RepetDBMySQL
import pyRepet.coord.Map
import pyRepet.coord.Set
import pyRepet.coord.Path


#---------------------------------------------------------------------------
class TableAdaptator(object):
    """
    Abstract class

    @ivar db: L{RepetDB<RepetDB>} instance
    @ivar tablename: table name
    """
    def __init__(self,db,tablename=""):
        """
        constructor

        @param db: L{RepetDB<RepetDB>} instance
        @param tablename: table name
        """
        self.db=db
        self.tablename=tablename
        

#---------------------------------------------------------------------------
class TablePathAdaptator(TableAdaptator):
    """
    Adaptator for Path tables
    """
    def insAPath(self,path, delayed=False):
        """
        Insert a L{Path<pyRepet.coord.Path.Path>} instance
        @param path: a path object of L{Path<pyRepet.coord.Path.Path>} instance       
        @param delayed: a boolean indicating if the insert must be delayed

        """
        path.range_query.seqname=path.range_query.seqname.replace("\\","\\\\")
        path.range_subject.seqname=path.range_subject.seqname.replace("\\","\\\\")
        if delayed:
            
            sql_cmd='INSERT DELAYED INTO %s VALUES (%d,"%s",%d,%d,"%s",%d,%d,%g,%d,%f)'\
                 %(self.tablename,\
                   path.id,\
                   path.range_query.seqname,\
                   path.range_query.start,\
                   path.range_query.end,\
                   path.range_subject.seqname,\
                   path.range_subject.start,\
                   path.range_subject.end,\
                   path.e_value,\
                   path.score,\
                   path.identity\
                   )
        else:
            sql_cmd='INSERT INTO %s VALUES (%d,"%s",%d,%d,"%s",%d,%d,%g,%d,%f)'\
                 %(self.tablename,\
                   path.id,\
                   path.range_query.seqname,\
                   path.range_query.start,\
                   path.range_query.end,\
                   path.range_subject.seqname,\
                   path.range_subject.start,\
                   path.range_subject.end,\
                   path.e_value,\
                   path.score,\
                   path.identity\
                   )
            
        self.db.execute(sql_cmd)

    def insPathList(self,lpath,delayed=False):
        """
        Insert a L{Path<pyRepet.coord.Path.Path>} instances list
        @param path: a path object of L{Path<pyRepet.coord.Path.Path>} instance       
        @param delayed: a boolean indicating if the insert must be delayed
        """
        for i in lpath:
            self.insAPath(i,delayed)
        
    def getPath_num(self):
        """
        Return a list of the identifier number contained in the table
        """
        sql_cmd='select distinct path from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(int(t[0]))
        return l

    def getContig_name(self):
        """
        Return a list of the query names contained in the table
        """
        sql_cmd='select distinct query_name from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(t[0])
        return l
        
    def getPathList_from_contig(self,contig):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list from the path contained on a query name

        @param contig: contig (=query) name
        """
        sql_cmd='select * from %s where query_name="%s";'%(self.tablename,contig)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lpath=[]
        for t in res:
            p=pyRepet.coord.Path.Path()
            p.set_from_tuple(t)
            lpath.append(p)
        return lpath


    def getSetList_from_contig(self,contig):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list from the path contained on a query name

        @param contig: contig (=query) name
        """
        lpath=self.getPathList_from_contig(contig)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)

    def getPathList_from_num(self,num):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list with a given identifier number

        @param num: identifier number
        @type num: integer
        """
        sql_cmd='select * from %s where path=%d;'%(self.tablename,num)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lpath=[]
        for t in res:
            p=pyRepet.coord.Path.Path()
            p.set_from_tuple(t)
            lpath.append(p)
        return lpath

    def getSetList_from_num(self,num):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list with a given identifier number

        @param num: identifier number
        @type num: integer
        """
        lpath=self.getPathList_from_num(num)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)


    def getPathList_from_numlist(self,lnum):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list with a list of identifier numbers

        @param lnum: list of identifier numbers
        @type lnum: python list of integers
        """
        lpath=[]
        if lnum==[]:
            return lpath
        sql_cmd='select * from %s where path=%d'%(self.tablename,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lpath=[]
        for t in res:
            p=pyRepet.coord.Path.Path()
            p.set_from_tuple(t)
            lpath.append(p)
        return lpath

    def getSetList_from_numlist(self,lnum):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list with a list of identifier numbers

        @param lnum: list of identifier numbers
        @type lnum: python list of integers
        """
        lpath=self.getPathList_from_numlist(lnum)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)
    
    def getPathList_from_qcoord(self,contig,start,end):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list overlapping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        sql_cmd='select distinct path from %s where query_name="%s" and ((query_start between least(%d,%d) and greatest(%d,%d) or query_end between least(%d,%d) and greatest(%d,%d)) or (least(query_start,query_end)<=least(%d,%d) and greatest(query_start,query_end)>=greatest(%d,%d)));'%(self.tablename,contig,start,end,start,end,start,end,start,end,start,end,start,end)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lnum=[]
        for t in res:
            lnum.append(int(t[0]))
        lpath=self.getPathList_from_numlist(lnum)
        return lpath

    def getSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list overlapping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lpath=self.getPathList_from_qcoord(contig,start,end)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)
    
    def getInPathList_from_qcoord(self,contig,start,end):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list included
        in a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        sql_cmd='select * from %s where query_name="%s" and ((query_start between least(%d,%d) and greatest(%d,%d) or query_end between least(%d,%d) and greatest(%d,%d)) or (least(query_start,query_end)<=least(%d,%d) and greatest(query_start,query_end)>=greatest(%d,%d)));'%(self.tablename,contig,start,end,start,end,start,end,start,end,start,end,start,end)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lpath=[]
        for t in res:
            p=pyRepet.coord.Path.Path()
            p.set_from_tuple(t)
            lpath.append(p)
        return lpath

    def getInSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list included a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lpath=self.getInPathList_from_qcoord(contig,start,end)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)

    def delPath_from_num(self,num):
        """
        Delete path corresponding to a given identifier number

        @param num: identifier number
        @type num: integer
        """
        sql_cmd='delete from %s where path=%d;'%(self.tablename,num)
        self.db.execute(sql_cmd)

    def delPath_from_listnum(self,lnum):
        """
        Delete path corresponding to a given list of identifier number

        @param lnum: list of identifier number
        @type lnum: python list of integer
        """
        if lnum==[]:
            return        
        sql_cmd='delete from %s where path=%d'%(self.tablename,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)

    def joinPath(self,id1,id2):
        """
        Join two path by changing id number of id1 and id2 path
        to the least of id1 and id2

        @param id1: id path number
        @param id2: id path number
        """
        if id1<id2:
            new_id=id1
            old_id=id2
        else:
            new_id=id2
            old_id=id1

        sql_cmd='UPDATE %s SET path=%d WHERE path=%d'\
                %(self.tablename,new_id,old_id)
        self.db.execute(sql_cmd)
        return new_id

    def getNewId(self):
        """
        Get a new id number
        """
        sql_cmd='select max(path) from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        max_id=self.db.fetchall()[0][0]
        if max_id==None:
            max_id=0
        return int(max_id)+1
    
    def insAddPathList(self,lpath):
        """
        Insert simply a L{Path<pyRepet.coord.Path.Path>} instances list changing the path id
        """
        id=self.getNewId()
        pyRepet.coord.Path.path_list_changeId(lpath,id)
        self.insPathList(lpath)

#---------------------------------------------------------------------------
class TableBinPathAdaptator(TablePathAdaptator):
    """
    Adaptator for Path tables with bin indexes
    """

    def __init__(self,db,tablename=""):
        """
        constructor

        @param db: L{RepetDB<RepetDB>} instance
        @param tablename: table name
        """
        self.db=db
        self.tablename=tablename
        self.tablename_bin=tablename+"_bin"
        self.create_bin()

    def create_bin( self, verbose=0 ):
        """
        Create a bin table for fast access
        """

        if verbose > 0:
            print "creating",self.tablename_bin,"for fast access"
        tmp_file=self.tablename+".tmp"+str(os.getpid())
        out=open(tmp_file,"w")

        tablename_range=self.tablename+"_range"
        self.db.path2path_range(self.tablename)
        table=TablePathAdaptator(self.db,tablename_range)
        contigs=table.getContig_name()
        for c in contigs:
            lpath=table.getPathList_from_contig(c)
            for i in lpath:
                bin=i.range_query.getBin()
                max=i.range_query.getMax()
                min=i.range_query.getMin()
                strand=i.range_query.isPlusStrand()
                out.write("%d\t%f\t%s\t%d\t%d\t%d\n"%(i.id,bin,i.range_query.seqname,min,max,strand))
        out.close();

        self.db.remove_if_exist(tablename_range)
        self.db.remove_if_exist(self.tablename_bin)
        sql_cmd="CREATE TABLE %s ( path int unsigned, bin float, contig varchar(255), min int, max int, strand int unsigned)"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        
        sql_cmd="LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' "%\
                 (tmp_file,self.tablename_bin)
        self.db.execute(sql_cmd)
        self.db.update_info_table(self.tablename_bin,self.tablename+" bin indexes")
        os.system("rm -f "+tmp_file)

        sql_cmd="CREATE INDEX id ON %s ( path );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX ibin ON %s ( bin );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX icontig ON %s ( contig );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX imin ON %s ( min );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX imax ON %s ( max );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX istrand ON %s ( strand );"% (self.tablename_bin)
        self.db.execute(sql_cmd)

    def insAPath(self,path,delayed=False):
        """
        Insert a L{Path<pyRepet.coord.Path.Path>} instance

        @param path: a path object of L{Path<pyRepet.coord.Path.Path>} instance       
        @param delayed: a boolean indicating if the insert must be delayed        
        """
        TablePathAdaptator.insAPath(self,path,delayed)
        path.range_query.seqname=path.range_query.seqname.replace("\\","\\\\")
        path.range_subject.seqname=path.range_subject.seqname.replace("\\","\\\\")
        bin=path.getBin()
        max=path.range_query.getMax()
        min=path.range_query.getMin()
        strand=path.range_query.isPlusStrand()
        if delayed:
            sql_cmd='INSERT DELAYED INTO %s VALUES (%d,%f,"%s",%d,%d,%d)'\
                 %(self.tablename_bin,\
                   path.id,\
                   bin,\
                   path.range_query.seqname,\
                   min,\
                   max,\
                   strand)
        else:
            sql_cmd='INSERT INTO %s VALUES (%d,%f,"%s",%d,%d,%d)'\
                 %(self.tablename_bin,\
                   path.id,\
                   bin,\
                   path.range_query.seqname,\
                   min,\
                   max,\
                   strand)
            
        self.db.execute(sql_cmd)

    def delPath_from_num(self,num):
        """
        Delete path corresponding to a given identifier number

        @param num: identifier number
        @type num: integer
        """
        TablePathAdaptator.delPath_from_num(self,num)
        sql_cmd='delete from %s where path=%d;'%(self.tablename_bin,num)
        self.db.execute(sql_cmd)

    def delPath_from_listnum(self,lnum):
        """
        Delete path corresponding to a given list of identifier number

        @param lnum: list of identifier number
        @type lnum: python list of integer
        """
        if lnum==[]:
            return
        TablePathAdaptator.delPath_from_numlist(self,lnum)
        sql_cmd='delete from %s where path=%d'%(self.tablename_bin,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)

    def joinPath(self,id1,id2):
        """
        Join two path by changing id number of id1 and id2 path
        to the least of id1 and id2

        @param id1: id path number
        @param id2: id path number
        """
        TablePathAdaptator.joinPath(self,id1,id2)
        if id1<id2:
            new_id=id1
            old_id=id2
        else:
            new_id=id2
            old_id=id1
        sql_cmd='UPDATE %s SET path=%d WHERE path=%d'\
                %(self.tablename_bin,new_id,old_id)
        self.db.execute(sql_cmd)
        return new_id

    def getNewId(self):
        """
        Get a new id number
        """
        sql_cmd='select max(path) from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        max_id=self.db.fetchall()[0][0]
        if max_id==None:
            max_id=0
        return int(max_id)+1

        
    def getPathList_from_qcoord(self,contig,start,end):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list overlaping
        a given region using the bin scheme

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """

        min_coord=min(start,end)
        max_coord=max(start,end)
        sql_cmd='select distinct path from %s where contig="%s" and ('\
                 %(self.tablename+"_bin",contig)
        for i in xrange(8,2,-1):
            bin_lvl=pow(10,i)
            if int(start/bin_lvl)==int(end/bin_lvl):       
                bin=float(bin_lvl+(int(start/bin_lvl)/1e10))
                sql_cmd+='bin=%f'%(bin)
            else:
                bin1=float(bin_lvl+(int(start/bin_lvl)/1e10))
                bin2=float(bin_lvl+(int(end/bin_lvl)/1e10))
                sql_cmd+='bin between %f and %f'%(bin1,bin2)
            if bin_lvl!=1000:
                sql_cmd+=" or "
                
        sql_cmd+=") and min<=%d and max>=%d;"%(max_coord,min_coord)
#        sql_cmd+=") and ((min<=%d and max>=%d) \
#        or (min between %d and %d) or (max between %d and %d));"\
#        %(max_coord,min_coord,max_coord,min_coord,max_coord,min_coord)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lnum=[]
        for i in res:
            lnum.append(int(i[0]))
        lpath=self.getPathList_from_numlist(lnum)
        return lpath

    def getInPathList_from_qcoord(self,contig,start,end):
        """
        Return a L{Path<pyRepet.coord.Path.Path>} instance list included
        in a given region using the bin scheme

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        min_coord=min(start,end)
        max_coord=max(start,end)
        lpath=self.getPathList_from_qcoord(contig,start,end)
        lpath_out=[]
        for i in lpath:
            if i.range_query.getMin()>min_coord and \
               i.range_query.getMax()<max_coord:
                lpath_out.append(i)
                            
        return lpath_out

    def getInSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list included a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lpath=self.getInPathList_from_qcoord(contig,start,end)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)

    def getSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list overlaping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lpath=self.getPathList_from_qcoord(contig,start,end)
        return pyRepet.coord.Path.path_list_rangeQ2Set(lpath)

    def getPath_num(self):
        """
        Return a list of the identifier number contained in the table
        """
        sql_cmd='select distinct path from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(int(t[0]))
        return l

    def getContig_name(self):
        """
        Return a list of the query names contained in the table
        """
        sql_cmd='select distinct contig from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(t[0])
        return l
        

#---------------------------------------------------------------------------
class TableSetAdaptator(TableAdaptator):
    """
    Adaptator for Set tables
    """
    def insASet(self,set,delayed=False):
        """
        Insert a L{Set<pyRepet.coord.Set.Set>} instance

        @param set: a set object of L{Set<pyRepet.coord.Set.Set>} instance
        @param delayed: a boolean indicating if the insert must be delayed
        """
        if set.empty():
            return
        set.name=set.name.replace("\\","\\\\")
        set.seqname=set.seqname.replace("\\","\\\\")
        if delayed:
            sql_cmd='INSERT DELAYED INTO %s VALUES (%d,"%s","%s",%d,%d)'\
                     %(self.tablename,\
                       set.id,\
                       set.name,\
                       set.seqname,\
                       set.start,\
                       set.end\
                       )
        else:
            sql_cmd='INSERT INTO %s VALUES (%d,"%s","%s",%d,%d)'\
                     %(self.tablename,\
                       set.id,\
                       set.name,\
                       set.seqname,\
                       set.start,\
                       set.end\
                       )
        self.db.execute(sql_cmd)

    def insSetList(self,lset,delayed=False):
        """
        Insert a L{Set<pyRepet.coord.Set.Set>} instances list
        @param lset: a set object list of L{Set<pyRepet.coord.Set.Set>} instances
        @param delayed: a boolean indicating if the insert must be delayed
        """
        for i in lset:
            self.insASet(i,delayed)

    def getPath_num(self):
        """
        Return a list of the identifier number contained in the table
        """
        return self.getSet_num()
            
    def getSet_num(self):
        """
        Return a list of the identifier number contained in the table
        """
        sql_cmd='select distinct path from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(int(t[0]))
        return l

    def getContig_name(self):
        """
        Return a list of the query names contained in the table
        """        
        sql_cmd='select distinct chr from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(t[0])
        return l
        
    def getSetList_from_contig(self,contig):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list from the set contained on a query name

        @param contig: contig (=query) name
        """
        sql_cmd='select * from %s where chr="%s";'%(self.tablename,contig)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lset=[]
        for t in res:
            p=pyRepet.coord.Set.Set()
            p.set_from_tuple(t)
            lset.append(p)
        return lset

    def getSetList_from_num(self,num):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list with a given identifier number

        @param num: identifier number
        @type num: integer
        """
        sql_cmd='select * from %s where path=%d;'%(self.tablename,num)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lset=[]
        for t in res:
            p=pyRepet.coord.Set.Set()
            p.set_from_tuple(t)
            lset.append(p)
        return lset

    def getSetList_from_numlist(self,lnum):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list with a list of identifier numbers

        @param lnum: list of identifier numbers
        @type lnum: python list of integers
        """
        lset=[]
        if lnum==[]:
            return lset
        sql_cmd='select * from %s where path=%d'%(self.tablename,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        for t in res:
            p=pyRepet.coord.Set.Set()
            p.set_from_tuple(t)
            lset.append(p)
        return lset

    def getSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list overlapping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        sql_cmd='select distinct path from %s where chr="%s" and ((start between least(%d,%d) and greatest(%d,%d) or end between least(%d,%d) and greatest(%d,%d)) or (least(start,end)<=least(%d,%d) and greatest(start,end)>=greatest(%d,%d)))  ;'%(self.tablename,contig,start,end,start,end,start,end,start,end,start,end,start,end)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lnum=[]
        for t in res:
            lnum.append(int(t[0]))
        lset=self.getSetList_from_numlist(lnum)
        return lset
    
    def delSet_from_num(self,num):
        """
        Delete set corresponding to a given identifier number

        @param num: identifier number
        @type num: integer
        """
        sql_cmd='delete from %s where path=%d;'%(self.tablename,num)
        self.db.execute(sql_cmd)

    def delSet_from_listnum(self,lnum):
        """
        Delete set corresponding to a given list of identifier number

        @param lnum: list of identifier number
        @type lnum: python list of integer
        """
        if lnum==[]:
            return
        sql_cmd='delete from %s where path=%d'%(self.tablename,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)

    def joinSet(self,id1,id2):
        """
        Join two set by changing id number of id1 and id2 set
        to the least of id1 and id2

        @param id1: id path number
        @param id2: id path number
        """       
        if id1<id2:
            new_id=id1
            old_id=id2
        else:
            new_id=id2
            old_id=id1

        sql_cmd='UPDATE %s SET path=%d WHERE path=%d'\
                %(self.tablename,new_id,old_id)
        self.db.execute(sql_cmd)

    def getNewId(self):
        """
        Get a new id number
        """
        sql_cmd='select max(path) from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        max_id=self.db.fetchall()[0][0]
        if max_id==None:
            max_id=0
        return int(max_id)+1


#---------------------------------------------------------------------------
class TableBinSetAdaptator(TableSetAdaptator):
    """
    Adaptator for Set tables with bin indexes
    """

    def __init__(self, db,tablename=""):
        """
        constructor

        @param db: L{RepetDB<RepetDB>} instance
        @param tablename: table name
        """
        self.db=db
        self.tablename=tablename
        self.tablename_bin=tablename+"_bin"
        self.create_bin()

    def create_bin( self, verbose=0 ):
        """
        Create a bin table for fast access
        """

        if verbose > 0:
            print "creating",self.tablename_bin,"for fast access"
        tmp_file=self.tablename+".tmp"+str(os.getpid())
        out=open(tmp_file,"w")

        tablename_range=self.tablename+"_range"
        self.db.set2set_range(self.tablename)
        table=TableSetAdaptator(self.db,tablename_range)
        contigs=table.getContig_name()
        for c in contigs:
            lset=table.getSetList_from_contig(c)
            for i in lset:
                bin=i.getBin()
                max=i.getMax()
                min=i.getMin()
                strand=i.isPlusStrand()
                out.write("%d\t%f\t%s\t%d\t%d\t%d\n"%(i.id,bin,i.seqname,min,max,strand))
        out.close();

        
        self.db.remove_if_exist(tablename_range)
        self.db.remove_if_exist(self.tablename_bin)
        sql_cmd="CREATE TABLE %s ( path int unsigned, bin float, contig varchar(255), min int, max int, strand int unsigned)"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        
        sql_cmd="LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' "%\
                 (tmp_file,self.tablename_bin)
        self.db.execute(sql_cmd)
        self.db.update_info_table(self.tablename_bin,self.tablename+" bin indexes")
        os.system("rm -f "+tmp_file)

        sql_cmd="CREATE INDEX id ON %s ( path );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX ibin ON %s ( bin );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX icontig ON %s ( contig );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX imin ON %s ( min );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX imax ON %s ( max );"% (self.tablename_bin)
        self.db.execute(sql_cmd)
        sql_cmd="CREATE INDEX istrand ON %s ( strand );"% (self.tablename_bin)
        self.db.execute(sql_cmd)

    def insASet(self,set,delayed=False):
        """
        Insert a L{Path<pyRepet.coord.Path.Path>} instance
        """
        TableSetAdaptator.insASet(self,set,delayed)
        set.seqname=set.seqname.replace("\\","\\\\")
        set.name=set.name.replace("\\","\\\\")
        bin=set.getBin()
        max=set.getMax()
        min=set.getMin()
        strand=set.isPlusStrand()
        if delayed:
            sql_cmd='INSERT DELAYED INTO %s VALUES (%d,%f,"%s",%d,%d,%d)'\
                 %(self.tablename_bin,\
                   set.id,\
                   bin,\
                   set.seqname,\
                   min,\
                   max,\
                   strand)
        else:
            sql_cmd='INSERT INTO %s VALUES (%d,%f,"%s",%d,%d,%d)'\
                 %(self.tablename_bin,\
                   set.id,\
                   bin,\
                   set.seqname,\
                   min,\
                   max,\
                   strand)
        self.db.execute(sql_cmd)

    def delSet_from_num(self,num):
        """
        Delete set corresponding to a given identifier number

        @param num: identifier number
        @type num: integer
        """

        TableSetAdaptator.delSet_from_num(self,num)
        sql_cmd='delete from %s where path=%d;'%(self.tablename_bin,num)
        self.db.execute(sql_cmd)

    def delSet_from_listnum(self,lnum):
        """
        Delete path corresponding to a given list of identifier number

        @param lnum: list of identifier number
        @type lnum: python list of integer
        """
        if lnum==[]:
            return
        TableSetAdaptator.delSet_from_numlist(self,lnum)
        sql_cmd='delete from %s where path=%d'%(self.tablename_bin,lnum[0])
        for i in lnum[1:]:
            sql_cmd+=" or path=%d"%(i)
        sql_cmd+=";"
        self.db.execute(sql_cmd)

    def joinSet(self,id1,id2):
        """
        Join two set by changing id number of id1 and id2 path
        to the least of id1 and id2

        @param id1: id path number
        @param id2: id path number
        """
        TableSetAdaptator.joinSet(self,id1,id2)
        if id1<id2:
            new_id=id1
            old_id=id2
        else:
            new_id=id2
            old_id=id1
        sql_cmd='UPDATE %s SET path=%d WHERE path=%d'\
                %(self.tablename_bin,new_id,old_id)
        self.db.execute(sql_cmd)
        return new_id

    def getNewId(self):
        """
        Get a new id number
        """
        sql_cmd='select max(path) from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        max_id=self.db.fetchall()[0][0]
        if max_id==None:
            max_id=0
        return int(max_id)+1

        
    def getSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list overlaping
        in a given region using the bin scheme

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """

        min_coord=min(start,end)
        max_coord=max(start,end)

        sql_cmd='select path from %s where contig="%s" and ('\
                 %(self.tablename+"_bin",contig)
        for i in xrange(8,2,-1):
            bin_lvl=pow(10,i)
            if int(start/bin_lvl)==int(end/bin_lvl):       
                bin=float(bin_lvl+(int(start/bin_lvl)/1e10))
                sql_cmd+='bin=%f'%(bin)
            else:
                bin1=float(bin_lvl+(int(start/bin_lvl)/1e10))
                bin2=float(bin_lvl+(int(end/bin_lvl)/1e10))
                sql_cmd+='bin between %f and %f'%(bin1,bin2)
            if bin_lvl!=1000:
                sql_cmd+=" or "

        sql_cmd+=") and min<=%d and max>=%d;"%(max_coord,min_coord);
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lnum=[]
        for i in res:
            lnum.append(int(i[0]))
        lset=self.getSetList_from_numlist(lnum)
        return lset

    def getInSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list included
        in a given region using the bin scheme

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lset=self.getSetList_from_qcoord(contig,start,end)       
        lset_out=[]
        for i in lset:
            if i.getMin()>min_coord and \
               i.getMax()<max_coord:
                lset_out.append(i)
                            
        return lset_out

    def getSet_num(self):
        """
        Return a list of the identifier number contained in the table
        """
        sql_cmd='select distinct path from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(int(t[0]))
        return l

    def getContig_name(self):
        """
        Return a list of the query names contained in the table
        """
        sql_cmd='select distinct contig from %s;'%(self.tablename_bin)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(t[0])
        return l
        
    def insAddSetList(self,lset):
        """
        Insert simply a L{Set<pyRepet.coord.Set.Set>} instances list changing the path id
        """
        id=self.getNewId()
        pyRepet.coord.Set.set_list_changeId(lset,id)
        self.insSetList(lset)

    def insMergeSetList(self,lset):
        """
        Insert a L{Set<pyRepet.coord.Set.Set>} instances list
        and merge it with existing overlaping L{Set<pyRepet.coord.Set.Set>}
        """
        min,max=pyRepet.coord.Set.set_list_boundaries(lset)
        olset=self.getSetList_from_qcoord(lset[0].seqname,min,max)
        oqhash=pyRepet.coord.Set.set_list_split(olset)
        qhash=pyRepet.coord.Set.set_list_split(lset)
        for k,alist in qhash.items():
            found=False
            for ok,oalist in oqhash.items():
                if pyRepet.coord.Set.set_list_overlap(alist,oalist):
                    oalist.extend(alist)
                    oalist=pyRepet.coord.Set.set_list_merge(oalist)
                    self.delSet_from_num(ok)
                    found=True
            if not found:
                self.insSetList(alist)
            else:
                id=self.getNewId()
                pyRepet.coord.Set.set_list_changeId(oalist,id)
                self.insSetList(oalist)
                
    def insDiffSetList(self,lset):
        """
        Insert a L{Set<pyRepet.coord.Set.Set>} instances list
        and remove overlaps with existing overlaping L{Set<pyRepet.coord.Set.Set>}
        """
        min,max=pyRepet.coord.Set.set_list_boundaries(lset)
        olset=self.getSetList_from_qcoord(lset[0].seqname,min,max)
        oqhash=pyRepet.coord.Set.set_list_split(olset)
        qhash=pyRepet.coord.Set.set_list_split(lset)
        for k,alist in qhash.items():
            for ok,oalist in oqhash.items():
                if pyRepet.coord.Set.set_list_overlap(alist,oalist):
                    alist=pyRepet.coord.Set.set_list_diff(oalist,alist)
            id=self.getNewId()
            pyRepet.coord.Set.set_list_changeId(alist,id)
            self.insSetList(alist)

#---------------------------------------------------------------------------
class TableMapAdaptator(TableAdaptator):
    """
    Adaptator for Map tables
    """
    def insAMap(self,map,delayed=False):
        """
        Insert a L{Map<pyRepet.coord.Map.Map>} instance
        """
        map.name=map.name.replace("\\","\\\\")
        map.seqname=map.seqname.replace("\\","\\\\")
        if delayed:
            sql_cmd='INSERT DELAYED INTO %s VALUES ("%s","%s",%d,%d)'\
                 %(self.tablename,\
                   map.name,\
                   map.seqname,\
                   map.start,\
                   map.end\
                   )
        else:
            sql_cmd='INSERT INTO %s VALUES ("%s","%s",%d,%d)'\
                 %(self.tablename,\
                   map.name,\
                   map.seqname,\
                   map.start,\
                   map.end\
                   )
            
        self.db.execute(sql_cmd)

    def insMapList(self,lmap,delayed=False):
        """
        Insert a L{Map<pyRepet.coord.Map.Map>} instances list
        """        
        for i in lmap:
            self.insAMap(i,delayed)
        
    def getContig_name(self):
        """
        Return a list of the sequence names contained in the table
        """
        sql_cmd='select distinct chr from %s;'%(self.tablename)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        l=[]
        for t in res:
            l.append(t[0])
        return l
        
    def getMapList_from_contig(self,contig):
        """
        Return a L{Map<pyRepet.coord.Map.Map>} instance list from the map contained on a query name

        @param contig: contig (=query) name
        """
        sql_cmd='select * from %s where chr="%s" ;'%(self.tablename,contig)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lmap=[]
        for t in res:
            map=pyRepet.coord.Map.Map()
            map.set_from_tuple(t)
            lmap.append(map)
        return lmap

    def getSetList_from_contig(self,contig):
        """
        Return a L{Set<pyRepet.coord.Set.Set>} instance list from the map contained on a query name

        @param contig: contig (=query) name
        """
        lmap=self.getMapList_from_contig(contig)
        return pyRepet.coord.Set.map_list2set(lmap)
       
    def getMapList_from_qcoord(self,contig,start,end):
        """
        Return a L{Map<pyRepet.coord.Map.Map>} instance list overlapping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        sql_cmd='select * from %s where chr="%s" and ((start between least(%d,%d) and greatest(%d,%d) or end between least(%d,%d) and greatest(%d,%d)) or (least(start,end)<=least(%d,%d) and greatest(start,end)>=greatest(%d,%d)))  ;'%(self.tablename,contig,start,end,start,end,start,end,start,end,start,end,start,end)
        self.db.execute(sql_cmd)
        res=self.db.fetchall()
        lmap=[]
        for t in res:
            map=pyRepet.coord.Map.Map()
            map.set_from_tuple(t)
            lmap.append(map)
        return lmap

    def getSetList_from_qcoord(self,contig,start,end):
        """
        Return a L{Set<pyRepet.coord.Set.Set>}  instance list overlapping a given region

        @param contig: contig name
        @type contig: string
        @param start: start coordinate
        @type start: integer
        @param end: end coordinate
        @type end: integer
        """
        lmap=self.getMapList_from_qcoord(contig,start,end)
        return pyRepet.coord.Set.map_list2set(lmap)

#------------------------------------------------------------------------------

class TableSeqAdaptator( TableAdaptator ):

    """
    Adaptator for 'seq' tables
    """

    #--------------------------------------------------------------------------

    def getSeq_accession( self ):

        """
        Return a list of the accessions contained in the table
        """

        sql_cmd = "SELECT DISTINCT accession FROM %s;" % (self.tablename)
        self.db.execute( sql_cmd )
        res = self.db.fetchall()
        lAccessions = []
        for t in res:
            lAccessions.append( t[0] )

        return lAccessions
