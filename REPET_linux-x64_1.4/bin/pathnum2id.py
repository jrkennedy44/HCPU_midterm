#!/usr/bin/env python

import os
import sys
import getopt

def setup_env():
    if "REPET_PATH" in os.environ.keys():
        sys.path.append( os.environ["REPET_PATH"] )
    else:
        print "*** Error: no environment variable REPET_PATH ***"
        sys.exit(1)
setup_env()

from pyRepetUnit.commons.parsing.PathNum2Id import PathNum2Id

#-----------------------------------------------------------------------------

def help():

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "option:"
    print "    -h: this help"
    print "    -i: input file name (path format)"
    print "    -o: output file name (path format, default=inFileName+'.path')"
    print ""

#-----------------------------------------------------------------------------

def main():

    inFileName = ""
    outFileName = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:o:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-o":
            outFileName = a

    if inFileName == "":
        print "*** Error: missing input file name"
        help()
        sys.exit(1)

    if outFileName == "":
        outFileName = inFileName + ".path"
        
    pathNum2Id = PathNum2Id()
    pathNum2Id.setInFileName( inFileName )
    pathNum2Id.setOutFileName( outFileName )
    pathNum2Id.run()

    return 0

#-----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
