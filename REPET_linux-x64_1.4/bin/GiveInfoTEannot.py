#!/usr/bin/env python

##@file
# Give summary information on a TE annotation table.
# options:
#     -h: this help
#     -t: analysis type (default = 1, 1: per transposable element (TE), 2: per cluster, 3: per classification, 4: with map input file)
#     -p: name of the table (_path) or file (.path) with the annotated TE copies
#     -s: name of the table (_seq) or file (.fasta or .fa) with the TE reference sequences
#     -g: length of the genome (in bp)
#     -m: name of the file with the group and the corresponding TE names (format = 'map')
#     -o: name of the output file (default = pathTableName + '_stats.txt')
#     -C: name of the configuration file to access MySQL (e.g. 'TEannot.cfg')
#     -c: remove map files and blastclust file (if analysis type is 2 or 3)
#     -I: identity coverage threshold (default = 0)
#     -L: length coverage threshold (default=0.8)
#     -v: verbosity level (default = 0)

import os
import re
import sys
import getopt
from pyRepetUnit.commons.sql.DbMySql import DbMySql
from pyRepetUnit.commons.sql.TablePathAdaptator import TablePathAdaptator
from pyRepetUnit.commons.sql.TableSeqAdaptator import TableSeqAdaptator
from pyRepetUnit.commons.utils.FileUtils import FileUtils
from pyRepetUnit.commons.stat.Stat import Stat
from repet_tools.getCumulLengthFromTEannot import getCumulLengthFromTEannot
from repet_tools.ManageConsensusClusters import ManageConsensusClusters
from repet_tools.GiveInfoTEannotWriter import GiveInfoTEannotWriter

CONSENSUS = "TE"
CLUSTER = "Cluster"
CLASSIF = "Classif"
GROUP = "Group"

class GiveInfoTEannot( object ):

    def __init__( self ):
        self._analyseType = "1"
        self._analyseName = CONSENSUS
        self._pathName = ""
        self._seqName = ""
        self._genomeLength = 0
        self._outFileName = ""
        self._configFileName = ""
        self._verbose = 0
        self._iDb = None
        self._iTablePathAdaptator = None
        self._iTableSeqAdaptator = None
        self._iMapConsensusPerGroup = None
        self._mapFileName = ""
        self._coverageThreshold = "0.8"
        self._identityThreshold = "0"
        self._save = False
        self._clean = False
        self._seqFileHaveToBeRemoved = False
        
    def help( self ):
        print
        print "usage:",sys.argv[0].split("/")[-1],"[options]"
        print "options:"
        print "     -h: this help"
        print "     -p: name of the table (_path) or file (.path) with the annotated TE (transposable element) copies"
        print "     -s: name of the table (_seq) or file (.fasta or .fa) with the TE reference sequences"
        print "        NOTE: if you give files, corresponding tables will be created, but not cleaned"
        print "     -g: length of the genome (in bp)"
        print "     -C: name of the configuration file to access MySQL (e.g. 'TEdenovo.cfg')"
        print "     -o: name of the output file (default = path table name + '_stats.txt')"
        print "     -l: load the results in database"
        print "     -v: verbosity level (default = 0, 1 or 2)"
        print "     -t: analysis type (default = 1, 1: per TE, 2: per cluster)"
#        print "     -t: analysis type (default = 1, 1: per TE, 2: per cluster, 3: per classification, 4: with map input file)"
        print
        print "    if -t 2:"
        print "     -c: remove map files and blastclust file"
        print "     -I: identity coverage threshold (default = 0) for blastclust"
        print "     -L: length coverage threshold (default = 0.8) for blastclust"
#        print "    if -t 2 or 3:"
#        print "     -c: remove map files and blastclust file"
#        print "     -I: identity coverage threshold (default = 0) for blastclust"
#        print "     -L: length coverage threshold (default = 0.8) for blastclust"
#        print
#        print "    if -t 4 :"
#        print "     -m: name of the file with the group and the corresponding TE names (format = 'map')"
        print        
        print "Examples:"
        print "    - Statistics per TEs:"
        print "        python GiveInfoTEannot.py -p DmelCaf1_chr_allTEs_nr_noSSR_join_path -s DmelCaf1_refTEs_seq -g 129919500 -C TEdenovo.cfg"
        print
        print "    - Statistics per cluster of TEs:"
        print "        python GiveInfoTEannot.py -p DmelCaf1_chr_allTEs_nr_noSSR_join_path -s DmelCaf1_refTEs_seq -g 129919500 -C TEdenovo.cfg -t 2 -c"
        print
        print "    - Statistics per cluster of TEs with 95% minimum of coverage between TEs:"
        print "        python GiveInfoTEannot.py -p DmelCaf1_chr_allTEs_nr_noSSR_join_path -s DmelCaf1_refTEs_seq -g 129919500 -C TEdenovo.cfg -t 2 -L 0.95 -c"
        print
#        print "    - Statistics per classification of TEs (clusters built by blastclust and clusters classification find from the TEdenovo headers):"
#        print "        python GiveInfoTEannot.py -p DmelCaf1_chr_allTEs_nr_noSSR_join_path -s DmelCaf1_refTEs_seq -g 129919500 -C TEdenovo.cfg -t 3 -c"
#        print
#        print "    - Statistics per any group of TEs (groups given by the map file):"
#        print "        python GiveInfoTEannot.py -p DmelCaf1_chr_allTEs_nr_noSSR_join_path -s DmelCaf1_refTEs_seq -g 129919500 -C TEdenovo.cfg -t 4 -m inputFileName.map"
        
    ## Set the attributes from the command-line
    #
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:],"ht:p:s:g:m:C:o:lcI:L:v:")
        except getopt.GetoptError, err:
            print str(err); self.help(); sys.exit(1)
        for o,a in opts:
            if o == "-h":
                self.help()
                sys.exit(0)
            elif o == "-t":
                self._analyseType = a
            elif o == "-p":
                self._pathName = a
            elif o == "-s":
                self._seqName = a
            elif o == "-g":
                self._genomeLength = int(a)
            elif o == "-m":
                self._mapFileName = a
            elif o == "-C":
                self._configFileName = a
            elif o == "-o":
                self._outFileName = a
            elif o == "-l":
                self._save = True
            elif o == "-c":
                self._clean = True
            elif o == "-I":
                self.setIdentityThreshold(a)
            elif o == "-L":
                self.setCoverageThreshold(a)
            elif o == "-v":
                self._verbose = int(a)
    
    ## Check the attributes are valid before running the algorithm
    #            
    def checkAttributes( self ):
        if self._pathName == "":
            print "ERROR: missing path option (-p)"
            self.help()
            sys.exit(1)
        if self._seqName == "":
            print "ERROR: missing seq option (-s)"
            self.help()
            sys.exit(1)
        if self._genomeLength == 0:
            print "ERROR: missing genome length (-g)"
            self.help()
            sys.exit(1)
        if self._configFileName == "":
            print "ERROR: missing configuration file"
            self.help()
            sys.exit(1)
        if self._analyseType == "4":
            self._analyseName = GROUP
            if self._mapFileName == "":
                print "ERROR: missing map file"
                self.help()
                sys.exit(1)
            if not FileUtils.isRessourceExists(self._mapFileName):
                sys.stderr.write("ERROR: %s file doesn't exist !\n" % self._mapFileName)
                sys.exit(1)
        
    def setCoverageThreshold( self, lengthThresh ):
        self._coverageThreshold = float(lengthThresh)
                
    def setIdentityThreshold( self, identityThresh ):
        self._identityThreshold = int(identityThresh)
            
    def setPathName(self, pathName):
        self._pathName = pathName
            
    def setSeqName(self, seqName):
        self._seqName = seqName
            
    def setAnalyseType(self, analyseType):
        self._analyseType = str(analyseType)
            
    def setPathTableName(self, pathTableName):
        self._pathTableName = pathTableName
        
    def setDBInstance(self, iDb):
        self._iDb = iDb
        
    def setTablePathAdaptator(self, iTablePathAdaptator):
        self._iTablePathAdaptator = iTablePathAdaptator
        
    def setTableSeqAdaptator(self, iTableSeqAdaptator):
        self._iTableSeqAdaptator = iTableSeqAdaptator
    
    ## Get the coverage of TE copies for a given family (using 'mapOp')
    #
    # @param consensus string name of a TE family ('subject_name' in the 'path' table)
    # @return cumulCoverage integer cumulative coverage
    #
    def getCumulCoverage( self, consensus = "" ):
        gclft = getCumulLengthFromTEannot()
        gclft.setInputTable( self._pathTableName )
        gclft.setTErefseq( consensus )
        gclft.setConfigFileName( self._configFileName )
        gclft.setClean()
        gclft._db = self._iDb
        gclft._tpA = self._iTablePathAdaptator
        mapFileName = gclft.getAllSubjectsAsMapOfQueries()
        mergeFileName = gclft.mergeRanges( mapFileName )
        cumulCoverage = gclft.getCumulLength( mergeFileName ) #self._iTablePathAdaptator.getCumulPathLength_from_subject( consensus )
        return cumulCoverage
    
    ## Get the number of full-lengths (95% <= L =< 105%)
    #
    # @param consensusLength integer
    # @param lLengths list of integers
    # @return fullLengthConsensusNb integer
    #
    def getNbFullLengths( self, consensusLength, lLengths ):
        fullLengthConsensusNb = 0
        for i in lLengths:
            if i / float(consensusLength ) >= 0.95 and i / float(consensusLength ) <= 1.05:
                fullLengthConsensusNb += 1
        return fullLengthConsensusNb
    
    def getStatPerGroup( self, lConsensusNames ):
        dOneGroupOfConsensus = { "maxLength": 0,
                                "meanLength": 0,
                        "cumulCoverage": 0,
                        "nbFragments": 0,
                        "nbFullLengthFragments": 0,
                        "nbCopies": 0,
                        "nbFullLengthCopies": 0,
                        "statsIdentityPerChain": Stat(),
                        "statsLengthPerChain": Stat(),
                        "statsLengthPerChainPerc": Stat()
                        }
        lLength = []
        lLengthPerFragment = []
        lLengthPerCopy = []
        lIdentityPerCopy = []
        cumulCoverageLength = 0
        for consensusName in lConsensusNames:
            lLength.append(self._iTableSeqAdaptator.getSeqLengthFromAccession(consensusName))
            cumulCoverageLength += self.getCumulCoverage(consensusName)
            lLengthPerFragment.extend(self._iTablePathAdaptator.getPathLengthListFromSubject(consensusName))
            lLengthPerCopy.extend(self._iTablePathAdaptator.getChainLengthListFromSubject(consensusName))
            lIdentityPerCopy.extend(self._iTablePathAdaptator.getChainIdentityListFromSubject(consensusName))
        dOneGroupOfConsensus["maxLength"] = int(max(lLength))
        dOneGroupOfConsensus["meanLength"] = self._getIntegerMean(lLength)
        dOneGroupOfConsensus["cumulCoverage"] = cumulCoverageLength
        dOneGroupOfConsensus["nbFragments"] = len(lLengthPerFragment)
        dOneGroupOfConsensus["nbFullLengthFragments"] = self.getNbFullLengths(dOneGroupOfConsensus["maxLength"], lLengthPerFragment)
        dOneGroupOfConsensus["nbCopies"] = len(lLengthPerCopy)
        dOneGroupOfConsensus["nbFullLengthCopies"] = self.getNbFullLengths( dOneGroupOfConsensus["maxLength"], lLengthPerCopy )
        self._statsForIdentityAndLength(dOneGroupOfConsensus, lLengthPerCopy, lIdentityPerCopy)
        return dOneGroupOfConsensus
    
    def createTablesAndSeqFileIfNeeded(self):
        if re.search("\.path", self._pathName):
            if FileUtils.isRessourceExists(self._pathName):
                pathFileName = os.path.basename(self._pathName)
                self._pathTableName = pathFileName.replace(".", "_")
                self._iDb.createTable(self._pathTableName, "path", self._pathName)
            else:
                sys.stderr.write("ERROR: %s file doesn't exist !\n" % self._pathName)
                sys.exit(1)
        else:
            self._pathTableName = self._pathName
            if not self._iDb.doesTableExist(self._pathTableName):
                sys.stderr.write("ERROR: %s table doesn't exist !\n" % self._pathTableName)
                sys.exit(1)
                
        if re.search("\.fasta", self._seqName) or re.search("\.fa", self._seqName):
            if FileUtils.isRessourceExists(self._seqName):
                self._seqFileName = self._seqName
                seqFileName = os.path.basename(self._seqName)
                self._seqTableName = seqFileName.replace(".", "_").replace("_fasta", "_seq").replace("_fa", "_seq")
                self._iDb.createTable(self._seqTableName, "seq", self._seqName)
            else:
                sys.stderr.write("ERROR: %s file doesn't exist !\n" % self._seqName)
                sys.exit(1)
        else:
            self._seqTableName = self._seqName
            if not self._iDb.doesTableExist(self._seqTableName):
                sys.stderr.write("ERROR: %s table doesn't exist !\n" % self._seqTableName)
                sys.exit(1)
            elif self._analyseType in "23":
                self._seqFileName = self._seqTableName.replace("_seq", ".fasta")
                if not os.path.exists(self._seqFileName):
                    iTableSeqAdaptator = TableSeqAdaptator(self._iDb, self._seqTableName)
                    iTableSeqAdaptator.exportInFastaFile(self._seqFileName)
                    self._seqFileHaveToBeRemoved = True
                    #TODO: do the same for path and seq tables ? Remove them if we create them ?
            
    def getDictFromMapFile(self, fileHandler):
        dGroupName2consensusList = {}
        for line in fileHandler.readlines():
            lElements = line.rstrip().split("\t")
            dGroupName2consensusList[lElements[0]] = lElements[1:]
        return dGroupName2consensusList
    
    def start( self ):
        self.checkAttributes()
        if self._verbose > 0:
            print "START %s" % type(self).__name__
            sys.stdout.flush()
        self._iDb = DbMySql(cfgFileName = self._configFileName)
        self.createTablesAndSeqFileIfNeeded()
        self._iTablePathAdaptator = TablePathAdaptator(self._iDb, self._pathTableName)
        self._iTableSeqAdaptator = TableSeqAdaptator(self._iDb, self._seqTableName)
        
    def end( self ):
        self._iDb.close()
        if self._verbose > 0:
            print "END %s" % type(self).__name__
            sys.stdout.flush()
    
    def run(self):
        self.start()
        
        if self._analyseType == "1":
            lNamesTErefseq = self._iTableSeqAdaptator.getAccessionsList()
            iList = ConsensusList(lNamesTErefseq)
        else:
            if self._analyseType in "23":
                self._writeMapFile()
            fileHandler = open(self._mapFileName, "r")
            dGroup2ConsensusList = self.getDictFromMapFile(fileHandler)
            fileHandler.close()
            if self._clean and not self._analyseType == "4":
                os.remove(self._mapFileName)
            if self._seqFileHaveToBeRemoved:
                os.remove(self._seqFileName)
            iList = GroupList(dGroup2ConsensusList, self._analyseType)
        
        self._computeStatsAndWriteOutputFile(iList)
        
        if self._save:
            outTableName = "%s_statsPer%s" % (self._pathTableName, self._analyseName)
            self._iDb.createPathStatTable(outTableName, self._outFileName)
        
        self.end()

    def _getIntegerMean(self, l):
        return int(round(sum(l)/float(len(l))))

    def _statsForIdentityAndLength(self, dStat, lLengthPerCopy, lIdentityPerCopy):
        for i in lIdentityPerCopy:
            dStat["statsIdentityPerChain"].add(i)
        #TODO: lLengthPercPerCopy ?
        lLengthPercPerCopy = []
        for i in lLengthPerCopy:
            dStat["statsLengthPerChain"].add(i)
            lperc = 100 * i / float(dStat["maxLength"])
            lLengthPercPerCopy.append(lperc)
            dStat["statsLengthPerChainPerc"].add(lperc)

    def _computeStatsAndWriteOutputFile(self, iConsensusOrGroupList):
        if self._outFileName == "":
            self._outFileName = "%s_statsPer%s.txt" % (self._pathTableName, self._analyseName)
        outF = open(self._outFileName, "w")
        string = "%s\tmaxLength\tmeanLength\tcovg" % self._analyseName
        string += "\tfrags\tfullLgthFrags\tcopies\tfullLgthCopies" # 4 items
        string += "\tmeanId\tsdId\tminId\tq25Id\tmedId\tq75Id\tmaxId" # 7 items
        string += "\tmeanLgth\tsdLgth\tminLgth\tq25Lgth\tmedLgth\tq75Lgth\tmaxLgth" # 7 items
        string += "\tmeanLgthPerc\tsdLgthPerc\tminLgthPerc\tq25LgthPerc\tmedLgthPerc\tq75LgthPerc\tmaxLgthPerc" # 7 items
        string += "\n"
        outF.write(string)
        
        iGiveInfoTEannotWriter = GiveInfoTEannotWriter()
        lNamesTErefseq = self._iTableSeqAdaptator.getAccessionsList()
        lDistinctSubjects = self._iTablePathAdaptator.getSubjectList()
        totalCumulCoverage = self.getCumulCoverage()
        
        if self._verbose > 0:
            iGiveInfoTEannotWriter.printResume(lNamesTErefseq, lDistinctSubjects, totalCumulCoverage, self._genomeLength)
  
        for consensusOrGroup in iConsensusOrGroupList:
            if self._verbose > 1:
                print "processing '%s'..." % consensusOrGroup
                sys.stdout.flush()

            dStatForOneGroup = self.getStatPerGroup(iConsensusOrGroupList.getConsensusList())
            if self._verbose > 1:
                iGiveInfoTEannotWriter.printStatsForOneTE(dStatForOneGroup)
            iGiveInfoTEannotWriter.addCalculsOfOneTE(dStatForOneGroup)
            string = iGiveInfoTEannotWriter.getStatAsString(consensusOrGroup, dStatForOneGroup)
            
            outF.write("%s\n" % string)
        
        outF.close()
        if self._verbose > 0:
            iGiveInfoTEannotWriter.printStatsForAllTEs(len(lNamesTErefseq))

    def _writeMapFile(self):
        self._iMCC = ManageConsensusClusters()
        if self._analyseType == "2":
            self._iMCC.setStep("1")
            self._mapFileName = self._iMCC.getClusterFileName()
            self._analyseName = CLUSTER
        elif self._analyseType == "3":
            self._iMCC.setStep("123")
            self._mapFileName = self._iMCC.getClusterGroupFileName()
            self._analyseName = CLASSIF
        self._iMCC.setInputFileName(self._seqFileName)
        self._iMCC.setVerbosity(self._verbose)
        self._iMCC.setIdentityThreshold(self._identityThreshold)
        self._iMCC.setCoverageThreshold(self._coverageThreshold)
        if not self._clean:
            self._iMCC.setClean()
        self._iMCC.run()


class GroupList (object):
    
    def __init__(self, dGroup2ConsensusList, type):
        self._dGroup2ConsensusList = dGroup2ConsensusList
        self._index = 0
        if type == "2":
            self._lGroup = sorted(dGroup2ConsensusList.keys(), key=int)
        else:
            self._lGroup = sorted(dGroup2ConsensusList.keys())

    def __iter__(self):
        return self
    
    def next(self):
        if self._index == len(self._lGroup):
            raise StopIteration
        else:
            next = self._lGroup[self._index]
            self._index += 1
            return next
        
    def getConsensusList(self):
        group = self._lGroup[self._index - 1]
        return self._dGroup2ConsensusList[group]
    
class ConsensusList(object):
    
    def __init__(self, lConsensus):
        self._lConsensus = lConsensus
        self._index = 0
        
    def __iter__(self):
        return self
    
    def next(self):
        if self._index == len(self._lConsensus):
            raise StopIteration
        else:
            next = self._lConsensus[self._index]
            self._index += 1
            return next
    
    def getConsensusList(self):
        consensus = self._lConsensus[self._index - 1]
        return [consensus]

if __name__ == "__main__":
    i = GiveInfoTEannot()
    i.setAttributesFromCmdLine()
    i.run()
