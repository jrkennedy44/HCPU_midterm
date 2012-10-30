#!/usr/bin/env python

import user, os, sys, getopt, exceptions, logging

if not "REPET_PATH" in os.environ.keys():
    print "*** Error: no environment variable REPET_PATH"
    sys.exit(1)
sys.path.append( os.environ["REPET_PATH"] )

#-----------------------------------------------------------------------------

def help():

    """
    Give the list of the command-line options.
    """

    print
    print "usage:",sys.argv[0]," [ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format=map)"
    print "     -c: clean"
    print "     -v: verbose (default=0/1)"
    print

#-----------------------------------------------------------------------------

def main():

    """
    This program merges ranges, i.e. coordinates of matches, and compute the cumulative coverage of these matches.
    """

    inFileName = ""
    clean = False
    verbose = 0
 
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hi:cv:")
    except getopt.GetoptError, err:
        print str(err)
        help()
        sys.exit(1)
    for o,a in opts:
        if o == "-h":
            help()
            sys.exit(0)
        elif o == "-i":
            inFileName = a
        elif o == "-c":
            clean = True
        elif o == "-v":
            verbose = int(a)
  
    if  inFileName == "":
        print "*** Error: missing input file name"
        help()
        sys.exit(1)

    if verbose > 0:
        print "\nbeginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    # create the 'log' file
    logFileName = "%s_cumulLength.log" % ( inFileName )
    if os.path.exists( logFileName ):
        os.remove( logFileName )
    handler = logging.FileHandler( logFileName )
    formatter = logging.Formatter( "%(asctime)s %(levelname)s: %(message)s" )
    handler.setFormatter( formatter )
    logging.getLogger('').addHandler( handler )
    logging.getLogger('').setLevel( logging.DEBUG )
    logging.info( "started" )

    # merge the ranges
    logging.info( "merge the matches with mapOp" )
    prg = os.environ["REPET_PATH"] + "/bin/mapOp"
    cmd = prg
    cmd += " -q %s" % ( inFileName )
    cmd += " -m"
    log = os.system( cmd )
    if log != 0:
        print "*** Error: %s returned %i" % ( prg, log )
        sys.exit(1)

    # compute the cumulative length
    logging.info( "compute the cumulative length of the matches" )
    mergeFile = open( inFileName + ".merge", "r" )
    total = 0
    line = mergeFile.readline()
    while True:
        if line == "":
            break
        line = line.split("\t")
        if int(line[2]) < int(line[3]):
            total += int(line[3]) - int(line[2]) + 1
        elif int(line[2]) > int(line[3]):
            total += int(line[2]) - int(line[3]) + 1
        line = mergeFile.readline()
    if clean == True:
        os.remove( inFileName + ".merge" )

    # return the total
    string = "cumulative length = %i bp" % ( total )
    logging.info( string )
    if verbose > 0:
        print string

    logging.info( "finished" )

    if verbose > 0:
        print "%s finished successfully\n" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    return 0

#----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
