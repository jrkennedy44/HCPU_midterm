import sys
from pyRepetUnit.commons.stat.Stat import Stat

class GiveInfoTEannotWriter(object):

    def __init__(self):
        self._dAllTErefseqs = { "sumCumulCoverage": 0,
                         "totalNbFragments": 0,
                         "totalNbFullLengthFragments": 0,
                         "totalNbCopies": 0,
                         "totalNbFullLengthCopies": 0,
                         "nbFamWithFullLengthFragments": 0,
                         "nbFamWithOneFullLengthFragment": 0,
                         "nbFamWithTwoFullLengthFragments": 0,
                         "nbFamWithThreeFullLengthFragments": 0,
                         "nbFamWithMoreThanThreeFullLengthFragments": 0,
                         "nbFamWithFullLengthCopies": 0,
                         "nbFamWithOneFullLengthCopy": 0,
                         "nbFamWithTwoFullLengthCopies": 0,
                         "nbFamWithThreeFullLengthCopies": 0,
                         "nbFamWithMoreThanThreeFullLengthCopies": 0,
                         "statsAllCopiesMedIdentity": Stat(),
                         "statsAllCopiesMedLengthPerc": Stat()
                         }
        
    def getAllTEsRefSeqDict(self):
        return self._dAllTErefseqs
        
    def getStatAsString( self, name, d ):
        """
        Return a string with all data properly formatted.
        """
        string = ""
        string += "%s" % name
        string += "\t%i" % d["maxLength"]
        string += "\t%i" % d["meanLength"]
        string += "\t%i" % d["cumulCoverage"]
        string += "\t%i" % d["nbFragments"]
        string += "\t%i" % d["nbFullLengthFragments"]
        string += "\t%i" % d["nbCopies"]
        string += "\t%i" % d["nbFullLengthCopies"]
        
        if d["statsIdentityPerChain"].getValuesNumber() != 0:
            string += "\t%.2f" % d["statsIdentityPerChain"].mean()
            string += "\t%.2f" % d["statsIdentityPerChain"].sd()
            string += "\t%.2f" % d["statsIdentityPerChain"].getMin()
            string += "\t%.2f" % d["statsIdentityPerChain"].quantile(0.25)
            string += "\t%.2f" % d["statsIdentityPerChain"].median()
            string += "\t%.2f" % d["statsIdentityPerChain"].quantile(0.75)
            string += "\t%.2f" % d["statsIdentityPerChain"].getMax()
        else:
            for i in range(0,7):
                string += "\tNA"
            
        if d["statsLengthPerChain"].getValuesNumber() != 0:
            string += "\t%.2f" % d["statsLengthPerChain"].mean()
            string += "\t%.2f" % d["statsLengthPerChain"].sd()
            string += "\t%i" % d["statsLengthPerChain"].getMin()
            string += "\t%.2f" % d["statsLengthPerChain"].quantile(0.25)
            string += "\t%.2f" % d["statsLengthPerChain"].median()
            string += "\t%.2f" % d["statsLengthPerChain"].quantile(0.75)
            string += "\t%i" % d["statsLengthPerChain"].getMax()
        else:
            for i in range(0,7):
                string += "\tNA"
                
        if d["statsLengthPerChainPerc"].getValuesNumber() != 0:
            string += "\t%.2f" % d["statsLengthPerChainPerc"].mean()
            string += "\t%.2f" % d["statsLengthPerChainPerc"].sd()
            string += "\t%.2f" % d["statsLengthPerChainPerc"].getMin()
            string += "\t%.2f" % d["statsLengthPerChainPerc"].quantile(0.25)
            string += "\t%.2f" % d["statsLengthPerChainPerc"].median()
            string += "\t%.2f" % d["statsLengthPerChainPerc"].quantile(0.75)
            string += "\t%.2f" % d["statsLengthPerChainPerc"].getMax()
        else:
            for i in range(0,7):
                string += "\tNA"
                
        return string
    
    def printStatsForOneTE(self, dOneTErefseq):
        print " max length: %i bp" % ( dOneTErefseq[ "maxLength" ] )
        print " mean length: %i bp" % ( dOneTErefseq[ "meanLength" ] )
        print " cumulative coverage: %i bp" % ( dOneTErefseq[ "cumulCoverage" ] )
        print " nb of fragments: %i" % ( dOneTErefseq[ "nbFragments" ] )
        print " nb full-length fragments: %i" % ( dOneTErefseq[ "nbFullLengthFragments" ] )
        print " nb of copies: %i" % ( dOneTErefseq[ "nbCopies" ] )
        if dOneTErefseq[ "nbCopies" ] != 0:
            print " nb full-length copies: %i" % ( dOneTErefseq[ "nbFullLengthCopies" ] )
            print " copy identity: %s" % ( dOneTErefseq[ "statsIdentityPerChain" ].string() )
            print " copy length: %s" % ( dOneTErefseq[ "statsLengthPerChain" ].string() )
    
    def addCalculsOfOneTE(self, dOneTErefseq):
        self._dAllTErefseqs[ "sumCumulCoverage" ] += dOneTErefseq[ "cumulCoverage" ]
        
        self._dAllTErefseqs[ "totalNbFragments" ] += dOneTErefseq[ "nbFragments" ]
        self._dAllTErefseqs[ "totalNbFullLengthFragments" ] += dOneTErefseq[ "nbFullLengthFragments" ]
        if dOneTErefseq[ "nbFullLengthFragments" ] > 0:
            self._dAllTErefseqs[ "nbFamWithFullLengthFragments" ] += 1
        if dOneTErefseq[ "nbFullLengthFragments" ] == 1:
            self._dAllTErefseqs[ "nbFamWithOneFullLengthFragment" ] += 1
        elif dOneTErefseq[ "nbFullLengthFragments" ] == 2:
            self._dAllTErefseqs[ "nbFamWithTwoFullLengthFragments" ] += 1
        elif dOneTErefseq[ "nbFullLengthFragments" ] == 3:
            self._dAllTErefseqs[ "nbFamWithThreeFullLengthFragments" ] += 1
        elif dOneTErefseq[ "nbFullLengthFragments" ] > 3:
            self._dAllTErefseqs[ "nbFamWithMoreThanThreeFullLengthFragments" ] += 1
        
        self._dAllTErefseqs[ "totalNbCopies" ] += dOneTErefseq[ "nbCopies" ]
        self._dAllTErefseqs[ "totalNbFullLengthCopies" ] += dOneTErefseq[ "nbFullLengthCopies" ]
        if dOneTErefseq[ "nbFullLengthCopies" ] > 0:
            self._dAllTErefseqs[ "nbFamWithFullLengthCopies" ] += 1
        if dOneTErefseq[ "nbFullLengthCopies" ] == 1:
            self._dAllTErefseqs[ "nbFamWithOneFullLengthCopy" ] += 1
        elif dOneTErefseq[ "nbFullLengthCopies" ] == 2:
            self._dAllTErefseqs[ "nbFamWithTwoFullLengthCopies" ] += 1
        elif dOneTErefseq[ "nbFullLengthCopies" ] == 3:
            self._dAllTErefseqs[ "nbFamWithThreeFullLengthCopies" ] += 1
        elif dOneTErefseq[ "nbFullLengthCopies" ] > 3:
            self._dAllTErefseqs[ "nbFamWithMoreThanThreeFullLengthCopies" ] += 1
        
        if dOneTErefseq[ "statsIdentityPerChain" ].getValuesNumber() != 0:
            self._dAllTErefseqs[ "statsAllCopiesMedIdentity" ].add( dOneTErefseq[ "statsIdentityPerChain" ].median() )
        
        if dOneTErefseq[ "statsLengthPerChainPerc" ].getValuesNumber() != 0:
            self._dAllTErefseqs[ "statsAllCopiesMedLengthPerc" ].add( dOneTErefseq[ "statsLengthPerChainPerc" ].median() )

    def printStatsForAllTEs(self, TEnb):
        print "(sum of cumulative coverages: %i bp)" % ( self._dAllTErefseqs[ "sumCumulCoverage" ] )
        print "total nb of TE fragments: %i" % ( self._dAllTErefseqs[ "totalNbFragments" ] )
        
        if self._dAllTErefseqs[ "totalNbFragments" ] != 0:
            
            print "total nb full-length fragments: %i (%.2f%%)" % \
            ( self._dAllTErefseqs[ "totalNbFullLengthFragments" ], \
              100*self._dAllTErefseqs[ "totalNbFullLengthFragments" ] / float(self._dAllTErefseqs[ "totalNbFragments" ]) )
            
            print "total nb of TE copies: %i" % ( self._dAllTErefseqs[ "totalNbCopies" ] )
            
            print "total nb full-length copies: %i (%.2f%%)" % \
            ( self._dAllTErefseqs[ "totalNbFullLengthCopies" ], \
              100*self._dAllTErefseqs[ "totalNbFullLengthCopies" ] / float(self._dAllTErefseqs[ "totalNbCopies" ]) )
            
            print "families with full-length fragments: %i (%.2f%%)" % \
            ( self._dAllTErefseqs[ "nbFamWithFullLengthFragments" ], \
              100*self._dAllTErefseqs[ "nbFamWithFullLengthFragments" ] / float(TEnb) )
            print " with only one full-length fragment: %i" % ( self._dAllTErefseqs[ "nbFamWithOneFullLengthFragment" ] )
            print " with only two full-length fragments: %i" % ( self._dAllTErefseqs[ "nbFamWithTwoFullLengthFragments" ] )
            print " with only three full-length fragments: %i" % ( self._dAllTErefseqs[ "nbFamWithThreeFullLengthFragments" ] )
            print " with more than three full-length fragments: %i" % ( self._dAllTErefseqs[ "nbFamWithMoreThanThreeFullLengthFragments" ] )
            
            print "families with full-length copies: %i (%.2f%%)" % \
            ( self._dAllTErefseqs[ "nbFamWithFullLengthCopies" ], \
              100*self._dAllTErefseqs[ "nbFamWithFullLengthCopies" ] / float(TEnb) )
            print " with only one full-length copy: %i" % ( self._dAllTErefseqs[ "nbFamWithOneFullLengthCopy" ] )
            print " with only two full-length copies: %i" % ( self._dAllTErefseqs[ "nbFamWithTwoFullLengthCopies" ] )
            print " with only three full-length copies: %i" % ( self._dAllTErefseqs[ "nbFamWithThreeFullLengthCopies" ] )
            print " with more than three full-length copies: %i" % ( self._dAllTErefseqs[ "nbFamWithMoreThanThreeFullLengthCopies" ] )
            
            print "mean of median identity among all families: %.2f +- %.2f" % \
            ( self._dAllTErefseqs[ "statsAllCopiesMedIdentity" ].mean(), \
              self._dAllTErefseqs[ "statsAllCopiesMedIdentity" ].sd() )
            
            print "mean of median length perc among all families: %.2f +- %.2f" % \
            ( self._dAllTErefseqs[ "statsAllCopiesMedLengthPerc" ].mean(), \
              self._dAllTErefseqs[ "statsAllCopiesMedLengthPerc" ].sd() )
            
    def printResume(self, lNamesTErefseq, lDistinctSubjects, totalCumulCoverage, genomeLength):
            print "nb of TE reference sequences: %i" % len(lNamesTErefseq)
            print "nb of distinct subjects: %i" % len(lDistinctSubjects)
            print "total cumulative coverage: %i bp" % totalCumulCoverage
            print "TE content: %.2f%%" % ( 100 * totalCumulCoverage / float(genomeLength) )
            print "processing the %i TE families..." % len(lNamesTErefseq)
            sys.stdout.flush()
            