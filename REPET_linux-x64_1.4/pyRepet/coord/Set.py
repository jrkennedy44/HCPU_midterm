import sys
from pyRepet.coord.Map import *
 
class Set(Map):
    """
    Record a named subsequence region with identifier

    @ivar name: the name of the region
    @type name: string

    @ivar id: identifier number
    @type id: integer
    """
    
    def __init__(self,id=-1,name="",seqname="",start=-1,end=-1):
        """
        constructor
        
        @param id: identifier number
        @type id: integer
    
        @param name: the name of the region
        @type name: string

        @param seqname: the sequence name
        @type seqname: string
        
        @param start: start coordinate
        @type start: integer

        @param end: end coordinate
        @type end: integer
        """
        Range.__init__(self,seqname,start,end)
        self.name=name
        self.id=id

    def set_from_tuple(self,tuple):
        """
        set attribute data from a tuple

        @param tuple: a tuple with (id,name,seqname,start,end)
        @type tuple: python tuple
        """        
        self.id=int(tuple[0])
        self.name=tuple[1]
        self.seqname=tuple[2]
        self.start=int(tuple[3])
        self.end=int(tuple[4])
        
    def read(self,file):
        """
        read attribute data from a set file

        @param file: file identifier of the file being read
        @type file: file identifier
        @return: 1 on success, 0 at the end of the file 
        """
        line=file.readline()
        if line=="":
            return 0
        liste=line.split("\t")
        self.set_from_tuple(liste)
        return 1

    def toString(self):
        """
        return a formated string of the attribut data
        """
        return "%d\t%s"%(self.id,Map.toString(self))

    def merge(self,s):
        """
        merge self with a L{Set<Set>} instance

        @param s: a L{Set<Set>} instance
        @type s: class L{Set<Set>}
        """
        Map.merge(self,s)
        self.id=min(self.id,s.id)

    def diff(self,s):
	n=Range.diff(self,s)
        new=Set()
        if not n.empty():
            new.id=self.id
            new.name=self.name
	    new.seqname=n.seqname
	    new.start=n.start
	    new.end=n.end
        return new

    def set2map(self):
        """
        return a L{Map<pyRepet.coord.Map.Map>} instance built from
        self attributes
        """
        return Map(self.name+"::"+str(self.id),self.seqname,self.start,self.end)
#-----------------------------------------------------------
# Function on set list

def set_list_changeId(set_list,newId):
    """
    change in place the id of L{Set<Set>} instances contained in a list

    @param set_list: lists of L{Set<Set>} instances
    @type set_list: python list of L{Set<Set>} instances

    @param newId: a new path number
    @type newId: integer
    """
    for i in set_list:
        i.id=newId

def set_list_overlap_size(lset1,lset2):
    """
    return the overlap size between two lists of L{Set<Set>} instances

    @param lset1: lists of L{Set<Set>} instances
    @type lset1: python list of L{Set<Set>} instances
    
    @param lset2: lists of L{Set<Set>} instances
    @type lset2: python list of L{Set<Set>} instances

    @return: a size of overlap
    """

    lset1.sort()
    lset2.sort()

    osize=0
    
    i=0
    j=0
    while i!= len(lset1):
        while j!= len(lset2) and lset1[i]>lset2[j]\
             and not(lset1[i].overlap(lset2[j])):
            j+=1
        jj=j
        while jj!= len(lset2) and lset1[i].overlap(lset2[jj]):
            osize+=lset1[i].overlap_size(lset2[jj])
            jj+=1
        i+=1
    return osize

def set_list_overlap(lset1,lset2):
    """
    return true if the two lists of L{Set<Set>} instances overlap

    @param lset1: lists of L{Set<Set>} instances
    @type lset1: python list of L{Set<Set>} instances
    
    @param lset2: lists of L{Set<Set>} instances
    @type lset2: python list of L{Set<Set>} instances
    """

    lset1.sort()
    lset2.sort()
    
    i=0
    j=0
    while i!= len(lset1):
        while j!= len(lset2) and lset1[i]>lset2[j]\
             and not(lset1[i].overlap(lset2[j])):
            j+=1
        if j!= len(lset2) and lset1[i].overlap(lset2[j]):
            return True
        i+=1
    return False

def set_list_size(set_list):
    """
    return the total size of L{Set<Set>} instances contained in a list

    @param set_list: lists of L{Set<Set>} instances
    @type set_list: python list of L{Set<Set>} instances
    """
    size=0
    for i in set_list:
        size=size+i.length()
    return size

def set_list_boundaries(set_list):
    """
    return min et max coordinates of L{Set<Set>} instances contained in a list

    @param set_list: lists of L{Set<Set>} instances
    @type set_list: python list of L{Set<Set>} instances

    @return: python tuple (min,max)
    """
    qmin=-1
    qmax=-1
    for i in set_list:
        if qmin==-1:
            qmin=i.start
        qmin=min(qmin,i.getMin())
        qmax=max(qmax,i.getMax())
    return (qmin,qmax)


def set_list_show(set_list):
    """
    show L{Set<Set>} attributes contained in a list

    @param set_list: a list of L{Set<Set>} instances
    """
    for i in set_list:
        i.show()
        
def set_list_write(set_list,filename,mode="w"):
    """
    write L{Set<Set>} contained in a list

    @param set_list: a list of L{Set<Set>} instances
    @param filename: a filename
    @param mode: the open mode of the file ""w"" or ""a"" 
    """
    file=open(filename,mode)
    for i in set_list:
        i.write(file)
        
def set_list_print_log(set_list,log_level):
    """
    show L{Set<Set>} attributes contained in a list

    @param set_list: a list of L{Set<Set>} instances
    @param log_level: a log level
    """
    for i in set_list:
        i.print_log(log_level)
        
def set_list_split(set_list):
    """
    split a L{Set<Set>} list in several L{Set<Set>}
    list according to the id number

    @param set_list: a list of L{Set<Set>} instances
    @return: several set list in a dictionary with the id as key
    """    
    by_id_list={}
    for i in set_list:
        if by_id_list.has_key(i.id):
            by_id_list[i.id].append(i)
        else:
            by_id_list[i.id]=[i]
    return by_id_list

def set_list2map(set_list):
    """
    return a L{Map<pyRepet.coord.Map.Map>} instance list from the L{Set<Set>}
    instances list

    @param set_list: a list of L{Set<Set>} instances
    """   
    l=[]
    for i in set_list:
        l.append(i.set2map())
    return l

def map_list2set(map_list):
    """
    construct a L{Set<Set>} instances list from a
    L{Map<pyRepet.coord.Map.Map>} instance list

    @param map_list: a list of  L{Map<pyRepet.coord.Map.Map>} instances
    """
    l=[]
    c=0
    for i in map_list:
        c+=1
        l.append(Set(c,i.name,i.seqname,i.start,i.end))
    return l
    

def set_list_merge(set_list):
    """
    new is SetUtils.mergeSetsInList
    merges all overlapping L{Set<Set>} instances in a list

    @return: a new list of the merged L{Set<Set>} instances
    """
    l=[]
    if len(set_list)==0:
	   return l

    set_list.sort()
    prev=set_list[0]
    for i in set_list[1:]:
        if prev.overlap(i):
            prev.merge(i)
        else:
            l.append(prev)
            prev=i
    l.append(prev)
    return l

def set_list_unjoin(pl1,pl2):
    """
    unjoin a L{Set<Set>} list according to another

    @param pl1: a list of L{Set<Set>} instances to keep 
    @param pl2: a list of L{Set<Set>} instances to unjoin

    @return: pl2 split in several list or an empty list if no split occurs 
    """
    pl1.sort()
    pl2.sort()
    i=0
    list_pl=[]
    while i<len(pl1):
        j1=0
        while j1<len(pl2) and pl1[i]>pl2[j1]:
            j1+=1
        if j1==len(pl2):
            break
        if j1!=0:
            list_pl.append(pl2[:j1])
            del pl2[:j1]
            j1=0
        if i+1==len(pl1):
            break
        j2=j1
        if j2<len(pl2) and pl1[i+1]>pl2[j2]:
            while j2<len(pl2) and pl1[i+1]>pl2[j2]:
                j2+=1
            list_pl.append(pl2[j1:j2])
            del pl2[j1:j2]
        i+=1

    if list_pl!=[]:
        list_pl.append(pl2)
    return list_pl

def set_list_diff(lset1,lset2):
    """
    remove overlapping L{Set<Set>} instances in the second list
    given in argument according to the first

    @return: a new list of the 'diff' L{Set<Set>} instances
    """
    for i in lset1:
        for idx,j in enumerate(lset2):
	    n=j.diff(i)
            if not n.empty() and n.length()>=20:
                lset2.append(n)
    diff_list=[]
    for i in lset2:
        if not i.empty() and i.length()>=20:
            diff_list.append(i)
    #set_list_unjoin(lset1,diff_list)
    return diff_list

def set_list_add_set(lset1,lset2,max_id=0):
    """
    add L{Set<Set>} instances in a list to another list

    @param lset1,lset2: a set object list of L{Set<pyRepet.coord.Set.Set>}
    instances. lset2 is added to lset1
    @param max_id: start id value for inserting new
    L{Set<pyRepet.coord.Set.Set>} instances
    @return: a new list of the diff L{Set<Set>} instances
    """
    lset_add=lset1
    idlist2=set_list_split(lset2)
    if max_id==0:
        idlist1=set_list_split(lset1)
        max_id=max(idlist1.keys())
    for id,alist in idlist2.items():
        set_list_changeId(alist,max_id)
        lset_add.extend(alist)
        max_id+=1
    return lset_add,max_id

def set_list_remove_doublons(lset):
    """
    find doublons L{Set<Set>} instances in the list

    @return: a list L{Set<Set>} instances with no doublons
    """

    lset_out=lset
    lset_out.sort()
    idx2del=[]
    i=0
    j=0
    while i< len(lset_out):
        while j< len(lset_out) and (lset_out[i]>lset_out[j] or i==j)\
            and not(lset_out[i].start==lset_out[j].start \
                    and lset_out[i].end==lset_out[j].end \
                    and lset_out[i].seqname==lset_out[j].seqname \
                    and lset_out[i].name==lset_out[j].name ):
            j+=1

        while j<len(lset_out) and lset_out[i].start==lset_out[j].start \
                    and lset_out[i].end==lset_out[j].end \
                    and lset_out[i].seqname==lset_out[j].seqname \
                    and lset_out[i].name==lset_out[j].name and i!=j :
            idx2del.append(j)
            j+=1
        i+=1
    idx2del.sort()
    idx2del.reverse()
    for idx in idx2del:
        del lset_out[idx]
    return lset_out

def set_list_find_self_overlaps(lset):
    """
    find overlapping L{Set<Set>} instances in the list

    @return: a list of overlapping path numbers
    """

    lset.sort()

    merge_list=[]
    merge_list_count=0

    id2merge_list_pos={}
    
    i=0
    j=0
    while i!= len(lset):
        while j!= len(lset) and (lset[i]>lset[j] or i==j)\
            and not(lset[i].overlap(lset[j])\
                    and lset[i].isPlusStrand()==lset[j].isPlusStrand()):
            j+=1

        while j!= len(lset) and lset[i].overlap(lset[j]) and i!=j \
                  and lset[i].isPlusStrand()==lset[j].isPlusStrand():
            id1=lset[i].id
            id2=lset[j].id
            if id2merge_list_pos.has_key(id1) \
                   and not id2merge_list_pos.has_key(id2):
                merge_list[id2merge_list_pos[id1]].append(id2)
                id2merge_list_pos[id2]=id2merge_list_pos[id1]
            if id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1):
                merge_list[id2merge_list_pos[id2]].append(id1)
                id2merge_list_pos[id1]=id2merge_list_pos[id2]
            if id2merge_list_pos.has_key(id2) \
                   and id2merge_list_pos.has_key(id1)\
                   and id2merge_list_pos[id1]!=id2merge_list_pos[id2]:
                for id in merge_list[id2merge_list_pos[id2]]:
                    if id not in merge_list[id2merge_list_pos[id1]]:
                        merge_list[id2merge_list_pos[id1]].append(id)
                merge_list[id2merge_list_pos[id2]]=[]      
                id2merge_list_pos[id2]=id2merge_list_pos[id1]
            if not id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1) and id1!=id2:
                merge_list.append([id1,id2])
                id2merge_list_pos[id1]=merge_list_count
                id2merge_list_pos[id2]=merge_list_count
                merge_list_count+=1
            j+=1
        i+=1
    return merge_list

def set_list_find_overlaps(lset1,lset2):
    """
    find overlapping L{Set<Set>} instances in the second list
    given in argument according to the first

    @return: a list of overlapping path numbers
    """

    lset1.sort()
    lset2.sort()

    merge_list=[]
    merge_list_count=0

    id2merge_list_pos={}
    
    i=0
    j=0
    while i!= len(lset1):
        while j!= len(lset2) and lset1[i]>lset2[j]\
             and not(lset1[i].overlap(lset2[j])\
                      and lset1[i].isPlusStrand()==lset2[j].isPlusStrand()):
            j+=1
        jj=j
        while jj!= len(lset2) and lset1[i].overlap(lset2[jj])\
                  and lset1[i].isPlusStrand()==lset2[jj].isPlusStrand():
            id1=lset1[i].id
            id2=lset2[jj].id*-1
            if id2merge_list_pos.has_key(id1) \
                   and not id2merge_list_pos.has_key(id2):
                merge_list[id2merge_list_pos[id1]].append(id2)
                id2merge_list_pos[id2]=id2merge_list_pos[id1]
            if id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1):
                merge_list[id2merge_list_pos[id2]].append(id1)
                id2merge_list_pos[id1]=id2merge_list_pos[id2]
            if id2merge_list_pos.has_key(id2) \
                   and id2merge_list_pos.has_key(id1)\
                   and id2merge_list_pos[id1]!=id2merge_list_pos[id2]:
                for id in merge_list[id2merge_list_pos[id2]]:
                    if id not in merge_list[id2merge_list_pos[id1]]:
                        merge_list[id2merge_list_pos[id1]].append(id)
                merge_list[id2merge_list_pos[id2]]=[]      
                id2merge_list_pos[id2]=id2merge_list_pos[id1]                
            if not id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1):
                merge_list.append([id1,id2])
                id2merge_list_pos[id1]=merge_list_count
                id2merge_list_pos[id2]=merge_list_count
                merge_list_count+=1
            jj+=1
        i+=1
    return merge_list

def set_list_find_overlaps_no_strand(lset1,lset2):
    """
    find overlapping L{Set<Set>} instances in the second list
    given in argument according to the first. Coordinates on different strand
    may overlaps

    @return: a list of overlapping path numbers
    """

    lset1.sort()
    lset2.sort()

    merge_list=[]
    merge_list_count=0

    id2merge_list_pos={}
    
    i=0
    j=0
    while i!= len(lset1):
        while j!= len(lset2) and lset1[i]>lset2[j]\
             and not lset1[i].overlap(lset2[j]):
            j+=1
        jj=j
        while jj!= len(lset2) and lset1[i].overlap(lset2[jj]):
            id1=lset1[i].id
            id2=lset2[jj].id*-1
            if id2merge_list_pos.has_key(id1) \
                   and not id2merge_list_pos.has_key(id2):
                merge_list[id2merge_list_pos[id1]].append(id2)
                id2merge_list_pos[id2]=id2merge_list_pos[id1]
            if id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1):
                merge_list[id2merge_list_pos[id2]].append(id1)
                id2merge_list_pos[id1]=id2merge_list_pos[id2]
            if id2merge_list_pos.has_key(id2) \
                   and id2merge_list_pos.has_key(id1)\
                   and id2merge_list_pos[id1]!=id2merge_list_pos[id2]:
                for id in merge_list[id2merge_list_pos[id2]]:
                    if id not in merge_list[id2merge_list_pos[id1]]:
                        merge_list[id2merge_list_pos[id1]].append(id)
                merge_list[id2merge_list_pos[id2]]=[]      
                id2merge_list_pos[id2]=id2merge_list_pos[id1]                
            if not id2merge_list_pos.has_key(id2) \
                   and not id2merge_list_pos.has_key(id1):
                merge_list.append([id1,id2])
                id2merge_list_pos[id1]=merge_list_count
                id2merge_list_pos[id2]=merge_list_count
                merge_list_count+=1
            jj+=1
        i+=1
    return merge_list

def set_list_self_merge_set(lset):
    """
    merges all overlapping L{Set<Set>} instances in a list

    @return: a new list of the merged L{Set<Set>} instances
    """
    lset_merged=[]
    list2merge=set_list_find_self_overlaps(lset)
    idlist=set_list_split(lset)
    for i in list2merge:
        if i==[]:
            continue
        l=[]
        for j in i:
            l.extend(idlist[j])
            del idlist[j]
        set_list_merge(l)
        set_list_changeId(l,min(i))
        lset_merged.extend(l)
    for id,alist in idlist.items():
        lset_merged.extend(alist)
    return lset_merged

def set_list_merge_set(lset1,lset2,max_id=0):
    """
    merges all overlapping L{Set<Set>} instances between two list

    @param lset1,lset2: a set object list of L{Set<pyRepet.coord.Set.Set>}
    instances
    @param max_id: start id value for inserting new
    L{Set<pyRepet.coord.Set.Set>} instances
    @return: a new list of the merged L{Set<Set>} instances
    """
    lset_merged=[]
    list2merge=set_list_find_overlaps(lset1,lset2)
    idlist1=set_list_split(lset1)
    idlist2=set_list_split(lset2)
    if max_id==0:
        max_id=max(idlist1.keys())
    for i in list2merge:
        if i==[]:
            continue
        l=[]
        min_id=max(i)
        for j in i:
            if j>0:
                if min_id>j:
                    min_id=j
                l.extend(idlist1[j])
                del idlist1[j]
            else:
                l.extend(idlist2[j*-1])
                del idlist2[j*-1]

        set_list_merge(l)
        set_list_changeId(l,min_id)
        lset_merged.extend(l)
    for id,alist in idlist1.items():
        lset_merged.extend(alist)
    for id,alist in idlist2.items():
        set_list_changeId(alist,max_id)
        lset_merged.extend(alist)
        max_id+=1
    return lset_merged,max_id

def set_list_add_diff_set(lset1,lset2,max_id=0):
    """
    diff all overlapping L{Set<Set>} lset2 instances
    according to lset1 before inserting lset2 in lset1

    @param lset1,lset2: a set object list of L{Set<pyRepet.coord.Set.Set>}
    instances
    @param max_id: start id value for inserting new
    L{Set<pyRepet.coord.Set.Set>} instances
    @return: a new list of the diff L{Set<Set>} instances
    """
    lset_merged=[]
    list2diff=set_list_find_overlaps_no_strand(lset1,lset2)
    idlist1=set_list_split(lset1)
    idlist2=set_list_split(lset2)
    if max_id==0:
        max_id=max(idlist1.keys())
    for i in list2diff:
        if i==[]:
            continue
        l1=[]
        l2=[]
        min_id=max(i)
        for j in i:
            if j>0:
                if min_id>j:
                    min_id=j
                l1.extend(idlist1[j])
                del idlist1[j]
            else:
                set_list_changeId(idlist2[j*-1],max_id)
                max_id+=1
                l2.extend(idlist2[j*-1])
                del idlist2[j*-1]

        ldiff=set_list_diff(l1,l2)
        lset_merged.extend(l1)
        lset_merged.extend(ldiff)
    for id,alist in idlist1.items():
        lset_merged.extend(alist)
    for id,alist in idlist2.items():
        set_list_changeId(alist,max_id)
        lset_merged.extend(alist)
        max_id+=1
    return lset_merged,max_id

def set_list_sub_set(lset1,lset2,max_id=0):
    """
    sub all overlapping L{Set<Set>} lset1 instances
    according to lset2

    @param lset1,lset2: a set object list of L{Set<pyRepet.coord.Set.Set>}
    instances
    @param max_id: start id value for inserting new
    L{Set<pyRepet.coord.Set.Set>} instances
    @return: a new list of the diff L{Set<Set>} instances
    """
    lset_sub=[]
    list2diff=set_list_find_overlaps_no_strand(lset1,lset2)
    idlist1=set_list_split(lset1)
    idlist2=set_list_split(lset2)
    if max_id==0:
        max_id=max(idlist1.keys())
    for i in list2diff:
        if i==[]:
            continue
        l1=[]
        l2=[]
        min_id=max(i)
        for j in i:
            if j>0:
                if min_id>j:
                    min_id=j
                l1.extend(idlist1[j])
                del idlist1[j]
            else:
                set_list_changeId(idlist2[j*-1],max_id)
                max_id+=1
                l2.extend(idlist2[j*-1])
                del idlist2[j*-1]

        ldiff=set_list_diff(l2,l1)
	lset_sub.extend(ldiff)
    for id,alist in idlist1.items():
        set_list_changeId(alist,max_id)
        lset_sub.extend(alist)
        max_id+=1
    return lset_sub,max_id

def set_list_split_by_name(set_list):
    """
    split a L{Set<Set>} list in several L{Set<Set>}
    list according to the name

    @param set_list: a list of L{Set<Set>} instances
    @return: several set list in a dictionary with the name as key
    """    
    by_name_dict={}
    for i in set_list:
        if by_name_dict.has_key(i.name):
            by_name_dict[i.name].append(i)
        else:
            by_name_dict[i.name]=[i]
    return by_name_dict
