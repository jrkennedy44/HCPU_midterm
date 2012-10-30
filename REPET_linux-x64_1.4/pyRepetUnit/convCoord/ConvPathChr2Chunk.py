'''
Created on 18 mai 2009

@author: hadi
'''
import os
import pyRepet
from copy import *
from pyRepet.sql.TableAdaptator import *

class ConvPathChr2Chunk(object):
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
        Convert a 'path' table format.
        """
    
        temp_file=str(os.getpid())+".on_chunk"
        fout=open(temp_file,'w')

        str_mask="SELECT * FROM "+\
            self._chunk_table+" WHERE chr='%s' AND ("+\
            "(%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
            " OR (%d BETWEEN LEAST(start,end) AND GREATEST(start,end))"+\
            " OR (%d <= LEAST(start,end) AND %d >= GREATEST(start,end)));"
                            
        self._db.create_path_index( self._tablename )
        qtablePathAdaptator = TablePathAdaptator( self._db, self._tablename )
        path_num_list = qtablePathAdaptator.getPath_num()

        for path_num in path_num_list:        
            slist=qtablePathAdaptator.getPathList_from_num( path_num )  
            for r in slist:
                 r_min,r_max=pyRepet.coord.Path.path_list_boundaries([r])   
                 sql_cmd=str_mask%(r.range_query.seqname,r_min,r_max,r_min,r_max)
                 self._db.execute(sql_cmd)
                 res=self._db.fetchall()
                 for i in res:
                    chunk=pyRepet.coord.Map.Map(i[0],i[1],int(i[2]),int(i[3]))
                
                    new_r=pyRepet.coord.Path.Path()
                    new_r=deepcopy(r)
                    new_r.range_query.seqname=chunk.name
 
                    if (r.range_query.start > chunk.start and r.range_query.start < chunk.end):
                        new_r.range_query.start=r.range_query.start-chunk.start+1 
                    if (r.range_query.end > chunk.start and r.range_query.end < chunk.end):
                        new_r.range_query.end=r.range_query.end-chunk.start+1
                                                   
                    if r.range_query.isPlusStrand():
                        if r.range_query.start <= chunk.start:
                            new_r.range_query.start=1
                        if r.range_query.end >= chunk.end:
                            new_r.range_query.end=chunk.end-chunk.start+1
                    else:
                        if r.range_query.end <= chunk.start:
                            new_r.range_query.end=1
                        if r.range_query.start >= chunk.end:
                            new_r.range_query.start=chunk.end-chunk.start+1
                            
                    new_r.write(fout)
 
        fout.close()
    
        self._db.create_path( self._outtable, temp_file )
    
        os.system( "rm -f " + temp_file )           