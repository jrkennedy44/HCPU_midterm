#!/usr/bin/env python

from repet_base.LaunchBlastclust import LaunchBlastclust
from repet_tools.ConsensusCluster import TEclassifierConsensusCluster
from repet_tools.ConsensusCluster import ConsensusCluster
from pyRepetUnit.commons.utils.FileUtils import FileUtils
from pyRepetUnit.commons.parsing.FastaParser import FastaParser
import getopt
import sys
import os
import re

#TODO: add blastclust options (identity, coverage)
#TODO: refactoring:
#    - options (optparse, ...)
#    - input file = blastclust output (not "LaunchBlastclust" output with formated headers)
#    - step 1
#    - findMainClassif() of ConsensusCluster
#    - clean files at end run

class ManageConsensusClusters(object):

    CONSENSUS = "TE"
    CLUSTER = "Cluster"

    def __init__(self):
        self._step = "123"
        self._inputFileName = ""
        self._outputFileName = ""
        self._blastclustFileName = ""
        self._clusterFileName = "%s2%s.map" % (self.CLUSTER, self.CONSENSUS)
        self._classifiedClusterFileName = "classified%s2%s.map" % (self.CLUSTER, self.CONSENSUS)
        self._clusterGroupFileName = "%sGroup2%s.map" % (self.CLUSTER, self.CONSENSUS)
        self._coverageThreshold = "0.8"
        self._identityThreshold = "0"
        self._clean = True
        self._isTEclassifierClassif = True
        self._verbose = 0
        
    def help(self):
        print
        print "usage:",sys.argv[0].split("/")[-1],"[options]"
        print "This script can be usefull after the TEdenovo pipeline to build TE families according to the classification"
        print
        print "options:"
        print "     -h: this help"
        print "     -s: step (default = 123)"
        print "            1: TE consensus clustering with Blastclust"
        print "            2: clusters classification"
        print "            3: clusters group according to classification"
        print "     -i: input file name (format = 'fasta')"
        print "     -o: output file name (format = 'map', default according to the step)"
#        print "     -P: is a classification from PASTEC"
        print        
#        print "Example: ManageConsensusClusters.py -i VV_chr12x_refTEs_WickerH.fa -P"
        print "Example: ManageConsensusClusters.py -i DmelChr4_denovoLibTEs.fa"
        
    ## Set the attributes from the command-line
    #
    def setAttributesFromCmdLine( self ):
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hs:i:o:P")
        except getopt.GetoptError, err:
            print str(err)
            self.help()
            sys.exit(1)
        for o, a in opts:
            if o == "-h":
                self.help()
                sys.exit(0)
            elif o == "-s":
                self._step = a
            elif o == "-i":
                self._inputFileName = a
            elif o == "-o":
                self._outputFileName = a
            elif o == "-P":
                self.setIsTEclassifierClassif()

    def setStep(self, step):
        self._step = step

    def setInputFileName(self, inFileName):
        self._inputFileName = inFileName
    
    def setClassifiedClusterFileName(self, fileName): 
        self._outputClassifiedClusterFileName = fileName
        
    def setClusterFileName(self, fileName):
        self._outputClusterFileName = fileName
        
    def setBlastclustFileName(self, fileName):
        self._blastclustFileName = fileName
        
    def setCoverageThreshold( self, lengthThresh ):
        self._coverageThreshold = float(lengthThresh)
                
    def setIdentityThreshold( self, identityThresh ):
        self._identityThreshold = int(identityThresh)
        
    def setClean(self):
        self._clean = False
        
    def setIsTEclassifierClassif(self):
        self._isTEclassifierClassif = False
        
    def setVerbosity(self, verbose):
        self._verbose = verbose
        
    def getClusterFileName(self):
        return self._clusterFileName
        
    def getClusterGroupFileName(self):
        return self._clusterGroupFileName
    
    ## Check the attributes are valid before running the algorithm
    #            
    def checkAttributes( self ):
        if self._step not in "123":
            print "ERROR: unknown specified step (-s option)"
            self.help()
            sys.exit(1)
        if self._inputFileName == "":
            print "ERROR: missing input file (-i option)"
            self.help()
            sys.exit(1)
        if not FileUtils.isRessourceExists(self._inputFileName):
            sys.stderr.write("ERROR: %s file doesn't exist !\n" % self._inputFileName)
            sys.exit(1)
        if "1" in self._step:
            self._blastclustFileName = self._inputFileName
            if self._outputFileName != "":
                self._clusterFileName = self._outputFileName
        elif "2" in self._step:
            self._clusterFileName = self._inputFileName
            if self._outputFileName != "":
                self._classifiedClusterFileName = self._outputFileName
        elif "3" in self._step:
            self._classifiedClusterFileName = self._inputFileName
            if self._outputFileName != "":
                self._clusterGroupFileName = self._outputFileName
    
    def launchBlastclust(self):
        inputFileName = "%s/%s" % (os.getcwd(), os.path.basename(self._inputFileName))
        if not os.path.exists(inputFileName):
            os.symlink(self._inputFileName, inputFileName)
        lbc = LaunchBlastclust()
        lbc.setInputFileName(inputFileName)
        lbc.setCoverageThreshold(self._coverageThreshold)
        lbc.setIdentityThreshold(self._identityThreshold)
        lbc.setBothSequences("F")
        lbc.setClean()
        lbc.setVerbosityLevel(self._verbose)
        lbc.run()
        if os.path.islink(inputFileName):
            os.remove(inputFileName)
        return "%s_blastclust.fa" % inputFileName
        
    def extractHeadersList(self):
        iFastaParser = FastaParser(self._blastclustFileName)
        iFastaParser.setTags()
        return iFastaParser.getTags().keys()
    
    def headerList2Dict(self, lHeaders):
        dCluster2ConsensusList = {}
        for header in lHeaders:
            clusterName, consensusName = self._extractClusterNameAndConsensusName(header)
            if clusterName in dCluster2ConsensusList.keys():
                dCluster2ConsensusList[clusterName].append(consensusName)
            else:
                dCluster2ConsensusList[clusterName] = [consensusName]
            dCluster2ConsensusList[clusterName].sort()
        return dCluster2ConsensusList
    
    def writeCluster2TE(self, outputFileName, dCluster2ConsensusList):
        f = open(outputFileName, "w")
        lClusterNames = dCluster2ConsensusList.keys()
        lClusterNames.sort()
        for clusterName in lClusterNames:
            f.write("%s\t%s\n" % (clusterName, "\t".join(dCluster2ConsensusList[clusterName])))
        f.close()
    
    def writeClassifiedCluster2TE (self, lConsensusClusters):
        f = open(self._classifiedClusterFileName, "w")
        for iCluster in lConsensusClusters:
            f.write("%s\n" % iCluster.toString())
        f.close()
    
    def createConsensusClusterList(self, isClassifiedClusterFile, fileHandler):
        line = fileHandler.readline()
        lConsensusCluster = []
        while line :
            id = line.rstrip().split('\t')[0]
            if self._isTEclassifierClassif:
                iConsensusCluster = TEclassifierConsensusCluster(id)
            else:
                iConsensusCluster = ConsensusCluster(id)
            if not isClassifiedClusterFile:
                lConsensus = line.rstrip().split('\t')[1:]
                iConsensusCluster.setConsensusList(lConsensus)
                iConsensusCluster.findMainClassif()
            else:
                classif = line.rstrip().split('\t')[1]
                iConsensusCluster.setClassif(classif)
                lConsensus = line.rstrip().split('\t')[2:]
                iConsensusCluster.setConsensusList(lConsensus)
            lConsensusCluster.append(iConsensusCluster)
            line = fileHandler.readline()
        return lConsensusCluster
    
    def createClusterGroupList(self, lConsensusClusters):
        dGroupConsensusClusters = {}
        for iConsensusCluster in lConsensusClusters:
            classif = iConsensusCluster.getMainClassifWithoutCompleteness()
            if dGroupConsensusClusters.has_key(classif):
                dGroupConsensusClusters[classif].extend(iConsensusCluster.getConsensusList())
            else:
                dGroupConsensusClusters[classif] = iConsensusCluster.getConsensusList()
        for classif in dGroupConsensusClusters.keys():       
            dGroupConsensusClusters[classif].sort()
        return dGroupConsensusClusters
        
    def run(self):
        self.checkAttributes()
        if "1" in self._step:
            isBlastclustInputFile = True
            if not re.search("_blastclust.fa$", self._inputFileName):
                isBlastclustInputFile = False
                self._blastclustFileName = self.launchBlastclust()
            
            lHeaders = self.extractHeadersList()
            if self._clean and not isBlastclustInputFile:
                os.remove(self._blastclustFileName)
            
            dCluster2ConsensusList = self.headerList2Dict(lHeaders)
            self.writeCluster2TE(self._clusterFileName, dCluster2ConsensusList)
        
        lConsensusClusters = None
        if "2" in self._step:
            fileHandler = open(self._clusterFileName, "r")
            lConsensusClusters = self.createConsensusClusterList(False, fileHandler)
            fileHandler.close()
            self.writeClassifiedCluster2TE(lConsensusClusters)
            
        if "3" in self._step:
            fileHandler = open(self._classifiedClusterFileName, "r")
            if not lConsensusClusters:
                lConsensusClusters = self.createConsensusClusterList(True, fileHandler)
            fileHandler.close()
            dGroupConsensusClusters = self.createClusterGroupList(lConsensusClusters)
            self.writeCluster2TE(self._clusterGroupFileName, dGroupConsensusClusters)

    def _extractClusterNameAndConsensusName(self, header):
        lElements = header.split("_")
        clusterNb = int(lElements[0].split("Cluster")[1].split("Mb")[0])
        consensusName = "_".join(lElements[1:])
        return clusterNb, consensusName
    

if __name__ == "__main__":
    i = ManageConsensusClusters()
    i.setAttributesFromCmdLine()
    i.run()