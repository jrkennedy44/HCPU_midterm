#!/usr/bin/env python

import user, os, sys, getopt, exceptions
import pyRepetUnit.fastaTranslation.allFrames.TranslateInAllFramesAndReplaceStopByX
from pyRepet.seq.Bioseq import *
from pyRepet.util.file.FileUtils import *

#------------------------------------------------------------------------------

def help():

    """
    Give the command-line parameters.
    """

    print ""
    print "usage: ",sys.argv[0],"[ options ]"
    print "options:"
    print "     -h: this help"
    print "     -i: name of the nucleotidic input file (format='fasta')"
    print "     -o: name of the output file (default=inFileName+'_aa')"
    print "     -v: verbose (default=0/1/2)"
    print "     -c: clean"
    print ""

#------------------------------------------------------------------------------

def main():

    inFileName = ""
    outFileName = ""
    verbose = 0
    clean = False

    try:
        opts,args=getopt.getopt(sys.argv[1:],"hi:o:v:c")
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
        elif o == "-v":
            verbose = int(a)
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
        outFileName = "%s_aa" % ( inFileName )
    
    TranslateInAllFramesAndReplaceStopByX = pyRepetUnit.fastaTranslation.allFrames.TranslateInAllFramesAndReplaceStopByX.TranslateInAllFramesAndReplaceStopByX( )
    TranslateInAllFramesAndReplaceStopByX.setInputFile( inFileName )
    TranslateInAllFramesAndReplaceStopByX.setOutputFile( outFileName )
    TranslateInAllFramesAndReplaceStopByX.run( )
    
    if clean == True:
        os.remove( inFileName )

    if verbose > 0:
        fileUtils = FileUtils( )
        if fileUtils.isRessourceExists( outFileName ) and not(fileUtils.isFileEmpty( outFileName )):
            print "%s finished successfully" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()
        else:
            print "warning %s execution failed" % (sys.argv[0].split("/")[-1])
            sys.stdout.flush()

    return 0

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()