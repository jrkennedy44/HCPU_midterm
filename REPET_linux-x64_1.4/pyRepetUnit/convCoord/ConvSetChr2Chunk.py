'''
Created on 18 mai 2009

@author: hadi
'''
import os
import pyRepet
from copy import *
from pyRepet.sql.TableAdaptator import *

class ConvSetChr2Chunk(object):
    '''
    classdocs
    '''


    def __init__(self,db,table,chunk_table,outtable):
        '''
        Constructor
        '''
        self._tablename=table
        self._chunk_table=chunk_table
        self._db=db
        self._outtable=outtable
        
    def run(self):
        """
        Convert a 'set' table format.
        """
    
        temp_file=str(os.getpid())+".on_chunk"
        fout=open(temp_file,'w')

        str_mask="SELECT * FROM "+\
            self._chunk_table+" WHERE chr='%s' AND ("+\
            "(%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
            " OR (%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
            " OR (%d <= LEAST(start,end) AND %d >= GREATEST(start,end)));"
                            
        self._db.create_set_index( self._tablename )
        qtableSetAdaptator = TableSetAdaptator( self._db, self._tablename )
        path_num_list = qtableSetAdaptator.getSet_num()

        for path_num in path_num_list:        
            slist=qtableSetAdaptator.getSetList_from_num( path_num )  
            for r in slist:
                 sql_cmd=str_mask%(r.seqname,r.getMin(),r.getMax(),r.getMin(),r.getMax())
                 self._db.execute(sql_cmd)
                 res=self._db.fetchall()
                 for i in res:
                    chunk=pyRepet.coord.Map.Map(i[0],i[1],int(i[2]),int(i[3]))
                
                    new_r=pyRepet.coord.Set.Set()
                    new_r=deepcopy(r)
                    new_r.seqname=chunk.name
 
                    if (r.start > chunk.start and r.start < chunk.end):
                        new_r.start=r.start-chunk.start+1 
                    if (r.end > chunk.start and r.end < chunk.end):
                        new_r.end=r.end-chunk.start+1
                                                   
                    if r.isPlusStrand():
                        if r.start <= chunk.start:
                            new_r.start=1
                        if r.end >= chunk.end:
                            new_r.end=chunk.end-chunk.start+1
                    else:
                        if r.end <= chunk.start:
                            new_r.end=1
                        if r.start >= chunk.end:
                            new_r.start=chunk.end-chunk.start+1
                            
                    new_r.write(fout)
 
        fout.close()
    
        self._db.create_set( self._outtable, temp_file )
    
        os.system( "rm -f " + temp_file )           