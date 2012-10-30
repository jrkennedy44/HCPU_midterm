import re

class ConsensusCluster(object):
    
    def __init__(self, id = "", lConsensus = [], classif = ""):
        self._id = id
        self._lConsensus = lConsensus
        self._classif = classif
        self._lClassif = []
        
    def __eq__(self, o):
        return self._id == o._id and self.getSortedConsensusList() == o.getSortedConsensusList() \
                and self._classif == o._classif and self._lClassif == o._lClassif
        
    def getMainClassif(self):
        return self._classif

    def getMainClassifWithoutCompleteness(self):
        return self._classif.replace("-incomp","").replace("-comp","")
    
    def getConsensusList(self):
        return self._lConsensus
        
    def getSortedConsensusList(self):
        return sorted(self._lConsensus)
    
    def getClassifList(self):
        return self._lClassif
    
    def setConsensusList(self, lConsensus):
        self._lConsensus = lConsensus
        
    def setClassif(self, classif):
        self._classif = classif
    
    def toString (self):
        lAttributes = [self._id, self._classif]
        lAttributes.extend(self._lConsensus)
        stringConsenusCluster = "\t".join(lAttributes)
        return stringConsenusCluster 

    def findMainClassif(self):
        self.createClassifInstancesAndCountClassifOccurrences()
        self._classif = "noCat"
        if len(self._lClassif) > 0:
            if len(self._lClassif) == 1:
                self._classif = str(self._lClassif[0])
            else:
                isEqual = False
                iMainClassif = self._lClassif[0]
                for iClassif in self._lClassif[1:]:
                    if iClassif.getOccurrencesNb() == iMainClassif.getOccurrencesNb():
                        isEqual = True
                    elif iClassif.getOccurrencesNb() > iMainClassif.getOccurrencesNb():
                        isEqual = False
                        iMainClassif = iClassif
                if isEqual:
                    self._classif = "confused"
                else:
                    self._classif = "%s_confused" % str(iMainClassif)
    
    def createClassifInstancesAndCountClassifOccurrences(self):
        for consensus in self._lConsensus:
            consensusClassif = consensus.split("_CLASSIF_")[1]
            lItems = consensusClassif.split("_")
            isChimeric = self._removeChimericItemIfExists(lItems)
            if len(lItems) == 1:
                code, completeness, isConfused = self._findClassifDetailsIfOnlyOneClassif(lItems)
            if len(lItems) == 2:
                code, completeness, isConfused = self._findClassifDetailsIfTwoClassifs(lItems)
            isClassifAlreadyCreated = False
            for iClassif in self._lClassif:
                if iClassif.getCode() == code and iClassif.getIsChimeric() == isChimeric:
                    iClassif.incremente()
                    if completeness == "comp":
                        iClassif.setCompleteness(completeness)
                    if isConfused:
                        iClassif.setIsConfused()
                    isClassifAlreadyCreated = True
                    break
            if not isClassifAlreadyCreated and not (code == "noCat" and not isChimeric):
                self._lClassif.append(Classif(code, isChimeric, completeness, isConfused))

    def _removeChimericItemIfExists(self, lItems):
        isChimeric = False
        if "chimeric" in lItems:
            isChimeric = True
            chimericIndex = lItems.index("chimeric")
            del lItems[chimericIndex]
        return isChimeric

    def _findClassifDetailsIfOnlyOneClassif(self, lItems):
        completeness = "NA"
        isConfused = False
        lClassifDetails = lItems[0].split("-")
        code = lClassifDetails[0]
        if "comp" in lClassifDetails:
            completeness = "comp"
        if "incomp" in lClassifDetails:
            completeness = "incomp"
        if "confused" in lClassifDetails:
            isConfused = True
        return code, completeness, isConfused

    def _findClassifDetailsIfTwoClassifs(self, lItems):
        completeness = "NA"
        isConfused = False
        lClassif1Details = lItems[0].split("-")
        lClassif2Details = lItems[1].split("-")
        code = "%s_%s" % (lClassif1Details[0], lClassif2Details[0])
        return code, completeness, isConfused

class Classif(object):
    
    def __init__(self, code = "", isChimeric = False, completeness = "NA", isConfused = False, occurrencesNb = 1):
        self._code = code
        self._isChimeric = isChimeric
        self._completeness = completeness
        self._isConfused = isConfused
        self._occurrencesNb = occurrencesNb
        
    def __eq__(self, o):
        return self._code == o._code and self._isChimeric == o._isChimeric and self._completeness == o._completeness \
                and self._isConfused == o._isConfused and self._occurrencesNb == o._occurrencesNb
                
    def __str__(self):
        classifWithDetails = self._code
        if self._completeness != "NA":
            classifWithDetails += "-%s" % self._completeness
#        if self._isConfused:
#            classifWithDetails += "-confused"
        if self._isChimeric:
            classifWithDetails += "_chimeric"
        return classifWithDetails
        
    def getCode(self):
        return self._code
    
    def getIsChimeric(self):
        return self._isChimeric
    
    def getCompleteness(self):
        return self._completeness
    
    def getOccurrencesNb(self):
        return self._occurrencesNb
    
    def setCompleteness(self, completeness):
        self._completeness = completeness
        
    def setIsConfused(self):
        self._isConfused = True
        
#    def isEquivalentTo(self, o):
#        return self._code == o._code and self._isChimeric == o._isChimeric
    
    def incremente(self):
        self._occurrencesNb += 1
    
class TEclassifierConsensusCluster(object):
    
    def __init__(self, id = "", lConsensus = [], classif = ""):
        self._id = id
        self._lConsensus = lConsensus
        self._classif = classif
        
    def __eq__(self, o):
        return self._id == o._id and self.getSortedConsensusList() == o.getSortedConsensusList() and self._classif == o._classif
        
    def getMainClassif(self):
        return self._classif
    
    def getMainClassifWithoutCompleteness(self):
        return self.getMainClassif()
    
    def getConsensusList(self):
        return self._lConsensus
        
    def getSortedConsensusList(self):
        return sorted(self._lConsensus)
    
    def setConsensusList(self, lConsensus):
        self._lConsensus = lConsensus
        
    def setClassif(self, classif):
        self._classif = classif
    
    def toString(self):
        lAttributes = [self._id, self._classif]
        lAttributes.extend(self._lConsensus)
        stringConsenusCluster = "\t".join(lAttributes)
        return stringConsenusCluster 
    
    def extractClassifFromConsensusName(self, consensus):
        if re.search('-', consensus.split('_')[-1]):
            classif = consensus.split('_')[-1].split('-')[1]
        else:
            classif = consensus.split('_')[-1]
        return classif

    def findMainClassif(self):
        self._classif = "noCat"
        s = set()
        for consensus in self._lConsensus:
            s.add(self.extractClassifFromConsensusName(consensus))
        s.discard("NoCat")
        if self._isMoreThanOneClassifOrConfusedInSet(s):
            self._classif = "confused"
        elif self._isOnlyOneClassifInSet(s):
            self._classif = s.pop()
            
    def _isMoreThanOneClassifOrConfusedInSet(self, s):
        return "confused" in s or len(s) > 1
    
    def _isOnlyOneClassifInSet(self, s):
        return len(s) == 1
        