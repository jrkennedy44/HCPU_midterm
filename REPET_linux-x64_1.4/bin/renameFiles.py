#!/usr/bin/env python

import user, os, sys, getopt, exceptions, logging, glob, ConfigParser, re, shutil

if not os.environ.has_key( "REPET_PATH" ):
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )


#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print ""
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: input extension"
    print "     -o: output extension"
    print "     -l: files to rename (default='*')"
    print "     -v: verbose (default=0/1/2)"
    print ""

#-----------------------------------------------------------------------------

def main():

    """
    This program takes a list of files for which the extension needs to be changed.
    """

    inExtension = ""
    outExtension = ""
    patternSuffix = "*"
    global verbose
    verbose = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:],"h:i:o:l:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inExtension = a
        elif o == "-o":
            outExtension = a
        elif o == "-l":
            patternSuffix = a
        elif o == "-v":
            verbose = int(a)

    if  inExtension == "" or outExtension == "" or  patternSuffix == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    lFiles = glob.glob( "%s" %(patternSuffix))

    if verbose > 0:
        print "nb of files: %s" % len((lFiles))

    for inFileName in lFiles:
        
        if os.path.exists(inFileName):
            
            newName = re.sub(inExtension, outExtension, inFileName)
            if verbose > 1:
                print "Change : %s to %s " %(inFileName, newName)
            os.system( "mv \""+inFileName+"\" "+newName )
        
    if verbose > 0:
        print "%s finished successfully" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
