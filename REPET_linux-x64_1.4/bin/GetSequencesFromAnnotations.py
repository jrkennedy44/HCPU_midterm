#!/usr/bin/env python

##@file
# Get the sequences corresponding to input coordinates


import os
import sys
import getopt
import time
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.sql.TableSeqAdaptator import TableSeqAdaptator
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils


## Get the sequences corresponding to input coordinates
#
class GetSequencesFromAnnotations( object ):
    
    def __init__( self ):
        self._inCoord = ""
        self._formatInCoord = "path"
        self._inGenome = ""
        self._inRefseqs = ""
        self._refseqName = ""
        self._data = "matches"
        self._minProp = 0.0
        self._getAnnot = False
        self._configFile = ""
        self._verbose = 0
        self._typeInCoord = "table"
        self._typeInGenome = "table"
        self._typeInRefseqs = "table"
        self._iDb = None
        self._coordAdaptator = None   # TablePathAdaptator() if format='path', a dictionary if format='set
        self._genomeAdaptator = None
        self._refseqsAdaptator = None
        self._outCoordFile = ""   # if getAnnot=True, file in which the coordinates of the saved annotations will be recorded
        self._outCoordFileHandler = None
        
        
    def help( self ):
        print
        print "usage: GetSequencesFromAnnotations.py [ options ]"
        print "options:"
        print "     -h: this help"
        print "     -i: input data with coordinates (file or table for 'path', file for 'set')"
        print "     -f: format of the input coordinates (default='path'/'set')"
        print "     -g: input data with genomic sequences (file or table, format='fasta', queries in 'path')"
        print "     -s: input data with the reference sequences (file or table, required with 'path', format='fasta')"
        print "     -r: name of a reference sequence (subject in 'path', all by default)"
        print "     -d: sequences to retrieve (default='matches'/'chains')"
        print "     -y: minimum copy proportion compare to reference sequences (default=0.0)"
        print "     -a: also retrieve the annotations (format='path')"
        print "     -C: configuration file"
        print "     -v: verbosity level (default=0/1/2)"
        print
        
        
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hi:f:g:s:r:d:y:aC:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-i":
                self._inCoord = a
            elif o == "-f":
                self._formatInCoord = a
            elif o == "-g":
                self._inGenome = a
            elif o == "-s":
                self._inRefseqs = a
            elif o == "-r":
                self._refseqName = a
            elif o == "-d":
                self._data = a
            elif o == "-y":
                self._minProp = float(a)
            elif o == "-a":
                self._getAnnot = True
            elif o == "-C":
                self._configFile = a
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        if self._inCoord == "":
            msg = "ERROR: missing input coordinates (-i)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._formatInCoord == "":
            msg = "ERROR: missing coordinate format (-f)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._formatInCoord not in [ "path", "set" ]:
            msg = "ERROR: unknown format '%s'" % ( self._formatInCoord )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._inGenome == "":
            msg = "ERROR: missing genomic sequences (-g)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if self._configFile == "":
            msg = "ERROR: missing configuration file (-C)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        if not os.path.exists( self._configFile ):
            msg = "ERROR: configuration file '%s' doesn't exist" % ( self._configFile )
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
        self._iDb = DbMySql( cfgFileName=self._configFile )
        if not self._iDb.doesTableExist( self._inGenome ):
            if not os.path.exists( self._inGenome ):
                msg = "ERROR: no file nor table for genomic sequences '%s' (-g)" % ( self._inGenome )
                sys.stderr.write( "%s\n" % ( msg ) )
                self.help(); sys.exit(1)
            else:
                self._typeInGenome = "file"
        else:
            self._typeInGenome = "table"
        if self._data not in [ "matches", "chains" ]:
            msg = "ERROR: missing requested data (-d)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
            
        if self._formatInCoord == "path":
            if self._inRefseqs == "":
                msg = "ERROR: missing reference sequences (-s)"
                sys.stderr.write( "%s\n" % ( msg ) )
                self.help(); sys.exit(1)
            if not self._iDb.doesTableExist( self._inCoord ):
                if not os.path.exists( self._inCoord ):
                    msg = "ERROR: no file nor table for input coordinates '%s' (-a)" % ( self._inCoord )
                    sys.stderr.write( "%s\n" % ( msg ) )
                    self.help(); sys.exit(1)
                else:
                    self._typeInCoord = "file"
            else:
                self._typeInCoord = "table"
            if not self._iDb.doesTableExist( self._inRefseqs ):
                if not os.path.exists( self._inRefseqs ):
                    msg = "ERROR: no file nor table for reference sequences '%s' (-s)" % ( self._inRefseqs )
                    sys.stderr.write( "%s\n" % ( msg ) )
                    self.help(); sys.exit(1)
                else:
                    self._typeInRefseqs = "file"
            else:
                self._typeInRefseqs = "table"
                
        elif self._formatInCoord == "set":
            if not os.path.exists( self._inCoord ):
                msg = "ERROR: annotation file '%s' doesn't exist" % ( self._inCoord )
                sys.stderr.write( "%s\n" % ( msg ) )
                self.help(); sys.exit(1)
            self._typeInCoord = "file"
            if self._data == "matches":
                msg = "ERROR: data 'matches' not yet available in 'set' format"
                sys.stderr.write( "%s\n" % ( msg ) )
                self.help(); sys.exit(1)
            if self._inRefseqs != "":
                if not self._iDb.doesTableExist( self._inRefseqs ):
                    if not os.path.exists( self._inRefseqs ):
                        msg = "ERROR: no file nor table for reference sequences '%s' (-s)" % ( self._inRefseqs )
                        sys.stderr.write( "%s\n" % ( msg ) )
                        self.help(); sys.exit(1)
                    else:
                        self._typeInRefseqs = "file"
                else:
                    self._typeInRefseqs = "table"
                    
        if self._minProp < 0 or self._minProp > 1:
            msg = "ERROR: minimum proportion outside range [0;1] (-y)"
            sys.stderr.write( "%s\n" % ( msg ) )
            self.help(); sys.exit(1)
            
            
    def getListRefseqNames( self ):
        """
        Return a list with the names of reference sequences (subjects for 'path' format).
        """
        if self._refseqName != "":
            return [ self._refseqName ]
        else:
            if self._verbose > 0:
                print "get the names of all reference sequences..."
                sys.stdout.flush()
            if self._formatInCoord == "path":
                lRefseqNames = self._coordAdaptator.getSubjectList()
            elif self._formatInCoord == "set":
                lRefseqNames = SetUtils.getListOfNames( self._inCoord )
            if i._verbose > 0:
                print "nb of reference sequences: %i" % ( len(lRefseqNames) )
                sys.stdout.flush()
            return lRefseqNames
        
        
    def getLengthRefseqs( self, lRefseqNames ):
        """
        Return a dictionary which keys are the names of reference sequences and values are their length.
        """
        dRefseq2Length = {}
        if self._inRefseqs != "":
            if self._verbose > 0:
                print "get the lengths of all reference sequences..."
                sys.stdout.flush()
            if self._typeInRefseqs == "table":
                for refseqName in lRefseqNames:
                    dRefseq2Length[ refseqName ] = self._refseqsAdaptator.getSeqLengthFromAccession( refseqName )
            else:
                dRefseq2Length = FastaUtils.getLengthPerHeader( self._inRefseqs, self._verbose - 1 )
            if i._verbose > 0:
                print "done"
                sys.stdout.flush()
        return dRefseq2Length
    
    
    def saveMatches( self, refseqName, refseqLength  ):
        """
        Save all the matches of a given reference sequence into a fasta file.
        """
        outFile = "%s_matches.fa" % ( refseqName )
        outFileHandler = open( outFile, "w" )
        lPaths = self._coordAdaptator.getPathListFromSubject( refseqName )
        if self._verbose > 0:
            msg = "refseq '%s' (%i bp): %i matches" % ( refseqName, refseqLength, len(lPaths) )
            print msg; sys.stdout.flush()
        nbSaved = 0
        for iPath in lPaths:
            if self._getAnnot:
                if iPath.getLengthOnQuery() / float(refseqLength) >= self._minProp:
                    iPath.save( self._outCoordFile )
        lSets = PathUtils.getSetListFromQueries( lPaths )
        for iSet in lSets:
            if self._verbose > 1:
                print iSet; sys.stdout.flush()
            if iSet.getLength() / float(refseqLength) >= self._minProp:
                bs = self._genomeAdaptator.getBioseqFromSetList( [ iSet ] )
                bs.write( outFileHandler )
                nbSaved += 1
            else:
                if self._verbose > 1:
                    print "too short"; sys.stdout.flush()
        outFileHandler.close()
        if self._verbose > 0:
            if nbSaved == 0:
                msg = "none saved"
                print msg; sys.stdout.flush()
            else:
                msg = "%i saved in file '%s'" % ( nbSaved, outFile )
                print msg; sys.stdout.flush()
        if nbSaved == 0:
            if os.path.exists( outFile ):
                os.remove( outFile )
                
                
    def saveChains( self, refseqName, refseqLength=0  ):
        """
        Save all the chains of matches of a given reference sequence into a fasta file.
        """
        outFile = "%s_chains.fa" % ( refseqName )
        outFileHandler = open( outFile, "a" )
        
        if self._formatInCoord == "path":
            lPathnums = self._coordAdaptator.getIdListFromSubject( refseqName )
            if self._verbose > 0:
                print "refseq '%s': %i chains" % ( refseqName, len(lPathnums) )
                sys.stdout.flush()
            for pathnum in lPathnums:
                lPaths = self._coordAdaptator.getPathListFromId( pathnum )  # lPaths is a chain
                if self._getAnnot:
                    if PathUtils.getLengthOnQueryFromPathList( lPaths ) / float(refseqLength) >= self._minProp:
                        PathUtils.writeListInFile( lPaths, self._outCoordFile, "a" )
                lSets = PathUtils.getSetListFromQueries( lPaths )
                if SetUtils.getCumulLength( lSets ) / float(refseqLength) >= self._minProp:
                    bs = self._genomeAdaptator.getBioseqFromSetList( lSets )
                    bs.write( outFileHandler )
                    
        elif self._formatInCoord == "set":
            dId2Sets = self._coordAdaptator[ refseqName ]
            if self._verbose > 0:
                print "refseq '%s': %i chain(s)" % ( refseqName, len(dId2Sets.keys()) )
                sys.stdout.flush()
            for id in dId2Sets.keys():
                lSets = dId2Sets[ id ]
                totalLength = SetUtils.getCumulLength( lSets )
                if refseqLength == 0 or ( refseqLength > 0 and \
                                          totalLength / float(refseqLength) >= self._minProp ):
                    bs = self._genomeAdaptator.getBioseqFromSetList( lSets )
                    bs.write( outFileHandler )
                    if self._getAnnot:
                        SetUtils.writeListInFile( lSets, self._outCoordFile, "a" )
                        
        outFileHandler.close()
        
        
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            msg = "START GetSequencesFromAnnotations.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            msg += "\ncoordinates: %s" % ( self._inCoord )
            msg += "\ngenome sequences: %s" % ( self._inGenome )
            msg += "\nreference sequences: %s" % ( self._inRefseqs )
            sys.stdout.write( "%s\n" % msg )
            sys.stdout.flush()
            
        if self._typeInGenome == "file":
            tmpSeqTable = self._inGenome.replace(".","_").replace("-","_")
            if not self._iDb.doesTableExist( tmpSeqTable ):
                self._iDb.createTable( tmpSeqTable, "fasta", self._inGenome, True, self._verbose-2 )
            self._genomeAdaptator = TableSeqAdaptator( self._iDb, tmpSeqTable )
        else:
            self._genomeAdaptator = TableSeqAdaptator( self._iDb, self._inGenome )
        if self._refseqName == "file":
            pass
        else:
            self._refseqsAdaptator = TableSeqAdaptator( self._iDb, self._inRefseqs )
            
        if self._formatInCoord == "path":
            if self._typeInCoord == "file":
                tmpCoordTable = self._inCoord.replace(".","_").replace("-","_")
                self._iDb.createTable( tmpCoordTable, self._formatInCoord, self._inCoord, True, self._verbose-2 )
                self._coordAdaptator = TablePathAdaptator( self._iDb, tmpCoordTable )
            else:
                self._coordAdaptator = TablePathAdaptator( self._iDb, self._inCoord )
                
        elif self._formatInCoord == "set":
            self._coordAdaptator = SetUtils.getDictOfDictsWithNamesThenIdAsKeyFromFile( self._inCoord )
            
        if self._getAnnot:
            if self._refseqName != "":
                self._outCoordFile = "%s.%s" % ( self._refseqName, self._formatInCoord )
            else:
                self._outCoordFile = "%s.%s" % ( self._inCoord, self._formatInCoord )
            self._outCoordFileHandler = open( self._outCoordFile, "w" )
            
            
    def end( self ):
        if self._formatInCoord == "path":
            if self._typeInCoord == "file":
                self._iDb.dropTable( self._coordAdaptator._table, self._verbose-1 )
            if self._typeInGenome == "file":
                self._iDb.dropTable( self._genomeAdaptator._table, self._verbose-1 )
            self._iDb.close()
            if self._getAnnot:
                self._outCoordFileHandler.close()
        if self._verbose > 0:
            print "END GetSequencesFromAnnotations.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            sys.stdout.flush()
            
            
    def run( self ):
        self.start()
        
        lRefseqNames = self.getListRefseqNames()
        
        dRefseq2Length = self.getLengthRefseqs( lRefseqNames )
        
        if self._verbose > 0:
            print "get the sequences from the annotations..."
            sys.stdout.flush()
        for refseqName in lRefseqNames:
            if self._verbose > 1:
                print "get seq for '%s'" % ( refseqName )
                sys.stdout.flush()
                
            if self._data == "matches":
                self.saveMatches( refseqName, dRefseq2Length[ refseqName ] )
                
            if self._data == "chains":
                if self._inRefseqs != "":
                    self.saveChains( refseqName, dRefseq2Length[ refseqName ] )
                else:
                    self.saveChains( refseqName )
                    
        self.end()
        
        
if __name__ == "__main__":
    i = GetSequencesFromAnnotations()
    i.setAttributesFromCmdLine()
    i.run()
