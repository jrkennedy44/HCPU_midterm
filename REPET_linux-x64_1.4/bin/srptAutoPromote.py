#!/usr/bin/env python

import sys
import getopt
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepet.sql.TableManip import add_table

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "option:"
    print "    -h: this help"
    print "    -f: name of the file in which are recorded tables and commands."
    print "         Structure of the command file:"
    print "          one line per command, each field seperated by one tabulation."
    print "         Fields in column order:"
    print "         <table_name>: Name of the table to insert"
    print "         <table_type>: Type of the table. Values=[path|set]"
    print "         <insert_type>: insertion type.Values=[merge|diff|add|sub]"
    print "         <rename_type>=<new_name>: Change name before insertion."
    print "           Rename type values=[prefix|replace|split]"
    print "    -o: name of the output table ('set' format)"
    print "     -v: verbose (default=0/1/2)"
    print ""

#-----------------------------------------------------------------------------

def main():

    cmdFileName = ""
    outTable = ""
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hf:o:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(1)
        elif o == "-f":
            cmdFileName = a
        elif o == "-o":
            outTable = a
        elif o == "-v":
            verbose = int(a)

    if cmdFileName == "" or outTable == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    db = DbMySql()

    db.dropTable( outTable, verbose - 1 )

    cmdFile = open( cmdFileName )
    lines = cmdFile.readlines()
    cmdFile.close()

    # for each input table
    for l in lines:

        rename = ""
        tok = l[:-1].split("\t")
        if len(tok) == 3:
            inTable, inTable_type, insert_type = tok  
        elif len(tok) == 4:
            inTable, inTable_type, insert_type, rename = tok
        else:
            print "*** Error when parsing '%s', found %d tokens in line '%s'" % ( cmdFileName, len(tok), l )
            sys.exit(1)

        if inTable[0] == "#":
            continue

        string = "table %s (type:%s) added to %s --> operation:%s" % ( inTable, inTable_type, outTable, insert_type )
        if rename != "":
            string += " rename:%s" % ( rename )
        if verbose > 1:
            print string; sys.stdout.flush()

        add_table( db, inTable, outTable, inTable_type, insert_type, rename, verbose - 1 )

    db.dropTable( outTable + "_bin", verbose - 1 )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
