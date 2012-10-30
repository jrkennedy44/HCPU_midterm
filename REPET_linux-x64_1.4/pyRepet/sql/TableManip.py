import os, sys

import pyRepet.sql.RepetDB
import pyRepet.sql.TableAdaptator
import pyRepet.coord.Map
import pyRepet.coord.Set
import pyRepet.coord.Path

#-----------------------------------------------------------------------------

def add_table( db, inTable, outTable, table_type, insert_type, rename, verbose=0 ):

    if table_type == "set":
        srcTableAdaptator = pyRepet.sql.TableAdaptator.TableSetAdaptator( db, inTable )
    elif table_type == "path":
        srcTableAdaptator = pyRepet.sql.TableAdaptator.TablePathAdaptator( db, inTable )
    elif table_type == "map":
        srcTableAdaptator = pyRepet.sql.TableAdaptator.TableMapAdaptator( db, inTable )
    else:
        print "*** Error: table type %s not implemented" % ( table_type )
        sys.exit(1)

    rename_type = rename
    name = ""
    if rename.find("=") != -1:
        rename_type, name = rename.split("=")
    else:
        if rename_type != "split" and rename_type != "":
            print "*** Error: rename type",rename_type, "not implemented"
            sys.exit(1)

    tmp_filename = outTable+".tmp"+str(os.getpid())+"-"+inTable

    destTableAdaptator = pyRepet.sql.TableAdaptator.TableSetAdaptator( db, outTable )

    if not db.exist( outTable ):
        lContigs = srcTableAdaptator.getContig_name()

        for c in lContigs:
            if verbose > 0:
                print "contig %s:" % ( c )
                print "get set list from %s" % ( inTable )
                sys.stdout.flush()
            slist = srcTableAdaptator.getSetList_from_contig( c )
            if verbose > 1:
                print "\tsrc",len(slist)
            if insert_type == "merge":
                if verbose > 1:
                    print "\tmerge set list"
                slist = pyRepet.coord.Set.set_list_self_merge_set( slist )
                if verbose > 1:
                    print "\tmerged",len(slist)
            elif insert_type == "add":
                if verbose > 1:
                    print "\tadd set list"
                    print "\tadded",len(slist)
            elif insert_type == "diff" or  insert_type == "sub":
                print "*** Error: %s not possible when destination table is created" % ( insert_type )
                sys.exit(1)
            else:
                print "*** Error: insert type %s not implemented" % ( insert_type )
                sys.exit(1)
            if rename_type == "prefix":
                for i in slist:
                    i.name = name + i.name
            elif rename_type == "replace":
                for i in slist:
                    i.name = name
            elif rename_type == "split":
                for i in slist:
                    i.name = i.name.split()[0]
            elif rename_type == "":
                pass
            slist = pyRepet.coord.Set.set_list_remove_doublons( slist )
            if verbose > 1:
                print "\twrite set"
            pyRepet.coord.Set.set_list_write( slist, tmp_filename, "a" )

        if verbose > 1:
            print "create destination table"
        db.create_set( outTable, tmp_filename )
        os.system( "rm -f " + tmp_filename )
        return


    rename_type = rename
    name = ""
    if rename.find("=") !=- 1:
        rename_type, name = rename.split("=")
    else:
        if rename_type != "split" and rename_type != "":
            print "*** Error: rename type",rename_type, "not implemented"
            sys.exit(1)

    contigs_src = srcTableAdaptator.getContig_name()
    contigs_dest = destTableAdaptator.getContig_name()
    newid = destTableAdaptator.getNewId()
    for c in contigs_src:
        if verbose > 0:
            print "contig",c,": \n\tget set from",inTable
        slist = srcTableAdaptator.getSetList_from_contig(c)
        if rename_type == "prefix":
            for i in slist:
                i.name=name+i.name
        elif rename_type == "replace":
            for i in slist:
                i.name=name
        elif rename_type == "split":
            for i in slist:
                i.name=i.name.split()[0]
        elif rename_type == "":
            pass
        if verbose > 1:
            print "\tsrc",len(slist)
        dlist = destTableAdaptator.getSetList_from_contig( c )
        if verbose > 1:
            print "\tdest",len(dlist)
        if len(dlist) > 0:
            contigs_dest.remove( c )
        if insert_type == "merge":
            if verbose > 1:
                print "\tmerge set list"
            slist = pyRepet.coord.Set.set_list_self_merge_set( slist )
            mlist, newid = pyRepet.coord.Set.set_list_merge_set( dlist, slist, newid )
            if verbose > 1:
                print "\tmerged",len(mlist)
        elif insert_type == "add":
            if verbose > 1:
                print "\tadd set list"
            mlist, newid = pyRepet.coord.Set.set_list_add_set( dlist, slist, newid )
            if verbose > 1:
                print "\tadded",len(mlist)
        elif insert_type == "diff":
            if verbose > 1:
                print "\tdiff set list"
            mlist, newid = pyRepet.coord.Set.set_list_add_diff_set( dlist, slist, newid )
            if verbose > 1:
                print "\tdiff'ed'",len(mlist)
        elif insert_type == "sub":
            if verbose > 1:
                print "\tsub set list"
            mlist, newid = pyRepet.coord.Set.set_list_sub_set( dlist, slist, newid )
            if verbose > 1:
                print "\tsub'ed'",len(mlist)
        else:
            print "*** Error: insert type",insert_type,"not implemented"
            sys.exit(1)
        mlist = pyRepet.coord.Set.set_list_remove_doublons( mlist )
        if verbose > 1:
            print "\twrite set"
        pyRepet.coord.Set.set_list_write( mlist, tmp_filename, "a" )

    if verbose > 0:
        print "write remaining dest contigs",contigs_dest
    for c in contigs_dest:
        if verbose > 1:
            print "remain contig",c,": \n\tget set list"
        dlist = destTableAdaptator.getSetList_from_contig(c)
        idlist = pyRepet.coord.Set.set_list_split(dlist)
        lset_merged = []
        for id,alist in idlist.items():
            if rename_type=="prefix":
                for i in alist:
                    i.name=name+i.name
            elif rename_type=="replace":
                for i in alist:
                    i.name=name
            elif rename_type=="split":
                for i in alist:
                    i.name=i.name.split()[0]
            elif rename_type=="":
                pass            
            pyRepet.coord.Set.set_list_changeId( alist, newid )
            alist = pyRepet.coord.Set.set_list_remove_doublons( alist )
            lset_merged.extend( alist )
            newid += 1
        if verbose > 1:
            print "\twrite set"
        pyRepet.coord.Set.set_list_write( lset_merged, tmp_filename, "a" )

    if verbose > 0:
        print "create destination table"
    db.create_set(outTable,tmp_filename)
    os.system("rm -f "+tmp_filename)

#-----------------------------------------------------------------------------

def manip_table(db,qtable,stable,rtable,qtable_type,stable_type,operation):

    if qtable_type=="set":
        qTableAdaptator=pyRepet.sql.TableAdaptator.TableSetAdaptator(db,qtable)
    elif qtable_type=="path":
        qTableAdaptator=pyRepet.sql.TableAdaptator.TablePathAdaptator(db,qtable)
    elif qtable_type=="map":
        qTableAdaptator=pyRepet.sql.TableAdaptator.TableMapAdaptator(db,qtable)
    else:
        print qtable_type, "not implemented"
        sys.exit()

    if stable_type=="set":
        sTableAdaptator=pyRepet.sql.TableAdaptator.TableSetAdaptator(db,stable)
    elif stable_type=="path":
        sTableAdaptator=pyRepet.sql.TableAdaptator.TablePathAdaptator(db,stable)
    elif stable_type=="map":
        sTableAdaptator=pyRepet.sql.TableAdaptator.TableMapAdaptator(db,stable)
    elif stable_type=="NA":
	pass	
    else:
        print stable_type, "not implemented"
        sys.exit()
        
    tmp_filename=rtable+".tmp"+str(os.getpid())+"-"+qtable
    
    contigs_q=qTableAdaptator.getContig_name()
    for c in contigs_q:
        print "contig",c,": \n\tget set from",qtable
        qlist=qTableAdaptator.getSetList_from_contig(c)
        print "\tquery",len(qlist)
	if stable!="":
            slist=sTableAdaptator.getSetList_from_contig(c)
            print "\tsubject",len(slist)
        if operation=="merge": #merge binary operator
            print "\tmerge set list"
            mlist=pyRepet.coord.Set.set_list_self_merge_set(qlist)
	    if stable!="":
            	mlist,newid=pyRepet.coord.Set.set_list_merge_set(mlist,slist)
            print "\tmerged",len(mlist)
        elif operation=="merge-self": #merge unary operator
	    if qtable_type=="map" or qtable_type=="path":
       		print qtable_type, "not implemented"
        	sys.exit(1)
            print "\tmerge set list"
            mlist=pyRepet.coord.Set.set_list_self_merge_set(qlist)
            print "\tmerged",len(mlist)
	elif operation=="range":
		if qtable_type=="map":
       			print qtable_type, "not implemented"
        		sys.exit(1)
		if qtable_type=="path":
			db.path2path_range(qtable)
		if qtable_type=="set":
			db.set2set_range(qtable)
		return
			
        elif operation=="add":
            print "\tadd set list"
            mlist,newid=pyRepet.coord.Set.set_list_add_set(qlist,slist)
            print "\tadded",len(mlist)
        elif operation=="sub":
            print "\tsub set list"
            mlist,newid=pyRepet.coord.Set.set_list_sub_set(qlist,slist)
            print "\tsub'ed'",len(mlist)
        else:
            print "operation type:",operation,"not implemented!"
            sys.exit()
        mlist=pyRepet.coord.Set.set_list_remove_doublons(mlist)
        print "\twrite set"
        pyRepet.coord.Set.set_list_write(mlist,tmp_filename,"a")

    print "create destination table"
    if rtable=="" and operation=="merge-self":
	rtable=qtable+"_merged"	
    elif rtable=="":
	print "no name given to output table"
        sys.exit(1)	
    db.create_set(rtable,tmp_filename)
    os.system("rm -f "+tmp_filename)

#-----------------------------------------------------------------------------
