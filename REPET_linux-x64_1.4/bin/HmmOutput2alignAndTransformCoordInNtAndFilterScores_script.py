#!/usr/bin/env python

import user, os, sys, getopt, exceptions
from pyRepetUnit.align.hmmOutputParsing.HmmpfamOutput2align import HmmpfamOutput2align
from pyRepetUnit.align.hmmOutputParsing.HmmscanOutput2align import HmmscanOutput2align
from pyRepetUnit.align.transformAACoordIntoNtCoord.TransformAACoordIntoNtCoordInAlignFormat import TransformAACoordIntoNtCoordInAlignFormat
from pyRepetUnit.commons.utils.FileUtils import FileUtils

#------------------------------------------------------------------------------

def help():

    """
    Give the command-line parameters.
    """

    print ""
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the input file (format='hmmpfam Output' or 'hmmscan Output)"
    print "     -o: name of the output file (default=inFileName+'.align')"
    print "     -T: name of the consensus File (To launch the transformation of aa positions in nt positions and Filter positive score, default=no transformation)"
    print "     -v: verbose (default=0/1/2)"
    print "     -p: name of program (default=hmmpfam, but you can specify hmmscan too)"
    print "     -c: clean"
    print ""

#------------------------------------------------------------------------------

def main():

    inFileName = ""
    outFileName = ""
    verbose = 0
    clean = False
    consensusFileName = ""
    program = "hmmpfam"

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hi:o:T:v:p:c")
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
        elif o == "-o":
            outFileName = a
        elif o == "-T":
            consensusFileName = a
        elif o == "-v":
            verbose = int(a)
        elif o == "-p":
            program = a
        elif o == "-c":
            clean = True
            
    if inFileName == "":
        print "*** Error: missing compulsory options"
        help()
        sys.exit(1)

    if verbose > 0:
        print "beginning of %s" % (sys.argv[0].split("/")[-1])
        sys.stdout.flush()

    if outFileName == "":
        outFileName = "%s.align" % ( inFileName )
    
    if program == "hmmpfam":
        hmmpfamOutput2align = HmmpfamOutput2align( )
        hmmpfamOutput2align.setInputFile( inFileName )
        if consensusFileName == "":
            hmmpfamOutput2align.setOutputFile( outFileName )
        else:
            hmmpfamOutput2align.setOutputFile( outFileName + ".tmp" )
        hmmpfamOutput2align.run( )
    else:
        if program == "hmmscan":
            hmmscanOutput2align = HmmscanOutput2align( )
            hmmscanOutput2align.setInputFile( inFileName )
            if consensusFileName == "":
                hmmscanOutput2align.setOutputFile( outFileName )
            else:
                hmmscanOutput2align.setOutputFile( outFileName + ".tmp" )
            hmmscanOutput2align.run( )
        else:
            print "\nWarning: You must specify a valid program (-p option). Only hmmpfam or hmmscan are supported !\n"
    
    if consensusFileName != "":
        alignTransformation = TransformAACoordIntoNtCoordInAlignFormat()
        alignTransformation.setInFileName( outFileName + ".tmp" )
        alignTransformation.setOutFileName( outFileName )
        alignTransformation.setConsensusFileName( consensusFileName ) 
        alignTransformation.setIsFiltered(True)
        alignTransformation.run()
        os.remove( outFileName + ".tmp" )
        
    
    if clean == True:
        os.remove( inFileName )

    if verbose > 0:
        if FileUtils.isRessourceExists( outFileName ) and not(FileUtils.isEmpty( outFileName )):
            print "%s finished successfully" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()
        else:
            print "warning %s execution failed" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()