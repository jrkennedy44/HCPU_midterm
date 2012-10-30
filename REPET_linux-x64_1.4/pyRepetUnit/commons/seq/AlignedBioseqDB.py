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


import sys
from pyRepetUnit.commons.seq.BioseqDB import BioseqDB
from pyRepetUnit.commons.seq.Bioseq import Bioseq
from pyRepetUnit.commons.coord.Align import Align
from pyRepetUnit.commons.coord.Range import Range
from pyRepet.util.Stat import Stat
from math import log


## Multiple Sequence Alignment Representation   
#   
#
class AlignedBioseqDB( BioseqDB ):
    
    def __init__( self, name="" ):
        BioseqDB.__init__( self, name )
        seqLength = self.getLength()
        if self.getSize() > 1:
            for bs in self.db[1:]:
                if bs.getLength() != seqLength:
                    print "ERROR: aligned sequences have different length"
                    
                    
    ## Get length of the alignment
    # 
    # @return length
    # @warning name before migration was 'length'
    #
    def getLength( self ):
        length = 0
        if self.db != []:
            length = self.db[0].getLength()
        return length
    
    
    ## Get the true length of a given sequence (without gaps)
    #
    # @param header string header of the sequence to analyze
    # @return length integer
    # @warning  name before migration was 'true_length'
    #
    def getSeqLengthWithoutGaps( self, header ):
        bs = self.fetch( header )
        count = 0
        for pos in xrange(0,len(bs.sequence)):
            if bs.sequence[pos] != "-":
                count += 1
        return count
    
    
    ## Record the occurrences of symbols (A, T, G, C, N, -, ...) at each site
    #
    # @return: list of dico whose keys are symbols and values are their occurrences
    #
    def getListOccPerSite( self ):
        lOccPerSite = []   # list of dictionaries, one per position on the sequence
        n = 0    # nb of sequences parsed from the input file
        firstSeq = True

        # for each sequence in the bank
        for bs in self.db:
            if bs.sequence == None:
                break
            n += 1

            # if it is the first to be parsed, create a dico at each site
            if firstSeq:
                for i in xrange(0,len(bs.sequence)):
                    lOccPerSite.append( {} )
                firstSeq = False

            # for each site, add its nucleotide
            for i in xrange(0,len(bs.sequence)):
                nuc = bs.sequence[i].upper()
                if lOccPerSite[i].has_key( nuc ):
                    lOccPerSite[i][nuc] += 1
                else:
                    lOccPerSite[i][nuc] = 1

        return lOccPerSite
    
    
    ## Make a consensus from the MSA
    #
    # @param minNbNt: minimum nb of nucleotides to edit a consensus
    # @param minPropNt: minimum proportion for the major nucleotide to be used, otherwise add 'N' (default=0.0)
    # @param verbose: level of information sent to stdout (default=0/1)
    # @return: consensus
    #
    def getConsensus( self, minNbNt, minPropNt=0.0, verbose=0 ):

        maxPropN = 0.40  # discard consensus if more than 40% of N's

        nbInSeq = self.getSize()
        if verbose > 0:
            print "nb of aligned sequences: %i" % ( nbInSeq ); sys.stdout.flush()
        if nbInSeq < 2:
            print "ERROR: can't make a consensus with less than 2 sequences"
            sys.exit(1)
        if minNbNt >= nbInSeq:
            minNbNt = nbInSeq - 1
            print "minNbNt=%i" % ( minNbNt )
        if minPropNt >= 1.0:
            print "ERROR: minPropNt=%.2f should be a proportion (below 1.0)" % ( minPropNt )
            sys.exit(1)

        lOccPerSite = self.getListOccPerSite()
        nbSites = len(lOccPerSite)
        if verbose > 0:
            print "nb of sites: %i" % ( nbSites ); sys.stdout.flush()

        seqConsensus = ""

        # for each site (i.e. each column of the MSA)
        nbRmvColumns = 0
        countSites = 0
        for dNt2Occ in lOccPerSite:
            countSites += 1
            if verbose > 1:
                print "site %s / %i" % ( str(countSites).zfill( len(str(nbSites)) ),
                                         nbSites )
                sys.stdout.flush()
            occMaxNt = 0   # occurrences of the predominant nucleotide at this site
            lBestNt = []
            nbNt = 0   # total nb of A, T, G and C (no gap)

            # for each distinct symbol at this site (A, T, G, C, N, -,...)
            for j in dNt2Occ.keys():
                if j != "-":
                    nbNt += dNt2Occ[j]
                    if verbose > 1:
                        print "%s: %i" % ( j, dNt2Occ[j] )
                    if dNt2Occ[j] > occMaxNt:
                        occMaxNt = dNt2Occ[j]
                        lBestNt = [ j ]
                    elif dNt2Occ[j] == occMaxNt:
                        lBestNt.append( j )
            if nbNt == 0:   # some MSA programs can remove some sequences (e.g. Muscle after Recon) or when using Refalign (non-alignable TE fragments put together via a refseq)
                nbRmvColumns += 1

            if len( lBestNt ) >= 1:
                bestNt = lBestNt[0]
            
            # if the predominant nucleotide occurs in less than x% of the sequences, put a "N"
            if minPropNt > 0.0 and nbNt != 0 and float(occMaxNt)/float(nbNt) < minPropNt:
                bestNt = "N"

            if int(nbNt) >= int(minNbNt):
                seqConsensus += bestNt
                if verbose > 1:
                    print "-> %s" % ( bestNt )

        if nbRmvColumns:
            print "WARNING: %i sites were removed (%.2f%%)" % ( nbRmvColumns, nbRmvColumns / float(nbSites) * 100 )
            sys.stdout.flush()
            if seqConsensus == "":
                print "WARNING: no consensus can be built (no sequence left)"
                return

        propN = seqConsensus.count("N") / float(len(seqConsensus))
        if propN >= maxPropN:
            print "WARNING: no consensus can be built (%i%% of N's >= %i%%)" % ( propN * 100, maxPropN * 100 )
            return
        elif propN >= maxPropN * 0.5:
            print "WARNING: %i%% of N's" % ( propN * 100 )

        consensus = Bioseq()
        consensus.sequence = seqConsensus
        consensus.header = "consensus=%s length=%i nbAlign=%i" % ( self.name, len(seqConsensus), self.getSize() )

        if verbose > 0:
       
            statEntropy = self.getEntropy( verbose - 1 )
            print "entropy: %s" % ( statEntropy.stringQuantiles() )
            sys.stdout.flush()

        return consensus
    
    
    ## Get the entropy of the whole multiple alignment (only for A, T, G and C)
    #
    # @param verbose level of verbosity
    #
    # @return statistics about the entropy of the MSA
    #
    def getEntropy( self, verbose=0 ):

        stats = Stat()

        # get the occurrences of symbols at each site
        lOccPerSite = self.getListOccPerSite()

        countSite = 0

        # for each site
        for dSymbol2Occ in lOccPerSite:
            countSite += 1

            # count the number of nucleotides (A, T, G and C, doesn't count gap '-')
            nbNt = 0
            dATGC2Occ = {}
            for base in ["A","T","G","C"]:
                dATGC2Occ[ base ] = 0.0
            for nt in dSymbol2Occ.keys():
                if nt != "-":
                    nbNt += dSymbol2Occ[ nt ]
                    checkedNt = self.getATGCNFromIUPAC( nt )
                    if checkedNt in ["A","T","G","C"] and dSymbol2Occ.has_key( checkedNt ):
                        dATGC2Occ[ checkedNt ] += 1 * dSymbol2Occ[ checkedNt ]
                    else:   # for 'N'
                        if dSymbol2Occ.has_key( checkedNt ):
                            dATGC2Occ[ "A" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "T" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "G" ] += 0.25 * dSymbol2Occ[ checkedNt ]
                            dATGC2Occ[ "C" ] += 0.25 * dSymbol2Occ[ checkedNt ]
            if verbose > 2:
                for base in dATGC2Occ.keys():
                    print "%s: %i" % ( base, dATGC2Occ[ base ] )

            # compute the entropy for the site
            entropySite = 0.0
            for nt in dATGC2Occ.keys():
                entropySite += self.computeEntropy( dATGC2Occ[ nt ], nbNt )
            if verbose > 1:
                print "site %i (%i nt): entropy = %.3f" % ( countSite, nbNt, entropySite )
            stats.add( entropySite )

        return stats
    
    
    ## Get A, T, G, C or N from an IUPAC letter
    #  IUPAC = ['A','T','G','C','U','R','Y','M','K','W','S','B','D','H','V','N']
    #
    # @return A, T, G, C or N
    #
    def getATGCNFromIUPAC( self, nt ):
        iBs = Bioseq()
        return iBs.getATGCNFromIUPAC( nt )
    
    
    ## Compute the entropy based on the occurrences of a certain nucleotide and the total number of nucleotides
    #
    def computeEntropy( self, nbOcc, nbNt ):
        if nbOcc == 0.0:
            return 0.0
        else:
            freq = nbOcc / float(nbNt)
            return - freq * log(freq) / log(2) 
        
        
    ## Save the multiple alignment as a matrix with '0' if gap, '1' otherwise
    #
    def saveAsBinaryMatrix( self, outFile ):
        outFileHandler = open( outFile, "w" )
        for bs in self.db:
            string = "%s" % ( bs.header )
            for nt in bs.sequence:
                if nt != "-":
                    string += "\t%i" % ( 1 )
                else:
                    string += "\t%i" % ( 0 )
            outFileHandler.write( "%s\n" % ( string ) )
        outFileHandler.close()
        
        
    ## Return a list of Align instances corresponding to the aligned regions (without gaps)
    #
    # @param query string header of the sequence considered as query
    # @param subject string header of the sequence considered as subject
    #
    def getAlignList( self, query, subject ):
        lAligns = []
        alignQ = self.fetch( query ).sequence
        alignS = self.fetch( subject ).sequence
        createNewAlign = True
        indexAlign = 0
        indexQ = 0
        indexS = 0
        while indexAlign < len(alignQ):
            if alignQ[ indexAlign ] != "-" and alignS[ indexAlign ] != "-":
                indexQ += 1
                indexS += 1
                if createNewAlign:
                    iAlign = Align( Range( query, indexQ, indexQ ),
                                    Range( subject, indexS, indexS ),
                                    0,
                                    int( alignQ[ indexAlign ] == alignS[ indexAlign ] ),
                                    int( alignQ[ indexAlign ] == alignS[ indexAlign ] ) )
                    lAligns.append( iAlign )
                    createNewAlign = False
                else:
                    lAligns[-1].range_query.end += 1
                    lAligns[-1].range_subject.end += 1
                    lAligns[-1].score += int( alignQ[ indexAlign ] == alignS[ indexAlign ] )
                    lAligns[-1].identity += int( alignQ[ indexAlign ] == alignS[ indexAlign ] )
            else:
                if not createNewAlign:
                    lAligns[-1].identity = 100 * lAligns[-1].identity / lAligns[-1].getLengthOnQuery()
                    createNewAlign = True
                if alignQ[ indexAlign ] != "-":
                    indexQ += 1
                elif alignS[ indexAlign ] != "-":
                    indexS += 1
            indexAlign += 1
        if not createNewAlign:
            lAligns[-1].identity = 100 * lAligns[-1].identity / lAligns[-1].getLengthOnQuery()
        return lAligns
    
    
    def removeGaps(self):
        for iBs in self.db:
            iBs.removeSymbol( "-" )
