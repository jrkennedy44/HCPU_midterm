#!/usr/bin/env python

import user, os, sys, getopt, ConfigParser
from os import listdir

def setup_env():
    if "REPET_PATH" in os.environ.keys():
        sys.path.append( os.environ["REPET_PATH"] )
    else:
        print "*** Error: no environment variable REPET_PATH ***"
        sys.exit(1)
setup_env()

from pyRepet.sql.RepetDB import *
from pyRepet.gamexml.Xml_writer import *
from pyRepet.gamexml.computational import *

#------------------------------------------------------------------------------

def help():

    print ""
    print "usage:",sys.argv[0],"[options]"
    print "options:"
    print "     -h: this help"
    print "     -f: fasta file (required to generate new '.gamexml' files)"
    print "     -n: annotation tier_name"
    print "     -g: gamexml file (for Apollo). If it's not mentionned, all '.gamexml' files will be updated with the result file"
    print "     -l: light gameXML file (without sequence)"
    print "     -r: result files (require -n)"
    print "     -R: reverse the query and subject of Blaster results"
    print "     -s: tier_name of an annotation to remove from a gameXML file"
    print "     -t: file of table name to use to create the gamexml files (tier name 'tab' format 'tab' table name)"
    print "     -c: configuration file from TEdenovo or TEannot pipeline"
    print "     -H: MySQL host (if no configuration file)"
    print "     -U: MySQL user (if no configuration file)"
    print "     -P: MySQL password (if no configuration file)"
    print "     -D: MySQL database (if no configuration file)"
    print "     -v: verbose (default=0/1/2)"
    print ""

#------------------------------------------------------------------------------

def automatisation( result_file, tier_name, reverse, comput ):

    if verbose > 1:
        print "Auto update"; sys.stdout.flush()
    writer = Xml_writer()
    file_liste = []
    liste_comp = []
    liste_comp = listdir('./')

    if result_file != "":
        for j in liste_comp:
            if writer.file_in_keys( j, comput ):
                file_liste = file_liste + [j]

        for i in file_liste:
            writer.update_gamexml( i, result_file, tier_name, comput )

    else:
        for j in liste_comp:
            if j.find( "gamexml" ) != -1:
                writer.parse_gamexml( j )
                writer.verif_name_prog( tier_name )
                writer.write( j )
                if verbose > 1:
                    print tier_name + " program from " +j +" removed"

#------------------------------------------------------------------------------

def main():

    f_result = ""
    f_gamexml = ""
    f_fasta = ""
    f_table = ""
    tier_name = ""
    substract_name = ""
    no_seq = 0
    configFileName = ""
    host = ""
    user = ""
    passwd = ""
    dbname = ""
    verbose = 0

    try:
        options,arguments=getopt.getopt(sys.argv[1:],"hn:f:g:r:s:lRt:c:H:U:P:D:v:",["help","tier_name=","fasta","gamexml","result","substract_program","light","reverse_result","table"])
    except getopt.GetoptError:
        help()
        sys.exit(1)
    if options == []:
        help()
        sys.exit(1)
    for o,a in options:
        if o == "-h" or o == "--help":
            help()
            sys.exit(0)
        elif o == "-f" or o == "--fasta":
            f_fasta = a
        elif o == "-g" or o == "--gamexml":
            f_gamexml = a 
        elif o == "-n" or o == "--tier_name":
            tier_name = a
        elif o == "-r" or o == "--result":
            f_result = a
        elif o == "-s" or o == "--subtract_program":
            substract_name = a
        elif o == "-l" or o == "--light":
            no_seq = 1
        elif o == "-R" or o == "--reverse_result":
            writer.set_reverse()
        elif o == "-t" or o == "--table":
            f_table = a
        elif o == "-c":
            configFileName = a
        elif o == "-H":
            host = a
        elif o == "-U":
            user = a 
        elif o == "-P":
            passwd = a
        elif o == "-D":
            dbname = a
        elif o == "-v":
            verbose = int(a)

    if tier_name == "" and substract_name == "" and f_result != "":
        print "*** Error: option -n required"
        help()
        sys.exit(1)

    if f_fasta == "" and f_gamexml == "":
        print "*** Error: options -g or -f required"
        help()
        sys.exit(1)
    
    if substract_name!="" and f_result!="" :
        print "Error: option -s and -r together"
        help()
        sys.exit(1)


    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if configFileName != "":
        config = ConfigParser.ConfigParser()
        config.readfp( open(configFileName) )
        host = config.get("repet_env","repet_host")
        user = config.get("repet_env","repet_user")
        passwd = config.get("repet_env","repet_pw")
        dbname = config.get("repet_env","repet_db")

    if host == "" and os.environ.get( "REPET_HOST" ) != None:
        host = os.environ.get( "REPET_HOST" )
    if user == "" and os.environ.get( "REPET_USER" ) != None:
        user = os.environ.get( "REPET_USER" )
    if passwd == "" and os.environ.get( "REPET_PW" ) != None:
        passwd = os.environ.get( "REPET_PW" )
    if dbname == "" and os.environ.get( "REPET_DB" ) != None:
        dbname = os.environ.get( "REPET_DB" )

    writer = Xml_writer()

    # create the dico
    comput = computational()

    # create all the ".gamexml" files (option '-f')
    if f_fasta != "":
        writer.create_gamexml( f_fasta, f_result, tier_name, comput, no_seq )

    # 
    if f_result != "":
       if f_gamexml != "":
           key = ".".join( f_gamexml.split(".")[:-1] )
       else:
           key = ""
       format = writer.find_type_file( f_result )
       resFile = open( f_result )
       if format == "path":
	       comput.load_dico_path_from_file( key, f_result )

    if f_table != "":
            if verbose > 1:
                print "parsing file %s... " % ( f_gamexml ); sys.stdout.flush()
	    writer.parse_gamexml( f_gamexml )

	    if f_gamexml != "":
##                key=".".join(f_gamexml.split(".")[:-1])
                key = f_gamexml.split(".")[0]
	    else:
                key = ""

	    tfile = open( f_table )
	    lines = tfile.readlines()
	    for l in lines:
                if l[0] == "#":
                    continue
                tok = l.split()
                #print tok
                if len(tok) == 0:
                    break
                tier_name = tok[0]
                format = tok[1]
                table = tok[2]
                alias = ""
                if verbose > 1:
                    print "table: " + table + " (format=" + format + ")"
                if len(tok) > 3:
                    alias = tok[3]
                    if verbose > 1:
                        print " alias=" + alias

                if host == "" or user == "" or passwd == "" or dbname == "":
                    print "*** Error: missing information about MySQL connection"
                    sys.exit(1)
                db = RepetDB( user, host, passwd, dbname )

                if format == "path":
                    comput.load_dico_path_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "rpath":
                    comput.load_dico_rpath_from_table( db, key, table, alias )
                elif format == "ipath":
                    comput.load_dico_ipath_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "align":
                    comput.load_dico_align_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "map":
                    comput.load_dico_map_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "rmap":
                    comput.load_dico_rmap_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "set":
                    comput.load_dico_set_from_table( db, key, table, alias )
                    writer.update_gamexml_comput( tier_name, comput )
                elif format == "annot":
                    comput.load_dico_annot_from_table( db, key, table, alias )
                    writer.update_gamexml_annot( table, comput )
                elif format == "annot_set":
                    comput.load_dico_annotset_from_table( db, key, table, alias )
                    writer.update_gamexml_annot( table, comput )
                else:
                    print "*** Error: unknown format '%s'" % ( format )
                    sys.exit(1)
            writer.write(f_gamexml)

            db.close()

    # 
    if f_gamexml == "" and f_result != "" and f_fasta == "":
        automatisation( f_result, tier_name, writer.get_reverse(), comput )

    # update a ".gamexml" file (options '-g' and '-t')
    if f_gamexml != "" and f_result != "":
        writer.update_gamexml( f_gamexml, f_result, tier_name, comput )

    # remove a comput
    if substract_name != "" and tier_name == "":
        if f_gamexml != "":
            writer.parse_gamexml( f_gamexml )
            writer.verif_name_prog( substract_name )
            writer.write( f_gamexml )
            if verbose > 1:
                print substract_name + " program from " + f_gamexml +" removed"
        else:
            automatisation( "", substract_name, 0, None )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
