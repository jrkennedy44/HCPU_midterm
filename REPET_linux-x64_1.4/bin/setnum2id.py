#!/usr/bin/env python

import os
import sys
import getopt
import exceptions

#-----------------------------------------------------------------------------

def help():

        print "\nusage:",sys.argv[0]," [ options ]"
        print "option:"
        print "    -h: this help"
        print "    -i: input set file"
        print "output on stdout\n"

#-----------------------------------------------------------------------------

def main():

    inFileName = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        if o == "-i":
            inFileName = a

    if inFileName == "":
        print "*** Error: missing input file name"
        help()
        sys.exit(1)

    inFile = open( inFileName, "r" )
    line = inFile.readline()

    dID2count = {}
    count = 1

    while 1:

        if line == "":
            break

        line = line.split()

        path = line[0]
        sbjName = line[1]
        qryName = line[2]
        qryStart = line[3]
        qryEnd = line[4]

        key_id = path + "-" + qryName + "-" + sbjName
        if key_id not in dID2count.keys():
	    newPath = count
	    count += 1
	    dID2count[ key_id ] = newPath
	else:
	    newPath = dID2count[ key_id ]

        data = str(newPath) + "\t" + sbjName + "\t" + qryName + "\t"
        data += qryStart + "\t" + qryEnd

        print data
        sys.stdout.flush()

        line = inFile.readline()

    inFile.close()

    return 0

#-----------------------------------------------------------------------------

if __name__ == '__main__':
	main()
