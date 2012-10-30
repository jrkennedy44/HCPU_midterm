from xml.dom.minidom import *
from pyRepet.gamexml.Xcoord import *
from pyRepet.sql.RepetDB import *
import copy

#------------------------------------------------------------------------------

class computational:

    #--------------------------------------------------------------------------

    def __init__(self,dico={}):
        self.__dico=dico
        self.count_limit=100000

    #--------------------------------------------------------------------------

    def get_key(self):
        return self.__dico.keys()

    #--------------------------------------------------------------------------

    def add_dico(self,coord,name):
        id=coord.get_id()
        name=name.split()[0]
        if not self.__dico.has_key(name):
            self.__dico[name]={}
        sdico=self.__dico[name]
        if not sdico.has_key(id):
            sdico[id]=[]
        sdico[id].append(copy.deepcopy(coord))
                    
    #--------------------------------------------------------------------------

    def load_dico_path_from_file(self,key,f_result):
        self.__dico={}
        path=Xpath()
        file=open(f_result)
        while path.read(file)!=0:
            if path.get_range_query().seqname==key \
                   or key=="":
                self.add_dico(path,path.range_query.seqname)

    #--------------------------------------------------------------------------

    def load_dico_path_from_table( self, db, key, table, alias="", verbose=0 ):

        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
                sys.exit()
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        path=Xpath()
        if key!="":
            db.execute('SELECT * FROM %s WHERE query_name="%s" OR query_name like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            path.set_from_tuple(i)
            if alias!="":
                path.range_subject.seqname=id2name[path.range_subject.seqname.split("|")[-1]]
            self.add_dico(path,path.range_query.seqname)

    #--------------------------------------------------------------------------

    def load_dico_ipath_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
                sys.exit()
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        path=Xpath()
        if key!="":
            db.execute('SELECT * FROM %s WHERE subject_name="%s" OR subject_name like "%s %%"  LIMIT 500;'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s  LIMIT 500;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            path.set_from_tuple(i)
            if alias!="":
                path.range_subject.seqname=id2name[path.range_subject.seqname.split("|")[-1]]
            dummy=path.range_subject
            path.range_subject=path.range_query
            path.range_query=dummy
            if not path.range_subject.isPlusStrand():
                path.reverse()
            self.add_dico(path,path.range_query.seqname)

    #--------------------------------------------------------------------------

    def load_dico_rpath_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        path=Xpath()
        if key!="":
            db.execute('SELECT * FROM %s WHERE query_name="%s" OR query_name like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            path.set_from_tuple(i)
            if alias!="":
                path.range_subject.seqname=id2name[path.range_subject.seqname.split("|")[-1]]
            path.reverse()
            self.add_dico(path,path.range_query.seqname)

    #--------------------------------------------------------------------------

    def load_dico_align_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        align=Xalign()
        match_table=table.replace("_"+table.split("_")[-1],"")
        if key!="":
            db.execute('SELECT query_name,query_start,query_end,subject_name,subject_start,subject_end,path FROM %s WHERE query_name="%s" OR query_name like "%s %%";'%(match_table,key,key))
        else:
            db.execute('SELECT query_name,query_start,query_end,subject_name,subject_start,subject_end,path  FROM %s;'%(match_table))
        if verbose > 0:
            print "load key",key,"from table",match_table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            align.range_query.seqname=i[0]
            align.range_subject.seqname=i[3]
            align.id=i[6]
            if i[4]<i[5]:
                align.range_query.start=i[1]
                align.range_query.end=i[2]
                align.range_subject.start=i[4]
                align.range_subject.end=i[5]
            else:
                align.range_query.start=i[2]
                align.range_query.end=i[1]
                align.range_subject.start=i[5]
                align.range_subject.end=i[4]
                
            if alias!="":
                align.range_subject.seqname=id2name[align.range_subject.seqname.split("|")[-1]]
            db.execute("SELECT query_aligned_seq, subject_aligned_seq FROM %s WHERE path=%d ;"%(table,align.get_id()))
            al=db.fetchall()
            if al!=():
                align.set_align(al[0][0],al[0][1])
            self.add_dico(align,align.range_query.seqname)

    #--------------------------------------------------------------------------

    def load_dico_map_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        map=Xmap()
        if key!="":
            db.execute('SELECT * FROM %s WHERE chr="%s" OR chr like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        count=0
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            count+=1
            map.set_from_tuple(i,count)
            if alias!="":
                map.name=id2name[map.name]

            self.add_dico(map,map.seqname)

    #--------------------------------------------------------------------------

    def load_dico_rmap_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        map=Xmap()
        if key!="":
            db.execute('SELECT * FROM %s WHERE chr="%s" OR chr like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        count=0
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            count+=1
            map.set_from_tuple(i,count)
            if alias!="":
                map.name=id2name[map.name]
            map.reverse()
            self.add_dico(map,map.seqname)

    #--------------------------------------------------------------------------

    def load_dico_set_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        set=Xset()
        if key!="":
            db.execute('SELECT * FROM %s WHERE chr="%s" OR chr like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            set.set_from_tuple(i)
            if alias!="":
                set.name=id2name[set.name]
            self.add_dico(set,set.seqname)

    #--------------------------------------------------------------------------

    def load_dico_annot_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        annot=Xannot()
        if key!="":
            db.execute('SELECT * FROM %s WHERE query_name="%s" OR query_name like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            annot.set_from_tuple(i)
            if alias!="":
                annot.range_subject.seqname=id2name[annot.range_subject.seqname.split("|")[-1]]
            self.add_dico(annot,annot.range_query.seqname)           
                
    #--------------------------------------------------------------------------

    def load_dico_annotset_from_table(self,db,key,table,alias="", verbose=0):
        id2name={}
        if alias!="":
            db.execute('SELECT id,name FROM %s;'%(alias))
            result=db.fetchall()
            if result==():
                print "no alias table:",alias
            for i in result:
                id2name[i[0]]=i[1]
                
        self.__dico={}
        annot=XsetAnnot()
        if key!="":
            db.execute('SELECT * FROM %s WHERE chr="%s" OR chr like "%s %%";'%(table,key,key))
        else:
            db.execute('SELECT * FROM %s;'%(table))
        if verbose > 0:
            print "load key",key,"from table",table    
        result=db.fetchall()
        if result==():
            if verbose > 0:
                print "\t\t===>>no key:",key,"in table:",table
        for i in result:
            annot.set_from_tuple(i)
            if alias!="":
                annot.name=id2name[annot.name.split("|")[-1]]
            self.add_dico(annot,annot.seqname)

    #--------------------------------------------------------------------------

    def add_computational(self,doc,name_prog, verbose=0):
        cle=doc.getElementsByTagName('seq').item(0).getAttribute('id')
        cle=cle.split()[0]
        if verbose > 0:
            print "  =>gamexml file key is **"+cle+"**"
        if not self.__dico.has_key(cle):
            if verbose > 0:
                print "Files aren't compatible: no key **" +cle+"** in results!!"
            return 0
        comput=doc.createElement('computational_analysis')
        racine=doc.documentElement
        racine.appendChild(comput)
        prog=doc.createElement('program')
        comput.appendChild(prog)
        prog.appendChild(doc.createTextNode(name_prog))
        db=doc.createElement('database')
        comput.appendChild(db)
        db.appendChild(doc.createTextNode('db'))
        sdico=self.__dico[cle]
        for id,set in sdico.items():
            result_set=doc.createElement('result_set')
            result_set.setAttribute('id',str(id))
            comput.appendChild(result_set)
            name_result=doc.createElement('name')
            name_result.appendChild(doc.createTextNode(set[0].get_name()+ '::' + str(id)))
            result_set.appendChild(name_result)
            for span in set:
                span.add_span(doc,result_set)
        return cle
             
        
    #--------------------------------------------------------------------------

    def add_annotation(self,doc,table, verbose=0):
        cle=doc.getElementsByTagName('seq').item(0).getAttribute('id')
        cle=cle.split()[0]
        if verbose > 0:
            print "  =>gamexml file key is **"+cle+"**"
        if not self.__dico.has_key(cle):
            if verbose > 0:
                print "Files aren't compatible: no key **" +cle+"** in annotations!!"
            return 0
        sdico=self.__dico[cle]
        for id,set in sdico.items():
            racine=doc.documentElement
            annot=doc.createElement('annotation')
            annot.setAttribute('id',str(id))
            racine.appendChild(annot)
            
            result_set=doc.createElement('feature_set')
            result_set.setAttribute('id',str(id))
            annot.appendChild(result_set)
            
            name_result=doc.createElement('name')
            name_result.appendChild(doc.createTextNode(set[0].get_name()+\
                                                       '::' + str(id)))
            result_set.appendChild(name_result)

            type=doc.createElement('type')
            type.appendChild(doc.createTextNode("transcript"))
            result_set.appendChild(type)

            comment=doc.createElement('comment')
            comment.setAttribute('internal','false')
            text=doc.createElement('text')
            text.appendChild(doc.createTextNode("Automatic promotion from table: "+table+", path # "+str(id)))
            comment.appendChild(text)
            result_set.appendChild(comment)
            
            for span in set:
                span.add_span(doc,result_set)
        return cle
