import os
from pyRepetUnit.commons.sql.TableSetAdaptator import TableSetAdaptator
from pyRepetUnit.commons.coord.SetUtils import SetUtils

#TODO: review. This class have to be on the same pattern of TableSetAdaptator

## Adaptator for Set tables with bin indexes
#
class TableBinSetAdaptator(TableSetAdaptator):
   
    ## constructor
    #
    # @param iDb DbMySql instance instance of DbMySql
    # @param tableName string table name (default = "")
    #
    def __init__(self, iDb, tableName = ""):
        TableSetAdaptator.__init__(self, iDb, tableName)
        self.tableName = tableName
#        self.tableName_bin = tableName + "_bin"
        self.tableName_bin = "%s_bin" % (self._table)
#        self.createBin()
        self.createBinSetTable()

    ## Create a bin table for fast access
    # 
    # @param verbose integer (default = 0)
    # @note old name is create_bin
    # @note Here the problem was that we should create table set and table bin set in this method
    #
    def createBinSetTable( self, verbose=0 ):
        if not self._iDb.doesTableExist(self._table):
            return
        
        if verbose > 0:
            print "creating %s for fast access" % (self.tableName_bin)

        table_range = self._table + "_range"
        self._iDb.set2set_range(self._table)
        table = TableSetAdaptator(self._iDb,table_range)
        
        self._iDb.remove_if_exist(self.tableName_bin)
        sql_cmd = "CREATE TABLE %s ( path int unsigned, bin float, contig varchar(255), min int, max int, strand int unsigned)" % (self.tableName_bin)
        self._iDb.execute(sql_cmd)
        
        if not table.isEmpty():
            tmp_file = self._table + ".tmp" + str(os.getpid())
            out = open(tmp_file, "w")
            lContigs = table.getSeqNameList()
            for c in lContigs:
                lSet = table.getSetListFromSeqName(c)
                for iSet in lSet:
                    bin = iSet.getBin()
                    max = iSet.getMax()
                    min = iSet.getMin()
                    strand = iSet.isOnDirectStrand()
                    out.write("%d\t%f\t%s\t%d\t%d\t%d\n"%(iSet.id, bin, iSet.seqname, min, max, strand))
            out.close();

            self._iDb.remove_if_exist(table_range)
            
            
            sql_cmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' " %\
                     (tmp_file, self.tableName_bin)
            self._iDb.execute(sql_cmd)
            self._iDb.update_info_table(self.tableName_bin, self._table + " bin indexes")
    
            sql_cmd = "CREATE INDEX id ON %s ( path );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            sql_cmd = "CREATE INDEX ibin ON %s ( bin );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            sql_cmd = "CREATE INDEX icontig ON %s ( contig );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            sql_cmd = "CREATE INDEX imin ON %s ( min );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            sql_cmd = "CREATE INDEX imax ON %s ( max );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            sql_cmd = "CREATE INDEX istrand ON %s ( strand );" % (self.tableName_bin)
            self._iDb.execute(sql_cmd)
            os.system("rm -f " + tmp_file)
        
#===============================================================================
#    def createBin( self, verbose=0 ):
#       
#        if verbose > 0:
#            print "creating", self.tableName_bin, "for fast access"
#        tmp_file = self.tableName + ".tmp" + str(os.getpid())
#        out = open(tmp_file, "w")
# 
#        tableName_range = self.tableName + "_range"
#        self._iDb.set2set_range(self.tableName)
#        table = TableSetAdaptator(self._iDb,tableName_range)
#        lContigs = table.getSeqNameList()
#        for c in lContigs:
#            lSet = table.getSetListFromSeqName(c)
#            for iSet in lSet:
#                bin = iSet.getBin()
#                max = iSet.getMax()
#                min = iSet.getMin()
#                strand = iSet.isOnDirectStrand()
#                out.write("%d\t%f\t%s\t%d\t%d\t%d\n"%(iSet.id, bin, iSet.seqname, min, max, strand))
#        out.close();
# 
#        self._iDb.remove_if_exist(tableName_range)
#        self._iDb.remove_if_exist(self.tableName_bin)
#        sql_cmd = "CREATE TABLE %s ( path int unsigned, bin float, contig varchar(255), min int, max int, strand int unsigned)" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        
#        sql_cmd = "LOAD DATA LOCAL INFILE '%s' INTO TABLE %s FIELDS ESCAPED BY '' " %\
#                 (tmp_file, self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        self._iDb.update_info_table(self.tableName_bin, self.tableName + " bin indexes")
#        os.system("rm -f " + tmp_file)
# 
#        sql_cmd = "CREATE INDEX id ON %s ( path );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        sql_cmd = "CREATE INDEX ibin ON %s ( bin );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        sql_cmd = "CREATE INDEX icontig ON %s ( contig );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        sql_cmd = "CREATE INDEX imin ON %s ( min );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        sql_cmd = "CREATE INDEX imax ON %s ( max );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#        sql_cmd = "CREATE INDEX istrand ON %s ( strand );" % (self.tableName_bin)
#        self._iDb.execute(sql_cmd)
#===============================================================================
        
    ## Insert a set instance in a set bin table
    # 
    # @param iSet set instance an instance of set object
    # @param delayed boolean an insert delayed or not
    #
    def insASetInSetAndBinTable(self, iSet, delayed = False):
        self.insert(iSet, delayed)
        iSet.seqname = iSet.seqname.replace("\\", "\\\\")
        iSet.name = iSet.name.replace("\\", "\\\\")
        bin = iSet.getBin()
        max = iSet.getMax()
        min = iSet.getMin()
        strand = iSet.isOnDirectStrand()
        sql_prefix = ''
        if delayed:
            sql_prefix = 'INSERT DELAYED INTO '
        else:
            sql_prefix = 'INSERT INTO '
        sql_cmd = sql_prefix + '%s VALUES (%d,%f,"%s",%d,%d,%d)'\
                 %(self.tableName_bin,\
                   iSet.id,\
                   bin,\
                   iSet.seqname,\
                   min,\
                   max,\
                   strand)
        self._iDb.execute(sql_cmd)

    ## Delete set corresponding to a given identifier number in set and bin set table
    # @param id integer identifier number
    # @note old name was delSet_from_num
    #
    def deleteFromIdFromSetAndBinTable(self, id):
        self.deleteFromId(id)
        sql_cmd = 'delete from %s where path=%d' % (self.tableName_bin, id)
        self._iDb.execute(sql_cmd)

    ## Delete path corresponding to a given list of identifier number
    #
    # @param lId integer list list of identifier number
    # @note old name was delSet_from_listnum
    #
    def deleteFromListIdFromSetAndBinTable(self, lId):
        if lId != []:
            self.deleteFromIdList(lId)
            sql_cmd = 'delete from %s where path=%d' % (self.tableName_bin, lId[0])
            for i in lId[1:]:
                sql_cmd += " or path=%d" % (i)
            self._iDb.execute(sql_cmd)

    ## Join two set by changing id number of id1 and id2 path
    # to the least of id1 and id2
    #
    # @param id1 integer id path number
    # @param id2 integer id path number
    # @return id integer new id
    # @note old name was joinSet
    #
    def joinTwoSetsFromSetAndBinTable(self, id1, id2):
        self.joinTwoSets(id1, id2)
        if id1 < id2:
            new_id = id1
            old_id = id2
        else:
            new_id = id2
            old_id = id1
        sql_cmd = 'UPDATE %s SET path=%d WHERE path=%d'\
                % (self.tableName_bin, new_id, old_id)
        self._iDb.execute(sql_cmd)
        return new_id
    
    ## Get a new id number from set bin table
    #
    def getNewId(self):
        sql_cmd = 'select max(path) from %s;' % (self.tableName_bin)
        self._iDb.execute(sql_cmd)
        max_id = self._iDb.fetchall()[0][0]
        if max_id != None:
            return int(max_id)+1
        else:
            return 1
        
    ## Get a set list instance between start and end parameters
    # using the bin scheme
    #
    # @param seqName reference seq name
    # @param start start coordinate
    # @param end end coordinate
    # @return lSet set list
    # @note old name was getSetList_from_qcoord
    #
    def getSetListFromQueryCoord(self, seqName, start, end):

        min_coord = min(start,end)
        max_coord = max(start,end)

        sql_cmd = 'select path from %s where contig="%s" and ('\
                 % (self.tableName + "_bin", seqName)
        for i in xrange(8, 2, -1):
            bin_lvl = pow(10, i)
            if int(start/bin_lvl) == int(end/bin_lvl):       
                bin = float(bin_lvl + (int(start / bin_lvl) / 1e10))
                sql_cmd += 'bin=%f' % (bin)
            else:
                bin1 = float(bin_lvl + (int(start / bin_lvl) / 1e10))
                bin2 = float(bin_lvl + (int(end  /bin_lvl) / 1e10))
                sql_cmd += 'bin between %f and %f' % (bin1, bin2)
            if bin_lvl != 1000:
                sql_cmd += " or "

        sql_cmd += ") and min<=%d and max>=%d" % (max_coord, min_coord);
        self._iDb.execute(sql_cmd)
        res = self._iDb.fetchall()
        lId = []
        for i in res:
            lId.append(int(i[0]))
        lSet = self.getSetListFromIdList(lId)
        return lSet

    ## Get a set list instances strictly included between start and end parameters
    # using the bin scheme
    #
    # @param seqName reference seq name
    # @param start start coordinate
    # @param end end coordinate
    # @return lSet set list
    # @note old name was getInSetList_from_qcoord
    # @warning the implementation has been changed : I added the two first lines
    #
    def getSetListStrictlyIncludedInQueryCoord(self, contig, start, end):
        min_coord = min(start,end)
        max_coord = max(start,end)
        lSet = self.getSetListFromQueryCoord(contig, start, end)       
        lSetStrictlyIncluded = []
        for iSet in lSet:
            if iSet.getMin() > min_coord and \
               iSet.getMax() < max_coord:
                lSetStrictlyIncluded.append(iSet)
                            
        return lSetStrictlyIncluded
    
    ## Get a list of the identifier Id contained in the table bin
    #
    # @return lId list of int list of identifier
    # @note old name was getSet_num
    #
    def getIdList(self):
        sql_cmd = 'select distinct path from %s;' % (self.tableName_bin)
        self._iDb.execute(sql_cmd)
        res = self._iDb.fetchall()
        lId = []
        for t in res:
            lId.append(int(t[0]))
        return lId
    
    ## Get a list of the query sequence name contained in the table bin
    #
    # @return lSeqName list of string list of query sequence name
    # @note old name was getContig_name
    #
    def getSeqNameList(self):
        sql_cmd = 'select distinct contig from %s;' % (self.tableName_bin)
        self._iDb.execute(sql_cmd)
        res = self._iDb.fetchall()
        lSeqName = []
        for t in res:
            lSeqName.append(t[0])
        return lSeqName
    
    ## Insert a Set list with the same new identifier in the table bin and set
    #
    # @note old name was insAddSetList
    #
    def insertListInSetAndBinTable(self, lSets, delayed = False):
        id = self.getNewId()
        SetUtils.changeIdInList( lSets, id )
        for iSet in lSets:
            self.insASetInSetAndBinTable(iSet, delayed)
    
    ## Insert a set list instances In table Bin and Set and merge all overlapping sets
    #
    # @param lSets reference seq name
    # @note old name was insMergeSetList
    #    
    def insertListInSetAndBinTableAndMergeAllSets(self, lSets):
        min, max = SetUtils.getListBoundaries(lSets)
        oldLSet = self.getSetListFromQueryCoord(lSets[0].seqname, min, max)
        oldQueryhash = SetUtils.getDictOfListsWithIdAsKey(oldLSet)
        qhash = SetUtils.getDictOfListsWithIdAsKey(lSets)
        for lNewSetById in qhash.values():
            found = False
            for currentId, oldLsetById in oldQueryhash.items():
                if SetUtils.areSetsOverlappingBetweenLists(lNewSetById, oldLsetById):
                    oldLsetById.extend(lNewSetById)
                    oldLsetById = SetUtils.mergeSetsInList(oldLsetById)
                    self.deleteFromIdFromSetAndBinTable(currentId)
                    found = True
            if not found:
                self.insertListInSetAndBinTable(lNewSetById)
            else:
                id = self.getNewId()
                SetUtils.changeIdInList(oldLsetById, id)
                self.insertListInSetAndBinTable(oldLsetById)
                
    ## Insert a set list instances In table Bin and Set after removing all overlaps between database and lSets
    #
    # @param lSets reference seq name
    # @note old name was insDiffSetList
    #    
    def insertListInSetAndBinTableAndRemoveOverlaps(self, lSets):
        min, max = SetUtils.getListBoundaries(lSets)
        oldLSet = self.getSetListFromQueryCoord(lSets[0].seqname, min, max)
        oldQueryHash = SetUtils.getDictOfListsWithIdAsKey(oldLSet)
        newQueryHash = SetUtils.getDictOfListsWithIdAsKey(lSets)
        for lNewSetById in newQueryHash.values():
            for lOldSetById in oldQueryHash.values():
                if SetUtils.areSetsOverlappingBetweenLists(lNewSetById, lOldSetById):
                    lNewSetById = SetUtils.getListOfSetWithoutOverlappingBetweenTwoListOfSet(lOldSetById, lNewSetById)
            self.insertListInSetAndBinTable(lNewSetById)
