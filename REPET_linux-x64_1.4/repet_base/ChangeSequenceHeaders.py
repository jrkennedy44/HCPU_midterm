#!/usr/bin/env python

# Copyright INRA (Institut National de la Recherche Agronomique)
# http://www.inra.fr
# http://urgi.versailles.inra.fr
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.


import os
import sys
import getopt

from pyRepetUnit.commons.coord.Align import Align
from pyRepetUnit.commons.coord.Path import Path
from pyRepetUnit.commons.coord.Match import Match


class ChangeSequenceHeaders( object ):
    
    def __init__( self ):
        self._name = "ChangeSequenceHeaders"
        self._inFile = ""
        self._format = ""
        self._step = 0
        self._prefix = "seq"
        self._linkFile = ""
        self._outFile = ""
        self._verbose = 0
        
        
    def help( self ):
        print
        print "usage: %s.py [ options ]" % ( self._name )
        print "options:"
        print "     -h: this help"
        print "     -i: name of the input file"
        print "     -f: format of the input file (fasta/newick/align/path/tab)"
        print "     -s: step (1: shorten headers / 2: retrieve initial headers)"
        print "     -p: prefix of new headers (with '-s 1', default='seq')"
        print "     -l: name of the 'link' file (with '-s 2', format=map)"
        print "     -o: name of the output file (default=inFile+'.newH'/'.initH')"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:f:s:p:l:o:v:")
        except getopt.GetoptError, err:
            sys.stderr.write( "%s\n" % ( str(err) ) )
            self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self.setInputFile( a )
            elif o == "-f":
                self.setFormat( a )
            elif o == "-s":
                self.setStep( a )
            elif o == "-p":
                self.setPrefix( a )
            elif o == "-l":
                self.setLinkFile( a )
            elif o == "-o":
                self.setOutputFile( a )
            elif o == "-v":
                self.setVerbosityLevel( a )
                
                
    def setInputFile( self, inFile ):
        self._inFile = inFile
        
    def setFormat( self, format ):
        self._format = format
        
    def setPrefix( self, prefix ):
        self._prefix = prefix
        
    def setStep( self, step ):
        self._step = int(step)
        
    def setLinkFile( self, linkFile ):
        self._linkFile = linkFile
        
    def setOutputFile( self, outFile ):
        self._outFile = outFile
        
    def setVerbosityLevel( self, verbose ):
        self._verbose = int(verbose)
        
        
    def checkAttributes( self ):
        if self._inFile == "":
            sys.stderr.write( "ERROR: missing input file name (-i)\n" )
            self.help(); sys.exit(1)
        if not os.path.exists( self._inFile ):
            sys.stderr.write( "ERROR: input file doesn't exist (-i)\n" )
            self.help(); sys.exit(1)
        if self._format not in ["fasta","newick","align","path","tab"]:
            sys.stderr.write( "ERROR: unrecognized format '%s' (-f)\n" )
            self.help(); sys.exit(1)
        if self._step not in [1,2]:
            sys.stderr.write( "ERROR: missing step (-s)\n" )
            self.help(); sys.exit(1)
        if self._step == 1 and self._prefix == "":
            sys.stderr.write( "ERROR: missing prefix (-p)\n" )
            self.help(); sys.exit(1)
        if self._step == 2:
            if self._linkFile == "":
                sys.stderr.write( "ERROR: missing link file name (-l)\n" )
                self.help(); sys.exit(1)
            if not os.path.exists( self._linkFile ):
                sys.stderr.write( "ERROR: link file doesn't exist (-l)\n" )
                self.help(); sys.exit(1)
        if self._outFile == "":
            if self._step == 1:
                self._outFile = "%s.newH" % ( self._inFile )
            elif self._step == 2:
                self._outFile = "%s.initH" % ( self._inFile )
                
                
    def shortenSequenceHeadersForFastaFile( self ):
        if self._verbose > 0:
            print "shorten sequence headers for fasta file..."
            sys.stdout.flush()
            if self._verbose > 1:
                print "save sequences in '%s'"  %( self._outFile )
        inFileHandler = open( self._inFile, "r" )
        linkFileHandler = open( self._linkFile, "w" )
        outFileHandler = open( self._outFile, "w" )
        countSeq = 0
        lengthSeq = 0
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                countSeq += 1
                newHeader = "%s%i" % ( self._prefix, countSeq )
                if self._verbose > 1:
                    print "initial '%s' -> new '%s'" % ( line[1:-1], newHeader )
                outFileHandler.write( ">%s\n" % ( newHeader ) )
                if lengthSeq != 0:
                    linkFileHandler.write( "\t%i\t%i\n" % ( 1, lengthSeq ) )
                    lengthSeq = 0
                linkFileHandler.write( "%s\t%s" % ( newHeader, line[1:-1] ) )
            else:
                lengthSeq += len( line.replace("\n","") )
                outFileHandler.write( line )
        linkFileHandler.write( "\t%i\t%i\n" % ( 1, lengthSeq ) )
        inFileHandler.close()
        linkFileHandler.close()
        outFileHandler.close()
        if self._verbose > 0:
            print "nb of sequences: %i" % ( countSeq )
            
            
    def getLinksNewToInitialHeaders( self ):
        if self._verbose > 0:
            print "retrieve the links new->initial headers"
            sys.stdout.flush()
        dNew2Init = {}
        linkFileHandler = open( self._linkFile,"r" )
        while True:
            line = linkFileHandler.readline()
            if line == "":
                break
            tokens = line.split("\t")
            if len(tokens) == 4:
                dNew2Init[ tokens[0] ] = tokens[1]
            elif len(tokens) == 2:
                dNew2Init[ tokens[0] ] = tokens[1].split("\n")[0]
            else:
                sys.stderr.write( "ERROR: link file is badly formatted\n" )
                sys.exit(1)
        linkFileHandler.close()
        if self._verbose > 0: print "nb of links: %i" % ( len(dNew2Init.keys()) ); sys.stdout.flush()
        return dNew2Init
    
    
    def retrieveInitialSequenceHeadersForFastaFile( self, dNew2Init ):
        if self._verbose > 0:
            print "retrieve initial headers for fasta file"
            sys.stdout.flush()
        inFileHandler = open( self._inFile, "r" )
        outFileHandler = open( self._outFile, "w" )
        countSeq = 0
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0] == ">":
                countSeq += 1
                newHeader = dNew2Init[ line[1:-1] ]
                outFileHandler.write( ">%s\n" % ( newHeader ) )
            else:
                outFileHandler.write( line )
        inFileHandler.close()
        outFileHandler.close()
        if self._verbose > 0:
            print "nb of sequences: %i" % ( countSeq )
            
            
    def retrieveInitialSequenceHeadersForNewickFile( self, dNew2Init ):
        inF = open( self._inFile, "r" )
        lines = inF.readlines()
        inF.close()
        line = "".join(lines)   #.replace(";","").replace("\n","")
        outF = open( self._outFile, "w" )
        for newH in dNew2Init.keys():
            line = line.replace( newH+":", dNew2Init[newH].replace(" ","_").replace("::","-").replace(":","-").replace(",","-")+":" )
        outF.write( line )
        outF.close()
        
        
    def retrieveInitialSequenceHeadersForAlignFile( self, dNew2Init ):
        inFileHandler = open( self._inFile, "r" )
        outFileHandler = open( self._outFile, "w" )
        a = Align()
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            a.setFromTuple( line.split("\t") )
            nameToBeReplaced = a.range_query.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                a.range_query.seqname = dNew2Init[ nameToBeReplaced ]
            nameToBeReplaced = a.range_subject.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                a.range_subject.seqname = dNew2Init[ nameToBeReplaced ]
            a.write( outFileHandler )
        inFileHandler.close()
        outFileHandler.close()
        
        
    def retrieveInitialSequenceHeadersForPathFile( self, dNew2Init ):
        inFileHandler = open( self._inFile, "r" )
        outFileHandler = open( self._outFile, "w" )
        p = Path()
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            p.setFromTuple( line.split("\t") )
            nameToBeReplaced = p.range_query.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                p.range_query.seqname = dNew2Init[ nameToBeReplaced ]
            nameToBeReplaced = p.range_subject.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                p.range_subject.seqname = dNew2Init[ nameToBeReplaced ]
            p.write( outFileHandler )
        inFileHandler.close()
        outFileHandler.close()
        
        
    def retrieveInitialSequenceHeadersForMatchFile( self, dNew2Init ):
        inFileHandler = open( self._inFile, "r" )
        outFileHandler = open( self._outFile, "w" )
        m = Match()
        while True:
            line = inFileHandler.readline()
            if line == "":
                break
            if line[0:10] == "query.name":
                continue
            m.setFromTuple( line.split("\t") )
            nameToBeReplaced = m.range_query.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                m.range_query.seqname = dNew2Init[ nameToBeReplaced ]
            nameToBeReplaced = m.range_subject.seqname
            if dNew2Init.has_key( nameToBeReplaced ):
                m.range_subject.seqname = dNew2Init[ nameToBeReplaced ]
            m.write( outFileHandler )
        inFileHandler.close()
        outFileHandler.close()
        
        
    def run( self ):
        self.checkAttributes()
        if self._step == 1:
            if self._linkFile == "":
                self._linkFile = "%s.newHlink" % ( self._inFile )
            if self._format == "fasta":
                self.shortenSequenceHeadersForFastaFile()
        if self._step == 2:
            dNew2Init = self.getLinksNewToInitialHeaders()
            if self._format == "fasta":
                self.retrieveInitialSequenceHeadersForFastaFile( dNew2Init )
            elif self._format == "newick":
                self.retrieveInitialSequenceHeadersForNewickFile( dNew2Init )
            elif self._format == "align":
                self.retrieveInitialSequenceHeadersForAlignFile( dNew2Init )
            elif self._format == "path":
                self.retrieveInitialSequenceHeadersForPathFile( dNew2Init )
            elif self._format in [ "tab", "match" ]:
                self.retrieveInitialSequenceHeadersForMatchFile( dNew2Init )
                
                
if __name__ == "__main__":
    i = ChangeSequenceHeaders()
    i.setAttributesFromCmdLine()
    i.run()
