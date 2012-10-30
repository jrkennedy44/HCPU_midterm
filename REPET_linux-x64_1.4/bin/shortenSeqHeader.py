#!/usr/bin/env python

import user, os, sys, getopt, exceptions

def setup_env():
    if "REPET_PATH" in os.environ.keys():
        sys.path.append( os.environ["REPET_PATH"] )
setup_env()

import pyRepet.seq.fastaDB

#------------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input fasta file"
    print "     -l: max length of the sequence headers (default=24)"
    print "     -p: pattern (default='seq')"
    print "     -o: name of the output fasta file"
    print "     -L: name of the file recording the link old header - new header (default=inFileName+'.shortHlink')"
    print "     -v: verbose (default=0/1)"
    print ""

#------------------------------------------------------------------------------

def main():

    inFileName = ""
    maxHeaderLgth = "24"
    pattern = "seq"
    outFileName = ""
    linkFileName = ""
    verbose = 0

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hi:l:p:o:L:v:")
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-l":
            maxHeaderLgth = a
        elif o == "-p":
            pattern = a
        elif o == "-o":
            outFileName = a
        elif o == "-L":
            linkFileName = a
        elif o == "-v":
            verbose = int(a)

    if inFileName == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "beginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if linkFileName == "":
        linkFileName = inFileName + ".shortHlink"

    log = pyRepet.seq.fastaDB.shortenSeqHeaders( inFileName, maxHeaderLgth, pattern, outFileName, linkFileName )
    if log != 0:
        print "*** Error: shortenSeqHeaders() returned %i" % ( log )
        sys.exit(1)

    if verbose > 0:
        print "%s finished successfully" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
