#!/usr/bin/env python

##@file
# Cluster a set of TE sequences, usually consensus obtained via the TEdenovo pipeline.

import os
import sys
import getopt
import glob
import ConfigParser
import shutil
import time

from pyRepet.launcher.programLauncher import programLauncher
from pyRepetUnit.commons.seq.FastaUtils import FastaUtils
from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
from pyRepetUnit.commons.coord.PathUtils import PathUtils
from pyRepetUnit.commons.coord.Match import Match
from pyRepetUnit.commons.coord.AlignUtils import AlignUtils
from pyRepetUnit.commons.coord.SetUtils import SetUtils
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.sql.TableSeqAdaptator import TableSeqAdaptator
from pyRepetUnit.commons.utils.FileUtils import FileUtils
from repet_base.OrientSequences import OrientSequences
from repet_base.LaunchBlastclust import LaunchBlastclust
from repet_tools.GiveInfoBlastclust import GiveInfoBlastclust

#TODO: bug with -m BlasterGrouper option (step 1)
#TODO: bug with -r option (step 2) : wrong headers (":")?
#TODO: bug with PhyML v3.0_exporte (not on Sauron)
#TODO: check -r option for step 2 => not mandatory

CLUSTER = "family"

class ClusterConsensus( object ):
    """
    Cluster a set of TE sequences, usually consensus obtained via the TEdenovo pipeline.
    """
    
    def __init__( self ):
        """
        Constructor.
        """
        self._step = ""
        self._inFileName = ""
        self._method = "Blastclust"
        self._identityThreshold = "0"
        self._coverageThreshold = "0.8"
        self._lengthFilter = "100"
        self._evalueFilter = "1e-10"
        self._annotTable = ""
        self._genomeSeqTable = ""
        self._configFileName = ""
        self._faRefFileName = ""
        self._compRefFileName = ""
        self._familyID = ""
        self._methodMsa = "Mafft"
        self._minLengthTEcopies = 100
        self._maxLongestTEcopies = 20
        self._minPropCopy = 0.5
        self._verbose = 0
        self._db = None
        self._pL = programLauncher()
        self._rootDir = ""
        
        
    def help( self ):
        """
        Display the help on stdout.
        """
        print
        print "This program can help for the manual curation of TE de novo consensus."
        print "It is best used with consensus from the TEdenovo pipeline."
        print "It may be good also to launch the TEannot pipeline before."
        print
        print "usage: %s [ options ]" % ( sys.argv[0].split("/")[-1] )
        print "global options:"
        print "-h this help"
        print "-i <input> (mandatory): Input fasta file name, containing TE consensus with short headers"
        print "-v <verbosity> (optional): Verbosity level (default = 0, you can also choose 1 or 2)"
        print
        print "additional options according to step :"
        print "step 1 : clustering of consensus"
        print "    -s 1"
        print "    -I <identity_threshold> (optional): Identity threshold for clustering (default = 0)"
        print "    -c <coverage> (optional): Coverage for clustering (default = 0.8)"
        print "    -r <reference_sequence> (optional): well-known reference TE sequences file name (format = 'fasta')"
#        print "    -m <method> (optional): Clustering method (default = 'Blastclust', or 'BlasterGrouper')"
        print
        print "step 2 : split consensus and associated information by family"
        print "    -s 2"
        print "    -C <config_file> (mandatory): TEdenovo pipeline configuration file to find sequences used to build consensus"
        print "    -a <table_name> (optional): annotation table name (<projectName>_chr_allTEs_nr_noSSR_join_path) to add copies information"
        print "    -r <reference_sequence_file_name> (optional): well-known reference TE sequences file name (format = 'fasta')"
        print
        print "step 3 : 5 different ways to build phylogeny by family"
        print "    -s 3a"
        print "    -F <%s_id> (mandatory): %s identifier" % (CLUSTER, CLUSTER)
        print "    -M <method> (optional): Multiple alignment method (default = 'Mafft', or 'Map' or 'Tcoffee')"
        print "            --------------"
        print "    -s 3b"
        print "    -F <%s_id> (mandatory): %s identifier" % (CLUSTER, CLUSTER)
        print "    -M <method> (optional): Multiple alignment method (default = 'Mafft', or 'Map' or 'Tcoffee')"
        print "            --------------"
        print "    -s 3c"
        print "    -F <%s_id> (mandatory): %s identifier" % (CLUSTER, CLUSTER)
        print "            --------------"
        print "    -s 3d"
        print "    -F <%s_id> (mandatory): %s identifier" % (CLUSTER, CLUSTER)
        print "    -a <table_name> (mandatory): Annotation table name (<projectName>_chr_allTEs_nr_noSSR_join_path)"
        print "    -g <table_name> (mandatory): Genome sequences table name (<projectName>_chr_seq)"
        print "    -C <config_file> (mandatory): Configuration file from TEdenovo pipeline"
        print "    -M <method> (optional): Multiple alignment method (default = 'Mafft', or 'Map' or 'Tcoffee')"
        print "    -l <length> (optional): TE copies' minimum length (in bp, default = 100)"
        print "    -n <number_longest_TE> (optional): Longest TE copies number (default = 20)"
        print "    -p <min_proportion> (optional): Minimum proportion of copy compared to its consensus (default = 0.5)"
        print "            --------------"
        print "    -s 3e"
        print "    -F <%s_id> (mandatory): %s identifier" % (CLUSTER, CLUSTER)
        print "    -n <number_longest_TE> (optional): Longest TE copies number (default = 20)"
        print
        print "Examples :"
        print "    python ClusterConsensus.py -s 1 -i DmelChr4_denovoLibTEs.fa -v 2"
        print "    python ClusterConsensus.py -s 2 -i DmelChr4_denovoLibTEs.fa -C TEdenovo.cfg -v 2"
        print "    python ClusterConsensus.py -s 3a -i DmelChr4_denovoLibTEs.fa -F 7 -M Map -v 2"
        print "    python ClusterConsensus.py -s 3b -i DmelChr4_denovoLibTEs.fa -F 7 -M Map -v 2"
        print "    python ClusterConsensus.py -s 3c -i DmelChr4_denovoLibTEs.fa -F 7 -v 2"
        print "    python ClusterConsensus.py -s 3d -i DmelChr4_denovoLibTEs.fa -F 7 -a DmelChr4_chr_allTEs_nr_noSSR_join_path -g DmelChr4_chr_seq -C TEdenovo.cfg -M Map -v 2"
        print "    python ClusterConsensus.py -s 3e -i DmelChr4_denovoLibTEs.fa -F 7 -v 2"
        print
        
    def setAttributesFromCmdLine( self ):
        """
        Set the attributes from the command-line.
        """
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hs:i:m:I:c:L:E:a:g:C:r:F:M:l:n:p:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help(); sys.exit(0)
            elif o == "-s":
                self._step = a
            elif o == "-i":
                self._inFileName = a
            elif o == "-m":
                self._method = a
            elif o == "-I":
                self._identityThreshold = a
            elif o == "-c":
                self._coverageThreshold = a
            elif o == "-L":
                self._lengthFilter = a
            elif o == "-E":
                self._evalueFilter = a
            elif o == "-a":
                self._annotTable = a
            elif o == "-g":
                self._genomeSeqTable = a
            elif o == "-C":
                self._configFileName = a
            elif o == "-r":
                self._faRefFileName = a
            elif o == "-F":
                self._familyID = a
            elif o == "-M":
                self._methodMsa = a
            elif o == "-l":
                self._minLengthTEcopies = int(a)
            elif o == "-n":
                self._maxLongestTEcopies = int(a)
            elif o == "-p":
                self._minPropCopy = float(a)
            elif o == "-v":
                self._verbose = int(a)
                
                
    def checkAttributes( self ):
        """
        Check the attributes are valid before running the algorithm.
        """
        if self._step not in ["1", "2", "3a", "3b", "3c", "3d", "3e"]:
            msg = "ERROR: the step you tape doesn't exist!\n"
            msg += "You should choose the steps from [1, 2, 3a, 3b, 3c, 3d, 3e]" 
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)  
        if self._inFileName == "" :
            msg = "ERROR: missing input file options (-i)"
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)      
        if not os.path.exists(self._inFileName):
            msg = "ERROR: input file '%s' doesn't exist" % self._inFileName
            sys.stderr.write( "%s\n" % msg )
            self.help()
            sys.exit(1)
            
        if self._step == "1":       
            if self._faRefFileName != "" and not os.path.exists(self._faRefFileName):
                msg = "ERROR: fasta reference file '%s' doesn't exist" % self._faRefFileName
                sys.stderr.write( "%s\n" % msg )
                self.help()
                sys.exit(1)
            if self._method not in ["Blastclust", "BlasterGrouper"]:
                msg = "ERROR: unknown clustering method '%s' (-m)" % ( self._method )
                sys.stderr.write( "%s\n" % msg )
                self.help()
                sys.exit(1)
                
        if self._step in ["2", "3d"]:
            self._db = DbMySql(cfgFileName = self._configFileName)
        
        if self._step == "2":
            if self._configFileName == "":
                msg = "ERROR: missing configuration file (-C)"    
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
            if not os.path.exists(self._configFileName):  
                msg = "ERROR: configuration file '%s' doesn't exist" % ( self._configFileName )
                sys.stderr.write( "%s\n" % msg )
                self.help()
                sys.exit(1)
            if self._annotTable != "" and not self._db.doesTableExist(self._annotTable):
                msg = "ERROR: '%s' annot table does not exist)" % (self._annotTable)
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
        #TODO: check option -r for step 2

        if self._step in ["3a", "3b", "3c", "3d", "3e"] and self._familyID == "":
                msg = "ERROR: missing %s id (-F)" % CLUSTER
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)            
        if self._step in ["3a", "3b", "3d"] and self._methodMsa not in ["Map", "Mafft", "Tcoffee"]:
                msg = "ERROR: '%s' not supported (-M)" % (self._methodMsa)
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)   
        if  self._step == "3d":
            if self._configFileName == "":
                msg = "ERROR: missing configuration file (-C)"    
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
            if not os.path.exists(self._configFileName):  
                msg = "ERROR: configuration file '%s' doesn't exist" % ( self._configFileName )
                sys.stderr.write( "%s\n" % msg )
                self.help()
                sys.exit(1)       
            if self._annotTable == "":
                msg = "ERROR: missing annotTable! (-a)"
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
            if not self._db.doesTableExist(self._annotTable):
                msg = "ERROR: '%s' annot table does not exist)" % (self._annotTable)
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
            if self._genomeSeqTable == "":
                msg = "ERROR: missing genome sequence Table! (-g)"
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)  
            if not self._db.doesTableExist(self._genomeSeqTable):
                msg = "ERROR: '%s' genome sequence table does not exist)" % (self._genomeSeqTable)
                sys.stderr.write("%s\n" % msg)
                self.help()
                sys.exit(1)
                
            
    def setCompRefFileName( self ):
        self._compRefFileName = "%s_vs_%s.m2.align.merged.match.tab" % ( self._inFileName, self._faRefFileName )
        
        
    def compareConsensusWithRefSeq( self ):
        """
        Compare the consensus and the reference sequences with 'compareFasta.py'.
        """
        workDir = "compRefTEs"
        if not os.path.exists( "%s/%s" % ( self._rootDir, workDir ) ):
            if self._verbose > 0:
                print "compare the input consensus with the reference sequences..."
                sys.stdout.flush()
            os.mkdir( "%s/%s" % ( self._rootDir, workDir ) )
            os.chdir( "%s/%s" % ( self._rootDir, workDir ) )
            os.system( "ln -s %s/%s ." % ( self._rootDir, self._inFileName ) )
            os.system( "ln -s %s/%s ."  % ( self._rootDir, self._faRefFileName ) )
            prg = "BenchmarkTEconsensus.py"
            cmd = prg
            cmd += " -q %s" % ( self._inFileName )
            cmd += " -s %s" % ( self._faRefFileName )
            cmd += " -m %s" % ( "2" )
            cmd += " -a"
            cmd += " -c"
            cmd += " -v %i" % ( self._verbose - 1 )
            self._pL.launch( prg, cmd )
        self.setCompRefFileName()
        os.chdir( self._rootDir )
        
        
    def compareConsensusWithBlaster( self ):
        """
        Compare the consensus with themselves using Blaster.
        """
        if self._verbose > 0:
            print "align consensus against themselves..."
            sys.stdout.flush()
        workDir = "Blaster"
        if os.path.exists( "%s/%s" % ( self._rootDir, workDir ) ):
            os.system( "rm -r %s/%s" % ( self._rootDir, workDir ) )
        os.mkdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.chdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.system( "ln -s %s/%s ." % ( self._rootDir, self._inFileName ) )
        self._pL.reset( self._inFileName )
        self._pL.launchBlaster( allByAll="yes", outPrefix=self._inFileName )
        if self._verbose > 0:
            compareInputSeqAndQueries( self._inFileName, self._verbose )
        os.chdir( self._rootDir )
        return "%s/%s.align" % ( workDir, self._inFileName )
    
    
    def clusterHspWithGrouper( self, alignFileName ):
        """
        Cluster the HSPs with Grouper.
        """
        if self._verbose > 0:
            print "cluster the HSPs..."; sys.stdout.flush()
        workDir = "Grouper"
        if os.path.exists( "%s/%s" % ( self._rootDir, workDir ) ):
            os.system( "rm -r %s/%s" % ( self._rootDir, workDir ) )
        os.mkdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.chdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.system( "ln -s %s/%s ." % ( self._rootDir, self._inFileName ) )
        os.system( "ln -s %s/%s ." % ( self._rootDir, alignFileName ) )
        outFaFileName = "%s.align.group.c%s.fa" % ( self._inFileName, self._coverageThreshold )
        prg = os.environ["REPET_PATH"] + "/bin/grouper"
        cmd = prg
        cmd += " -m %s" % ( self._inFileName+".align" )
        cmd += " -q %s" % ( self._inFileName )
        cmd += " -j"
        cmd += " -L %s" % ( self._lengthFilter )
        cmd += " -C %s" % ( self._coverageThreshold )
        cmd += " -I %s" % ( self._identityThreshold )
        cmd += " -E %s" % ( self._evalueFilter )
        cmd += " -Z 1"
        cmd += " -X 0"
        cmd += " -v %i" % ( self._verbose-1 )
        self._pL.launch( prg, cmd )
        prg = os.environ["REPET_PATH"] + "/bin/giveInfoGrouper.py"
        cmd = prg
        cmd += " -f %s" % ( self._inFileName )
        cmd += " -m %s.align.group.c%s.map" % ( self._inFileName, self._coverageThreshold )
        self._pL.launch( prg, cmd, self._verbose-1 )
        os.symlink( outFaFileName, "clusteredSequences.fa" )
        os.chdir( self._rootDir )
        return "%s/clusteredSequences.fa" % ( workDir )
    
    
    def clusterConsensusWithBlastClust( self ):
        """
        Cluster the consensus with Blastclust.
        """
        if self._verbose > 0:
            print "cluster consensus with Blastclust..."; sys.stdout.flush()
        workDir = "Blastclust"
        if os.path.exists( "%s/%s" % ( self._rootDir, workDir ) ):
            os.system( "rm -r %s/%s" % ( self._rootDir, workDir ) )
        os.mkdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.chdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.system( "ln -s %s/%s ." % ( self._rootDir, self._inFileName ) )
        lbc = LaunchBlastclust()
        lbc.setInputFileName( self._inFileName )
        lbc.setCoverageThreshold( self._coverageThreshold )
        lbc.setIdentityThreshold( self._identityThreshold )
        lbc.setBothSequences( "F" )
        #lbc.setFilterUnclusteredSequences()
        lbc.setClean()
        lbc.setVerbosityLevel( self._verbose )
        lbc.run()
        outFileName = "%s_blastclust.fa"  %( self._inFileName )
        gib = GiveInfoBlastclust()
        gib.setInputFileName( outFileName )
        gib.setFormat( "fasta" )
        gib.setVerbosityLevel( self._verbose )
        gib.run()
        os.symlink( outFileName, "clusteredSequences.fa" )
        os.chdir( self._rootDir )
        return "%s/clusteredSequences.fa" % ( workDir )
    
    
    ## Split the the input sequences per TEs cluster
    #
    def splitSequencesPerFamily( self ):
        if self._verbose > 0:
            print "split sequences per %s..." % CLUSTER
            sys.stdout.flush()
        workDir = "data_per_%s" % CLUSTER
        if os.path.exists( "%s/%s" % ( self._rootDir, workDir ) ):
            os.system( "rm -r %s/%s" % ( self._rootDir, workDir ) )
        os.mkdir( "%s/%s" % ( self._rootDir, workDir ) )
        os.chdir( "%s/%s" % ( self._rootDir, workDir ) )
        if self._method == "BlasterGrouper":
            os.system( "ln -s %s/Grouper/clusteredSequences.fa ." % ( self._rootDir ) )
            FastaUtils.splitSeqPerCluster( "clusteredSequences.fa", "Grouper", False, True, CLUSTER, self._verbose )
        else:
            os.system( "ln -s %s/Blastclust/clusteredSequences.fa ." % ( self._rootDir ) )
            FastaUtils.splitSeqPerCluster( "clusteredSequences.fa", "Blastclust", False, True, CLUSTER, self._verbose )
        lGroupDirs = glob.glob( "clusteredSequences.fa_cluster_*" )
        for groupDir in lGroupDirs:
            groupID = groupDir.split( "_cluster_" )[-1]
            os.system( "mv %s %s_%s" % ( groupDir, CLUSTER, groupID.zfill( len(str(len(lGroupDirs))) ) ) )
        os.chdir( self._rootDir )
        
        
    def launchMsa( self, inFaFileName ):
        outAfaFile = "%s.oriented_%s.afa" % ( inFaFileName, self._methodMsa.lower() )
        if self._verbose > 0:
            print "build multiple alignment for '%s'..." % ( inFaFileName )
            sys.stdout.flush()
        ors = OrientSequences()
        ors.setInputFileName( inFaFileName )
        ors.setPrgToOrient( "mummer" )
        ors.setClean()
        ors.setVerbosityLevel( self._verbose-1 )
        ors.run()
        ors.clean()
        if self._methodMsa in ["Mafft","Map"]:
            prg = os.environ["REPET_PATH"] + "/bin/%sProgramLauncher.py" % ( self._methodMsa )
        elif self._methodMsa in ["Tcoffee"]:
            prg = os.environ["REPET_PATH"] + "/bin/launchTCoffee.py"
        cmd = prg
        cmd += " -i %s.oriented" % ( inFaFileName )
        cmd += " -o %s" % ( outAfaFile )
        cmd += " -c"
        cmd += " -v %i" % ( self._verbose - 1 )
        self._pL.launch( prg, cmd )
        return outAfaFile
    
    
    def launchPhylogeny( self, inAlnFaFileName ):
        if self._verbose > 0:
            print "build phylogeny for '%s'..." % ( inAlnFaFileName )
            sys.stdout.flush()
        prg = os.environ["REPET_PATH"] + "/bin/launchPhyML.py"
        cmd = prg
        cmd += " -i %s" % ( inAlnFaFileName )
        cmd += " -c"
        cmd += " -v %i" % ( self._verbose - 1 )
        self._pL.launch( prg, cmd )
        
        
    def saveCopiesFromConsensus( self, clean=False ):
        if self._annotTable == "" or self._genomeSeqTable == "":
            msg = "ERROR: can't save copies, require annotation and genome tables (-a -g)"
            sys.stderr.write( "%s\n" % msg )
            sys.exit(1)
        if self._verbose > 0:
            print "saving copies..."; sys.stdout.flush()
        if not os.path.exists( self._configFileName ):
            os.symlink( "../../%s" % ( self._configFileName ), self._configFileName )
        tpA = TablePathAdaptator( self._db, self._annotTable )
        tsA = TableSeqAdaptator( self._db, self._genomeSeqTable )
        dHeader2Length = FastaUtils.getLengthPerHeader( "%s%s.fa.fullS" % ( CLUSTER, self._familyID ) )
        totalNbSavedCopies = 0
        for header in dHeader2Length.keys():
            lPathNums = tpA.getIdListSortedByDecreasingChainLengthFromSubject( header )
            nbCopies = len(lPathNums)
            if self._verbose > 1: print "%s: %i copies" % ( header, nbCopies )
            if nbCopies > 0:
                allcopiesFileName = "%s_%iLongestCopies.fa" % ( header, self._maxLongestTEcopies )
                allcopiesFile = open( allcopiesFileName, "w" )
                i = 0
                nbSavedCopies = 0
                while i < len(lPathNums) and nbSavedCopies < self._maxLongestTEcopies:
                    lPaths = tpA.getPathListFromId( lPathNums[i] )
                    lSets = PathUtils.getSetListFromQueries( lPaths )
                    copyLength = SetUtils.getCumulLength( lSets )
                    if copyLength >= self._minLengthTEcopies \
                    and copyLength >=  self._minPropCopy * dHeader2Length[ header ]:
                        bs = tsA.getBioseqFromSetList( lSets )
                        bs.write( allcopiesFile )
                        nbSavedCopies += 1
                    i += 1
                allcopiesFile.close()
                totalNbSavedCopies += nbSavedCopies
        if totalNbSavedCopies == 0:
            return ""
        outFileName = "%s%s_BestRefseqsConsensus%iCopies.fa" % ( CLUSTER, self._familyID, self._maxLongestTEcopies )
        if os.path.exists( outFileName ): os.remove( outFileName )
        for bestRefFile in glob.glob( "*_bestRef.fa" ):
            FileUtils.appendFileContent( bestRefFile, outFileName )
        for header in dHeader2Length.keys():
            copiesFile = "%s_%iLongestCopies.fa" % ( header, self._maxLongestTEcopies )
            if os.path.exists( copiesFile ):
                consensusFile = "%s_consensus.fa" % ( header )
                FileUtils.appendFileContent( consensusFile, outFileName )
                FileUtils.appendFileContent( copiesFile, outFileName )
        return outFileName
    
    
    #unused ?
    def buildConsensusOfCopies( self ):
        prg = os.environ["REPET_PATH"] + "/bin/dbConsensus.py"
        cmd = prg
        cmd += " -i %s%s_best%icopies.fa.fa_aln" % ( CLUSTER, self._familyID, self._maxLongestTEcopies )
        cmd += " -n 2"
        cmd += " -o %s%s_best%icopies.fa.fa_aln.cons" % ( CLUSTER, self._familyID, self._maxLongestTEcopies )
        cmd += " -v %i" % ( self._verbose )
        self._pL.launch( prg, cmd, self._verbose-1 )
        
        
    #unused ?
    def addConsensusSeqInCopiesFileWithRefSeq( self ):
        fU = FileUtils()
        lFiles = []
        allConsensusFileName = "%s%s.fa.fullS.seqlen.clust" % ( CLUSTER, self._familyID )
        if os.path.exists( allConsensusFileName + ".copy.bestRef" ):
            allConsensusFileName += ".copy.bestRef"
        elif os.path.exists( allConsensusFileName + ".bestRef" ):
            allConsensusFileName += ".bestRef"
        lFiles.append( allConsensusFileName )
        lFiles.append( "%s%s_best%icopies.fa" % ( CLUSTER, self._familyID, self._maxLongestTEcopies ) )
        outFileName = "%s%s_ConsensusAndCopiesWithRefSeq.fa" % ( CLUSTER, self._familyID )
        fU.concatFiles( lFiles, outFileName )
        return outFileName
    
    
    def launchRefalignForEachSetOfConsensusAbaMatches( self ):
        lProfilesFiles = []
        
        ors = OrientSequences()
        ors.setInputFileName( "%s%s.fa.fullS" % ( CLUSTER, self._familyID ) )
        ors.setPrgToOrient( "mummer" )
        ors.setClean()
        ors.setVerbosityLevel( self._verbose-1 )
        lConsensusToReverse = ors.getSequencesToReverse()
        ors.clean()
        
        lAbaFiles = glob.glob( "*_AbaMatches.fa" )
        for f in lAbaFiles:
            consensusName = f.split( "_AbaMatches.fa" )[0]
            inFaFileName = "consensus_%s_withAbaMatches.fa" % ( consensusName )
            if os.path.exists( inFaFileName ):
                os.remove( inFaFileName )
            FileUtils.catFilesFromList( [ "%s_consensus.fa" % ( consensusName ), f ],
                                          inFaFileName,
                                          sort=False )
            if consensusName in lConsensusToReverse:
                bsDB = BioseqDB( inFaFileName )
                for bs in bsDB.db: bs.header += " re-oriented"
                bsDB.reverseComplement()
                bsDB.save( "%s.oriented" % ( inFaFileName ) )
            else:
                shutil.copy( inFaFileName, "%s.oriented" % ( inFaFileName ) )
            prg = os.environ["REPET_PATH"] + "/bin/launchRefalign.py"
            cmd = prg
            cmd += " -i %s.oriented" % ( inFaFileName )
            cmd += " -r"
            cmd += " -o %s.oriented.fa_aln" % ( inFaFileName )
            cmd += " -v %i" % ( self._verbose )
            self._pL.launch( prg, cmd )
            lProfilesFiles.append( "%s.oriented.fa_aln" % ( inFaFileName ) )
            
        return lProfilesFiles
    
    
    def launchRefalignForEachSetOfConsensusCopies( self ):
        lProfilesFiles = []
        
        lCopiesFiles = glob.glob( "*_%iLongestCopies.fa" % ( self._maxLongestTEcopies ) )
        if len(lCopiesFiles) == 0:
            msg = "ERROR: can't run this step because data about copies are missing"
            sys.stderr.write( "%s\n" % msg )
            sys.exit(1)
            
        ors = OrientSequences()
        ors.setInputFileName( "%s%s.fa.fullS" % ( CLUSTER, self._familyID ) )
        ors.setPrgToOrient( "mummer" )
        ors.setClean()
        ors.setVerbosityLevel( self._verbose-1 )
        lConsensusToReverse = ors.getSequencesToReverse()
        ors.clean()
        
        for f in lCopiesFiles:
            consensusName = f.split( "_%iLongestCopies.fa" % ( self._maxLongestTEcopies ) )[0]
            if FastaUtils.dbSize( f ) < 1:
                if self._verbose > 0:
                    print "no long-enough copies, keep only the consensus '%s'" % ( consensusName )
                lProfilesFiles.append( "%s_consensus.fa" % ( consensusName ) )
                continue
            if self._verbose > 0:
                print "use Refalign for consensus '%s' and its copies... " % ( consensusName )
                sys.stdout.flush()
            inFaFileName = "consensus_%s_withCopies.fa" % ( consensusName )
            if os.path.exists( inFaFileName ):
                os.remove( inFaFileName )
            FileUtils.catFilesFromList( [ "%s_consensus.fa" % ( consensusName ), f ],
                                          inFaFileName,
                                          sort=False )
            if consensusName in lConsensusToReverse:
                bsDB = BioseqDB( inFaFileName )
                for bs in bsDB.db: bs.header += " re-oriented"
                bsDB.reverseComplement()
                bsDB.save( "%s.oriented" % ( inFaFileName ) )
            else:
                shutil.copy( inFaFileName, "%s.oriented" % ( inFaFileName ) )
            prg = os.environ["REPET_PATH"] + "/bin/launchRefalign.py"
            cmd = prg
            cmd += " -i %s.oriented" % ( inFaFileName )
            cmd += " -r"
            cmd += " -o %s.oriented.fa_aln" % ( inFaFileName )
            cmd += " -v %i" % ( self._verbose )
            self._pL.launch( prg, cmd )
            lProfilesFiles.append( "%s.oriented.fa_aln" % ( inFaFileName ) )
            
        return lProfilesFiles
    
    
    def alignProfilesAndBestRefseqs( self, lProfilesFiles, outFile="" ):
        if outFile == "":
            outFile = "%s%s_profiles.fa_aln" % ( CLUSTER, self._familyID )
        if self._verbose > 0:
            print "build multiple alignment from %i profiles..." % ( len(lProfilesFiles) )
            sys.stdout.flush()
            
        i = 1
        if os.path.exists( "%s.%i" % ( outFile, i ) ):
            os.remove( "%s.%i" % ( outFile, i ) )
        prg = "muscle"
        cmd = prg
        cmd += " -profile"
        cmd += " -in1 %s" % ( lProfilesFiles[i-1] )
        cmd += " -in2 %s" % ( lProfilesFiles[i] )
        cmd += " -out %s.%i" % ( outFile, i )
        self._pL.launch( prg, cmd )
        i += 1
        
        while i < len(lProfilesFiles):
            if os.path.exists( "%s.%i" % ( outFile, i ) ):
                os.remove( "%s.%i" % ( outFile, i ) )
            prg = "muscle"
            cmd = prg
            cmd += " -profile"
            cmd += " -in1 %s.%i" % ( outFile, i-1 )
            cmd += " -in2 %s" % ( lProfilesFiles[i] )
            cmd += " -out %s.%i" % ( outFile, i )
            self._pL.launch( prg, cmd )
            os.remove( "%s.%i" % ( outFile, i-1 ) )
            i += 1
            
        lBestRefseqs = glob.glob( "*_bestRef.fa" )
        for j in xrange( 0, len(lBestRefseqs) ):
            if os.path.exists( "%s.%i" % ( outFile, i ) ):
                os.remove( "%s.%i" % ( outFile, i ) )
            prg = "muscle"
            cmd = prg
            cmd += " -profile"
            cmd += " -in1 %s.%i" % ( outFile, i-1 )
            cmd += " -in2 %s" % ( lBestRefseqs[j] )
            cmd += " -out %s.%i" % ( outFile, i )
            self._pL.launch( prg, cmd )
            os.remove( "%s.%i" % ( outFile, i-1 ) )
            i += 1
            
#        lBestRefseqs = glob.glob( "*_bestRef.fa" )
#        i = 0
#        cmd = "launchTCoffee.py"
#        if len(lBestRefseqs) > 0:
#            cmd += " -i %s" % ( lBestRefseqs[0] )
#        cmd += " -P '-type=dna"
#        cmd += " -output=fasta_aln"
#        cmd += " -profile=%s" % ( lProfilesFiles[0] )
#        for f in lProfilesFiles[1:]:
#            cmd += ",%s" % ( f )
#        cmd += "'"
#        cmd += " -o %s.%i" % ( outFile, i )
#        self._pL.launch( "launchTCoffee.py", cmd )
#        
#        for i in xrange( 1, len(lBestRefseqs) ):
#            cmd = "launchTCoffee.py"
#            cmd += " -i %s" % ( lBestRefseqs[0] )
#            cmd += " -P '-type=dna"
#            cmd += " -output=fasta_aln"
#            cmd += " -profile=%s.%i'" % ( outFile, i-1 )
#            cmd += " -o %s.%i" % ( outFile, i )
#            self._pL.launch( "launchTCoffee.py", cmd )
            
        if os.path.exists( outFile ): os.remove( outFile )
        os.rename( "%s.%i" % ( outFile, i-1 ), outFile )
        
        
    def start( self ):
        """
        Useful commands before running the program.
        """
        self.checkAttributes()
        if self._verbose > 0:
            print "START ClusterConsensus.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            sys.stdout.flush()
        self._rootDir = os.getcwd()
        
        
    def end( self ):
        """
        Useful commands before ending the program.
        """
        if self._db != None:
            self._db.close()
        if self._verbose > 0:
            print "END ClusterConsensus.py (%s)" % ( time.strftime("%m/%d/%Y %H:%M:%S") )
            sys.stdout.flush()
            
            
    def run( self ):
        """
        Run the program.
        """
        self.start()
        
        if "1" in self._step:
            if self._verbose > 0:
                print "nb of input consensus: %i" % ( FastaUtils.dbSize(self._inFileName) ); sys.stdout.flush()
            if self._method == "BlasterGrouper":
                alignFileName = self.compareConsensusWithBlaster()
                self.clusterHspWithGrouper( alignFileName )
            elif self._method == "Blastclust":
                self.clusterConsensusWithBlastClust()
            if self._faRefFileName != "":
                self.compareConsensusWithRefSeq()
                
        if "2" in self._step:
            if self._faRefFileName != "":
                self.compareConsensusWithRefSeq()
            self.setCompRefFileName()
            self.splitSequencesPerFamily()
            pathToFaRefFileName = ""
            if self._faRefFileName != "":
                pathToFaRefFileName = "%s/compRefTEs/%s" % (self._rootDir, self._faRefFileName)
            s4 = HandleAllGroupsOfConsensus( pathToFaInFileName="%s/%s" % ( self._rootDir, self._inFileName ), 
                                             pathToFaGrpFileName="%s/%s/clusteredSequences.fa" % ( self._rootDir, self._method.replace("Blaster","") ),
                                             clusteringMethod=self._method,
                                             annotTable=self._annotTable,
                                             configFileName=self._configFileName,
                                             pathToFaRefFileName = pathToFaRefFileName,
                                             pathToCompRefFileName = "%s/compRefTEs/%s" % ( self._rootDir, self._compRefFileName ),
                                             verbose=self._verbose )
            s4.run( keepSeqWithoutCopy=False, cleanEmptyGroup=True )
            
        if "3" in self._step:
            os.chdir( "data_per_%s" % CLUSTER)
            nbFamilies = len( glob.glob( "%s_*" % CLUSTER ) )
            os.chdir( "%s_%s" % ( CLUSTER, self._familyID.zfill( len(str(nbFamilies)) ) ) )
            
            # consensus (+ ref seq if any)
            if "3a" in self._step:
                inFaFileName = "%s%s.fa.fullS.seqlen" % ( CLUSTER, self._familyID )
                if self._method == "BlasterGrouper":
                    inFaFileName += ".clust"
                if os.path.exists( "%s.copy" % ( inFaFileName ) ):
                    inFaFileName += ".copy"
                if os.path.exists( "%s.bestRefs" % ( inFaFileName ) ):
                    inFaFileName += ".bestRefs"
                if os.path.exists( inFaFileName ):
                    alnFaFileName = self.launchMsa( inFaFileName )
                    self.launchPhylogeny( alnFaFileName )
                    
            # consensus + all-by-all matches used to build them (+ ref seq if any)
            if "3b" in self._step:
                inFaFileName = "%s%s.fa.fullS.seqlen" % ( CLUSTER, self._familyID )
                if self._method == "BlasterGrouper":
                    inFaFileName += ".clust"
                if os.path.exists( "%s.copy" % ( inFaFileName ) ):
                    inFaFileName += ".copy"
                if os.path.exists( "%s.aBa" % ( inFaFileName ) ):
                    inFaFileName += ".aBa"
                if os.path.exists( "%s.bestRefs" % ( inFaFileName ) ):
                    inFaFileName += ".bestRefs"
                if os.path.exists( inFaFileName ):
                    alnFaFileName = self.launchMsa( inFaFileName )
                    self.launchPhylogeny( alnFaFileName )
                    
            # MSA consensus+aBa, then MSA profiles (+ refseq if any)
            if "3c" in self._step:
                inFaFileName = "%s%s.fa.fullS.seqlen" % ( CLUSTER, self._familyID )
                if self._method == "BlasterGrouper":
                    inFaFileName += ".clust"
                if os.path.exists( "%s.copy" % ( inFaFileName ) ):
                    inFaFileName += ".copy"
                if os.path.exists( "%s.aBa" % ( inFaFileName ) ):
                    inFaFileName += ".aBa"
                if os.path.exists( "%s.bestRefs" % ( inFaFileName ) ):
                    inFaFileName += ".bestRefs"
                lProfilesFiles = self.launchRefalignForEachSetOfConsensusAbaMatches()
                alnFile = "%s%s_profilesAba.afa" % ( CLUSTER, self._familyID )
                self.alignProfilesAndBestRefseqs( lProfilesFiles, alnFile )
                self.launchPhylogeny( alnFile )
                
            # consensus + copies (+ ref seq if any)
            if "3d" in self._step:
                inFaFileName = "%s%s.fa.fullS.seqlen" % ( CLUSTER, self._familyID )
                if self._method == "BlasterGrouper":
                    inFaFileName += ".clust"
                if os.path.exists( "%s.copy" % ( inFaFileName ) ):
                    inFaFileName += ".copy"
                if os.path.exists( "%s.bestRefs" % ( inFaFileName ) ):
                    inFaFileName += ".bestRefs"
                if os.path.exists( inFaFileName ):
                    allFileName = self.saveCopiesFromConsensus()
                    if allFileName != "":
                        alnAllFileName = self.launchMsa( allFileName )
                        self.launchPhylogeny( alnAllFileName )
                else:
                    msg = "ERROR: can't run this step because data are missing"
                    sys.stderr.write( "%s\n" % msg )
                    sys.exit(1)
                        
            # MSA consensus+copies, then MSA profiles (+ refseq if any)
            if "3e" in self._step:
                lProfilesFiles = self.launchRefalignForEachSetOfConsensusCopies()
                alnFile = "%s%s_profilesCopies.afa" % ( CLUSTER, self._familyID )
                self.alignProfilesAndBestRefseqs( lProfilesFiles, alnFile )
                self.launchPhylogeny( alnFile )
                
        os.chdir( "../.." )
        
        self.end()
        
#-----------------------------------------------------------------------------

class HandleAllGroupsOfConsensus:
    
    def __init__( self, pathToFaInFileName, pathToFaGrpFileName, clusteringMethod, annotTable="", configFileName="", pathToFaRefFileName="", pathToCompRefFileName="", verbose=0 ):
        self._workingDir = "data_per_%s" % CLUSTER
        self._pathToFaInFileName = pathToFaInFileName
        self._faInFileName = os.path.basename( self._pathToFaInFileName )
        self._dSeq2Length = FastaUtils.getLengthPerHeader( self._faInFileName )
        self._pathToFaGrpFileName = pathToFaGrpFileName
        self._faGrpFileName = os.path.basename( self._pathToFaGrpFileName )
        self._clusteringMethod = clusteringMethod
        self._annotTable = annotTable
        self._configFileName = configFileName
        self._config = ConfigParser.ConfigParser()
        if self._configFileName != "" and os.path.exists( self._configFileName ):
            self._config.readfp( open( self._configFileName ) )
#        self._faRefFileName = os.path.basename(pathToFaRefFileName)
#        self._pathToFaRefFileName = os.path.dirname(pathToFaRefFileName)
        self._pathToFaRefFileName = pathToFaRefFileName
        self._pathToCompRefFileName = pathToCompRefFileName
        self._verbose = verbose
        self._db = None
        self._tpA = None
        if self._configFileName != "":
            self._db = DbMySql( cfgFileName=self._configFileName )
            self._tpA = TablePathAdaptator( self._db, self._annotTable )
        self._dSeq2NbCopies = {}
        self._dSeq2NbFlCopies = {}
        self._dSeq2Group = {}
        self._dSeq2Cluster = {}
        
    def loadDataAboutClustering( self ):
        if self._verbose > 0:
            print "load data about the clustering..."
            sys.stdout.flush()
        lHeaders = FastaUtils.dbHeaders( self._pathToFaGrpFileName )
        lGroups = []
        for header in lHeaders:
            clusteringData = header.split("_")[0]
            seqname = "_".join(header.split("_")[1:])
            if self._clusteringMethod == "BlasterGrouper":
                clusterID = clusteringData.split("Cl")[1]
                groupID = clusteringData.split("Cl")[0].split("Gr")[1]
            else:
                clusterID = clusteringData.split("Cluster")[1].split("Mb")[0]
                groupID = "0"
            if not self._dSeq2Cluster.has_key( seqname ):
                self._dSeq2Cluster[ seqname ] = []
            if clusterID not in self._dSeq2Cluster[ seqname ]:
                self._dSeq2Cluster[ seqname ].append( clusterID )
            if not self._dSeq2Group.has_key( seqname ):
                self._dSeq2Group[ seqname ] = []
            if groupID not in self._dSeq2Group[ seqname ]:
                self._dSeq2Group[ seqname ].append( groupID )
            if groupID not in lGroups:
                lGroups.append( groupID )
        if self._verbose > 0 and self._clusteringMethod == "BlasterGrouper":
            print "nb of groups (members): %i" % ( len(lGroups) )
            sys.stdout.flush()
            
    def getNbCopiesPerConsensus( self ):
        if self._verbose > 0:
            print "retrieve the nb of copies per sequence..."
            sys.stdout.flush()
        for sbj in self._tpA.getSubjectList():
            self._dSeq2NbCopies[sbj] = len( self._tpA.getIdListFromSubject(sbj) )
        if self._verbose > 0:
            print "nb of consensus with copies: %i" % ( len(self._dSeq2NbCopies) )
            sys.stdout.flush()
            
    def getNbFlCopiesPerConsensus( self ):
        """
        By full-length, we mean +-5% of the length of the consensus sequence.
        """
        if self._verbose > 0:
            print "retrieve the nb of full-length copies per sequence..."
            sys.stdout.flush()
        for sbj in self._tpA.getSubjectList():
            lIdFlCopies = self._tpA.getIdListFromSubjectWhereChainsLongerThanThreshold( sbj,
                                                                                        0.95 * self._dSeq2Length[sbj] )
            self._dSeq2NbFlCopies[ sbj ] = len( lIdFlCopies )
        if self._verbose > 0:
            print "nb of consensus with full-length copies: %i" % ( len(self._dSeq2NbFlCopies) )
            sys.stdout.flush()
            
    def loadFaRef( self ):
        if self._verbose > 0:
            print "load reference sequences..."
            sys.stdout.flush()
        bank = BioseqDB( self._pathToFaRefFileName )
        if self._verbose > 0:
            print "nb of reference sequences: %i" % ( bank.getSize() )
            sys.stdout.flush()
        return bank
    
    def loadCompRef( self ):
        if self._verbose > 0:
            print "load comparison 'de novo consensus' versus 'reference sequences'..."
            sys.stdout.flush()
        dQuery2Matches = {}
        compRefF = open( self._pathToCompRefFileName, "r" )
        line = compRefF.readline()
        while True:
            line = compRefF.readline()
            if line == "": break
            tokens = line.split("\t")
            m = Match()
            m.setFromTuple( tokens )
            if not dQuery2Matches.has_key( m.range_query.seqname ):
                dQuery2Matches[ m.range_query.seqname ] = []
            if m.getScore() != 0:
                dQuery2Matches[ m.range_query.seqname ].append( m )
        compRefF.close()
        if self._verbose > 0:
            print "nb of refseq with matches: %i" % ( len(dQuery2Matches.keys()) )
            sys.stdout.flush()
        return dQuery2Matches
    
    def retrieveFullSeqWithCopies( self, qryDB, familyID ):
        if self._verbose > 1:
            print " retrieve full sequences..."
        memberFileName = "%s%s.fa" % ( CLUSTER, familyID )
        memberDB = BioseqDB( memberFileName )
        fullseqFileName = "%s.fullS" % ( memberFileName )
        if os.path.exists( fullseqFileName ):
            os.remove( fullseqFileName )
        fullseqDB = BioseqDB()
        for bs in memberDB.db:
            bsTmp = qryDB.fetch( "_".join(bs.header.split("_")[1:]) )
            if not fullseqDB.idx.has_key( bsTmp.header ):
                fullseqDB.add( bsTmp )
                if self._verbose > 2:
                    print "  add '%s'" % ( bsTmp.header ); sys.stdout.flush()
                bsTmp.save( "%s_consensus.fa" % ( bsTmp.header ) )
        fullseqDB.save( fullseqFileName )
        if self._verbose > 1:
            print " retrieved %i sequences" % ( fullseqDB.getSize() )
            sys.stdout.flush()
        del fullseqDB
        return fullseqFileName
    
    def addSequenceLengthToHeaders( self, inFileName ):
        if self._verbose > 1:
            print " add sequence length to headers..."; sys.stdout.flush()
        inDB = BioseqDB( inFileName )
        outFileName = "%s.seqlen" % ( inFileName )
        if os.path.exists( outFileName ):
            os.remove( outFileName )
        outDB = BioseqDB()
        for bs in inDB.db:
            if self._verbose > 2:
                print "  %s: %i bp" % ( bs.header, bs.getLength() )
                sys.stdout.flush()
            newH = "%s|%ibp" % ( bs.header, bs.getLength() )
            bs.header = newH
            outDB.add( bs )
        outDB.save( outFileName )
        del outDB
        return outFileName
    
    def addClusteringDataToHeaders( self, inFileName ):
        if self._verbose > 1:
            print " add clustering data to headers..."; sys.stdout.flush()
        inDB = BioseqDB( inFileName )
        clustFileName = "%s.clust" % ( inFileName )
        if os.path.exists( clustFileName ):
            os.remove( clustFileName )
        clustDB = BioseqDB()
        for bs in inDB.db:
            newH = "%s|%icl-%igr" % ( bs.header, len(self._dSeq2Cluster[bs.header]), len(self._dSeq2Group[bs.header]) )
            bs.header = newH
            clustDB.add( bs )
        clustDB.save( clustFileName )
        del clustDB
        return clustFileName
    
    def addNbCopiesToHeaders( self, inFileName, keepSeqWithoutCopy=True ):
        if self._verbose > 1:
            print " add nb of copies to headers..."; sys.stdout.flush()
        inDB = BioseqDB( inFileName )
        copyFileName = "%s.copy" % ( inFileName )
        if os.path.exists( copyFileName ):
            os.remove( copyFileName )
        copyDB = BioseqDB()
        for bs in inDB.db:
            initH = bs.header.split("|")[0]
            if self._dSeq2NbCopies.has_key( initH ):
                if self._verbose > 2:
                    print "  %s: %i copies %i full-length" % ( initH,
                                                               self._dSeq2NbCopies[ initH ],
                                                               self._dSeq2NbFlCopies[ initH ] )
                    sys.stdout.flush()
                if self._dSeq2NbCopies[ initH ] == 1:
                    bs.header += "|%icopy" % ( self._dSeq2NbCopies[ initH ] )
                elif self._dSeq2NbCopies[ initH ] > 1:
                    bs.header += "|%icopies" % ( self._dSeq2NbCopies[ initH ] )
                bs.header += "-%ifl" % ( self._dSeq2NbFlCopies[ initH ] )
                copyDB.add( bs )
            else:
                bs.header += "|0copy"
                if keepSeqWithoutCopy:
                    copyDB.add( bs )
        copyDB.save( copyFileName )
        del copyDB
        return copyFileName
    
    def addRefSeqsMatchingWithDeNovoConsensus( self, inFileName, dQuery2Matches, refDB, minCoverageOnRefSeq, category, outFileName ):
        if self._verbose > 1:
            print " add reference sequences (%s, coverage >= %i%%)..." % ( category, minCoverageOnRefSeq * 100 )
            sys.stdout.flush()
        inDB = BioseqDB( inFileName )
        if os.path.exists( outFileName ):
            os.remove( outFileName )
        outDB = BioseqDB()
        nbAddedRefSeqs = 0
        for bs in inDB.db:
            consensusH = bs.header.split("|")[0]
            if dQuery2Matches.has_key( consensusH ):
                lSortedMatches = AlignUtils.getAlignListSortedByDecreasingScoreThenLength( dQuery2Matches[ consensusH ] )
                i = 0
                match = lSortedMatches[i]
                while match.getLengthPercOnSubject() >= minCoverageOnRefSeq:
                    simRefH = match.range_subject.seqname
                    if not outDB.idx.has_key( simRefH ):
                        nbAddedRefSeqs += 1
                        if minCoverageOnRefSeq > 0 and self._verbose > 2:
                            print "  add '%s' (%i bp, coverage=%i%%)" % ( simRefH ,
                                                                          match.subject_length,
                                                                          match.getLengthPercOnSubject()*100 )
                            sys.stdout.flush()
                        bsRef = refDB.fetch( simRefH )
                        outDB.add( bsRef )
                        refF = open( "%s_%s.fa" % ( simRefH, category ), "w" )
                        bsRef.write( refF )
                        refF.close()
                    i += 1
                    if i < len(lSortedMatches):
                        match = lSortedMatches[i]
                    else:
                        break
        for bs in inDB.db:
            outDB.add( bs )
        outDB.save( outFileName )
        if self._verbose > 1:
            print " added %i sequence(s)" % ( nbAddedRefSeqs )
            sys.stdout.flush()
        del outDB
        return outFileName
    
    def addAllByAllSeqUsedToMakeConsensus( self, inFileName ):
        outFileName = "%s.aBa" % ( inFileName )
        if self._verbose > 1:
            print " add all-by-all sequences to '%s'..." % ( inFileName )
        if self._configFileName == "":
            shutil.copyfile( inFileName, outFileName )
            return outFileName
        TEdenovoProjectName = self._config.get( "project", "project_name" )
        TEdenovoProjectDirectory = self._config.get( "project", "project_dir" )
        lAllByAllFiles = [ inFileName ]
        lHeaderConsensus = FastaUtils.dbHeaders( inFileName )
        for header in lHeaderConsensus:
            if TEdenovoProjectName not in header: continue
            initHeader = header.split("|")[0]
            if self._verbose > 2:
                print "  add for consensus '%s'" % ( initHeader )
                sys.stdout.flush()
            if "-" in initHeader:
                selfalignMethod = initHeader.split("-")[1]
                clusteringMethod = initHeader.split("-")[2]
                clusterId = clusteringMethod[1:]
                multiplalignMethod = initHeader.split("-")[3]
            else:
                selfalignMethod = initHeader.split("_")[1]
                clusteringMethod = initHeader.split("_")[2]
                clusterId = initHeader.split("_")[3]
                multiplalignMethod = initHeader.split("_")[4]
            if "B" in selfalignMethod:
                selfalignMethod = "Blaster"
            elif "P" in selfalignMethod:
                selfalignMethod = "Pals"
            if "G" in clusteringMethod:
                clusteringMethod = "Grouper"
            elif "R" in clusteringMethod:
                clusteringMethod = "Recon"
            elif "P" in clusteringMethod:
                clusteringMethod = "Piler"
            if "Map" in multiplalignMethod:
                multiplalignMethod = "Map"
            elif "MAP" in multiplalignMethod:
                multiplalignMethod = "MAP"
            elif "Mafft" in multiplalignMethod:
                multiplalignMethod = "Mafft"
            else:
                print "method '%s' not yet supported" % ( multiplalignMethod )
                sys.exit(1)
            targetDir = "%s/%s_%s_%s_%s" % ( TEdenovoProjectDirectory, TEdenovoProjectName, selfalignMethod, clusteringMethod, multiplalignMethod )
            if os.path.exists( "%s/seqCluster%s.fa.chr" % ( targetDir, clusterId ) ):
                lAllByAllFiles.append( "%s/seqCluster%s.fa.chr" % ( targetDir, clusterId ) )
                shutil.copy( "%s/seqCluster%s.fa.chr" % ( targetDir, clusterId ), "%s_AbaMatches.fa" % ( initHeader ) )
            else:
                lAllByAllFiles.append( "%s/seqCluster%s.fa" % ( targetDir, clusterId ) )
                shutil.copy( "%s/seqCluster%s.fa" % ( targetDir, clusterId ), "%s_AbaMatches.fa" % ( initHeader ) )
        FileUtils.catFilesFromList( lAllByAllFiles, outFileName )
        return outFileName
    
    def run( self, keepSeqWithoutCopy=True, cleanEmptyGroup=False ):
        if self._verbose > 0:
            print "add data to headers and filter..."; sys.stdout.flush()
            
        self.loadDataAboutClustering()
        qryDB = BioseqDB( self._pathToFaInFileName )
        if self._annotTable != "":
            self.getNbCopiesPerConsensus()
            self.getNbFlCopiesPerConsensus()
        if os.path.exists( self._pathToFaRefFileName ):
            refDB = self.loadFaRef()
        if os.path.exists( self._pathToCompRefFileName ):
            dQuery2Matches = self.loadCompRef()
            
        os.chdir( self._workingDir )
        if os.path.exists( self._faInFileName ):
            os.remove( self._faInFileName )
        os.symlink( self._pathToFaInFileName, self._faInFileName )
        
        lFamilyDirs = glob.glob( "%s_*" % CLUSTER)
        lFamilyDirs.sort()
        nbFamiliesWithoutCopy = 0
        nbFamiliesWithOneSeq = 0
        countFamily = 0
        for familyDir in lFamilyDirs:
            countFamily += 1
            familyID = str( int( familyDir.split( "%s_" % CLUSTER )[1] ) )
            if self._verbose > 1:
                print "processing %s %s (%i/%i)..." % ( CLUSTER, familyID, countFamily, len(lFamilyDirs) )
            os.chdir( familyDir )
            tmpFileName = self.retrieveFullSeqWithCopies( qryDB, familyID )
            if FastaUtils.dbSize( tmpFileName ) == 1:
                nbFamiliesWithOneSeq += 1
            if self._clusteringMethod == "BlasterGrouper":
                tmpFileName = self.addClusteringDataToHeaders( tmpFileName )
            tmpFileName = self.addSequenceLengthToHeaders( tmpFileName )
            if self._annotTable != "":
                tmpFileName = self.addNbCopiesToHeaders( tmpFileName, keepSeqWithoutCopy )
                if not keepSeqWithoutCopy and cleanEmptyGroup:
                    copyDB = BioseqDB( tmpFileName )
                    if copyDB.getSize() == 0:
                        print "%s '%s' removed because no consensus has copy" % ( CLUSTER, familyID ); sys.stdout.flush()
                        os.chdir( ".." )
                        os.system( "rm -r %s" % ( familyDir ) )
                        nbFamiliesWithoutCopy += 1
                        continue
            if os.path.exists( self._pathToCompRefFileName ) and os.path.exists( self._pathToFaRefFileName ):
                self.addRefSeqsMatchingWithDeNovoConsensus( tmpFileName, dQuery2Matches, refDB, 0, "allRef", tmpFileName + ".allRefs" )
                self.addRefSeqsMatchingWithDeNovoConsensus( tmpFileName, dQuery2Matches, refDB, 0.5, "bestRef", tmpFileName + ".bestRefs" )
            self.addAllByAllSeqUsedToMakeConsensus( tmpFileName )
            if os.path.exists( self._pathToCompRefFileName ) and os.path.exists( self._pathToFaRefFileName ):
                self.addRefSeqsMatchingWithDeNovoConsensus( tmpFileName + ".aBa", dQuery2Matches, refDB, 0, "allRef", tmpFileName + ".aBa.allRefs" )
                self.addRefSeqsMatchingWithDeNovoConsensus( tmpFileName + ".aBa", dQuery2Matches, refDB, 0.5, "bestRef", tmpFileName + ".aBa.bestRefs" )
            os.chdir( ".." )
            
        if self._verbose > 0 and self._annotTable != "":
            print "nb of TE families: %i" % ( len(lFamilyDirs) )
            print "nb of TE families with copies: %i" % ( len(lFamilyDirs) - nbFamiliesWithoutCopy )
            print "nb of TE families with variants: %i" % ( len(lFamilyDirs) - nbFamiliesWithOneSeq )
        os.chdir( ".." )
        if self._db != None:
            self._db.close()

#-----------------------------------------------------------------------------

def compareInputSeqAndQueries( inFileName, verbose ):

    lDistinctQueries = []
    alignFile = open( "%s.align" % ( inFileName ), "r" )
    line = alignFile.readline()
    while True:
        if line == "":
            break
        queryName = line.split("\t")[0]
        if queryName not in lDistinctQueries:
            lDistinctQueries.append( queryName )
        line = alignFile.readline()
    alignFile.close()
    
    lDistinctInputSequences = []
    lOrphanSequences = []
    faFile = open( inFileName, "r" )
    line = faFile.readline()
    while True:
        if line == "":
            break
        if line[0] == ">":
            seqName = line[1:-1]
            if seqName not in lDistinctInputSequences:
                lDistinctInputSequences.append( seqName )
            if seqName not in lDistinctQueries:
                lOrphanSequences.append( seqName )
        line = faFile.readline()
    faFile.close()
    
    if verbose > 0:
        print "nb of distinct sequences in '%s': %i" % ( inFileName, len(lDistinctInputSequences) )
        print "nb of distinct queries in '%s.align': %i" % (  inFileName, len(lDistinctQueries) )
        print "percentage of input sequences having a match: %.2f%%" % ( 100 * len(lDistinctQueries) / float(len(lDistinctInputSequences)) )
        sys.stdout.flush()
        
    outFileName = "%s.orphan" % ( inFileName )
    outF = open( outFileName, "w" )
    for seqName in lOrphanSequences:
        outF.write( "%s\n" % ( seqName ) )
        if verbose > 1:
            print "input sequence '%s' has no match with other input sequences" % ( seqName )
    outF.close()
    
#-----------------------------------------------------------------------------

if __name__ == "__main__":
    i = ClusterConsensus()
    i.setAttributesFromCmdLine()
    i.run()
